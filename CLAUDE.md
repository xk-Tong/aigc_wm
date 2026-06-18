# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIGC Digital Watermarking System — a three-tier application for embedding and extracting watermarks in AI-generated images, point clouds, 3D meshes, and 3D Gaussian Splatting (3DGS) assets.

## Architecture

```
Frontend (Vue 3 SPA)  --HTTP-->  Business Backend (FastAPI, port 8000)  --HTTP-->  Algorithm Backend(s) (ports 8001/8002/8003/8004)
```

- **Frontend**: Vue 3 + Vite + Element Plus + Tailwind CSS + Three.js (3D visualization)
- **Business Backend**: FastAPI (async), SQLAlchemy + aiomysql (async MySQL), Redis (session cache), httpx (async algo client)
- **Algorithm Backends**: Standalone services for image (8004), point cloud (8001), mesh (8002), 3DGS (8003) — current repo has mock implementations

Key architectural points:
- Business backend never calls ML models directly — it proxies via `AlgoClient` (httpx async HTTP)
- Auth uses Redis-backed UUID tokens (not JWT as PLAN.md suggests)
- Storage is local disk served via FastAPI `StaticFiles` mounts
- Each media type (image/pointcloud/mesh/gs) follows identical route pattern: `generate-watermarked` + `extract-watermark` POST endpoints
- Three user roles: USER, ADMIN, SUPER_ADMIN — role-based access enforced on both backend routes and frontend router

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
    record.py           — Watermark record CRUD (registry)
    log.py              — Operation log query
    user.py             — User management (admin)
    profile.py          — User profile (self-service)
  services/
    algo_client.py      — AlgoClient: httpx async wrapper calling algo services
  crud/
    auth.py             — User DB ops + Redis session management
  models/
    auth.py             — SQLAlchemy User model
    record.py           — WatermarkRecord model
    operation_log.py    — OperationLog model
  schemas/
    auth.py, image.py, pointcloud.py, mesh.py, gs.py, record.py, log.py — Pydantic request/response models
  tests/                — unittest with IsolatedAsyncioTestCase + AsyncMock
  storage/              — Generated/uploaded images (gitignored)
  storage_pointcloud/   — Generated/uploaded point clouds (gitignored)
  storage_mesh/         — Generated/uploaded meshes (gitignored)
  storage_gs/           — Generated/uploaded 3DGS assets (gitignored)

frontend/
  src/
    router/index.js     — Vue Router with auth guard (WHITE_LIST + token verify + role check)
    utils/request.js    — Axios instance (auto Bearer token, 401 redirect)
    layouts/            — MainLayout with sidebar nav
    views/              — Page components per feature
      Dashboard.vue
      ImageEmbed.vue / ImageExtract.vue
      PointcloudEmbed.vue / PointcloudExtract.vue
      MeshEmbed.vue / MeshExtract.vue
      GsEmbed.vue / GsExtract.vue
      History.vue              — User's watermark history
      WatermarkRegistry.vue    — Admin: watermark registry
      OperationLog.vue         — Admin: operation logs
      UserManagement.vue       — Admin: user management
      UserProfile.vue          — Self-service profile
      Login.vue / Register.vue
      Placeholder.vue          — Stub for Tracing, System Config

mock_algo_service/         — Mock image algo
mock_algo_point_service/   — Mock point cloud algo (synthetic PLY sphere)
mock_algo_mesh_service/    — Mock mesh algo (synthetic OBJ cube)
mock_algo_gs_service/      — Mock 3DGS algo
```

## Config & Environment

All backend configs are environment-overridable (see `backend/config/service_conf.py`):

| Variable | Default | Description |
|---|---|---|
| `ALGO_IMAGE_BASE_URL` | `http://127.0.0.1:8004` | Image algo service |
| `ALGO_IMAGE_TIMEOUT_SECONDS` | `120` | Image algo call timeout |
| `ALGO_IMAGE_API_KEY` | `""` | Image algo auth key |
| `BIZ_IMAGE_STORAGE_ROOT` | `backend/storage` | Image local file storage |
| `ALGO_POINTCLOUD_BASE_URL` | `http://127.0.0.1:8001` | Point cloud algo service |
| `ALGO_POINTCLOUD_TIMEOUT_SECONDS` | `180` | Point cloud algo call timeout |
| `ALGO_POINTCLOUD_API_KEY` | `""` | Point cloud algo auth key |
| `BIZ_POINTCLOUD_STORAGE_ROOT` | `backend/storage_pointcloud` | Point cloud local file storage |
| `ALGO_MESH_BASE_URL` | `http://127.0.0.1:8002` | Mesh algo service |
| `ALGO_MESH_TIMEOUT_SECONDS` | `180` | Mesh algo call timeout |
| `ALGO_MESH_API_KEY` | `""` | Mesh algo auth key |
| `BIZ_MESH_STORAGE_ROOT` | `backend/storage_mesh` | Mesh local file storage |
| `ALGO_GS_BASE_URL` | `http://127.0.0.1:8003` | 3DGS algo service |
| `ALGO_GS_TIMEOUT_SECONDS` | `180` | 3DGS algo call timeout |
| `ALGO_GS_API_KEY` | `""` | 3DGS algo auth key |
| `BIZ_GS_STORAGE_ROOT` | `backend/storage_gs` | 3DGS local file storage |

## Important Patterns

- **AlgoClient** (`backend/services/algo_client.py`): All algo communication goes through this class. It raises `AlgoServiceError` with a `status_code`; routers catch it and re-raise as `HTTPException`.
- **Auth dependency**: Router endpoints use `get_current_user` dependency to validate tokens. Admin-only endpoints additionally check the user's role (ADMIN or SUPER_ADMIN).
- **Response format**: All endpoints return `{"code": 200, "message": "ok", "data": {...}}`.
- **Media consistency**: Image, pointcloud, mesh, and 3DGS routers follow identical structure — adding a new media type means replicating `algo_client.py`, `routers/*.py`, `schemas/*.py` patterns.
- **Role-based access**: Three roles — USER (default), ADMIN, SUPER_ADMIN. Frontend router checks `meta.roles` to guard admin pages; backend endpoints use role checks in the auth dependency.
- **Unimplemented features**: Tracing (溯源验真) and System Config (系统配置) still use `Placeholder.vue`. All other features have real implementations.
- **No DB migrations**: SQLAlchemy models exist but no Alembic setup. Tables are created via `Base.metadata.create_all` on startup.
- **No production deployment**: No Docker, CI/CD, or nginx configs.
