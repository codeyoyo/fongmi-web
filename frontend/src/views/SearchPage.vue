<template>
  <div class="search-page">
    <div class="search-header">
      <n-input
        v-model:value="keyword"
        placeholder="输入关键词搜索..."
        class="search-input"
        round
        autofocus
        @keyup.enter="doSearch"
      >
        <template #prefix>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
        </template>
      </n-input>
    </div>

    <div v-if="loading" class="skeleton-grid">
      <div v-for="i in 12" :key="i" class="skeleton-card">
        <n-skeleton width="100%" :height="270" bordered />
      </div>
    </div>
    <div v-else-if="results.length" class="results-grid">
      <div v-for="v in results" :key="v._site_key + '_' + v.vod_id" class="video-card" @click="goDetail(v)">
        <div class="card-cover">
          <img :src="imgUrl(v.vod_pic) || defaultPic" loading="lazy" />
          <div v-if="v.vod_remarks" class="cover-badge">{{ v.vod_remarks }}</div>
        </div>
        <div class="card-info">
          <div class="video-name">{{ v.vod_name }}</div>
          <div class="video-site" v-if="v._site_name">{{ v._site_name }}</div>
        </div>
      </div>
    </div>
    <div v-else-if="searched" class="no-result"><n-empty description="未找到相关结果" /></div>
    <div v-else class="start-search">
      <div class="start-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:#555">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
        </svg>
      </div>
      <p>输入关键词开始搜索...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NInput, NEmpty, NSkeleton } from 'naive-ui'
import { imgUrl } from '@/api/img'

const route = useRoute()
const router = useRouter()
const keyword = ref((route.query.wd as string) || '')
const loading = ref(false)
const searched = ref(false)
const results = ref<any[]>([])
const defaultPic = imgUrl('')

onMounted(async () => {
  if (keyword.value) await doSearch()
})

async function doSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = true
  try {
    const { vodAPI } = await import('@/api/vod')
    const res: any = await vodAPI.search(keyword.value)
    results.value = Array.isArray(res) ? res : (res?.list || [])
  } catch (e: any) {
    window.$message?.error('搜索失败')
    results.value = []
  } finally {
    loading.value = false
  }
}

function goDetail(v: any) {
  const siteKey = v._site_key
  const vodId = v.vod_id
  if (siteKey && vodId) {
    router.push(`/detail/${siteKey}/${vodId}`)
  }
}
</script>

<style scoped>
.search-page { padding: 20px; max-width: 1400px; margin: 0 auto; }
.search-input { margin-bottom: 20px; }
.skeleton-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.skeleton-card { border-radius: 12px; overflow: hidden; }
.results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.no-result { padding: 60px 0; display: flex; justify-content: center; }
.start-search { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; color: #888; }
.start-icon { margin-bottom: 16px; }
.start-search p { font-size: 16px; }
.video-card { border-radius: 12px; overflow: hidden; background: var(--n-card-color); cursor: pointer; transition: all 0.3s; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.video-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); }
.card-cover { position: relative; aspect-ratio: 2/3; background: #1a1a2e; }
.card-cover img { width: 100%; height: 100%; object-fit: cover; }
.cover-badge { position: absolute; top: 8px; right: 8px; background: rgba(255,80,80,0.9); color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.card-info { padding: 10px 12px; }
.video-name { font-size: 13px; font-weight: 500; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
.video-site { font-size: 11px; color: #888; margin-top: 2px; }
</style>
