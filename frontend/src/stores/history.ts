import { defineStore } from 'pinia'
import { ref } from 'vue'
import { historyAPI, keepAPI } from '@/api/history'

export const useHistoryStore = defineStore('history', () => {
  const historyList = ref<any[]>([])
  const keepList = ref<any[]>([])
  const loading = ref(false)

  async function loadHistory() {
    loading.value = true
    try {
      const res = await historyAPI.list()
      const data = (res as any).data || res
      historyList.value = Array.isArray(data) ? data : (data.list || [])
    } finally {
      loading.value = false
    }
  }

  async function loadKeep() {
    loading.value = true
    try {
      const res = await keepAPI.list()
      const data = (res as any).data || res
      keepList.value = Array.isArray(data) ? data : (data.list || [])
    } finally {
      loading.value = false
    }
  }

  async function addHistory(data: any) {
    await historyAPI.add(data)
    await loadHistory()
  }

  async function deleteHistory(id: number) {
    await historyAPI.delete(id)
    await loadHistory()
  }

  async function clearHistory() {
    await historyAPI.clear()
    historyList.value = []
  }

  async function addKeep(data: any) {
    await keepAPI.add(data)
    await loadKeep()
  }

  async function deleteKeep(id: number) {
    await keepAPI.delete(id)
    await loadKeep()
  }

  async function checkKeep(siteKey: string, vodId: string): Promise<boolean> {
    const res = await keepAPI.check(siteKey, vodId)
    const data = (res as any).data || res
    return !!data
  }

  return {
    historyList, keepList, loading,
    loadHistory, loadKeep, addHistory, deleteHistory, clearHistory, addKeep, deleteKeep, checkKeep
  }
})
