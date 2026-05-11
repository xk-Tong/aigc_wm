# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIGC Digital Watermarking System — a three-tier application for embedding and extracting watermarks in AI-generated images, point clouds, and 3D meshes.

## Architecture

```
Frontend (Vue 3 SPA)  --HTTP-->  Business Backend (FastAPI, port 8000)  --HTTP-->  Algorithm Backend(s) (ports 9001/9002/9003)
```

- **Frontend**: Vue 3 + Vite + Element Plus + Tailwind CSS + Three.js (3D visualization)
- **Business Backend**: FastAPI (async), SQLAlchemy + aiomysql (async MySQL), Redis (session cache), httpx (async algo client)
- **Algorithm Backends**: Standalone services for image (9001), point cloud (9002), mesh (9003) — current repo has mock implementations

Key architectural points:
- Business backend never calls ML models directly — it proxies via `AlgoClient` (httpx async HTTP)
- Auth uses Redis-backed UUID tokens (not JWT as PLAN.md suggests)
- Storage is local disk served via FastAPI `StaticFiles` mounts
- Each media type (image/pointcloud/mesh) follows identical route pattern: `generate-watermarked` + `extract-watermark` POST endpoints

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Mock Algorithm Services
```bash
# Image algo service (port 9001)
cd mock_algo_service
pip install -r requirements.txt
uvicorn main:app --reload --port 9001

# Point cloud algo service (port 9002)
cd mock_algo_point_service
pip install -r requirements.txt
uvicorn main:app --reload --port 9002

# Mesh algo service (port 9003)
cd mock_algo_mesh_service
pip install -r requirements.txt
uvicorn main:app --reload --port 9003
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
  services/
    algo_client.py      — AlgoClient: httpx async wrapper calling algo services
  crud/
    auth.py             — User DB ops + Redis session management
  models/
    auth.py             — SQLAlchemy User model
  schemas/
    auth.py, image.py, pointcloud.py, mesh.py — Pydantic request/response models
  tests/                — unittest with IsolatedAsyncioTestCase + AsyncMock
  storage/              — Generated/uploaded images (gitignored)
  storage_pointcloud/   — Generated/uploaded point clouds (gitignored)
  storage_mesh/         — Generated/uploaded meshes (gitignored)

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
      Placeholder.vue   — Stub for unimplemented features

mock_algo_service/         — Mock image algo (test.png)
mock_algo_point_service/   — Mock point cloud algo (synthetic PLY sphere)
mock_algo_mesh_service/    — Mock mesh algo (synthetic OBJ cube)
```

## Config & Environment

All backend configs are environment-overridable (see `backend/config/service_conf.py`):

| Variable | Default | Description |
|---|---|---|
| `ALGO_IMAGE_BASE_URL` | `http://10.1.115.170:8000` | Image algo service |
| `ALGO_POINTCLOUD_BASE_URL` | `http://10.1.115.170:8001` | Point cloud algo service |
| `ALGO_MESH_BASE_URL` | `http://10.1.115.170:8002` | Mesh algo service |
| `IMAGE_REQUIRE_AUTH` | `true` | Require auth for image endpoints |
| `ALGO_IMAGE_TIMEOUT_SECONDS` | `120` | Algo call timeout |
| `BIZ_IMAGE_STORAGE_ROOT` | `backend/storage` | Local file storage |

For local development, set algo URLs to `http://127.0.0.1:9001` etc.

## Important Patterns

- **AlgoClient** (`backend/services/algo_client.py`): All algo communication goes through this class. It raises `AlgoServiceError` with a `status_code`; routers catch it and re-raise as `HTTPException`.
- **Auth decorator**: Router endpoints use `get_current_user` dependency to validate tokens.
- **Response format**: All endpoints return `{"code": 200, "message": "ok", "data": {...}}`.
- **Media consistency**: Image, pointcloud, and mesh routers follow identical structure — adding a new media type means replicating `algo_client.py`, `routers/*.py`, `schemas/*.py` patterns.
- **Unimplemented features**: Tracing, Data Registry, Logs, User Management, System Config all use `Placeholder.vue`.
- **No DB migrations**: SQLAlchemy models exist but no Alembic setup.
- **No production deployment**: No Docker, CI/CD, or nginx configs.
