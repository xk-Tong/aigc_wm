const now = () => {
  if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
    return performance.now()
  }
  return Date.now()
}

export const startOperationTimer = () => now()

export const elapsedMsSince = (startedAt) => Math.max(0, Math.round(now() - startedAt))

export const formatElapsedSeconds = (startedAt, fractionDigits = 1) => {
  return (elapsedMsSince(startedAt) / 1000).toFixed(fractionDigits)
}

export const waitForAnimationFrame = () => {
  return new Promise((resolve) => {
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(() => resolve())
      return
    }
    setTimeout(resolve, 16)
  })
}

export const waitForAnimationFrames = async (count = 2) => {
  for (let index = 0; index < count; index += 1) {
    await waitForAnimationFrame()
  }
}

export const waitForImagePreview = (url) => {
  return new Promise((resolve, reject) => {
    if (!url) {
      reject(new Error('Image preview URL is missing'))
      return
    }

    const image = new Image()
    image.onload = async () => {
      try {
        if (typeof image.decode === 'function') {
          await image.decode()
        }
      } catch {
        // onload is enough for preview readiness when decode is unavailable or already complete.
      }
      resolve()
    }
    image.onerror = () => reject(new Error('Image preview failed to load'))
    image.src = url
  })
}

export const waitForImagePreviews = (urls) => {
  return Promise.all(urls.filter(Boolean).map((url) => waitForImagePreview(url)))
}
