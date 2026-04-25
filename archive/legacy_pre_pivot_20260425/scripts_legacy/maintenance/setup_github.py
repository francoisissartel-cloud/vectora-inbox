#!/usr/bin/env python3
"""
Configuration automatique GitHub via API
Usage: python scripts/maintenance/setup_github.py --token YOUR_GITHUB_TOKEN
"""
import argparse
import requests
import json

REPO_OWNER = "francoisissartel-cloud"
REPO_NAME = "vectora-inbox"

def setup_branch_protection(token, branch):
    """Configurer protection de branche"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches/{branch}/protection"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "required_status_checks": None,
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 1
        },
        "restrictions": None,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"   ✅ Branch protection configurée pour '{branch}'")
        return True
    else:
        print(f"   ❌ Erreur pour '{branch}': {response.status_code}")
        print(f"      {response.text}")
        return False

def create_label(token, name, color, description):
    """Créer un label"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/labels"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": name,
        "color": color.lstrip('#'),
        "description": description
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"   ✅ Label '{name}' créé")
        return True
    elif response.status_code == 422:
        print(f"   ⚠️  Label '{name}' existe déjà")
        return True
    else:
        print(f"   ❌ Erreur pour '{name}': {response.status_code}")
        return False

def main(token):
    print("=" * 60)
    print("Configuration GitHub - Vectora Inbox")
    print("=" * 60)
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    print()
    
    # 1. Branch Protection
    print("🔒 Configuration Branch Protection...")
    print("-" * 60)
    
    setup_branch_protection(token, "main")
    setup_branch_protection(token, "develop")
    
    print()
    
    # 2. Labels
    print("🏷️  Création des Labels...")
    print("-" * 60)
    
    labels = [
        ("feature", "#0E8A16", "New feature or enhancement"),
        ("bugfix", "#FFA500", "Bug fix (non-urgent)"),
        ("hotfix", "#D73A4A", "Critical bug fix (urgent)"),
        ("documentation", "#0075CA", "Documentation only changes"),
        ("refactoring", "#FBCA04", "Code refactoring (no functional change)"),
        ("configuration", "#BFD4F2", "Configuration changes (canonical, client config)"),
        ("infrastructure", "#5319E7", "Infrastructure changes (CloudFormation, IAM)"),
        ("needs-review", "#FBCA04", "Waiting for code review"),
        ("approved", "#0E8A16", "Approved and ready to merge"),
        ("blocked", "#D73A4A", "Blocked by dependencies or issues")
    ]
    
    for name, color, description in labels:
        create_label(token, name, color, description)
    
    print()
    print("=" * 60)
    print("✅ Configuration terminée!")
    print("=" * 60)
    print()
    print("📋 Prochaines étapes:")
    print("1. Vérifier sur GitHub: https://github.com/francoisissartel-cloud/vectora-inbox/settings/branches")
    print("2. Vérifier labels: https://github.com/francoisissartel-cloud/vectora-inbox/labels")
    print("3. Commit CODEOWNERS:")
    print("   git add .github/CODEOWNERS")
    print("   git commit -m 'chore: update CODEOWNERS'")
    print("   git push origin main")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Configure GitHub repository')
    parser.add_argument('--token', required=True, help='GitHub Personal Access Token')
    
    args = parser.parse_args()
    
    try:
        main(args.token)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        exit(1)
