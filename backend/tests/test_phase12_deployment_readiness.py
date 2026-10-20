import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.app import app
from backend.config import settings
from backend.security import get_secret_key
from scripts.backup import create_backup
from scripts.restore import restore_backup, calculate_sha256, verify_sqlite_integrity

client = TestClient(app)


def test_liveness_probe_and_security_headers():
    """Verify /health returns 200 and standard security headers."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "project" in data

    # Verify security headers injected by middleware
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in response.headers
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10


def test_readiness_probe_healthy():
    """Verify /health/ready returns connected DB and writable storage."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "degraded")
    assert data["components"]["database"]["status"] == "connected"
    assert data["components"]["storage"]["status"] == "writable"
    assert "ai_synthesis" in data["components"]


def test_readiness_probe_database_failure():
    """Verify /health/ready returns 503 when the database is unavailable."""
    from backend.database import get_db

    def mock_broken_get_db():
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("DB Connection Timeout")
        yield mock_session

    app.dependency_overrides[get_db] = mock_broken_get_db
    try:
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["components"]["database"]["status"] == "unavailable"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_readiness_probe_storage_failure():
    """Verify /health/ready returns 503 when storage directories cannot be written to."""
    with patch("builtins.open", side_effect=PermissionError("Permission denied: Read-only volume")):
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["components"]["storage"]["status"] == "unwritable"


def test_readiness_probe_degraded_ai_mode():
    """Verify /health/ready returns 200 with degraded status when GEMINI_API_KEY is not set."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["components"]["ai_synthesis"]["status"] == "degraded"


def test_production_secret_key_rejection():
    """Verify that insecure development keys are strictly rejected in production."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        # Test default insecure key
        with patch.object(settings, "SECRET_KEY", "change_this_to_a_secure_random_string_in_production"):
            with patch.object(settings, "JWT_SECRET_KEY", ""):
                with pytest.raises(ValueError, match="Insecure SECRET_KEY configured for production"):
                    get_secret_key()

        # Test short key (< 32 characters)
        with patch.object(settings, "SECRET_KEY", "short_secret_key"):
            with patch.object(settings, "JWT_SECRET_KEY", ""):
                with pytest.raises(ValueError, match="at least 32 characters"):
                    get_secret_key()

        # Test strong 64-char production key
        strong_key = "a" * 64
        with patch.object(settings, "SECRET_KEY", strong_key):
            with patch.object(settings, "JWT_SECRET_KEY", strong_key):
                assert get_secret_key() == strong_key


def test_backup_and_restore_cycle():
    """Verify scripts/backup.py and scripts/restore.py execute cleanly and maintain integrity."""
    temp_dir = tempfile.mkdtemp(prefix="lexora_test_unit_backup_")
    try:
        backup_dir = os.path.join(temp_dir, "backups")
        restore_dir = os.path.join(temp_dir, "restore")
        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(restore_dir, exist_ok=True)

        # 1. Create backup
        backup_path = create_backup(output_dir=backup_dir)
        assert os.path.exists(backup_path)
        sha256_hash = calculate_sha256(backup_path)
        assert len(sha256_hash) == 64

        # 2. Verify checksum
        assert calculate_sha256(backup_path) == sha256_hash
        assert calculate_sha256(backup_path) != "0" * 64

        # 3. Restore to target directory
        restored_db = os.path.join(restore_dir, "restored.db")
        restored_storage = os.path.join(restore_dir, "storage")
        res = restore_backup(
            archive_path=backup_path,
            target_db_path=restored_db,
            target_storage_dir=restored_storage,
            verify_checksum=True,
        )
        assert res is True
        assert os.path.exists(restored_db)
        assert verify_sqlite_integrity(restored_db) is True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
