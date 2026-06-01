# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

AIGC Digital Watermarking System — a three-tier application for embedding and extracting watermarks in AI-generated images, point clouds, 3D meshes, and 3D Gaussian Splatting (3DGS).

## Architecture

```
Frontend (Vue 3 SPA)  --HTTP-->  Business Backend (FastAPI, port 8000)  --HTTP-->  Algorithm Backend(s)
```

- **Frontend**: Vue 3 + Vite + Element Plus + Tailwind CSS + Three.js (3D visualization) + gaussian-splats-3d (3DGS rendering)
- **Business Backend**: FastAPI (async), SQLAlchemy + aiomysql (async MySQL), Redis (session cache), httpx (async algo client)
- **Algorithm Backends**: Standalone services for image (8004), point cloud (8001), mesh (8002), 3DGS (8003) — current repo has mock implementations

Key architectural points:
- Business backend never calls ML models directly — it proxies via `AlgoClient` (httpx async HTTP)
- Auth uses Redis-backed UUID tokens (not JWT)
- Storage is local disk served via FastAPI `StaticFiles` mounts
- Each media type (image/pointcloud/mesh/gs) follows identical route pattern: `generate-watermarked` + `extract-watermark` POST endpoints
- Role system: `USER` < `ADMIN` < `SUPER_ADMIN` (see `ROLE_HIERARCHY` in `models/auth.py`)
- Auth dependency lives in `deps.py`: `get_current_user` (token verify) + `require_role(*roles)` factory

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Mock Algorithm Services
```bash
# Image algo service (port 8004)
cd mock_algo_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8004

# Point cloud algo service (port 8001)
cd mock_algo_point_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Mesh algo service (port 8002)
cd mock_algo_mesh_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# 3DGS algo service (port 8003)
cd mock_algo_gs_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# All backend tests (requires dependencies)
python -m unittest discover -s backend/tests -v

# Individual test file
python -m unittest backend/tests.test_image_flow -v
```

## Project Structure

```
backend/
  main.py              — FastAPI app, CORS, static mounts, router includes
  deps.py              — Shared FastAPI dependencies: get_current_user, require_role
  config/
    service_conf.py     — Algo service URLs, timeouts, API keys, storage roots (env-configurable)
    db_conf.py          — Async MySQL connection
    cache_conf.py       — Redis config
  routers/
    auth.py             — Register, login, verify-token, logout
    image.py            — Image watermark generate/extract
    pointcloud.py       — Point cloud watermark generate/extract
    mesh.py             — Mesh watermark generate/extract
    gs.py               — 3DGS watermark generate/extract
    record.py           — Task record list/detail (GET /api/v1/records)
    log.py              — Operation log list (GET /api/v1/logs)
    user.py             — User management: list, status/role update, reset-password (ADMIN+)
    profile.py          — Current user profile & change-password (GET/PUT /api/v1/profile)
  services/
    algo_client.py      — AlgoClient: httpx async wrapper calling algo services
  crud/
    auth.py             — User DB ops + Redis session management
    record.py           — WmTaskRecord CRUD (get_user_records, get_all_records, get_record_by_id)
    log.py              — OperationLog CRUD (get_operation_logs)
  models/
    auth.py             — SQLAlchemy User model; UserRole constants; ROLE_HIERARCHY dict
    record.py           — WmTaskRecord model (wm_task_record table)
    operation_log.py    — OperationLog model (operation log table)
  schemas/
    auth.py             — Auth + user management Pydantic schemas
    image.py, pointcloud.py, mesh.py, gs.py — Watermark request/response schemas
    record.py           — TaskRecordResponse / TaskRecordListResponse
    log.py              — OperationLogResponse / OperationLogListResponse
  utils/
    security.py         — Password hashing helpers (get_password_hash, verify_password)
  tests/                — unittest with IsolatedAsyncioTestCase + AsyncMock
  storage/              — Generated/uploaded images (gitignored)
  storage_pointcloud/   — Generated/uploaded point clouds (gitignored)
  storage_mesh/         — Generated/uploaded meshes (gitignored)
  storage_gs/           — Generated/uploaded 3DGS files (gitignored)

frontend/
  src/
    router/index.js     — Vue Router with auth guard (WHITE_LIST + token verify)
    utils/request.js    — Axios instance (auto Bearer token, 401 redirect)
    layouts/            — MainLayout with sidebar nav
    views/              — Page components per feature
      Dashboard.vue
      ImageEmbed.vue / ImageExtract.vue
      PointcloudEmbed.vue / PointcloudExtract.vue
      MeshEmbed.vue / MeshExtract.vue
      GsEmbed.vue / GsExtract.vue
      History.vue           — Unified watermark task history (calls /api/v1/records)
      OperationLog.vue      — Operation audit log (calls /api/v1/logs)
      UserManagement.vue    — User list, status/role/password management (ADMIN+)
      UserProfile.vue       — Current user profile & change password
      WatermarkRegistry.vue — Watermark registry placeholder/view
      Register.vue          — User self-registration page
      Login.vue
      Placeholder.vue       — Stub for unimplemented features

mock_algo_service/         — Mock image algo (port 8004)
mock_algo_point_service/   — Mock point cloud algo (port 8001)
mock_algo_mesh_service/    — Mock mesh algo (port 8002)
mock_algo_gs_service/      — Mock 3DGS algo (port 8003)
```

## Config & Environment

All backend configs are environment-overridable (see `backend/config/service_conf.py`):

| Variable | Default | Description |
|---|---|---|
| `ALGO_IMAGE_BASE_URL` | `http://127.0.0.1:8004` | Image algo service |
| `ALGO_POINTCLOUD_BASE_URL` | `http://127.0.0.1:8001` | Point cloud algo service |
| `ALGO_MESH_BASE_URL` | `http://127.0.0.1:8002` | Mesh algo service |
| `ALGO_GS_BASE_URL` | `http://127.0.0.1:8003` | 3DGS algo service |
| `ALGO_IMAGE_TIMEOUT_SECONDS` | `120` | Image algo call timeout (seconds) |
| `ALGO_POINTCLOUD_TIMEOUT_SECONDS` | `180` | Point cloud algo call timeout |
| `ALGO_MESH_TIMEOUT_SECONDS` | `180` | Mesh algo call timeout |
| `ALGO_GS_TIMEOUT_SECONDS` | `180` | 3DGS algo call timeout |
| `BIZ_IMAGE_STORAGE_ROOT` | `backend/storage` | Local image file storage |
| `BIZ_POINTCLOUD_STORAGE_ROOT` | `backend/storage_pointcloud` | Local point cloud storage |
| `BIZ_MESH_STORAGE_ROOT` | `backend/storage_mesh` | Local mesh storage |
| `BIZ_GS_STORAGE_ROOT` | `backend/storage_gs` | Local 3DGS storage |

## Important Patterns

- **AlgoClient** (`backend/services/algo_client.py`): All algo communication goes through this class. It raises `AlgoServiceError` with a `status_code`; routers catch it and re-raise as `HTTPException`.
- **Auth dependency** (`backend/deps.py`): Use `get_current_user` to validate tokens; use `require_role("ADMIN")` factory for role-gated endpoints.
- **Role system** (`backend/models/auth.py`): `ROLE_HIERARCHY = {USER: 0, ADMIN: 1, SUPER_ADMIN: 2}`. Higher level includes lower-level permissions.
- **Response format**: All endpoints return `{"code": 200, "message": "...", "data": {...}}`.
- **Media consistency**: Image, pointcloud, mesh, and 3DGS routers follow identical structure — adding a new media type means replicating `algo_client.py`, `routers/*.py`, `schemas/*.py` patterns.
- **Task records**: Every watermark generate/extract operation should write a `WmTaskRecord` row (via `crud/record.py`) for audit and history display.
- **No DB migrations**: SQLAlchemy models use `Base.metadata.create_all` on startup — no Alembic setup.
- **No production deployment**: No Docker, CI/CD, or nginx configs.
