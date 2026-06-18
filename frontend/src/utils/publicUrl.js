const STORAGE_PREFIXES = [
  '/storage/',
  '/storage_pointcloud/',
  '/storage_mesh/',
  '/storage_gs/',
]

export function resolvePublicUrl(url) {
  if (!url) return url

  try {
    const parsed = new URL(url, window.location.origin)
    const isLocalBackend =
      ['localhost', '127.0.0.1', '0.0.0.0'].includes(parsed.hostname) &&
      ['8000', ''].includes(parsed.port)

    if (isLocalBackend && STORAGE_PREFIXES.some((prefix) => parsed.pathname.startsWith(prefix))) {
      return `${parsed.pathname}${parsed.search}${parsed.hash}`
    }
  } catch {
    // Keep the original value when it is not a URL-like string.
  }

  return url
}
