import { defineStore } from 'pinia'
import { ref } from 'vue'
import { liveAPI } from '@/api/live'

export const useLiveStore = defineStore('live', () => {
  const groups = ref<any[]>([])
  const channels = ref<any[]>([])
  const currentSourceIdx = ref(0)
  const currentChannelIdx = ref(0)
  const playUrl = ref('')
  const epgList = ref<any[]>([])
  const loading = ref(false)

  async function loadGroups() {
    loading.value = true
    try {
      const res = await liveAPI.groups()
      const data = (res as any).data || res
      groups.value = Array.isArray(data) ? data : []
      if (groups.value.length > 0) {
        await loadChannels(0)
      }
    } finally {
      loading.value = false
    }
  }

  async function loadChannels(sourceIdx: number) {
    loading.value = true
    currentSourceIdx.value = sourceIdx
    try {
      const res = await liveAPI.channels(sourceIdx)
      const data = (res as any).data || res
      channels.value = Array.isArray(data) ? data : []
      if (channels.value.length > 0) {
        currentChannelIdx.value = 0
        await playChannel(sourceIdx, 0)
      }
    } finally {
      loading.value = false
    }
  }

  async function playChannel(sourceIdx: number, channelIdx: number) {
    currentSourceIdx.value = sourceIdx
    currentChannelIdx.value = channelIdx
    loading.value = true
    try {
      const res = await liveAPI.playUrl(sourceIdx, channelIdx)
      const data = (res as any).data || res
      playUrl.value = data.url || data.playurl || ''
      const channel = channels.value[channelIdx]
      if (channel) {
        await loadEpg(channel.name || channel.channel || '')
      }
    } finally {
      loading.value = false
    }
  }

  async function loadEpg(channel: string) {
    try {
      const res = await liveAPI.epg(channel)
      const data = (res as any).data || res
      epgList.value = Array.isArray(data) ? data : []
    } catch {
      epgList.value = []
    }
  }

  return {
    groups, channels, currentSourceIdx, currentChannelIdx, playUrl, epgList, loading,
    loadGroups, loadChannels, playChannel, loadEpg
  }
})
