import { reactive } from 'vue'

export const siteStore = reactive({
  siteList: [] as any[],
  get hasSite() { return this.siteList.length > 0 },
  async fetchSites() {
    const { getSites } = await import('@/api/config')
    const res: any = await getSites()
    this.siteList = res.data || []
  },
})
