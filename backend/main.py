from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.service_conf import BIZ_GS_STORAGE_ROOT, BIZ_IMAGE_STORAGE_ROOT, BIZ_MESH_STORAGE_ROOT, BIZ_POINTCLOUD_STORAGE_ROOT
from routers import auth, gs, image, mesh, pointcloud

# 创建 FastAPI 应用并挂载业务路由。
app = FastAPI()


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
