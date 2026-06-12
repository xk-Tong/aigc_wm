from urllib.parse import urlsplit

from config.service_conf import BIZ_PUBLIC_BASE_URL


STORAGE_PREFIXES = (
    "/storage/",
    "/storage_pointcloud/",
    "/storage_mesh/",
    "/storage_gs/",
)


def build_public_url(path: str) -> str:
    normalized_path = "/" + path.lstrip("/")
    if BIZ_PUBLIC_BASE_URL:
        return f"{BIZ_PUBLIC_BASE_URL}{normalized_path}"
    return normalized_path


def normalize_public_url(url: str | None) -> str | None:
    if not url:
        return url

    parsed = urlsplit(url)
    path = parsed.path if parsed.scheme and parsed.netloc else url

    for prefix in STORAGE_PREFIXES:
        if path.startswith(prefix):
            return build_public_url(path)

    return url
