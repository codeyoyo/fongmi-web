<template>
  <div class="play-page">
    <div class="player-box">
      <video ref="videoRef" controls autoplay preload="auto" style="width:100%;max-height:80vh;background:#000"></video>
    </div>
    <div class="play-controls">
      <n-button text @click="$router.back()">← 返回</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import Hls from 'hls.js'

const route = useRoute()
const videoRef = ref<HTMLVideoElement | null>(null)
let hls: Hls | null = null

onMounted(() => {
  const url = route.query.url as string
  if (!url || !videoRef.value) return
  if (url.includes('.m3u8') && Hls.isSupported()) {
    hls = new Hls()
    hls.loadSource(url)
    hls.attachMedia(videoRef.value)
  } else {
    videoRef.value.src = url
  }
})

onBeforeUnmount(() => { if (hls) hls.destroy() })
</script>

<style scoped>
.play-page { padding: 20px; max-width: 1200px; margin: 0 auto; }
.player-box { border-radius: 12px; overflow: hidden; background: #000; }
.play-controls { margin-top: 12px; }
</style>
