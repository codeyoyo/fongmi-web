import { reactive } from 'vue'
import { vodAPI as api } from '@/api/vod'

interface VodInfo {
  vod_id: string
  vod_name: string
  vod_pic?: string
  vod_remarks?: string
  vod_year?: string
  vod_area?: string
  vod_actor?: string
  vod_director?: string
  vod_content?: string
  vod_play_from?: string
  vod_play_url?: string
  vod_tag?: string
  type_name?: string
}

interface ClassItem {
  type_id: string
  type_name: string
  type_flag?: string
}

export const vodStore = reactive({
  siteKey: '',
  classes: [] as ClassItem[],
  videos: [] as VodInfo[],
  detail: null as VodInfo | null,
  loading: false,
  pg: 1,
  tid: '',
  extend: {} as Record<string, string>,
  pagecount: 1,
  total: 0,
  setSite(siteKey: string) {
    this.siteKey = siteKey
  },
  async loadHome(siteKey: string) {
    this.loading = true
    this.siteKey = siteKey
    try {
      const res: any = await api.home(siteKey)
      this.classes = res.class || []
      this.videos = res.list || []
      this.pagecount = res.pagecount || 1
      this.total = res.total || 0
    } finally {
      this.loading = false
    }
  },
  async loadCategory(siteKey: string, tid: string, pg = 1) {
    this.loading = true
    this.siteKey = siteKey
    this.tid = tid
    this.pg = pg
    try {
      const res: any = await api.category(siteKey, tid, pg, this.extend)
      this.videos = res.list || []
      this.pagecount = res.pagecount || 1
      this.total = res.total || 0
    } finally {
      this.loading = false
    }
  },
  async loadDetail(siteKey: string, ids: string) {
    this.loading = true
    this.siteKey = siteKey
    try {
      const res: any = await api.detail(siteKey, ids)
      if (res.list && res.list.length > 0) {
        this.detail = res.list[0]
      }
    } finally {
      this.loading = false
    }
  },
  parseEpisodes(): { flag: string; name: string; episodes: { name: string; url: string }[] }[] {
    if (!this.detail) return []
    const playFrom = (this.detail.vod_play_from || '').split('$$$')
    const playUrl = (this.detail.vod_play_url || '').split('$$$')
    return playFrom.map((flag, i) => {
      const eps = (playUrl[i] || '').split('#').filter(Boolean).map(ep => {
        const [name, url] = ep.split('$')
        return { name: name || '播放', url: url || '' }
      }).filter(e => e.url)
      return { flag: flag || `源${i + 1}`, name: flag || `源${i + 1}`, episodes: eps }
    })
  },
})
