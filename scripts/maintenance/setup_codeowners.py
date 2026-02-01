#!/usr/bin/env python3
"""
Script interactif pour configurer CODEOWNERS
Usage: python scripts/maintenance/setup_codeowners.py
"""

def main():
    print("=" * 60)
    print("Configuration CODEOWNERS - Vectora Inbox")
    print("=" * 60)
    print()
    
    print("Ce script va vous aider à configurer le fichier CODEOWNERS.")
    print()
    
    # Collecter les informations
    print("📝 Étape 1: Identifier les collaborateurs")
    print("-" * 60)
    print()
    
    lead_dev = input("Username GitHub du Lead Developer (ex: @francois-dupont): ").strip()
    if not lead_dev.startswith('@'):
        lead_dev = '@' + lead_dev
    
    print()
    dev_team = input("Usernames GitHub de l'équipe Dev (séparés par des espaces): ").strip()
    dev_team_list = [('@' + u if not u.startswith('@') else u) for u in dev_team.split()]
    
    print()
    data_team = input("Usernames GitHub de l'équipe Data (séparés par des espaces): ").strip()
    data_team_list = [('@' + u if not u.startswith('@') else u) for u in data_team.split()]
    
    # Générer le contenu CODEOWNERS
    print()
    print("=" * 60)
    print("📄 Contenu CODEOWNERS généré:")
    print("=" * 60)
    print()
    
    codeowners_content = f"""# Code Owners - Vectora Inbox

# Default owner (lead dev)
* {lead_dev}

# Q Context and Documentation
/.q-context/ {lead_dev}
/docs/ {lead_dev} {' '.join(dev_team_list)}

# Source Code
/src_v2/vectora_core/ {lead_dev} {' '.join(dev_team_list)}
/src_v2/lambdas/ {lead_dev} {' '.join(dev_team_list)}

# Infrastructure (admin only)
/infra/ {lead_dev}
/scripts/deploy/ {lead_dev}
/scripts/maintenance/ {lead_dev}

# Configuration
/canonical/ {lead_dev} {' '.join(data_team_list)}
/client-config-examples/ {lead_dev} {' '.join(data_team_list)}

# Critical Files (admin only)
/VERSION {lead_dev}
/.github/ {lead_dev}
/.gitignore {lead_dev}

# Tests
/tests/ {' '.join(dev_team_list)} {' '.join(data_team_list)}
"""
    
    print(codeowners_content)
    
    # Demander confirmation
    print()
    print("=" * 60)
    save = input("Voulez-vous sauvegarder ce contenu dans .github/CODEOWNERS? (yes/no): ").strip().lower()
    
    if save == 'yes':
        with open('.github/CODEOWNERS', 'w') as f:
            f.write(codeowners_content)
        
        print()
        print("✅ Fichier .github/CODEOWNERS créé avec succès!")
        print()
        print("📋 Prochaines étapes:")
        print("1. Vérifier le contenu: cat .github/CODEOWNERS")
        print("2. Commit: git add .github/CODEOWNERS")
        print("3. Commit: git commit -m 'chore: update CODEOWNERS'")
        print("4. Push: git push origin main")
    else:
        print()
        print("❌ Fichier non sauvegardé. Copiez le contenu ci-dessus manuellement.")
    
    print()
    print("=" * 60)
    print("Configuration terminée!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration annulée.")
        exit(0)
