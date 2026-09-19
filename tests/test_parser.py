import io
import json
import pytest
import pandas as pd
from utils.parser import validate_email, parse_lead_file


def test_validate_email():
    assert validate_email("user@example.com") is True
    assert validate_email("john.doe+test@sub.domain.co.uk") is True
    assert validate_email("tech_hub123@domain.org") is True

    assert validate_email("invalid") is False
    assert validate_email("user@") is False
    assert validate_email("@domain.com") is False
    assert validate_email("user@domain") is False
    assert validate_email("") is False
    assert validate_email(None) is False
    assert validate_email(12345) is False


def test_parse_csv_exact_and_case_varying_headers(tmp_path):
    # CSV 1: Title Case headers
    csv_1 = tmp_path / "leads_1.csv"
    csv_1.write_text("Channel Name,Primary Email\nTech Hub,tech@example.com\nDesign Pro,design@example.com", encoding="utf-8")

    res_1 = parse_lead_file(str(csv_1), "leads_1.csv")
    assert len(res_1) == 2
    assert res_1[0] == {"channel_name": "Tech Hub", "primary_email": "tech@example.com"}
    assert res_1[1] == {"channel_name": "Design Pro", "primary_email": "design@example.com"}

    # CSV 2: Uppercase snake_case headers with whitespace
    csv_2 = tmp_path / "leads_2.csv"
    csv_2.write_text("CHANNEL_NAME , PRIMARY_EMAIL \n  Code Zone  , code@example.com ", encoding="utf-8")

    res_2 = parse_lead_file(str(csv_2), "leads_2.csv")
    assert len(res_2) == 1
    assert res_2[0] == {"channel_name": "Code Zone", "primary_email": "code@example.com"}

    # CSV 3: Alternate headers ("name", "mail")
    csv_3 = tmp_path / "leads_3.csv"
    csv_3.write_text("name,mail\nAlpha,alpha@example.com", encoding="utf-8")

    res_3 = parse_lead_file(str(csv_3), "leads_3.csv")
    assert len(res_3) == 1
    assert res_3[0] == {"channel_name": "Alpha", "primary_email": "alpha@example.com"}


def test_parse_excel_xlsx(tmp_path):
    excel_path = tmp_path / "leads.xlsx"
    df = pd.DataFrame([
        {"Channel Name": "Excel Channel", "Primary Email": "excel@example.com"},
        {"Channel Name": "Py World", "Primary Email": "python@example.com"}
    ])
    df.to_excel(excel_path, index=False)

    # Test path string
    res = parse_lead_file(str(excel_path), "leads.xlsx")
    assert len(res) == 2
    assert res[0] == {"channel_name": "Excel Channel", "primary_email": "excel@example.com"}
    assert res[1] == {"channel_name": "Py World", "primary_email": "python@example.com"}

    # Test bytes input
    with open(excel_path, "rb") as f:
        bytes_data = f.read()

    res_bytes = parse_lead_file(bytes_data, "leads.xlsx")
    assert len(res_bytes) == 2
    assert res_bytes[0] == {"channel_name": "Excel Channel", "primary_email": "excel@example.com"}


def test_parse_json_structures(tmp_path):
    # JSON 1: Array of objects
    json_1 = tmp_path / "leads_list.json"
    json_1.write_text(json.dumps([
        {"channel_name": "JSON Hub", "primary_email": "json@example.com"},
        {"channel_name": "Data Stream", "primary_email": "data@example.com"}
    ]), encoding="utf-8")

    res_1 = parse_lead_file(str(json_1), "leads_list.json")
    assert len(res_1) == 2
    assert res_1[0] == {"channel_name": "JSON Hub", "primary_email": "json@example.com"}

    # JSON 2: Dict structure with list under key "leads"
    json_2 = tmp_path / "leads_dict.json"
    json_2.write_text(json.dumps({
        "leads": [
            {"channel": "Nested Channel", "email": "nested@example.com"}
        ]
    }), encoding="utf-8")

    res_2 = parse_lead_file(str(json_2), "leads_dict.json")
    assert len(res_2) == 1
    assert res_2[0] == {"channel_name": "Nested Channel", "primary_email": "nested@example.com"}


def test_validation_and_skipping_invalid_emails(tmp_path):
    csv_file = tmp_path / "invalid_emails.csv"
    csv_file.write_text(
        "channel_name,email\n"
        "Valid One,valid@example.com\n"
        "Invalid One,not-an-email\n"
        "Invalid Two,user@domain\n"
        "Valid Two,valid2@example.com\n",
        encoding="utf-8"
    )

    res = parse_lead_file(str(csv_file), "invalid_emails.csv")
    assert len(res) == 2
    assert res[0]["primary_email"] == "valid@example.com"
    assert res[1]["primary_email"] == "valid2@example.com"


def test_fallback_channel_name_when_missing(tmp_path):
    # Case 1: No channel name column in CSV
    csv_file = tmp_path / "no_channel_col.csv"
    csv_file.write_text(
        "primary_email\n"
        "dev.team@company.org\n"
        "support@company.org\n",
        encoding="utf-8"
    )

    res = parse_lead_file(str(csv_file), "no_channel_col.csv")
    assert len(res) == 2
    assert res[0] == {"channel_name": "dev.team", "primary_email": "dev.team@company.org"}
    assert res[1] == {"channel_name": "support", "primary_email": "support@company.org"}

    # Case 2: Channel column present but row is empty
    csv_file_2 = tmp_path / "empty_channel_val.csv"
    csv_file_2.write_text(
        "channel_name,email\n"
        ",user123@example.com\n",
        encoding="utf-8"
    )

    res_2 = parse_lead_file(str(csv_file_2), "empty_channel_val.csv")
    assert len(res_2) == 1
    assert res_2[0] == {"channel_name": "user123", "primary_email": "user123@example.com"}


def test_deduplication(tmp_path):
    csv_file = tmp_path / "dups.csv"
    csv_file.write_text(
        "channel_name,email\n"
        "First,tech@example.com\n"
        "Second,TECH@EXAMPLE.COM\n"
        "Third,tech@example.com\n",
        encoding="utf-8"
    )

    res = parse_lead_file(str(csv_file), "dups.csv")
    assert len(res) == 1
    assert res[0] == {"channel_name": "First", "primary_email": "tech@example.com"}


def test_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        parse_lead_file("content", "leads.txt")
