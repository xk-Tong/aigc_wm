import os
from pathlib import Path

# 后端根目录，后续用于拼接默认存储路径。
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# 算法服务基础地址：业务后端会把请求转发到这个地址。
ALGO_IMAGE_BASE_URL = os.getenv("ALGO_IMAGE_BASE_URL", "http://10.1.115.170:8000").rstrip("/")
# ALGO_IMAGE_BASE_URL = os.getenv("ALGO_IMAGE_BASE_URL", "http://127.0.0.1:9001").rstrip("/")
# 调用算法服务的超时时间（秒），避免请求长期阻塞。
ALGO_IMAGE_TIMEOUT_SECONDS = float(os.getenv("ALGO_IMAGE_TIMEOUT_SECONDS", "120"))
# 服务间鉴权密钥：如果算法服务开启校验，可在请求头中携带。
ALGO_IMAGE_API_KEY = os.getenv("ALGO_IMAGE_API_KEY", "")
# 图像接口是否要求登录鉴权：本地联调可设为 false，线上建议保持 true。
IMAGE_REQUIRE_AUTH = os.getenv("IMAGE_REQUIRE_AUTH", "true").lower() in {
    "1",
    "true",
    "yes",
}

# 业务后端本地存储目录：生成图片会保存到该路径下。
BIZ_IMAGE_STORAGE_ROOT = os.getenv(
    "BIZ_IMAGE_STORAGE_ROOT",
    str((BACKEND_ROOT / "storage").resolve()),
)
