from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.service_conf import BIZ_IMAGE_STORAGE_ROOT, BIZ_POINTCLOUD_STORAGE_ROOT
from routers import auth, image, pointcloud

# 创建 FastAPI 应用并挂载业务路由。
app = FastAPI()
app.include_router(auth.router)
app.include_router(image.router)
app.include_router(pointcloud.router)

Path(BIZ_IMAGE_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=BIZ_IMAGE_STORAGE_ROOT), name="storage")

Path(BIZ_POINTCLOUD_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage_pointcloud", StaticFiles(directory=BIZ_POINTCLOUD_STORAGE_ROOT), name="storage_pointcloud")

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