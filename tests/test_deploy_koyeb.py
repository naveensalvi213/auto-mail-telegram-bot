import os
import pytest
from unittest.mock import patch, MagicMock
from deploy_to_koyeb import load_env, deploy_to_koyeb

def test_load_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GITHUB_TOKEN=token123\nKOYEB_API_TOKEN=koyeb456\n# comment\n", encoding="utf-8")
    env_dict = load_env(str(env_file))
    assert env_dict["GITHUB_TOKEN"] == "token123"
    assert env_dict["KOYEB_API_TOKEN"] == "koyeb456"

@patch("deploy_to_koyeb.load_env")
@patch("requests.get")
@patch("requests.post")
@patch("requests.patch")
@patch("subprocess.run")
def test_deploy_to_koyeb_with_token(mock_subproc, mock_patch, mock_post, mock_get, mock_load):
    mock_load.return_value = {
        "GITHUB_TOKEN": "gh_test_token",
        "KOYEB_API_TOKEN": "koyeb_test_token",
        "GITHUB_REPO_NAME": "auto-mail-telegram-bot",
        "BOT_TOKEN": "123:ABC"
    }

    # GitHub username response
    res_gh_user = MagicMock()
    res_gh_user.status_code = 200
    res_gh_user.json.return_value = {"login": "testuser"}

    # GitHub repo creation response
    res_gh_repo = MagicMock()
    res_gh_repo.status_code = 201

    # Koyeb profile response
    res_koyeb_prof = MagicMock()
    res_koyeb_prof.status_code = 200

    # Koyeb apps list response
    res_koyeb_apps = MagicMock()
    res_koyeb_apps.status_code = 200
    res_koyeb_apps.json.return_value = {"apps": [{"id": "app_123", "name": "auto-mail-bot"}]}

    # Koyeb services list response
    res_koyeb_svcs = MagicMock()
    res_koyeb_svcs.status_code = 200
    res_koyeb_svcs.json.return_value = {"services": [{"id": "svc_123", "name": "auto-mail-worker"}]}

    # Koyeb patch response
    res_koyeb_patch = MagicMock()
    res_koyeb_patch.status_code = 200

    mock_get.side_effect = [res_gh_user, res_koyeb_prof, res_koyeb_apps, res_koyeb_svcs]
    mock_post.side_effect = [res_gh_repo]
    mock_patch.side_effect = [res_koyeb_patch]

    mock_subproc.return_value = MagicMock(returncode=0)

    deploy_to_koyeb()

    assert mock_subproc.call_count >= 3
    mock_patch.assert_called_once()
