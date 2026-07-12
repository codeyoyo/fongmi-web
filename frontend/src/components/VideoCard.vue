<template>
  <n-card hoverable class="video-card" @click="onClick">
    <template #cover>
      <div class="cover-wrapper">
        <n-image
          :src="video.vod_pic"
          :alt="video.vod_name"
          object-fit="cover"
          preview-disabled
          class="cover-image"
        />
        <div v-if="video.vod_remarks" class="cover-badge">
          <n-tag size="small" type="error" :bordered="false">{{ video.vod_remarks }}</n-tag>
        </div>
      </div>
    </template>
    <n-ellipsis :line-clamp="2" class="video-title">{{ video.vod_name }}</n-ellipsis>
    <div class="video-meta">
      <n-text depth="3" v-if="video.vod_year">{{ video.vod_year }}</n-text>
      <n-text depth="3" v-if="video.vod_area"> · {{ video.vod_area }}</n-text>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { NCard, NImage, NTag, NEllipsis, NText } from 'naive-ui'

defineProps<{
  video: {
    vod_id: string | number
    vod_name: string
    vod_pic?: string
    vod_remarks?: string
    vod_year?: string
    vod_area?: string
  }
}>()

const emit = defineEmits<{
  click: []
}>()

function onClick() {
  emit('click')
}
</script>

<style scoped>
.video-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.video-card:hover {
  transform: translateY(-4px);
}
.cover-wrapper {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
}
.cover-image {
  width: 100%;
  height: 100%;
}
.cover-badge {
  position: absolute;
  top: 6px;
  right: 6px;
}
.video-title {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.4;
}
.video-meta {
  margin-top: 4px;
  font-size: 12px;
}
</style>
