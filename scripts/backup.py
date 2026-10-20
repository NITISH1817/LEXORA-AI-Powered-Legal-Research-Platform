#!/usr/bin/env python3
"""
LEXORA Automated Production Backup Utility — Phase 12

Performs an atomic, non-blocking backup of:
1. SQLite database using the SQLite Online Backup API (zero-lock / zero-corruption).
2. Document storage (uploads, processed pages cache, pilot monitoring records).
3. Local vector index (ChromaDB if present).

Outputs a gzip-compressed archive with SHA-256 checksum and JSON manifest.
"""

import os
import sys
import tarfile
import sqlite3
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
import argparse


def calculate_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_backup(
    db_path: str = "legal_intel.db",
    storage_dir: str = "storage",
    chroma_dir: str = "chroma_db",
    output_dir: str = "backups"
) -> str:
    """
    Executes consistent backup and returns path to archive file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_name = f"lexora_backup_{timestamp_str}.tar.gz"
    archive_path = os.path.join(output_dir, archive_name)

    temp_stage = tempfile.mkdtemp(prefix="lexora_backup_stage_")

    try:
        manifest = {
            "application": "LEXORA AI-Powered Legal Intelligence Platform",
            "backup_version": "1.0",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_db": db_path,
            "components": {}
        }

        # 1. Hot Backup of SQLite Database via Online Backup API
        if os.path.exists(db_path):
            staged_db = os.path.join(temp_stage, "database.sqlite")
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(staged_db)
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()

            manifest["components"]["database"] = {
                "original_path": db_path,
                "staged_name": "database.sqlite",
                "size_bytes": os.path.getsize(staged_db)
            }
        else:
            manifest["components"]["database"] = {"status": "missing_or_uninitialized"}

        # 2. Copy Storage Directory (uploads, processed, monitoring)
        if os.path.exists(storage_dir):
            staged_storage = os.path.join(temp_stage, "storage")
            shutil.copytree(storage_dir, staged_storage, dirs_exist_ok=True)
            files_count = sum(len(files) for _, _, files in os.walk(staged_storage))
            manifest["components"]["storage"] = {
                "original_path": storage_dir,
                "staged_name": "storage",
                "files_count": files_count
            }
        else:
            manifest["components"]["storage"] = {"status": "missing_or_empty"}

        # 3. Copy Chroma Vector Store (if present)
        if os.path.exists(chroma_dir):
            staged_chroma = os.path.join(temp_stage, "chroma_db")
            shutil.copytree(chroma_dir, staged_chroma, dirs_exist_ok=True)
            manifest["components"]["chroma_db"] = {
                "original_path": chroma_dir,
                "staged_name": "chroma_db"
            }

        # 4. Write manifest
        manifest_path = os.path.join(temp_stage, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 5. Build Compressed Tarball
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in os.listdir(temp_stage):
                tar.add(os.path.join(temp_stage, item), arcname=item)

        # 6. Compute Checksum
        checksum = calculate_sha256(archive_path)
        checksum_path = f"{archive_path}.sha256"
        with open(checksum_path, "w", encoding="utf-8") as f:
            f.write(f"{checksum}  {archive_name}\n")

        # Restrict permissions where supported
        try:
            os.chmod(archive_path, 0o600)
            os.chmod(checksum_path, 0o600)
        except (AttributeError, PermissionError):
            pass

        print(f"[LEXORA Backup] Successfully created backup: {archive_path}")
        print(f"[LEXORA Backup] SHA-256 Checksum: {checksum}")
        return archive_path

    finally:
        shutil.rmtree(temp_stage, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LEXORA Production Backup Utility")
    parser.add_argument("--db-path", default="legal_intel.db", help="Path to SQLite database")
    parser.add_argument("--storage-dir", default="storage", help="Path to storage directory")
    parser.add_argument("--chroma-dir", default="chroma_db", help="Path to ChromaDB directory")
    parser.add_argument("--output-dir", default="backups", help="Destination backup directory")
    args = parser.parse_args()

    create_backup(
        db_path=args.db_path,
        storage_dir=args.storage_dir,
        chroma_dir=args.chroma_dir,
        output_dir=args.output_dir
    )
