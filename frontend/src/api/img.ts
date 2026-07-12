/**
 * Image URL helper - routes through proxy to avoid CORS
 */
const FALLBACK = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 140%22%3E%3Crect fill=%22%23333%22 width=%22100%22 height=%22140%22/%3E%3C/svg%3E'

export function imgUrl(url: string | undefined | null): string {
  if (!url) return FALLBACK
  if (url.startsWith('data:') || url.startsWith('/api/')) return url
  return `/api/img/proxy?url=${encodeURIComponent(url)}`
}
