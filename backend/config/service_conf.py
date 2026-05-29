import os
from pathlib import Path

# 后端根目录，后续用于拼接默认存储路径。
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# 算法服务基础地址：业务后端会把请求转发到这个地址。
# ALGO_IMAGE_BASE_URL = os.getenv("ALGO_IMAGE_BASE_URL", "http://10.1.115.170:8004").rstrip("/")
ALGO_IMAGE_BASE_URL = os.getenv("ALGO_IMAGE_BASE_URL", "http://127.0.0.1:8004").rstrip("/")
# 调用算法服务的超时时间（秒），避免请求长期阻塞。
ALGO_IMAGE_TIMEOUT_SECONDS = float(os.getenv("ALGO_IMAGE_TIMEOUT_SECONDS", "120"))
# 服务间鉴权密钥：如果算法服务开启校验，可在请求头中携带。
ALGO_IMAGE_API_KEY = os.getenv("ALGO_IMAGE_API_KEY", "")
# 业务后端本地存储目录：生成图片会保存到该路径下。
BIZ_IMAGE_STORAGE_ROOT = os.getenv(
    "BIZ_IMAGE_STORAGE_ROOT",
    str((BACKEND_ROOT / "storage").resolve()),
)

ALGO_POINTCLOUD_BASE_URL = os.getenv("ALGO_POINTCLOUD_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
# ALGO_POINTCLOUD_BASE_URL = os.getenv("ALGO_POINTCLOUD_BASE_URL", "http://10.1.115.170:8001").rstrip("/")
ALGO_POINTCLOUD_TIMEOUT_SECONDS = float(os.getenv("ALGO_POINTCLOUD_TIMEOUT_SECONDS", "180"))
ALGO_POINTCLOUD_API_KEY = os.getenv("ALGO_POINTCLOUD_API_KEY", "")
BIZ_POINTCLOUD_STORAGE_ROOT = os.getenv(
    "BIZ_POINTCLOUD_STORAGE_ROOT",
    str((BACKEND_ROOT / "storage_pointcloud").resolve()),
)

ALGO_MESH_BASE_URL = os.getenv("ALGO_MESH_BASE_URL", "http://127.0.0.1:8002").rstrip("/")
# ALGO_MESH_BASE_URL = os.getenv("ALGO_MESH_BASE_URL", "http://10.1.115.170:8002").rstrip("/")
ALGO_MESH_TIMEOUT_SECONDS = float(os.getenv("ALGO_MESH_TIMEOUT_SECONDS", "180"))
ALGO_MESH_API_KEY = os.getenv("ALGO_MESH_API_KEY", "")
BIZ_MESH_STORAGE_ROOT = os.getenv(
    "BIZ_MESH_STORAGE_ROOT",
    str((BACKEND_ROOT / "storage_mesh").resolve()),
)

# 3DGS（3D Gaussian Splatting）算法服务配置。
ALGO_GS_BASE_URL = os.getenv("ALGO_GS_BASE_URL", "http://127.0.0.1:8003").rstrip("/")
# ALGO_GS_BASE_URL = os.getenv("ALGO_GS_BASE_URL", "http://10.1.115.170:8003").rstrip("/")
ALGO_GS_TIMEOUT_SECONDS = float(os.getenv("ALGO_GS_TIMEOUT_SECONDS", "180"))
ALGO_GS_API_KEY = os.getenv("ALGO_GS_API_KEY", "")
BIZ_GS_STORAGE_ROOT = os.getenv(
    "BIZ_GS_STORAGE_ROOT",
    str((BACKEND_ROOT / "storage_gs").resolve()),
)
