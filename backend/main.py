from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.db_conf import async_engine
from config.service_conf import BIZ_GS_STORAGE_ROOT, BIZ_IMAGE_STORAGE_ROOT, BIZ_MESH_STORAGE_ROOT, BIZ_POINTCLOUD_STORAGE_ROOT
from models.auth import Base
from routers import auth, gs, image, log, mesh, pointcloud, profile, record, user

# 引入模型模块确保 create_all 能发现所有表
import models.record  # noqa: F401
import models.operation_log  # noqa: F401

# 创建 FastAPI 应用并挂载业务路由。
app = FastAPI()


@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.middleware("http")
async def add_cross_origin_resource_policy(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response


app.include_router(auth.router)
app.include_router(image.router)
app.include_router(pointcloud.router)
app.include_router(mesh.router)
app.include_router(gs.router)
app.include_router(record.router)
app.include_router(log.router)
app.include_router(user.router)
app.include_router(profile.router)

Path(BIZ_IMAGE_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=BIZ_IMAGE_STORAGE_ROOT), name="storage")

Path(BIZ_POINTCLOUD_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage_pointcloud", StaticFiles(directory=BIZ_POINTCLOUD_STORAGE_ROOT), name="storage_pointcloud")

Path(BIZ_MESH_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage_mesh", StaticFiles(directory=BIZ_MESH_STORAGE_ROOT), name="storage_mesh")

Path(BIZ_GS_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage_gs", StaticFiles(directory=BIZ_GS_STORAGE_ROOT), name="storage_gs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    # 基础健康返回，便于快速确认服务已启动。
    return {"Hello": "World"}
