<template>
  <div class="detail-page">
    <div v-if="!siteKey" class="empty-tip"><n-empty description="请先选择站点" /></div>

    <div v-else-if="detail" class="detail-layout">
      <!-- Left: Player -->
      <div class="player-column">
        <div class="player-sticky">
          <div v-if="currentUrl" class="player-container">
            <div class="video-wrapper">
              <video ref="videoRef" controls autoplay preload="auto" style="width:100%;background:#000;border-radius:8px;max-height:45vh"></video>
              <div class="vod-player-overlay">
                <span class="vod-resolution" v-if="videoResolution">{{ videoResolution }}</span>
              </div>
              <div class="player-buffer-bar" v-if="bufferPercent > 0">
                <div class="buffer-fill" :style="{ width: bufferPercent + '%' }"></div>
              </div>
              <div v-if="isBuffering" class="buffering-indicator">
                <div class="buffering-spinner"></div>
                <span class="buffering-text" v-if="downloadSpeed">{{ downloadSpeed }}</span>
              </div>
            </div>
            <div class="current-ep">{{ currentEpName }}</div>
          </div>
          <div v-else class="player-placeholder" @click="playFirst">
            <img :src="imgUrl(detail.vod_pic) || defaultPic" class="placeholder-bg" />
            <div class="placeholder-overlay">
              <span class="play-big">▶</span>
              <p>点击选择剧集播放</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Info + Episodes -->
      <div class="info-column">
        <div class="info-section">
          <div class="title-row">
            <h1>{{ detail.vod_name }}</h1>
            <button :class="['fav-btn', { active: isKeep }]" @click="toggleKeep">
              <span class="fav-icon">{{ isKeep ? '❤️' : '🤍' }}</span>
              <span class="fav-text">{{ isKeep ? '已收藏' : '收藏' }}</span>
            </button>
          </div>
          <div class="info-meta">
            <n-tag v-if="detail.vod_year" size="small">{{ detail.vod_year }}</n-tag>
            <n-tag v-if="detail.vod_area" size="small">{{ detail.vod_area }}</n-tag>
            <n-tag v-if="detail.vod_type" size="small">{{ detail.vod_type }}</n-tag>
          </div>
          <div v-if="detail.vod_director" class="info-row"><span class="label">导演：</span>{{ detail.vod_director }}</div>
          <div v-if="detail.vod_actor" class="info-row"><span class="label">主演：</span>{{ detail.vod_actor }}</div>
          <div v-if="detail.vod_content" class="info-desc">
            <n-ellipsis :line-clamp="3" :tooltip="false">{{ detail.vod_content }}</n-ellipsis>
          </div>
        </div>

        <!-- Episode selection -->
        <div v-if="flags.length" class="play-section">
          <n-tabs v-model:value="activeFlag" type="line" animated>
            <n-tab-pane v-for="f in flags" :key="f.flag" :name="f.flag" :tab="f.name">
              <div class="episode-grid">
                <button
                  v-for="(ep, idx) in f.episodes"
                  :key="idx"
                  :class="['ep-btn', { active: currentUrl === ep.url }]"
                  @click="playEpisode(f.flag, ep)"
                >
                  {{ ep.name }}
                </button>
              </div>
            </n-tab-pane>
          </n-tabs>
        </div>
      </div>
    </div>

    <div v-else class="loading-area"><n-spin size="large" /></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { NTag, NTabs, NTabPane, NEllipsis, NSpin, NEmpty } from 'naive-ui'
import Hls from 'hls.js'
import { imgUrl } from '@/api/img'

const route = useRoute()
const videoRef = ref<HTMLVideoElement | null>(null)
const videoResolution = ref('')
const bufferPercent = ref(0)
const isBuffering = ref(false)
const downloadSpeed = ref('')
let hls: Hls | null = null
let speedTimer: ReturnType<typeof setInterval> | null = null
let lastLoadedBytes = 0
let lastSpeedTime = 0

const flags = ref<{ flag: string; name: string; episodes: { name: string; url: string }[] }[]>([])
const activeFlag = ref('')
const currentUrl = ref('')
const currentEpName = ref('')
const detail = ref<any>(null)
const siteKey = ref('')
const isKeep = ref(false)
const loading = ref(false)
const defaultPic = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 140"><rect fill="%23333" width="100" height="140"/></svg>'

onMounted(async () => {
  siteKey.value = route.params.site as string
  const ids = route.params.ids as string
  await loadDetail(ids)
})

async function loadDetail(ids: string) {
  loading.value = true
  try {
    const { vodAPI } = await import('@/api/vod')
    const res: any = await vodAPI.detail(siteKey.value, ids)
    if (res.list && res.list.length > 0) {
      detail.value = res.list[0]
    }
    parseEpisodes()
    if (flags.value.length) {
      activeFlag.value = flags.value[0].flag
    }
    await checkKeep()
  } finally {
    loading.value = false
  }
}

function parseEpisodes() {
  if (!detail.value) return
  const playFrom = (detail.value.vod_play_from || '').split('$$$')
  const playUrl = (detail.value.vod_play_url || '').split('$$$')
  flags.value = playFrom.map((flag, i) => {
    const eps = (playUrl[i] || '').split('#').filter(Boolean).map(ep => {
      const parts = ep.split('$')
      return { name: parts[0] || '播放', url: parts[1] || parts[0] || '' }
    }).filter(e => e.url)
    return { flag, name: flag || `源${i + 1}`, episodes: eps }
  })
}

async function checkKeep() {
  if (!detail.value) return
  try {
    const { keepAPI } = await import('@/api/vod')
    const res: any = await keepAPI.check(siteKey.value, detail.value.vod_id)
    isKeep.value = !!(res && res.is_keep)
  } catch { isKeep.value = false }
}

async function toggleKeep() {
  if (!detail.value) return
  const { keepAPI } = await import('@/api/vod')
  if (isKeep.value) {
    // Find and delete keep
    try {
      const listRes: any = await keepAPI.list()
      const list = listRes?.data || []
      const found = list.find((k: any) => k.site_key === siteKey.value && k.vod_id === detail.value.vod_id)
      if (found) {
        await keepAPI.delete(found.id)
        isKeep.value = false
      }
    } catch (e) { console.error(e) }
  } else {
    try {
      await keepAPI.add({
        site_key: siteKey.value,
        vod_id: detail.value.vod_id,
        name: detail.value.vod_name,
        pic: detail.value.vod_pic || '',
      })
      isKeep.value = true
    } catch (e) { console.error(e) }
  }
}

function setupVideoEvents() {
  const el = videoRef.value
  if (!el) return
  el.onloadedmetadata = () => {
    videoResolution.value = el.videoWidth && el.videoHeight
      ? `${el.videoWidth} × ${el.videoHeight}`
      : ''
  }
  el.onresize = () => {
    videoResolution.value = el.videoWidth && el.videoHeight
      ? `${el.videoWidth} × ${el.videoHeight}`
      : ''
  }
  el.onprogress = () => {
    if (el.buffered.length > 0 && el.duration > 0) {
      const end = el.buffered.end(el.buffered.length - 1)
      bufferPercent.value = Math.round((end / el.duration) * 100)
    }
  }
  el.onwaiting = () => {
    isBuffering.value = true
    if (!speedTimer) startSpeedMonitor()
  }
  el.oncanplay = () => { isBuffering.value = false }
  el.onplaying = () => {
    isBuffering.value = false
    stopSpeedMonitor()
  }
  el.onerror = () => {
    isBuffering.value = false
    stopSpeedMonitor()
  }
}

function startSpeedMonitor() {
  lastLoadedBytes = 0
  lastSpeedTime = Date.now()
  speedTimer = setInterval(() => {
    const el = videoRef.value
    if (!el) return
    const now = Date.now()
    const elapsed = (now - lastSpeedTime) / 1000
    if (elapsed <= 0) return
    const buffered = el.buffered
    const loadedBytes = buffered.length > 0 ? buffered.end(buffered.length - 1) : 0
    const bytesDelta = loadedBytes - lastLoadedBytes
    if (bytesDelta > 0 && elapsed > 0) {
      const speed = bytesDelta / elapsed
      downloadSpeed.value = speed >= 1024 * 1024
        ? `${(speed / 1024 / 1024).toFixed(1)} MB/s`
        : `${(speed / 1024).toFixed(0)} KB/s`
    }
    lastLoadedBytes = loadedBytes
    lastSpeedTime = now
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

function playEpisode(flag: string, ep: { name: string; url: string }) {
  activeFlag.value = flag
  currentUrl.value = ep.url
  currentEpName.value = ep.name
  resetVideoInfo()
  setTimeout(() => {
    setupVideoEvents()
    initPlayer(ep.url)
  }, 100)
  saveHistory(ep.url, ep.name)
}

function playFirst() {
  if (flags.value.length && flags.value[0].episodes.length) {
    playEpisode(flags.value[0].flag, flags.value[0].episodes[0])
  }
}

function initPlayer(url: string) {
  if (!videoRef.value) return
  if (hls) { hls.destroy(); hls = null }
  if (url.includes('.m3u8') && Hls.isSupported()) {
    hls = new Hls()
    hls.loadSource(url)
    hls.attachMedia(videoRef.value)
    hls.on(Hls.Events.ERROR, (_: any, data: any) => {
      if (data.fatal) console.error('HLS error:', data)
    })
  } else {
    videoRef.value.src = url
  }
}

async function saveHistory(url: string, name: string) {
  const { historyAPI } = await import('@/api/vod')
  await historyAPI.add({
    site_key: siteKey.value,
    vod_id: detail.value.vod_id,
    name: detail.value.vod_name,
    pic: detail.value.vod_pic || '',
    episode: url,
  })
}

onBeforeUnmount(() => {
  if (hls) { hls.destroy(); hls = null }
  stopSpeedMonitor()
})
</script>

<style scoped>
.detail-page { padding: 20px; max-width: 1400px; margin: 0 auto; }
.detail-layout { display: grid; grid-template-columns: 380px 1fr; gap: 24px; }

.player-column { position: relative; }
.player-sticky { position: sticky; top: 20px; }
.player-container { background: #000; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.video-wrapper { position: relative; }
.vod-player-overlay {
  position: absolute; top: 0; left: 0; right: 0; padding: 10px 14px;
  background: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent);
  pointer-events: none;
}
.vod-resolution { font-size: 11px; color: #aaa; background: rgba(0,0,0,0.5); padding: 2px 8px; border-radius: 8px; }
.player-buffer-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.15); z-index: 10; }
.buffer-fill { height: 100%; background: rgba(0,122,255,0.5); transition: width 0.3s; border-radius: 0 2px 2px 0; }
.buffering-indicator {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 10;
}
.buffering-spinner { width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
.buffering-text { font-size: 11px; color: #aaa; }
.current-ep { text-align: center; padding: 8px; font-size: 13px; color: #888; }
.player-placeholder { position: relative; aspect-ratio: 16/9; border-radius: 12px; overflow: hidden; cursor: pointer; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.placeholder-bg { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.3); }
.placeholder-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.play-big { width: 64px; height: 64px; background: rgba(255,255,255,0.9); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; color: #333; padding-left: 6px; transition: transform 0.2s; }
.player-placeholder:hover .play-big { transform: scale(1.1); }
.placeholder-overlay p { color: #ccc; font-size: 13px; }

.info-section { background: var(--n-card-color); border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.title-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.title-row h1 { flex: 1; font-size: 22px; margin: 0; }
.fav-btn {
  flex-shrink: 0; display: flex; align-items: center; gap: 4px;
  padding: 6px 12px; border: 1px solid var(--n-border-color); border-radius: 20px;
  background: transparent; cursor: pointer; transition: all 0.2s; font-size: 12px;
}
.fav-btn:hover { border-color: #f5222d; color: #f5222d; }
.fav-btn.active { border-color: #f5222d; background: rgba(245,34,45,0.1); color: #f5222d; }
.fav-icon { font-size: 16px; }
.fav-text { white-space: nowrap; }

.info-meta { display: flex; gap: 6px; margin-bottom: 12px; }
.info-row { font-size: 14px; color: #aaa; margin-bottom: 6px; }
.info-row .label { color: #666; }
.info-desc { font-size: 13px; color: #aaa; line-height: 1.6; margin-top: 8px; }

.play-section { background: var(--n-card-color); border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.episode-grid { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 0; }
.ep-btn { padding: 6px 14px; border: 1px solid var(--n-border-color); border-radius: 6px; background: transparent; cursor: pointer; font-size: 12px; transition: all 0.2s; color: #ccc; }
.ep-btn:hover { border-color: var(--n-primary-color); color: var(--n-primary-color); }
.ep-btn.active { background: var(--n-primary-color); border-color: var(--n-primary-color); color: #fff; }

.empty-tip { display: flex; justify-content: center; padding: 60px 0; }
.loading-area { display: flex; justify-content: center; padding: 60px 0; }
</style>
