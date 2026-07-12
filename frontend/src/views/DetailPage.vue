<template>
  <div class="detail-page">
    <div v-if="!siteKey" class="empty-tip"><n-empty description="请先选择站点" /></div>

    <div v-else-if="detail" class="detail-layout fade-in">
      <!-- Left: Player -->
      <div class="player-column">
        <div class="player-sticky">
          <div v-if="currentUrl" class="player-container">
            <div class="video-wrapper">
              <video ref="videoRef" controls autoplay preload="auto" style="width:100%;background:#000;border-radius:8px;max-height:45vh"></video>
              <div class="vod-player-overlay">
                <span class="vod-resolution" v-if="videoResolution">{{ videoResolution }}</span>
                <button class="proxy-toggle" @click="toggleProxy" :title="useProxy ? '当前：代理加速（缓存段，点击切换直连）' : '当前：直连播放（点击切换代理加速）'">
                  {{ useProxy ? '加速' : '直连' }}
                </button>
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
            <button class="change-btn" @click="openSourceSwitch">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:3px"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
              换源
            </button>
            <button :class="['fav-btn', { active: isKeep }]" @click="toggleKeep">
              <span class="fav-text">{{ isKeep ? '♥ 已收藏' : '♡ 收藏' }}</span>
            </button>
          </div>

          <!-- 换源弹窗 -->
          <n-modal v-model:show="showSourceModal" title="切换播放源" :mask-closable="true" preset="card" style="max-width:560px">
            <n-input v-model:value="sourceKeyword" placeholder="搜索其他站点的同片资源..." clearable @keyup.enter="doSearchSources" style="margin-bottom:12px" />
            <n-button @click="doSearchSources" :loading="sourcesLoading" size="small" style="margin-bottom:12px">搜索</n-button>
            <div v-if="sources.length === 0 && !sourcesLoading" style="text-align:center;padding:20px;color:#888">输入关键词搜索其他源</div>
            <div v-for="s in sources" :key="s._site_key + s.vod_id" class="source-item" @click="switchToSource(s)">
              <img :src="imgUrl(s.vod_pic) || defaultPic" class="source-pic" />
              <div class="source-info">
                <div class="source-name">{{ s.vod_name }}</div>
                <div class="source-site">{{ s._site_name || s._site_key }}</div>
              </div>
            </div>
          </n-modal>
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

    <div v-else-if="loading" class="loading-fullscreen">
      <div class="loading-spinner"></div>
      <p class="loading-text">正在加载详情...</p>
    </div>

    <div v-else-if="!detail" class="loading-area">
      <div class="skeleton-info">
        <n-skeleton width="60%" :height="32" />
        <n-skeleton width="40%" :height="20" style="margin-top:12px" />
        <n-skeleton width="100%" :height="80" style="margin-top:16px" />
      </div>
      <n-skeleton width="100%" :height="200" style="margin-top:20px" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTag, NTabs, NTabPane, NEllipsis, NEmpty, NSkeleton, NModal, NInput, NButton } from 'naive-ui'
import { imgUrl } from '@/api/img'
import { usePlayer } from '@/composables/usePlayer'

const route = useRoute()
const router = useRouter()
const { videoRef, videoResolution, bufferPercent, isBuffering, downloadSpeed, initPlayer, setupVideoEvents, resetVideoInfo, useProxy } = usePlayer()

const flags = ref<{ flag: string; name: string; episodes: { name: string; url: string }[] }[]>([])
const activeFlag = ref('')
const currentUrl = ref('')
const currentEpName = ref('')
const detail = ref<any>(null)
const siteKey = ref('')
const isKeep = ref(false)
const loading = ref(false)
const defaultPic = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 140"><rect fill="%23333" width="100" height="140"/></svg>'

const showSourceModal = ref(false)
const sourceKeyword = ref('')
const sources = ref<any[]>([])
const sourcesLoading = ref(false)

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
  } catch (e: any) {
    window.$message?.error('加载详情失败: ' + (e?.message || ''))
  } finally {
    loading.value = false
  }
}

function parseEpisodes() {
  if (!detail.value) return
  const playFrom: string[] = (detail.value.vod_play_from || '').split('$$$')
  const playUrl: string[] = (detail.value.vod_play_url || '').split('$$$')
  flags.value = playFrom.map((flag: string, i: number) => {
    const eps = (playUrl[i] || '').split('#').filter(Boolean).map((ep: string) => {
      const parts = ep.split('$')
      return { name: parts[0] || '播放', url: parts[1] || parts[0] || '' }
    }).filter((ep: { url: string }) => ep.url)
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
    try {
      const listRes: any = await keepAPI.list()
      const list = listRes?.data || []
      const found = list.find((k: any) => k.site_key === siteKey.value && k.vod_id === detail.value.vod_id)
      if (found) {
        await keepAPI.delete(found.id)
        isKeep.value = false
      }
    } catch (e: any) { window.$message?.error('取消收藏失败') }
  } else {
    try {
      await keepAPI.add({
        site_key: siteKey.value,
        vod_id: detail.value.vod_id,
        name: detail.value.vod_name,
        pic: detail.value.vod_pic || '',
      })
      isKeep.value = true
    } catch (e: any) { window.$message?.error('收藏失败') }
  }
}

function toggleProxy() {
  useProxy.value = !useProxy.value
  if (currentUrl.value) {
    window.$message?.info(useProxy.value ? '已切换为代理加速（缓存段，快速回看）' : '已切换为直连播放')
  }
}

function openSourceSwitch() {
  sourceKeyword.value = detail.value?.vod_name || ''
  sources.value = []
  showSourceModal.value = true
  if (sourceKeyword.value) doSearchSources()
}

async function doSearchSources() {
  if (!sourceKeyword.value.trim()) return
  sourcesLoading.value = true
  try {
    const { vodAPI } = await import('@/api/vod')
    const res: any = await vodAPI.search(sourceKeyword.value.trim())
    const list = Array.isArray(res) ? res : (res?.list || res?.data || [])
    sources.value = list.filter((item: any) => item._site_key !== siteKey.value)
  } catch (e: any) {
    window.$message?.error('搜索失败: ' + (e?.message || ''))
  } finally {
    sourcesLoading.value = false
  }
}

function switchToSource(item: any) {
  showSourceModal.value = false
  const siteKey = item._site_key
  const vodId = item.vod_id
  if (siteKey && vodId) {
    router.push(`/detail/${siteKey}/${vodId}`)
  }
}

function playEpisode(flag: string, ep: { name: string; url: string }) {
  activeFlag.value = flag
  currentUrl.value = ep.url
  currentEpName.value = ep.name
  resetVideoInfo()
  setTimeout(() => {
    setupVideoEvents()
    setupPositionTracking()
    initPlayer(ep.url)
    checkHistoryPosition()
  }, 100)
  saveHistory(ep.url, ep.name)
}

function playFirst() {
  if (flags.value.length && flags.value[0].episodes.length) {
    playEpisode(flags.value[0].flag, flags.value[0].episodes[0])
  }
}

async function saveHistory(url: string, _name: string) {
  const { historyAPI } = await import('@/api/vod')
  await historyAPI.add({
    site_key: siteKey.value,
    vod_id: detail.value.vod_id,
    name: detail.value.vod_name,
    pic: detail.value.vod_pic || '',
    episode: url,
  })
}

function setupPositionTracking() {
  const el = videoRef.value
  if (!el) return
  el.ontimeupdate = throttle(() => {
    if (el && el.duration > 0 && currentUrl.value) {
      savePosition(el.currentTime, el.duration)
    }
  }, 10000)
}

function savePosition(currentTime: number, duration: number) {
  import('@/api/vod').then(mod => {
    mod.historyAPI.add({
      site_key: siteKey.value,
      vod_id: detail.value.vod_id,
      position: Math.floor(currentTime * 1000),
      duration: Math.floor(duration * 1000),
    })
  }).catch(() => {})
}

async function checkHistoryPosition() {
  try {
    const { historyAPI } = await import('@/api/vod')
    const res: any = await historyAPI.list(1, 100)
    const list = Array.isArray(res) ? res : (res?.data || [])
    const found = list.find((h: any) => h.site_key === siteKey.value && h.vod_id === detail.value.vod_id)
    if (found && found.position) {
      setTimeout(() => {
        if (videoRef.value) {
          videoRef.value.currentTime = found.position / 1000
        }
      }, 500)
    }
  } catch { /* ignore */ }
}

function throttle(fn: (...args: any[]) => void, delay: number) {
  let last = 0
  return (...args: any[]) => {
    const now = Date.now()
    if (now - last >= delay) {
      last = now
      fn(...args)
    }
  }
}
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
  pointer-events: none; display: flex; gap: 8px; align-items: center;
}
.vod-resolution { font-size: 11px; color: #aaa; background: rgba(0,0,0,0.5); padding: 2px 8px; border-radius: 8px; }
.proxy-toggle {
  font-size: 10px; color: #0ae; background: rgba(0,0,0,0.5); border: 1px solid rgba(0,170,238,0.4);
  padding: 1px 8px; border-radius: 8px; cursor: pointer; pointer-events: auto; line-height: 1.6;
}
.proxy-toggle:hover { background: rgba(0,170,238,0.2); }
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
.change-btn {
  flex-shrink: 0; display: flex; align-items: center; gap: 2px;
  padding: 6px 12px; border: 1px solid var(--n-border-color); border-radius: 20px;
  background: transparent; cursor: pointer; transition: all 0.2s; font-size: 12px; color: #ccc;
}
.change-btn:hover { border-color: #0ae; color: #0ae; }

.source-item {
  display: flex; gap: 12px; padding: 10px; border-radius: 8px; cursor: pointer;
  transition: background 0.2s; align-items: center;
}
.source-item:hover { background: rgba(255,255,255,0.05); }
.source-pic { width: 48px; height: 64px; object-fit: cover; border-radius: 4px; background: #222; }
.source-info { flex: 1; min-width: 0; }
.source-name { font-size: 14px; color: #eee; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-site { font-size: 12px; color: #888; margin-top: 2px; }

.fav-btn {
  flex-shrink: 0; display: flex; align-items: center; gap: 4px;
  padding: 6px 12px; border: 1px solid var(--n-border-color); border-radius: 20px;
  background: transparent; cursor: pointer; transition: all 0.2s; font-size: 12px;
}
.fav-btn:hover { border-color: #f5222d; color: #f5222d; }
.fav-btn.active { border-color: #f5222d; background: rgba(245,34,45,0.1); color: #f5222d; }
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
.loading-fullscreen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 60vh; gap: 16px;
}
.loading-spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--n-primary-color); border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-text { font-size: 14px; color: #888; }
.loading-area { padding: 20px; }
.skeleton-info { background: var(--n-card-color); border-radius: 12px; padding: 20px; }

.fade-in { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
