import { request } from './request'

export const liveAPI = {
  groups: () => request.get('/api/live/groups'),
  channels: (sourceIdx: number) => request.get('/api/live/channels', { params: { source_idx: sourceIdx } }),
  epg: (channel: string) => request.get('/api/live/epg', { params: { channel } }),
  playUrl: (sourceIdx: number, channelIdx: number) =>
    request.get('/api/player/live_url', { params: { source_idx: sourceIdx, channel_idx: channelIdx } }),
}
