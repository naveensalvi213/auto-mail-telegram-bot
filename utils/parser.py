import io
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Union

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

CHANNEL_NAME_COLS = ["channel name", "channel_name", "channel", "title", "name"]
EMAIL_COLS = ["primary email", "primary_email", "email", "e-mail", "mail"]


def validate_email(email_str: str) -> bool:
    """Uses regex to validate standard email format."""
    if not email_str or not isinstance(email_str, str):
        return False
    email_str = email_str.strip()
    return bool(EMAIL_REGEX.match(email_str))


def _find_column(df_columns, candidates: List[str]) -> Union[str, None]:
    """Finds matching column name case-insensitively and with space/underscore variations."""
    col_map = {}
    for col in df_columns:
        c_str = str(col).strip()
        c_lower = c_str.lower()
        col_map[c_lower] = col
        col_map[c_lower.replace('_', ' ')] = col
        col_map[c_lower.replace('-', ' ')] = col
        col_map[c_lower.replace(' ', '_')] = col

    for cand in candidates:
        cand_lower = cand.lower().strip()
        if cand_lower in col_map:
            return col_map[cand_lower]
        cand_space = cand_lower.replace('_', ' ').replace('-', ' ')
        if cand_space in col_map:
            return col_map[cand_space]
        cand_underscore = cand_lower.replace(' ', '_').replace('-', '_')
        if cand_underscore in col_map:
            return col_map[cand_underscore]

    return None


def parse_lead_file(file_source: Any, filename: str) -> List[Dict[str, str]]:
    """
    Accepts file path string or bytes buffer / file-like object, inspects extension (.xlsx, .xls, .csv, .json).
    Reads contents into pandas DataFrame / JSON dict.
    Finds channel name column matching case-insensitively: ["channel name", "channel_name", "channel", "title", "name"].
    Finds email column matching case-insensitively: ["primary email", "primary_email", "email", "e-mail", "mail"].
    If no explicit channel name column found, falls back to parsing string before `@` in email or "Creator".
    Cleans whitespace, ignores invalid emails, drops duplicate emails within the file.
    Returns list of dicts: [{"channel_name": "Tech Hub", "primary_email": "tech@example.com"}, ...]
    """
    import pandas as pd

    ext = Path(filename).suffix.lower()

    if isinstance(file_source, bytes):
        buffer = io.BytesIO(file_source)
    elif isinstance(file_source, (str, Path)):
        buffer = str(file_source)
    elif hasattr(file_source, "read"):
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        content = file_source.read()
        if isinstance(content, str):
            content = content.encode("utf-8")
        buffer = io.BytesIO(content)
    else:
        raise ValueError(f"Unsupported file source type: {type(file_source)}")

    df = None
    if ext == ".csv":
        try:
            df = pd.read_csv(buffer, dtype=str)
        except Exception:
            if isinstance(buffer, io.BytesIO):
                buffer.seek(0)
            df = pd.read_csv(buffer, dtype=str, encoding="latin1")
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(buffer, dtype=str)
    elif ext == ".json":
        if isinstance(buffer, io.BytesIO):
            buffer.seek(0)
            raw_data = json.load(buffer)
        elif isinstance(buffer, str):
            with open(buffer, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        else:
            raw_data = json.load(buffer)

        if isinstance(raw_data, list):
            df = pd.DataFrame(raw_data)
        elif isinstance(raw_data, dict):
            list_key = None
            for k, v in raw_data.items():
                if isinstance(v, list) and (len(v) == 0 or isinstance(v[0], dict)):
                    list_key = k
                    break
            if list_key is not None:
                df = pd.DataFrame(raw_data[list_key])
            else:
                df = pd.DataFrame(raw_data)
        else:
            raise ValueError(f"Unsupported JSON format: {type(raw_data)}")
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    if df is None or df.empty:
        return []

    email_col = _find_column(df.columns, EMAIL_COLS)
    if not email_col:
        return []

    channel_col = _find_column(df.columns, CHANNEL_NAME_COLS)

    results = []
    seen_emails = set()

    for _, row in df.iterrows():
        raw_email = row[email_col]
        if pd.isna(raw_email) or raw_email is None:
            continue
        email_clean = str(raw_email).strip()
        if not validate_email(email_clean):
            continue

        email_key = email_clean.lower()
        if email_key in seen_emails:
            continue
        seen_emails.add(email_key)

        channel_name = None
        if channel_col and channel_col in row:
            raw_channel = row[channel_col]
            if not pd.isna(raw_channel) and raw_channel is not None:
                c_str = str(raw_channel).strip()
                if c_str:
                    channel_name = c_str

        if not channel_name:
            local_part = email_clean.split("@")[0].strip()
            channel_name = local_part if local_part else "Creator"

        results.append({
            "channel_name": channel_name,
            "primary_email": email_clean
        })

    return results
