<template>
  <div class="history-page">
    <div class="page-header">
      <n-button text @click="$router.back()">← 返回</n-button>
      <h2>⏱️ 观看历史</h2>
      <n-button v-if="list.length" text type="error" @click="clearAll">清空</n-button>
    </div>
    <div v-if="loading" class="loading"><n-spin size="large" /></div>
    <div v-else-if="!list.length" class="empty"><n-empty description="暂无观看记录" /></div>
    <div v-else class="history-list">
      <div v-for="item in list" :key="item.id" class="history-card" @click="goPlay(item)">
        <div class="h-cover"><img :src="imgUrl(item.pic) || defaultPic" /></div>
        <div class="h-info">
          <div class="h-name">{{ item.name }}</div>
          <div class="h-time">{{ formatTime(item.time) }}</div>
        </div>
        <n-button text type="error" size="small" @click.stop="remove(item.id)">删除</n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpin, NEmpty } from 'naive-ui'
import { historyAPI } from '@/api/vod'
import { imgUrl } from '@/api/img'

const router = useRouter()
const list = ref<any[]>([])
const loading = ref(false)
const defaultPic = imgUrl('')

onMounted(loadList)

async function loadList() {
  loading.value = true
  try {
    const res: any = await historyAPI.list()
    list.value = Array.isArray(res) ? res : []
  } finally {
    loading.value = false
  }
}

function formatTime(t: string) {
  if (!t) return ''
  try { return new Date(t).toLocaleString('zh-CN') } catch { return t }
}

function goPlay(item: any) {
  if (item.episode) {
    router.push({ path: '/play', query: { url: item.episode } })
  }
}

async function remove(id: number) {
  await historyAPI.delete(id)
  await loadList()
}

async function clearAll() {
  await historyAPI.clear()
  list.value = []
}
</script>

<style scoped>
.history-page { padding: 20px; max-width: 1000px; margin: 0 auto; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; flex: 1; }
.loading, .empty { padding: 60px 0; display: flex; justify-content: center; }
.history-list { display: flex; flex-direction: column; gap: 8px; }
.history-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px; background: var(--n-card-color); border-radius: 10px;
  cursor: pointer; transition: all 0.2s;
}
.history-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.h-cover { width: 80px; flex-shrink: 0; }
.h-cover img { width: 80px; border-radius: 6px; aspect-ratio: 2/3; object-fit: cover; }
.h-info { flex: 1; min-width: 0; }
.h-name { font-size: 14px; font-weight: 500; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.h-time { font-size: 12px; color: var(--n-text-color-3); }
</style>
