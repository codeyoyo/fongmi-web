<template>
  <div class="play-page">
    <div class="player-box">
      <div class="video-wrapper">
        <video ref="videoRef" controls autoplay preload="auto" style="width:100%;max-height:80vh;background:#000"></video>
        <div class="player-overlay">
          <span class="resolution-tag" v-if="videoResolution">{{ videoResolution }}</span>
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
    </div>
    <div class="play-controls">
      <n-button text @click="$router.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:4px">
          <path d="m15 18-6-6 6-6"/>
        </svg>
        返回
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NButton } from 'naive-ui'
import { usePlayer } from '@/composables/usePlayer'

const route = useRoute()
const { videoRef, videoResolution, bufferPercent, isBuffering, downloadSpeed, initPlayer, setupVideoEvents, useProxy } = usePlayer()

function toggleProxy() {
  useProxy.value = !useProxy.value
  window.$message?.info(useProxy.value ? '已切换为代理加速（缓存段，快速回看）' : '已切换为直连播放')
  const url = route.query.url as string
  if (url && videoRef.value) {
    setupVideoEvents()
    initPlayer(url)
  }
}

onMounted(() => {
  const url = route.query.url as string
  if (!url || !videoRef.value) return
  setupVideoEvents()
  initPlayer(url)
})
</script>

<style scoped>
.play-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.player-box { border-radius: 12px; overflow: hidden; background: #000; position: relative; }
.video-wrapper { position: relative; }
.player-overlay { position: absolute; top: 0; left: 0; right: 0; padding: 10px 14px; background: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent); pointer-events: none; display: flex; gap: 8px; align-items: center; }
.resolution-tag { font-size: 11px; color: #aaa; background: rgba(0,0,0,0.5); padding: 2px 8px; border-radius: 8px; }
.proxy-toggle {
  font-size: 10px; color: #0ae; background: rgba(0,0,0,0.5); border: 1px solid rgba(0,170,238,0.4);
  padding: 1px 8px; border-radius: 8px; cursor: pointer; pointer-events: auto; line-height: 1.6;
}
.proxy-toggle:hover { background: rgba(0,170,238,0.2); }
.player-buffer-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.15); z-index: 10; }
.buffer-fill { height: 100%; background: rgba(0,122,255,0.5); transition: width 0.3s; }
.buffering-indicator { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 10; }
.buffering-spinner { width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
.buffering-text { font-size: 11px; color: #aaa; }
@keyframes spin { to { transform: rotate(360deg); } }
.play-controls { margin-top: 12px; }
</style>
