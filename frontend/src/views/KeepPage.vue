<template>
  <div class="keep-page">
    <div class="page-header">
      <h2>❤️ 我的收藏</h2>
    </div>
    <div v-if="loading" class="loading"><n-spin size="large" /></div>
    <div v-else-if="!list.length" class="empty"><n-empty description="暂无收藏" /></div>
    <div v-else class="grid">
      <div v-for="item in list" :key="item.id" class="video-card" @click="goDetail(item)">
        <div class="card-cover"><img :src="imgUrl(item.pic) || defaultPic" /></div>
        <div class="card-info"><div class="video-name">{{ item.name }}</div></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpin, NEmpty } from 'naive-ui'
import { keepAPI } from '@/api/vod'
import { imgUrl } from '@/api/img'

const router = useRouter()
const list = ref<any[]>([])
const loading = ref(false)
const defaultPic = imgUrl('')

onMounted(loadList)

async function loadList() {
  loading.value = true
  try {
    const res: any = await keepAPI.list()
    // API returns array directly
    list.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error(e)
    list.value = []
  } finally {
    loading.value = false
  }
}

function goDetail(item: any) {
  router.push(`/detail/${item.site_key}/${item.vod_id}`)
}
</script>

<style scoped>
.keep-page { padding: 20px; max-width: 1600px; margin: 0 auto; }
.page-header h2 { margin: 0 0 20px; }
.loading, .empty { padding: 60px 0; display: flex; justify-content: center; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.video-card { border-radius: 12px; overflow: hidden; background: var(--n-card-color); cursor: pointer; transition: all 0.3s; }
.video-card:hover { transform: translateY(-4px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.card-cover { aspect-ratio: 2/3; background: #1a1a2e; }
.card-cover img { width: 100%; height: 100%; object-fit: cover; }
.card-info { padding: 10px 12px; }
.video-name { font-size: 13px; font-weight: 500; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
</style>
