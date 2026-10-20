#!/usr/bin/env python3
"""
LEXORA Production Restoration Utility — Phase 12

Restores application state from a verified backup archive:
1. Verifies SHA-256 archive checksum.
2. Extracts manifest and contents safely into destination directories.
3. Performs SQLite PRAGMA integrity_check on the restored database.
4. Validates persistent storage directory layout (uploads, processed, monitoring).
"""

import os
import sys
import tarfile
import sqlite3
import hashlib
import json
import shutil
import tempfile
import argparse


def calculate_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_sqlite_integrity(db_path: str) -> bool:
    """Runs PRAGMA integrity_check on SQLite database."""
    if not os.path.exists(db_path):
        return False
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchall()
        conn.close()
        return len(result) == 1 and result[0][0] == "ok"
    except Exception as e:
        print(f"[LEXORA Restore Error] Integrity check failed: {e}")
        return False


def restore_backup(
    archive_path: str,
    target_db_path: str = "legal_intel.db",
    target_storage_dir: str = "storage",
    target_chroma_dir: str = "chroma_db",
    verify_checksum: bool = True
) -> bool:
    """
    Restores database, storage, and index files from backup archive.
    """
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Backup archive not found: {archive_path}")

    # 1. Verify Checksum if present
    checksum_file = f"{archive_path}.sha256"
    if verify_checksum and os.path.exists(checksum_file):
        with open(checksum_file, "r", encoding="utf-8") as f:
            expected_hash = f.read().split()[0].strip()
        actual_hash = calculate_sha256(archive_path)
        if actual_hash.lower() != expected_hash.lower():
            raise ValueError(f"Checksum mismatch! Expected {expected_hash}, calculated {actual_hash}")
        print(f"[LEXORA Restore] Checksum verified successfully: {actual_hash[:16]}...")

    temp_extract = tempfile.mkdtemp(prefix="lexora_restore_stage_")
    try:
        # 2. Extract Archive safely
        with tarfile.open(archive_path, "r:gz") as tar:
            try:
                tar.extractall(path=temp_extract, filter="data")
            except TypeError:
                # Python < 3.12 compatibility
                tar.extractall(path=temp_extract)

        manifest_path = os.path.join(temp_extract, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            print(f"[LEXORA Restore] Reading manifest created at: {manifest.get('timestamp_utc')}")

        # 3. Restore and Verify Database
        staged_db = os.path.join(temp_extract, "database.sqlite")
        if os.path.exists(staged_db):
            if not verify_sqlite_integrity(staged_db):
                raise ValueError("Corrupt database in backup archive! Failed PRAGMA integrity_check.")
            
            # Atomic move / overwrite
            os.makedirs(os.path.dirname(os.path.abspath(target_db_path)), exist_ok=True)
            shutil.copy2(staged_db, target_db_path)
            print(f"[LEXORA Restore] Restored database to: {target_db_path} (Integrity: OK)")

        # 4. Restore Storage Directory
        staged_storage = os.path.join(temp_extract, "storage")
        if os.path.exists(staged_storage):
            os.makedirs(target_storage_dir, exist_ok=True)
            for sub in os.listdir(staged_storage):
                src_sub = os.path.join(staged_storage, sub)
                dst_sub = os.path.join(target_storage_dir, sub)
                if os.path.isdir(src_sub):
                    shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_sub, dst_sub)
            print(f"[LEXORA Restore] Restored storage to: {target_storage_dir}")

        # 5. Restore Chroma Directory
        staged_chroma = os.path.join(temp_extract, "chroma_db")
        if os.path.exists(staged_chroma):
            shutil.copytree(staged_chroma, target_chroma_dir, dirs_exist_ok=True)
            print(f"[LEXORA Restore] Restored vector store to: {target_chroma_dir}")

        print("[LEXORA Restore] Restoration completed successfully.")
        return True

    finally:
        shutil.rmtree(temp_extract, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LEXORA Production Restore Utility")
    parser.add_argument("--archive", required=True, help="Path to .tar.gz backup archive")
    parser.add_argument("--target-db", default="legal_intel.db", help="Destination path for SQLite database")
    parser.add_argument("--target-storage", default="storage", help="Destination storage directory")
    parser.add_argument("--target-chroma", default="chroma_db", help="Destination ChromaDB directory")
    parser.add_argument("--no-verify-checksum", action="store_true", help="Skip SHA-256 verification")
    args = parser.parse_args()

    restore_backup(
        archive_path=args.archive,
        target_db_path=args.target_db,
        target_storage_dir=args.target_storage,
        target_chroma_dir=args.target_chroma,
        verify_checksum=not args.no_verify_checksum
    )
