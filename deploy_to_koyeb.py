import os
import sys
import subprocess
import requests

def load_env(env_path=".env"):
    """Loads environment variables from .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars


def deploy_to_koyeb():
    """
    Automated deployment script for Koyeb (koyeb.com).
    Koyeb Free Tier supports outbound SMTP on ports 465 & 587 24/7 without credit card.
    Bypasses Render's [Errno 101] Network is unreachable outbound SMTP firewall block.
    """
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("🚀 Starting Automated GitHub & Koyeb 24/7 Deployment...")
    env = load_env()

    gh_token = env.get("GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    koyeb_token = (
        env.get("KOYEB_API_TOKEN") or
        env.get("KOYEB_TOKEN") or
        os.environ.get("KOYEB_API_TOKEN") or
        os.environ.get("KOYEB_TOKEN")
    )
    repo_name = env.get("GITHUB_REPO_NAME", "auto-mail-telegram-bot")
    bot_token = env.get("BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

    if not gh_token:
        print("❌ Missing GITHUB_TOKEN in .env file.")
        sys.exit(1)

    gh_headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Fetch GitHub username
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

    # 2. Create GitHub Repository via API
    print(f"📦 Creating/verifying GitHub repository '{repo_name}' for user '{gh_user}'...")
    create_repo_url = "https://api.github.com/user/repos"
    repo_resp = requests.post(create_repo_url, headers=gh_headers, json={
        "name": repo_name,
        "private": False,
        "description": "Auto Mail Telegram Outreach Bot"
    })

    if repo_resp.status_code in [201, 422]:
        print(f"✅ GitHub repository '{repo_name}' ready.")
    else:
        print(f"⚠️ GitHub Repo response: {repo_resp.status_code} - {repo_resp.text}")

    # 3. Push repository to GitHub
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

    # 4. Create Koyeb Deployment
    if not koyeb_token:
        print("\n" + "=" * 60)
        print("⚠️ KOYEB_API_TOKEN not found in .env file.")
        print("💡 Koyeb provides 24/7 FREE hosting with outbound SMTP (ports 465 & 587) enabled without credit card!")
        print("\nTo automate Koyeb deployment with 1 command:")
        print("1. Get a free API token at: https://app.koyeb.com/user/settings/api")
        print("2. Add `KOYEB_API_TOKEN=your_token` to your .env file.")
        print("3. Re-run `python deploy_to_koyeb.py`.")
        print("\nAlternatively, deploy manually via Koyeb Web Dashboard:")
        print("1. Visit https://app.koyeb.com/apps/deploy")
        print(f"2. Select GitHub repository: {gh_user}/{repo_name}")
        print("3. Choose 'Buildpack' builder and instance type 'Nano'.")
        print(f"4. Add Environment Variable: BOT_TOKEN={bot_token or '<your_bot_token>'}")
        print("5. Click 'Deploy' - Your bot is live with outbound email capability 24/7!")
        print("=" * 60 + "\n")
        return

    print("🌐 Connecting to Koyeb API...")
    koyeb_headers = {
        "Authorization": f"Bearer {koyeb_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    prof_resp = requests.get("https://app.koyeb.com/v1/account/profile", headers=koyeb_headers)
    if prof_resp.status_code != 200:
        print(f"❌ Koyeb API authentication failed: {prof_resp.status_code} - {prof_resp.text}")
        sys.exit(1)

    print("✅ Authenticated with Koyeb API successfully!")

    app_name = "auto-mail-bot"
    apps_resp = requests.get("https://app.koyeb.com/v1/apps", headers=koyeb_headers)
    app_id = None
    if apps_resp.status_code == 200:
        apps = apps_resp.json().get("apps", [])
        for a in apps:
            if a.get("name") == app_name:
                app_id = a.get("id")
                break

    if not app_id:
        print(f"📦 Creating Koyeb App '{app_name}'...")
        create_app_resp = requests.post("https://app.koyeb.com/v1/apps", headers=koyeb_headers, json={"name": app_name})
        if create_app_resp.status_code in [200, 201]:
            app_id = create_app_resp.json().get("app", {}).get("id")
            print(f"✅ Koyeb App created successfully (ID: {app_id})")
        else:
            print(f"❌ Failed to create Koyeb App: {create_app_resp.status_code} - {create_app_resp.text}")
            sys.exit(1)
    else:
        print(f"✅ Koyeb App '{app_name}' exists (ID: {app_id})")

    print("🚀 Configuring 24/7 Koyeb Service (with outbound SMTP enabled)...")

    env_vars_list = []
    if bot_token:
        env_vars_list.append({"scopes": ["*"], "key": "BOT_TOKEN", "value": bot_token})

    svc_definition = {
        "name": "auto-mail-worker",
        "git": {
            "repository": f"github.com/{gh_user}/{repo_name}",
            "branch": "main",
            "builder": "buildpack"
        },
        "instance_types": [
            { "type": "nano" }
        ],
        "scalings": [
            { "min": 1, "max": 1 }
        ],
        "env": env_vars_list
    }

    svcs_resp = requests.get(f"https://app.koyeb.com/v1/services?app_id={app_id}", headers=koyeb_headers)
    svc_id = None
    if svcs_resp.status_code == 200:
        services = svcs_resp.json().get("services", [])
        for s in services:
            if s.get("name") == "auto-mail-worker":
                svc_id = s.get("id")
                break

    if svc_id:
        print(f"🔄 Updating existing Koyeb service (ID: {svc_id})...")
        update_resp = requests.patch(f"https://app.koyeb.com/v1/services/{svc_id}", headers=koyeb_headers, json={"definition": svc_definition})
        if update_resp.status_code in [200, 201]:
            print("🎉 KOYEB SERVICE UPDATED & REDEPLOYED SUCCESSFULLY!")
        else:
            print(f"⚠️ Koyeb Service update response: {update_resp.status_code} - {update_resp.text}")
    else:
        print("🚀 Deploying new Koyeb service...")
        create_svc_resp = requests.post("https://app.koyeb.com/v1/services", headers=koyeb_headers, json={
            "app_id": app_id,
            "definition": svc_definition
        })
        if create_svc_resp.status_code in [200, 201]:
            new_id = create_svc_resp.json().get("service", {}).get("id", "N/A")
            print(f"🎉 KOYEB SERVICE CREATED SUCCESSFULLY! (Service ID: {new_id})")
        else:
            print(f"⚠️ Koyeb Service Creation response: {create_svc_resp.status_code} - {create_svc_resp.text}")

    print("\n✅ Deployment complete! Your bot is live on Koyeb with 24/7 SMTP outbound capabilities.")


if __name__ == "__main__":
    deploy_to_koyeb()
