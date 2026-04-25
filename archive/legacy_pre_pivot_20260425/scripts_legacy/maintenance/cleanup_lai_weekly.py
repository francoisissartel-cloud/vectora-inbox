#!/usr/bin/env python3
"""
Script de nettoyage lai_weekly - Repo + AWS S3
Usage: python scripts/maintenance/cleanup_lai_weekly.py [--execute]
"""

import argparse
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

AWS_PROFILE = "rag-lai-prod"
BACKUP_BUCKET = "vectora-inbox-backup-20260130"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def backup_local_archive():
    """Backup archive/ localement avant suppression."""
    archive_dir = Path("client-config-examples/archive")
    if not archive_dir.exists():
        log("Aucun dossier archive/ a backup", "SKIP")
        return True
    
    backup_dir = Path(f".backup/archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    log(f"Backup archive/ -> {backup_dir}")
    shutil.copytree(archive_dir, backup_dir / "archive")
    log("[OK] Backup local complete", "SUCCESS")
    return True

def cleanup_repo_local(dry_run=True):
    """Phase 1: Nettoyage repo local."""
    log("="*60)
    log("PHASE 1: NETTOYAGE REPO LOCAL")
    log("="*60)
    
    actions = []
    
    # 1. Deplacer v9 vers production
    v9_source = Path("client-config-examples/archive/lai_weekly_v9.yaml")
    v9_dest = Path("client-config-examples/production/lai_weekly_dev.yaml")
    if v9_source.exists():
        actions.append(("MOVE", v9_source, v9_dest))
    
    # 2. Supprimer archive/
    archive_dir = Path("client-config-examples/archive")
    if archive_dir.exists():
        actions.append(("DELETE_DIR", archive_dir, None))
    
    # 3. Supprimer fichiers legacy racine
    legacy_files = [
        "client-config-examples/lai_weekly.yaml",
        "client-config-examples/client_config_template.yaml",
        "client-config-examples/client_template_v2.yaml"
    ]
    for f in legacy_files:
        fp = Path(f)
        if fp.exists():
            actions.append(("DELETE_FILE", fp, None))
    
    # Afficher actions
    log(f"\nActions planifiees: {len(actions)}")
    for action_type, source, dest in actions:
        if action_type == "MOVE":
            log(f"  MOVE: {source} -> {dest}")
        elif action_type == "DELETE_DIR":
            log(f"  DELETE DIR: {source}")
        elif action_type == "DELETE_FILE":
            log(f"  DELETE FILE: {source}")
    
    if dry_run:
        log("\n[DRY-RUN] Aucune action executee", "INFO")
        return True
    
    # Executer actions
    log("\nExecution...")
    for action_type, source, dest in actions:
        try:
            if action_type == "MOVE":
                shutil.move(str(source), str(dest))
                log(f"[OK] Moved: {source.name}", "SUCCESS")
            elif action_type == "DELETE_DIR":
                shutil.rmtree(source)
                log(f"[OK] Deleted dir: {source.name}", "SUCCESS")
            elif action_type == "DELETE_FILE":
                source.unlink()
                log(f"[OK] Deleted file: {source.name}", "SUCCESS")
        except Exception as e:
            log(f"[ERROR] Erreur: {e}", "ERROR")
            return False
    
    log("\n[OK] Phase 1 completee", "SUCCESS")
    return True

def analyze_s3_size():
    """Phase 2: Analyser taille donnees S3."""
    log("="*60)
    log("PHASE 2: ANALYSE TAILLE S3 DEV")
    log("="*60)
    
    versions = ["lai_weekly_v3", "lai_weekly_v4", "lai_weekly_v5", 
                "lai_weekly_v6", "lai_weekly_v8"]
    
    total_size = 0
    for version in versions:
        cmd = [
            "aws", "s3", "ls",
            f"s3://vectora-inbox-data-dev/curated/{version}/",
            "--recursive", "--summarize",
            "--profile", AWS_PROFILE
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                # Parser output pour extraire taille
                for line in result.stdout.split('\n'):
                    if "Total Size:" in line:
                        size_str = line.split("Total Size:")[1].strip()
                        log(f"  {version}: {size_str}")
                        break
            else:
                log(f"  {version}: Erreur lecture", "WARNING")
        except Exception as e:
            log(f"  {version}: Exception {e}", "ERROR")
    
    log("\n[OK] Phase 2 completee", "SUCCESS")
    return True

def cleanup_s3_dev(dry_run=True):
    """Phase 3: Archivage et suppression S3 dev."""
    log("="*60)
    log("PHASE 3: NETTOYAGE S3 DEV")
    log("="*60)
    
    versions_to_archive = ["lai_weekly_v3", "lai_weekly_v4", "lai_weekly_v5", 
                           "lai_weekly_v6", "lai_weekly_v8"]
    
    log(f"\nVersions a archiver: {len(versions_to_archive)}")
    for v in versions_to_archive:
        log(f"  - {v}")
    
    if dry_run:
        log("\n[DRY-RUN] Aucune action executee", "INFO")
        return True
    
    # Archiver puis supprimer
    for version in versions_to_archive:
        source = f"s3://vectora-inbox-data-dev/curated/{version}/"
        dest = f"s3://{BACKUP_BUCKET}/archive/dev/{version}/"
        
        log(f"\nArchivage: {version}")
        
        # Sync vers backup
        cmd_sync = [
            "aws", "s3", "sync", source, dest,
            "--profile", AWS_PROFILE
        ]
        result = subprocess.run(cmd_sync, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"[ERROR] Erreur sync: {result.stderr}", "ERROR")
            return False
        
        log(f"[OK] Archive: {version}", "SUCCESS")
        
        # Supprimer original
        cmd_rm = [
            "aws", "s3", "rm", source,
            "--recursive", "--profile", AWS_PROFILE
        ]
        result = subprocess.run(cmd_rm, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"[ERROR] Erreur suppression: {result.stderr}", "ERROR")
            return False
        
        log(f"[OK] Supprime: {version}", "SUCCESS")
    
    log("\n[OK] Phase 3 completee", "SUCCESS")
    return True

def cleanup_invoke_scripts(dry_run=True):
    """Phase 4: Nettoyage scripts invoke."""
    log("="*60)
    log("PHASE 4: NETTOYAGE SCRIPTS INVOKE")
    log("="*60)
    
    files_to_delete = [
        "scripts/invoke/test_events/lai_weekly_v3.json",
        "scripts/invoke/test_events/lai_weekly_v7.json"
    ]
    
    log(f"\nFichiers a supprimer: {len(files_to_delete)}")
    for f in files_to_delete:
        log(f"  - {f}")
    
    if dry_run:
        log("\n[DRY-RUN] Aucune action executee", "INFO")
        return True
    
    for filepath in files_to_delete:
        fp = Path(filepath)
        if fp.exists():
            fp.unlink()
            log(f"[OK] Supprime: {fp.name}", "SUCCESS")
        else:
            log(f"[WARN] Fichier inexistant: {fp.name}", "WARNING")
    
    log("\n[OK] Phase 4 completee", "SUCCESS")
    return True

def main():
    parser = argparse.ArgumentParser(description="Nettoyage lai_weekly")
    parser.add_argument("--execute", action="store_true", 
                       help="Executer (sinon dry-run)")
    parser.add_argument("--phase", choices=["1", "2", "3", "4", "all"],
                       default="all", help="Phase a executer")
    parser.add_argument("--yes", action="store_true",
                       help="Auto-confirmer (skip prompt)")
    
    args = parser.parse_args()
    dry_run = not args.execute
    
    log("="*60)
    log("CLEANUP LAI_WEEKLY")
    log("="*60)
    log(f"Mode: {'EXECUTION' if args.execute else 'DRY-RUN'}")
    log(f"Phase: {args.phase}")
    log("")
    
    if not dry_run and not args.yes:
        confirm = input("[WARN] Mode EXECUTION active. Continuer? (yes/no): ")
        if confirm.lower() != "yes":
            log("Annule par utilisateur", "INFO")
            return
        
        # Backup avant execution
        log("\nBackup prealable...")
        if not backup_local_archive():
            log("[ERROR] Backup echoue - Arret", "ERROR")
            return
    
    # Executer phases
    phases = {
        "1": cleanup_repo_local,
        "2": analyze_s3_size,
        "3": cleanup_s3_dev,
        "4": cleanup_invoke_scripts
    }
    
    if args.phase == "all":
        for phase_num, phase_func in phases.items():
            if phase_num == "2":
                phase_func()  # Analyse toujours en lecture seule
            else:
                if not phase_func(dry_run):
                    log(f"[ERROR] Phase {phase_num} echouee", "ERROR")
                    return
    else:
        phase_func = phases[args.phase]
        if args.phase == "2":
            phase_func()
        else:
            phase_func(dry_run)
    
    log("\n" + "="*60)
    log("[OK] NETTOYAGE COMPLETE")
    log("="*60)

if __name__ == "__main__":
    main()
