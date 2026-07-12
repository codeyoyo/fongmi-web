import { ref, onBeforeUnmount } from 'vue'
import Hls from 'hls.js'
import flvjs from 'flv.js'

export function usePlayer() {
  const videoRef = ref<HTMLVideoElement | null>(null)
  const videoResolution = ref('')
  const bufferPercent = ref(0)
  const isBuffering = ref(false)
  const downloadSpeed = ref('')
  const isPlaying = ref(false)
  const useProxy = ref(true)

  let hls: Hls | null = null
  let flvPlayer: any = null
  let speedTimer: ReturnType<typeof setInterval> | null = null
  let lastLoadedBytes = 0
  let lastSpeedTime = 0

  function buildProxyUrl(url: string, headers: Record<string, string> | null | undefined): string {
    if (!useProxy.value) return url
    if (headers && Object.keys(headers).length > 0) {
      return `/api/player/proxy/${encodeURIComponent(url)}?extra_headers=${encodeURIComponent(JSON.stringify(headers))}`
    }
    return `/api/player/proxy/${encodeURIComponent(url)}`
  }

  function initPlayer(url: string, headers?: Record<string, string> | null) {
    destroyPlayer()
    if (!videoRef.value) return

    const finalUrl = buildProxyUrl(url, headers || null)

    if (finalUrl.includes('.m3u8') && Hls.isSupported()) {
      hls = new Hls({
        maxBufferLength: 60,
        maxMaxBufferLength: 120,
        maxBufferSize: 100 * 1000 * 1000,
        startFragPrefetch: true,
        enableWorker: true,
        backBufferLength: 60,
        fragLoadingMaxRetry: 6,
        manifestLoadingMaxRetry: 8,
        levelLoadingMaxRetry: 8,
        liveSyncDurationCount: 7,
      })
      hls.loadSource(finalUrl)
      hls.attachMedia(videoRef.value)
      hls.on(Hls.Events.ERROR, (_: any, data: any) => {
        if (data.fatal) {
          console.error('HLS fatal error:', data)
          if (videoRef.value && hls) {
            hls.destroy()
            hls = null
            videoRef.value.src = finalUrl
          }
        }
      })
    } else if ((finalUrl.includes('.flv') || finalUrl.includes('?format=flv')) && flvjs.isSupported()) {
      flvPlayer = flvjs.createPlayer({ type: 'flv', url: finalUrl })
      flvPlayer.attachMediaElement(videoRef.value)
      flvPlayer.load()
    } else {
      videoRef.value.src = finalUrl
    }
  }

  function destroyPlayer() {
    if (hls) { hls.destroy(); hls = null }
    if (flvPlayer) { flvPlayer.destroy(); flvPlayer = null }
    stopSpeedMonitor()
  }

  function setupVideoEvents() {
    const el = videoRef.value
    if (!el) return
    el.onloadedmetadata = () => {
      videoResolution.value = el.videoWidth && el.videoHeight
        ? `${el.videoWidth} × ${el.videoHeight}` : ''
    }
    el.onresize = () => {
      videoResolution.value = el.videoWidth && el.videoHeight
        ? `${el.videoWidth} × ${el.videoHeight}` : ''
    }
    el.onprogress = () => {
      if (el.buffered.length > 0 && el.duration > 0) {
        bufferPercent.value = Math.round((el.buffered.end(el.buffered.length - 1) / el.duration) * 100)
      }
    }
    el.onwaiting = () => {
      isBuffering.value = true
      if (!speedTimer) startSpeedMonitor()
    }
    el.oncanplay = () => { isBuffering.value = false }
    el.onplaying = () => { isBuffering.value = false; stopSpeedMonitor() }
    el.onerror = () => { isBuffering.value = false; stopSpeedMonitor() }
  }

  function startSpeedMonitor() {
    lastLoadedBytes = 0; lastSpeedTime = Date.now()
    speedTimer = setInterval(() => {
      const el = videoRef.value
      if (!el) return
      const now = Date.now()
      const elapsed = (now - lastSpeedTime) / 1000
      if (elapsed <= 0) return
      const loadedBytes = el.buffered.length > 0 ? el.buffered.end(el.buffered.length - 1) : 0
      const bytesDelta = loadedBytes - lastLoadedBytes
      if (bytesDelta > 0) {
        const speed = bytesDelta / elapsed
        downloadSpeed.value = speed >= 1024 * 1024
          ? `${(speed / 1024 / 1024).toFixed(1)} MB/s`
          : `${(speed / 1024).toFixed(0)} KB/s`
      }
      lastLoadedBytes = loadedBytes; lastSpeedTime = now
    }, 1000)
  }

  function stopSpeedMonitor() {
    if (speedTimer) { clearInterval(speedTimer); speedTimer = null }
    downloadSpeed.value = ''
  }

  function resetVideoInfo() {
    videoResolution.value = ''
    bufferPercent.value = 0
    isBuffering.value = false
    downloadSpeed.value = ''
    stopSpeedMonitor()
  }

  onBeforeUnmount(() => { destroyPlayer() })

  return {
    videoRef, videoResolution, bufferPercent, isBuffering, downloadSpeed, isPlaying, useProxy,
    initPlayer, destroyPlayer, setupVideoEvents, resetVideoInfo
  }
}
