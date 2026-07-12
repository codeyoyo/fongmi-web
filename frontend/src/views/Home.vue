<template>
  <div class="home-page">
    <!-- Loading state -->
    <div v-if="initLoading" class="init-loading">
      <n-spin size="large" />
      <p style="margin-top:12px;color:#888">加载中...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="!hasSite" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:#555">
          <rect x="2" y="7" width="20" height="15" rx="2" ry="2"/>
          <polygon points="10 11 16 14.5 10 18 10 11"/>
        </svg>
      </div>
      <h2>欢迎来到 FongMi TV</h2>
      <p>请先导入您的订阅配置即可开始观看</p>
      <n-button type="primary" size="large" round @click="$router.push('/setting')">
        <template #icon>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
        </template>
        前往设置导入
      </n-button>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="home-header">
        <n-select
          v-model:value="selectedSite"
          :options="vodSiteOptions"
          placeholder="选择点播站点"
          class="site-select"
          filterable
          @update:value="onSiteChange"
        />
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索视频..."
          class="search-input"
          round
          clearable
          @keyup.enter="doSearch"
        >
          <template #prefix>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
            </svg>
          </template>
        </n-input>
      </div>

      <!-- Category tags -->
      <div v-if="classes.length" class="class-bar">
        <n-scrollbar x-scrollable>
          <div class="class-tags">
            <button
              v-for="cls in classes"
              :key="cls.type_id"
              :class="['class-tag', { active: currentTid === cls.type_id }]"
              @click="onCategoryClick(cls.type_id, cls.type_name)"
            >
              {{ cls.type_name }}
            </button>
          </div>
        </n-scrollbar>
      </div>

      <!-- Quick entry -->
      <div class="quick-entry">
        <div class="quick-card" @click="$router.push('/live')">
          <div class="quick-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
          </div>
          <span>电视直播</span>
        </div>
        <div class="quick-card" @click="$router.push('/history')">
          <div class="quick-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <span>观看历史</span>
        </div>
        <div class="quick-card" @click="$router.push('/keep')">
          <div class="quick-icon">♥</div>
          <span>我的收藏</span>
        </div>
      </div>

      <!-- Video grid -->
      <div class="video-section">
        <div v-if="loading" class="skeleton-grid">
          <div v-for="i in 12" :key="i" class="skeleton-card">
            <n-skeleton width="100%" :height="270" bordered />
          </div>
        </div>
        <template v-else>
          <div v-if="!videos.length" class="no-data">
            <p>暂无数据</p>
          </div>
          <div class="video-grid">
            <div v-for="video in videos" :key="video.vod_id" class="video-card" @click="goDetail(video.vod_id)">
              <div class="card-cover">
                <img :src="imgUrl(video.vod_pic) || defaultPic" :alt="video.vod_name" loading="lazy" />
                <div v-if="video.vod_remarks" class="cover-badge">{{ video.vod_remarks }}</div>
                <div class="cover-overlay"><span class="play-icon">▶</span></div>
              </div>
              <div class="card-info">
                <div class="video-name">{{ video.vod_name }}</div>
                <div class="video-meta">
                  <span v-if="video.vod_year" class="meta-tag">{{ video.vod_year }}</span>
                  <span v-if="video.vod_area" class="meta-tag">{{ video.vod_area }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
        <div v-if="pagecount > 1" class="pagination">
          <n-pagination v-model:page="currentPage" :page-count="pagecount" @update:page="onPageChange" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NInput, NSelect, NScrollbar, NSpin, NPagination, NSkeleton } from 'naive-ui'
import { imgUrl } from '@/api/img'

const router = useRouter()
const initLoading = ref(true)
const loading = ref(false)
const selectedSite = ref('')
const searchKeyword = ref('')
const classes = ref<any[]>([])
const videos = ref<any[]>([])
const currentTid = ref('')
const currentPage = ref(1)
const pagecount = ref(1)
const allSites = ref<any[]>([])
const defaultPic = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 140"><rect fill="%23333" width="100" height="140"/></svg>'

// 只显示点播站点（过滤掉直播/体育相关站点）
const LIVE_KEYWORDS = ['直播', '体育', '赛事', '球']
const vodSites = computed(() => allSites.value.filter(s => {
  if (s.type !== 1) return false
  const name = s.name || s.key || ''
  return !LIVE_KEYWORDS.some(kw => name.includes(kw))
}))

const vodSiteOptions = computed(() => vodSites.value.map(s => ({ label: s.name, value: s.key })))
const hasSite = computed(() => vodSites.value.length > 0)

async function fetchSites() {
  const { getSites } = await import('@/api/config')
  const res: any = await getSites()
  allSites.value = res.data || []
}

async function loadHome() {
  loading.value = true
  try {
    const { vodAPI } = await import('@/api/vod')
    const res: any = await vodAPI.home(selectedSite.value, true)
    classes.value = res.class || []
    videos.value = res.list || []
    pagecount.value = res.pagecount || 1
  } catch (e: any) {
    window.$message?.error('加载首页失败')
  } finally {
    loading.value = false
  }
}

function onSiteChange(_key: string) {
  currentTid.value = ''
  currentPage.value = 1
  loadHome()
}

async function onCategoryClick(tid: string, _name: string) {
  currentTid.value = tid
  currentPage.value = 1
  await loadCategory()
}

async function loadCategory() {
  loading.value = true
  try {
    const { vodAPI } = await import('@/api/vod')
    const res: any = await vodAPI.category(selectedSite.value, currentTid.value, 1)
    videos.value = res.list || []
    pagecount.value = res.pagecount || 1
  } catch (e: any) {
    window.$message?.error('加载分类失败')
  } finally {
    loading.value = false
  }
}

async function onPageChange(page: number) {
  currentPage.value = page
  loading.value = true
  try {
    const { vodAPI } = await import('@/api/vod')
    const res: any = await vodAPI.category(selectedSite.value, currentTid.value, page)
    videos.value = res.list || []
  } catch (e: any) {
    window.$message?.error('加载分页失败')
  } finally {
    loading.value = false
  }
}

function doSearch() {
  if (!searchKeyword.value.trim()) return
  router.push({ path: '/search', query: { wd: searchKeyword.value } })
}

function goDetail(id: string) {
  router.push(`/detail/${selectedSite.value}/${id}`)
}

onMounted(async () => {
  await fetchSites()
  if (vodSites.value.length > 0) {
    selectedSite.value = vodSites.value[0].key
    await loadHome()
  }
  initLoading.value = false
})
</script>

<style scoped>
.home-page { padding: 20px; max-width: 1600px; margin: 0 auto; min-height: 100vh; }
.init-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; text-align: center; }
.empty-icon { margin-bottom: 16px; }
.empty-state h2 { font-size: 28px; margin: 0 0 8px; }
.empty-state p { font-size: 16px; color: #888; margin: 0 0 24px; }
.home-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.site-select { width: 280px; }
.search-input { flex: 1; }
.class-bar { margin-bottom: 20px; background: var(--n-card-color); border-radius: 12px; padding: 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.class-tags { display: flex; gap: 8px; flex-wrap: nowrap; }
.class-tag {
  flex-shrink: 0; padding: 6px 16px; border: 1px solid rgba(255,255,255,0.15);
  border-radius: 20px; background: rgba(255,255,255,0.06); cursor: pointer; font-size: 13px;
  transition: all 0.2s; white-space: nowrap; color: #ccc;
}
.class-tag:hover { border-color: var(--n-primary-color); color: #fff; background: rgba(0,170,238,0.1); }
.class-tag.active { background: var(--n-primary-color); border-color: var(--n-primary-color); color: #fff; }
.quick-entry { display: flex; gap: 12px; margin-bottom: 24px; }
.quick-card { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 16px; background: var(--n-card-color); border-radius: 12px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.quick-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); color: var(--n-primary-color); }
.quick-card span { font-size: 14px; font-weight: 500; }
.quick-icon { font-size: 24px; display:flex; align-items:center; }
.video-section { margin-bottom: 24px; }
.no-data { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; }
.no-data p { color: #888; }
.skeleton-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.skeleton-card { border-radius: 12px; overflow: hidden; }
.video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.video-card { border-radius: 12px; overflow: hidden; background: var(--n-card-color); cursor: pointer; transition: all 0.3s; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.video-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); }
.card-cover { position: relative; aspect-ratio: 2/3; overflow: hidden; background: #1a1a2e; }
.card-cover img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
.video-card:hover .card-cover img { transform: scale(1.05); }
.cover-badge { position: absolute; top: 8px; right: 8px; background: rgba(255,80,80,0.9); color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 500; }
.cover-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.4); opacity: 0; transition: opacity 0.3s; }
.video-card:hover .cover-overlay { opacity: 1; }
.play-icon { width: 48px; height: 48px; background: rgba(255,255,255,0.9); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #333; padding-left: 4px; }
.card-info { padding: 10px 12px; }
.video-name { font-size: 13px; font-weight: 500; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 6px; }
.video-meta { display: flex; gap: 4px; flex-wrap: wrap; }
.meta-tag { font-size: 10px; color: #888; background: var(--n-divider-color); padding: 1px 6px; border-radius: 3px; }
.pagination { display: flex; justify-content: center; margin-top: 24px; }
</style>
