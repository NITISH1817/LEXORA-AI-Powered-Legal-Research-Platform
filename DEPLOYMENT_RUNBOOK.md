# LEXORA — Phase 12 Controlled Pilot Deployment Runbook

> **Audience:** Legal engineering, devops administrators, and designated pilot coordinators.  
> **Classification:** Controlled Pilot Operational Runbook (Phase 12).  
> **Status:** Active & Verified.  
> **Mandatory Disclaimer:** LEXORA is an AI-powered legal intelligence assistant designed to accelerate research. It does **not** provide legal advice and is **not** a substitute for qualified legal counsel. All outputs, citations, and analyses must be reviewed by an admitted legal practitioner.

---

## 1. System Architecture & Concurrency Model

LEXORA operates as a secure, containerized, **single-instance** service designed specifically for controlled pilot deployments (5–20 designated legal researchers).

```
                      +-----------------------------+
                      |   Reverse Proxy / Ingress   |
                      |     (Nginx / Port 80/443)   |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
    +----------------------+                   +----------------------+
    |   Frontend Service   |                   |    Backend Service   |
    | (Vite SPA via Nginx) |                   |  (FastAPI / Uvicorn) |
    |      Port 80         |                   |      Port 8000       |
    +----------------------+                   +-----------+----------+
                                                           |
                    +--------------------+-----------------+--------------------+
                    |                    |                                      |
                    v                    v                                      v
         +--------------------+  +--------------------+               +--------------------+
         |   SQLite 3 (WAL)   |  |   ChromaDB Store   |               | Persistent Storage |
         |  (legal_intel.db)  |  |    (chroma_db/)    |               |  (storage/volumes) |
         +--------------------+  +--------------------+               +--------------------+
```

### Architectural Constraints & Invariants
1. **Single-Instance SQLite Database:** The primary relational store is SQLite 3 in Write-Ahead Logging (WAL) mode. **Do not run multiple backend container instances** against the same SQLite database file to avoid file lock contention (`database is locked`).
2. **Process-Local Ingestion Pipeline:** Document extraction, sentence chunking, and vector embedding execute within background worker tasks in the single backend container process.
3. **No External Message Broker Required:** For the pilot scale, local worker threads process uploaded PDFs/DOCX files directly. If pilot volume exceeds 20 concurrent document uploads, migration to PostgreSQL + Celery/Redis is documented in Section 11.
4. **Persistent Named Docker Volumes:** All stateful data is mounted via isolated, non-root Docker named volumes:
   - `lexora_db_data`: `/app/data` (stores `legal_intel.db` and SQLite WAL files).
   - `lexora_uploads_data`: `/app/storage/uploads` (uploaded source briefs/statutes).
   - `lexora_processed_data`: `/app/storage/processed` (extracted text & metadata).
   - `lexora_monitoring_data`: `/app/storage/monitoring` (redacted pilot telemetry).
   - `lexora_chroma_data`: `/app/chroma_db` (dense vector embeddings).
   - `lexora_backups_data`: `/app/backups` (automated backup archives).

---

## 2. Prerequisites & Resource Sizing

### Host Requirements
- **OS:** Linux (Ubuntu 22.04 LTS / Debian 12 recommended) or Windows Server 2022 with WSL2 / Docker Desktop.
- **Docker Engine:** Docker 24.0+ and Docker Compose v2.20+.
- **Python (for host utilities):** Python 3.11+ (if running backup/restore or acceptance scripts directly on host).
- **CPU:** 4 vCPUs recommended (supports concurrent sentence-transformer embeddings and hybrid retrieval).
- **RAM:** 8 GB RAM minimum (4 GB RAM allocated to backend for MiniLM model weights and ChromaDB in-memory index; 1 GB for Nginx/frontend; 3 GB headroom).
- **Storage:** 20 GB NVMe or SSD storage with periodic backup volume pruning.
- **Network:** Outbound HTTPS access to `generativelanguage.googleapis.com` (Gemini API) and `huggingface.co` (initial MiniLM model weights download, cached thereafter).

---

## 3. Secret and Environment Configuration

### Step 3.1: Generate Production Secrets
Never reuse development keys or placeholder values. In a clean shell, generate strong random cryptographic secrets:

```bash
# Generate a 64-character (32-byte) hex JWT secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3.2: Configure `.env`
Copy `.env.production.example` to `.env` in the project root:

```bash
cp .env.production.example .env
chmod 600 .env
```

Edit `.env` and configure each parameter:

```ini
# =================================================================
# LEXORA Production Environment Configuration — Controlled Pilot
# =================================================================

# Environment Mode: Setting to 'production' strictly enforces security controls
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="LEXORA Legal Intelligence"

# Security & Session Authentication
# MUST be at least 32 characters long. Insecure keys cause startup abort.
SECRET_KEY=YOUR_GENERATED_64_CHAR_HEX_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Provider Configuration
# Required for RAG synthesis. If missing/invalid, system operates safely in degraded mode.
GEMINI_API_KEY=AIzaSy...YOUR_VALID_GEMINI_API_KEY
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash

# Database Configuration (Single-instance SQLite with WAL mode)
DATABASE_URL=sqlite:///./data/legal_intel.db

# Storage Directories (Within Docker container volume mounts)
UPLOAD_DIR=/app/storage/uploads
PROCESSED_DIR=/app/storage/processed
PILOT_MONITORING_DIR=/app/storage/monitoring
CHROMA_PERSIST_DIR=/app/chroma_db

# CORS Configuration: Strict allowlist of authorized frontend origins
CORS_ORIGINS=https://lexora.yourfirm.com,http://localhost:5173

# Pilot Telemetry & Privacy Controls
PILOT_MONITORING_ENABLED=true
# Default FALSE: Raw queries are never logged without explicit consent
PILOT_MONITORING_LOG_QUERIES=false
# Automatic data retention purge window in days
PILOT_MONITORING_RETENTION_DAYS=30
```

> [!CAUTION]
> If `ENVIRONMENT=production` is set and `SECRET_KEY` is `< 32` characters or matches known development defaults (`change_this_to_a_secure_random_string_in_production`), the backend **refuses to start** and throws an explicit `ValueError`.

---

## 4. Build, Startup, and Health Verification

### Step 4.1: Build and Launch with Docker Compose

```bash
# 1. Build containers with clean cache
docker compose build --no-cache

# 2. Launch in detached mode with named persistent volumes
docker compose up -d

# 3. Follow container logs
docker compose logs -f backend
```

Expected startup log output:
```
==================================================
Starting LEXORA Legal Intelligence (Env: production)
Database: sqlite://***
CORS Allowed Origins: https://lexora.yourfirm.com
Storage Paths: uploads=/app/storage/uploads, processed=/app/storage/processed, monitoring=/app/storage/monitoring
Pilot Monitoring: enabled=True, log_queries=False, retention=30d
AI Synthesis Provider: READY (Gemini configured)
==================================================
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 4.2: Health Verification (Liveness & Readiness)

Check the container's operational health via the dedicated probes:

#### 1. Liveness Probe (`GET /health`)
Verifies the process is alive and responding:
```bash
curl -i http://localhost:8000/health
```
Expected response:
```http
HTTP/1.1 200 OK
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Request-ID: e627a44f-d00d-4074-b52e-ec04192d64f0
Content-Type: application/json

{"status":"ok","project":"LEXORA Legal Intelligence"}
```

#### 2. Readiness Probe (`GET /health/ready`)
Verifies database connectivity, storage volume writability, and AI synthesis provider status:
```bash
curl -i http://localhost:8000/health/ready
```
Expected response (Fully Operational):
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ready",
  "components": {
    "database": {"status": "connected"},
    "storage": {"status": "writable"},
    "ai_synthesis": {"status": "configured"}
  },
  "project": "LEXORA Legal Intelligence"
}
```

Degraded Mode (When `GEMINI_API_KEY` is not set):
- Returns HTTP 200 with `"status": "degraded"`.
- Hybrid search, case comparison, timeline extraction, and document processing remain fully operational.

Unhealthy State (Database offline or storage volume unwritable):
- Returns **HTTP 503 Service Unavailable** with error diagnostic. Ingress proxies will automatically route traffic away or alert operations.

---

## 5. Automated Acceptance Testing

Before inviting pilot participants, execute the 15-point automated acceptance suite:

```bash
# Execute acceptance test inside the backend container
docker compose exec backend python scripts/pilot_acceptance_test.py
```

All 15 verification steps must report `[PASSED]`:
1. Provision Pilot Account (Server-side RBAC)
2. Login & Protected Feature Access (JWT issue & verification)
3. Upload Supported Legal Document (PDF/DOCX validation)
4. Verify Document Processing & Extraction (Pipeline extraction)
5. Run Search & Verify Relevance (Hybrid BM25 + Vector)
6. Ask Research Question & Inspect Citations (Evidence grounding)
7. Verify Correct Abstention (Refuses unsupported queries)
8. Compare Cases & Inspect Evidence (Comparative matrix)
9. Inspect Timeline & Date Precision (Chronological ordering)
10. Submit Pilot Feedback & Flagging (Audit logging)
11. Verify User Monitoring Isolation & Deletion (Right to be Forgotten)
12. Confirm Persistence Across Restarts (Data volume survival)
13. Restore from Backup in Isolated Environment (Hot backup & SHA-256)
14. Verify Unauthorized Access Denied (401 & 403 enforcement)
15. Verify Safe Behavior When LLM Unavailable (Zero hallucination)

---

## 6. Backup and Scheduled Snapshot Procedures

Backups capture a point-in-time consistent state of:
- SQLite relational database (using SQLite Online Backup API — no locking or service interruption).
- User uploads (`storage/uploads`).
- Extracted documents (`storage/processed`).
- Redacted telemetry logs (`storage/monitoring`).
- Dense vector index (`chroma_db`).
- Archive manifest and SHA-256 integrity checksum.

### Step 6.1: Run Manual Backup
```bash
docker compose exec backend python scripts/backup.py \
  --db-path /app/data/legal_intel.db \
  --storage-dir /app/storage \
  --chroma-dir /app/chroma_db \
  --output-dir /app/backups
```

Output:
```
[LEXORA Backup] Successfully created backup: /app/backups/lexora_backup_20261020_121041.tar.gz
[LEXORA Backup] SHA-256 Checksum: 0b14a5c445bdd4606fbb47439fcd8f9df43d6c003fc25e3b5a956fa90761ef3f
```

### Step 6.2: Automated Nightly Cron Job
On the host system, add the following cron job (`crontab -e`) to take daily snapshots at 02:00 UTC and retain the last 14 days:

```cron
0 2 * * * docker compose -f /opt/lexora/docker-compose.yml exec -T backend python scripts/backup.py --output-dir /app/backups >> /var/log/lexora_backup.log 2>&1
0 3 * * * find /var/lib/docker/volumes/lexora_lexora_backups_data/_data -name "*.tar.gz*" -mtime +14 -delete
```

---

## 7. Restoration and Disaster Recovery

### Step 7.1: Pre-Restoration Verification
1. Verify the archive's SHA-256 checksum:
   ```bash
   sha256sum -c lexora_backup_20261020_121041.tar.gz.sha256
   ```
2. Stop the running backend service to prevent write race conditions:
   ```bash
   docker compose stop backend
   ```

### Step 7.2: Execute Restoration
Execute `scripts/restore.py` specifying the backup archive and target paths:

```bash
docker compose run --rm backend python scripts/restore.py \
  --archive /app/backups/lexora_backup_20261020_121041.tar.gz \
  --target-db /app/data/legal_intel.db \
  --target-storage /app/storage \
  --target-chroma /app/chroma_db
```

The restore script automatically:
1. Validates the SHA-256 archive checksum against `.sha256`.
2. Inspects the archive manifest.
3. Restores relational data, uploads, extracted files, and vector indices.
4. Executes `PRAGMA integrity_check;` on SQLite.
5. Verifies storage directory layout.

### Step 7.3: Restart Services & Verify Health
```bash
docker compose up -d backend
curl -f http://localhost:8000/health/ready
```

---

## 8. Rollback Procedure

If an application update or database migration introduces errors:

1. **Stop active services:**
   ```bash
   docker compose down
   ```
2. **Revert container images to the previous stable release tag:**
   ```yaml
   # docker-compose.yml
   image: lexora-backend:v11-stable
   ```
3. **Restore pre-upgrade database snapshot:**
   ```bash
   python scripts/restore.py --archive /path/to/pre_upgrade_backup.tar.gz
   ```
4. **Restart services:**
   ```bash
   docker compose up -d
   ```
5. **Execute smoke acceptance test:**
   ```bash
   python scripts/pilot_acceptance_test.py
   ```

---

## 9. Security, Privacy, and Incident Response

### Secret Rotation Procedures

#### 1. Rotating JWT Secret Key (`SECRET_KEY`)
If a JWT secret key is suspected of being compromised:
1. Generate a new 64-character secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `SECRET_KEY` in `.env`.
3. Restart the backend service:
   ```bash
   docker compose restart backend
   ```
4. **Effect:** All existing pilot user sessions are immediately invalidated. Users must re-authenticate with their credentials.

#### 2. Rotating Gemini AI Provider Key (`GEMINI_API_KEY`)
1. Generate a new API key in the Google AI Studio console.
2. Update `GEMINI_API_KEY` in `.env`.
3. Restart backend service:
   ```bash
   docker compose restart backend
   ```
4. Run readiness probe `curl http://localhost:8000/health/ready` to verify `ai_synthesis: {"status": "configured"}`.
5. Revoke the old key in Google Cloud / AI Studio console.

### Incident Response for Suspected Data Exposure
1. **Containment:** Stop external ingress immediately:
   ```bash
   docker compose stop frontend
   ```
2. **Audit Telemetry:** Inspect `/app/storage/monitoring/events.jsonl`. Verify that default redaction scrubbed emails, case numbers, and query terms.
3. **Inspect Logs:** Ensure no database credentials or full document bodies were emitted to logs (`docker compose logs backend | grep -i "password\|secret\|key"`).
4. **Purge User Data (Right to Be Forgotten):**
   Pilot users can delete their own telemetry records via `DELETE /api/evaluation/monitoring/my-events`. Administrators can purge all pilot telemetry older than the retention window:
   ```bash
   docker compose exec backend python -c "from backend.database import SessionLocal; from backend.services.monitoring_service import purge_expired_monitoring_records; db=SessionLocal(); print(purge_expired_monitoring_records(db)); db.close()"
   ```

---

## 10. Search Index Inconsistency Recovery

If the local ChromaDB vector store or BM25 index becomes desynchronized from SQLite (e.g. after container crash during indexing):

1. **Check consistency:**
   Inspect SQLite count:
   ```bash
   docker compose exec backend python -c "from backend.database import SessionLocal; from backend.models.document_intel import DocumentChunk; db=SessionLocal(); print('Indexed chunks in SQLite:', db.query(DocumentChunk).count()); db.close()"
   ```
2. **Re-index all documents:**
   Re-index all active documents from SQLite into ChromaDB:
   ```bash
   docker compose exec backend python scripts/reindex_all.py
   ```
3. Verify search relevance with `scripts/pilot_acceptance_test.py`.

---

## 11. Known Limitations & Phase 13+ Scaling Path

| Dimension | Current Pilot Implementation (Phase 12) | Phase 13+ Production Scale |
| :--- | :--- | :--- |
| **User Load** | 5–20 concurrent pilot attorneys | 100+ concurrent enterprise users |
| **Relational Database** | Single-instance SQLite 3 (WAL mode) | Managed PostgreSQL 15+ (Amazon RDS / Cloud SQL) |
| **Document Jobs** | Local process background threads | Distributed Celery / Redis task queue |
| **Vector Store** | Local ChromaDB persistent volume | Managed Qdrant / Pinecone / pgvector cluster |
| **High Availability** | Single container with rapid restart (<5s) | Multi-AZ Kubernetes cluster with auto-scaling |
| **Backup Storage** | Local volume + host cron rsync | Encrypted object storage (AWS S3 / GCS bucket) with versioning |

---

## 12. Operator Sign-Off Checklist

Before inviting pilot users to log in, the deployment operator must check off:

- [ ] `.env` created from `.env.production.example` with generated 64-char `SECRET_KEY`.
- [ ] `GEMINI_API_KEY` configured and tested with readiness probe.
- [ ] Docker named volumes confirmed persistent across container rebuilds.
- [ ] `GET /health` and `GET /health/ready` both return HTTP 200 OK.
- [ ] `python scripts/pilot_acceptance_test.py` passes 15/15 checks.
- [ ] Frontend displays visible pilot disclaimer banner and corpus scope notice.
- [ ] Backup script (`scripts/backup.py`) creates verified archive and SHA-256 digest.
- [ ] Initial test backup successfully restored and verified with `scripts/restore.py`.
