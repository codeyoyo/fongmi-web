import { defineStore } from 'pinia'
import { ref } from 'vue'
import { importConfig, getConfigs, deleteConfig, activateConfig, getSites } from '@/api/config'
import type { ConfigInfo, SiteInfo } from '@/types'

export const useConfigStore = defineStore('config', () => {
  const configList = ref<ConfigInfo[]>([])
  const activeConfig = ref<ConfigInfo | null>(null)
  const siteList = ref<SiteInfo[]>([])
  const activeSite = ref<SiteInfo | null>(null)

  async function importConfigAction(data: { url?: string; content?: string; type: string }) {
    return await importConfig(data)
  }

  async function fetchConfigs() {
    const res = await getConfigs()
    configList.value = res.data
  }

  async function activateConfigAction(id: number | string) {
    await activateConfig(Number(id))
    await fetchConfigs()
  }

  async function deleteConfigAction(id: number | string) {
    await deleteConfig(Number(id))
    await fetchConfigs()
  }

  async function fetchSites() {
    const res = await getSites()
    siteList.value = res.data
  }

  return {
    configList,
    activeConfig,
    siteList,
    activeSite,
    importConfig: importConfigAction,
    fetchConfigs,
    activateConfig: activateConfigAction,
    deleteConfig: deleteConfigAction,
    fetchSites
  }
})
