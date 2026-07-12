import { request } from './request'

export const historyAPI = {
  list: (page = 1, size = 20) => request.get('/api/history', { params: { page, size } }),
  add: (data: any) => request.post('/api/history', data),
  update: (data: any) => request.put('/api/history', data),
  delete: (id: number) => request.delete(`/api/history/${id}`),
  clear: () => request.delete('/api/history'),
}

export const keepAPI = {
  list: (page = 1, size = 20) => request.get('/api/keep', { params: { page, size } }),
  add: (data: any) => request.post('/api/keep', data),
  delete: (id: number) => request.delete(`/api/keep/${id}`),
  check: (siteKey: string, vodId: string) => request.get('/api/keep/check', { params: { site_key: siteKey, vod_id: vodId } }),
}
