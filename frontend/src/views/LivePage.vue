<template>
  <div class="live-page">
    <div class="live-header">
      <h2>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-4px;margin-right:6px">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        IPTV 电视直播
      </h2>
      <span class="source-count" v-if="sources.length">{{ sources.length }} 个源</span>
    </div>

    <!-- Source selector -->
    <div v-if="sources.length" class="source-bar">
      <n-scrollbar x-scrollable>
        <div class="source-tags">
          <button
            v-for="(src, idx) in sources"
            :key="idx"
            :class="['source-tag', { active: currentSource === idx }]"
            @click="switchSource(idx)"
          >
            <span class="tag-name">{{ src.name }}</span>
            <span v-if="loadingSource === idx" class="tag-loading"></span>
          </button>
        </div>
      </n-scrollbar>
    </div>

    <div class="live-content">
      <!-- Left: Channel list -->
      <div class="groups-panel">
        <div v-if="loading" class="loading-area">
          <n-skeleton width="100%" :height="40" v-for="i in 6" :key="i" style="margin-bottom:8px" />
        </div>

        <template v-if="!loading">
          <div class="channel-search" v-if="flatChannels.length > 0">
            <span class="search-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
              </svg>
            </span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索频道..."
              class="search-input"
            />
          </div>

          <div class="groups-control" v-if="filteredChannels.length > 0">
            <button
              class="collapse-all-btn"
              @click="allCollapsed ? expandAll() : collapseAll()"
            >
              {{ allCollapsed ? '全部展开' : '全部折叠' }}
            </button>
          </div>

          <template v-for="group in filteredChannels" :key="group.name">
            <div class="group-section">
              <div class="group-title" @click="toggleGroup(group.name)">
                <span class="group-arrow">{{ collapsedGroups[group.name] ? '▶' : '▼' }}</span>
                <span class="group-name">{{ group.name }}</span>
                <span class="group-count" v-if="group.channels.length">{{ group.channels.length }}</span>
              </div>
              <div class="channels-list" v-if="!collapsedGroups[group.name]">
                <div
                  v-for="(ch, idx) in group.channels"
                  :key="idx"
                  :class="['channel-item', { active: currentChannel?.name === ch.name }]"
                  @click="playChannel(ch)"
                >
                  <span class="ch-name">{{ ch.name }}</span>
                  <span class="ch-lines-badge" v-if="ch.urls && ch.urls.length > 1">{{ ch.urls.length }}路</span>
                  <span v-if="currentChannel?.name === ch.name && isPlaying" class="ch-live">● LIVE</span>
                </div>
              </div>
            </div>
          </template>

          <div v-if="!flatChannels.length" class="no-channels">
            <p>该源无频道数据</p>
          </div>
          <div v-if="searchQuery && filteredChannels.length === 0 && flatChannels.length > 0" class="no-channels">
            <p>未找到匹配的频道</p>
          </div>
        </template>
      </div>

      <!-- Right: Player -->
      <div class="player-panel">
        <div v-if="currentUrl" class="player-wrapper">
          <video ref="videoRef" controls autoplay preload="auto" style="width:100%;height:100%;background:#000;border-radius:8px"></video>
          <div class="player-overlay">
            <div class="player-info">
              <span class="player-ch-name">{{ currentChannel?.name }}</span>
              <span class="player-line-info" v-if="currentChannel && currentChannel.urls && currentChannel.urls.length > 1">
                线路 {{ currentLineIndex + 1 }} / {{ currentChannel.urls.length }}
              </span>
              <span class="player-resolution" v-if="videoResolution">{{ videoResolution }}</span>
            </div>
            <button
              v-if="currentChannel && currentChannel.urls && currentChannel.urls.length > 1"
              class="line-switch-btn"
              @click="switchLine"
              title="切换线路"
            >
              换线
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
        <div v-else class="player-placeholder">
          <p>选择左侧频道开始播放</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { NScrollbar, NSkeleton } from 'naive-ui'
import { usePlayer } from '@/composables/usePlayer'

const sources = ref<any[]>([])
const channelsMap = ref<Record<number, any[]>>({})
const currentSource = ref(0)
const currentChannel = ref<any>(null)
const currentLineIndex = ref(0)
const isPlaying = ref(false)
const loading = ref(false)
const loadingSource = ref(-1)
const searchQuery = ref('')
const collapsedGroups = ref<Record<string, boolean>>({})

const { videoRef, videoResolution, bufferPercent, isBuffering, downloadSpeed, initPlayer, setupVideoEvents, resetVideoInfo } = usePlayer()

const currentUrl = computed(() => {
  const ch = currentChannel.value
  if (!ch || !ch.urls || ch.urls.length === 0) return ''
  return ch.urls[currentLineIndex.value] || ch.urls[0]
})

const currentHeaders = computed(() => {
  const ch = currentChannel.value
  if (!ch || !ch.headers || ch.headers.length === 0) return null
  return ch.headers[currentLineIndex.value] || null
})

const currentChannels = computed(() => channelsMap.value[currentSource.value] || [])

const flatChannels = computed(() => {
  const result: { name: string; urls: string[] }[] = []
  for (const group of currentChannels.value) {
    if (group.channels) {
      for (const ch of group.channels) {
        result.push(ch)
      }
    }
  }
  return result
})

const filteredChannels = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return currentChannels.value

  return currentChannels.value
    .map(group => ({
      ...group,
      channels: group.channels.filter((ch: any) =>
        ch.name.toLowerCase().includes(q)
      )
    }))
    .filter(group => group.channels.length > 0)
})

const allCollapsed = computed(() => {
  const groups = filteredChannels.value
  if (!groups.length) return false
  return groups.every(g => collapsedGroups.value[g.name])
})

function toggleGroup(name: string) {
  collapsedGroups.value[name] = !collapsedGroups.value[name]
}

function collapseAll() {
  for (const g of filteredChannels.value) {
    collapsedGroups.value[g.name] = true
  }
}

function expandAll() {
  for (const g of filteredChannels.value) {
    collapsedGroups.value[g.name] = false
  }
}

function playChannel(ch: any) {
  if (currentChannel.value?.name === ch.name && isPlaying.value) {
    switchLine()
    return
  }
  resetVideoInfo()
  currentChannel.value = ch
  currentLineIndex.value = 0
  isPlaying.value = true
  nextTick(() => {
    setupVideoEvents()
    initPlayer(ch.urls[0], currentHeaders.value)
  })
}

function switchLine() {
  const ch = currentChannel.value
  if (!ch || !ch.urls || ch.urls.length <= 1) return
  const next = (currentLineIndex.value + 1) % ch.urls.length
  currentLineIndex.value = next
  resetVideoInfo()
  nextTick(() => {
    setupVideoEvents()
    initPlayer(ch.urls[next], currentHeaders.value)
  })
}

onMounted(async () => {
  await loadSources()
  if (sources.value.length > 0) {
    await loadChannels(0)
  }
})

async function loadSources() {
  try {
    const { liveAPI } = await import('@/api/vod')
    const res = await liveAPI.groups()
    sources.value = Array.isArray(res) ? res : []
  } catch (e: any) {
    window.$message?.error('加载源列表失败')
  }
}

async function switchSource(idx: number) {
  currentSource.value = idx
  currentChannel.value = null
  currentLineIndex.value = 0
  isPlaying.value = false
  searchQuery.value = ''
  collapsedGroups.value = {}

  if (channelsMap.value[idx]) {
    channelsMap.value[idx] = [...channelsMap.value[idx]]
    return
  }
  await loadChannels(idx)
}

async function loadChannels(idx: number) {
  if (channelsMap.value[idx]) return
  loading.value = true
  loadingSource.value = idx
  try {
    const { liveAPI } = await import('@/api/vod')
    const res = await liveAPI.channels(idx)
    const data = Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : [])
    channelsMap.value[idx] = data
  } catch (e: any) {
    window.$message?.error('加载频道列表失败')
    channelsMap.value[idx] = []
  } finally {
    loading.value = false
    loadingSource.value = -1
  }
}
</script>

<style scoped>
.live-page { padding: 20px; height: calc(100vh - 20px); display: flex; flex-direction: column; }
.live-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.live-header h2 { margin: 0; font-size: 20px; }
.source-count { font-size: 12px; color: #888; background: var(--n-divider-color); padding: 2px 10px; border-radius: 12px; }
.source-bar { margin-bottom: 16px; flex-shrink: 0; }
.source-tags { display: flex; gap: 8px; flex-wrap: nowrap; }
.source-tag {
  flex-shrink: 0; padding: 8px 16px; border: 1px solid var(--n-divider-color);
  border-radius: 20px; background: var(--n-color); cursor: pointer;
  font-size: 13px; transition: all 0.2s; display: flex;
  align-items: center; gap: 6px; min-height: 36px; color: var(--n-text-color);
}
.source-tag:hover { border-color: var(--n-primary-color); color: var(--n-primary-color); }
.source-tag.active { border-color: var(--n-primary-color); background: rgba(0,122,255,0.1); color: var(--n-primary-color); font-weight: 600; }
.tag-name { white-space: nowrap; }
.tag-loading { width: 12px; height: 12px; border: 2px solid var(--n-primary-color); border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.live-content { display: flex; gap: 16px; flex: 1; min-height: 0; }

.groups-panel {
  width: 340px; flex-shrink: 0; overflow-y: auto;
  background: var(--n-card-color); border-radius: 12px; padding: 12px;
  position: relative;
}
.loading-area { padding: 12px 0; }

.channel-search {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; margin-bottom: 8px;
  background: var(--n-divider-color); border-radius: 8px;
}
.search-icon { font-size: 13px; flex-shrink: 0; display:flex; align-items:center; }
.search-input {
  flex: 1; background: transparent; border: none; outline: none;
  color: var(--n-text-color); font-size: 13px; width: 100%;
}

.groups-control { display: flex; justify-content: flex-end; margin-bottom: 6px; }
.collapse-all-btn {
  padding: 3px 12px; font-size: 11px; border: 1px solid var(--n-divider-color);
  border-radius: 10px; background: transparent; color: #888;
  cursor: pointer; transition: all 0.15s;
}
.collapse-all-btn:hover { color: var(--n-primary-color); border-color: var(--n-primary-color); }

.group-section { margin-bottom: 4px; }
.group-title {
  display: flex; align-items: center; gap: 6px;
  padding: 8px; border-radius: 6px; margin-bottom: 2px;
  cursor: pointer; user-select: none; transition: background 0.15s;
}
.group-title:hover { background: rgba(255,255,255,0.05); }
.group-arrow { font-size: 10px; color: #888; width: 12px; flex-shrink: 0; }
.group-name { flex: 1; font-size: 13px; font-weight: 600; color: var(--n-primary-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.group-count { font-size: 11px; color: #888; background: var(--n-divider-color); padding: 1px 8px; border-radius: 10px; }

.channels-list { display: flex; flex-direction: column; gap: 2px; padding-left: 28px; }
.channel-item { display: flex; align-items: center; gap: 6px; padding: 7px 10px; border-radius: 6px; cursor: pointer; transition: all 0.15s; font-size: 13px; }
.channel-item:hover { background: rgba(255,255,255,0.05); }
.channel-item.active { background: rgba(0,122,255,0.1); color: var(--n-primary-color); }
.ch-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ch-lines-badge { font-size: 10px; color: #888; background: var(--n-divider-color); padding: 1px 6px; border-radius: 8px; flex-shrink: 0; }
.ch-live { font-size: 10px; color: #f5222d; animation: blink 1.5s infinite; flex-shrink: 0; }
@keyframes blink { 50% { opacity: 0.3; } }

.no-channels { padding: 40px 0; text-align: center; }
.no-channels p { color: #888; }

.player-panel { flex: 1; background: #000; border-radius: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; }
.player-wrapper { width: 100%; height: 100%; position: relative; }
.player-overlay {
  position: absolute; top: 0; left: 0; right: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7), transparent);
  pointer-events: none;
}
.player-overlay > * { pointer-events: auto; }
.player-info { display: flex; align-items: center; gap: 8px; }
.player-ch-name { font-size: 14px; font-weight: 600; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
.player-line-info { font-size: 11px; color: #aaa; background: rgba(0,0,0,0.5); padding: 2px 8px; border-radius: 8px; }
.player-resolution { font-size: 11px; color: #aaa; background: rgba(0,0,0,0.5); padding: 2px 8px; border-radius: 8px; }
.player-buffer-bar {
  position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.15); z-index: 10;
}
.buffer-fill { height: 100%; background: rgba(0,122,255,0.5); transition: width 0.3s; border-radius: 0 2px 2px 0; }
.buffering-indicator {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 10;
}
.buffering-spinner { width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
.buffering-text { font-size: 11px; color: #aaa; }
.line-switch-btn {
  padding: 6px 14px; font-size: 12px; border: 1px solid rgba(255,255,255,0.3);
  border-radius: 16px; background: rgba(0,0,0,0.5); color: #fff;
  cursor: pointer; transition: all 0.15s;
}
.line-switch-btn:hover { background: rgba(255,255,255,0.15); }
.player-placeholder { text-align: center; color: #555; }
</style>
