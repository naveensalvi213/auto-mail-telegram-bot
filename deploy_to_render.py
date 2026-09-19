import os
import sys
import subprocess
import requests

def load_env(env_path=".env"):
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("🚀 Starting Automated GitHub & Render Deployment...")
    env = load_env()
    
    gh_token = env.get("GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    render_key = env.get("RENDER_API_KEY") or os.environ.get("RENDER_API_KEY")
    repo_name = env.get("GITHUB_REPO_NAME", "auto-mail-telegram-bot")

    if not gh_token:
        print("❌ Missing GITHUB_TOKEN in .env file.")
        sys.exit(1)

    gh_headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Auto-fetch GitHub username if not provided
    gh_user = env.get("GITHUB_USERNAME") or os.environ.get("GITHUB_USERNAME")
    if not gh_user:
        print("🔍 Fetching GitHub username from token...")
        user_resp = requests.get("https://api.github.com/user", headers=gh_headers)
        if user_resp.status_code == 200:
            gh_user = user_resp.json().get("login")
            print(f"✅ Authenticated as GitHub User: '{gh_user}'")
        else:
            print(f"❌ Failed to authenticate GitHub token: {user_resp.status_code} - {user_resp.text}")
            sys.exit(1)

    # 1. Create GitHub Repository via API
    print(f"📦 Creating GitHub repository '{repo_name}' for user '{gh_user}'...")
    create_repo_url = "https://api.github.com/user/repos"
    repo_resp = requests.post(create_repo_url, headers=gh_headers, json={
        "name": repo_name,
        "private": False,
        "description": "Auto Mail Telegram Outreach Bot"
    })

    if repo_resp.status_code in [201, 422]:  # 201 Created, 422 Already exists
        print(f"✅ GitHub repository '{repo_name}' ready.")
    else:
        print(f"⚠️ GitHub Repo response: {repo_resp.status_code} - {repo_resp.text}")

    # 2. Push repository to GitHub
    print("📤 Pushing code to GitHub...")
    remote_url = f"https://{gh_token}@github.com/{gh_user}/{repo_name}.git"
    
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], capture_output=True)
    
    push_res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
    if push_res.returncode == 0:
        print(f"✅ Code pushed to https://github.com/{gh_user}/{repo_name} successfully!")
    else:
        print(f"❌ Git push failed: {push_res.stderr}")
        sys.exit(1)

    # 3. Create Render Background Worker Service
    if not render_key:
        print("⚠️ RENDER_API_KEY not found in .env. Skipping Render auto-creation.")
        return

    print("🌐 Connecting to Render API...")
    render_headers = {
        "Authorization": f"Bearer {render_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Get Owner ID
    owners_resp = requests.get("https://api.render.com/v1/owners", headers=render_headers)
    if owners_resp.status_code != 200:
        print(f"❌ Render API authentication failed: {owners_resp.status_code} - {owners_resp.text}")
        sys.exit(1)

    owners = owners_resp.json()
    if not owners:
        print("❌ No Render owner found for this API key.")
        sys.exit(1)

    owner_id = owners[0]["owner"]["id"]
    print(f"✅ Render Owner ID retrieved: {owner_id}")

    # Create Background Worker Service
    print("🚀 Creating 24/7 Render Background Worker...")
    service_payload = {
        "type": "background_worker",
        "name": repo_name,
        "ownerId": owner_id,
        "repo": f"https://github.com/{gh_user}/{repo_name}",
        "autoDeploy": "yes",
        "branch": "main",
        "plan": "free",
        "serviceDetails": {
            "env": "python",
            "envSpecificDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python main.py"
            }
        }
    }

    create_svc_resp = requests.post("https://api.render.com/v1/services", headers=render_headers, json=service_payload)
    if create_svc_resp.status_code in [200, 201]:
        svc_data = create_svc_resp.json()
        svc_id = svc_data.get("service", {}).get("id", "N/A")
        print(f"🎉 RENDER BACKGROUND WORKER CREATED SUCCESSFULLY! (Service ID: {svc_id})")
        print("Your bot is now deployed and will run 24/7 on Render!")
    else:
        print(f"⚠️ Render Service Creation response: {create_svc_resp.status_code} - {create_svc_resp.text}")

if __name__ == "__main__":
    main()
