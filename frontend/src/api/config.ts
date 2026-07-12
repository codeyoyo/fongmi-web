import request from './request'

export function importConfig(data: { url?: string; content?: string; type: string }) {
  return request.post('/config/import', data)
}

export function getConfigs() {
  return request.get('/config/') as unknown as Promise<{ code: number; data: any[] }>
}

export function deleteConfig(id: number) {
  return request.delete(`/config/${id}`)
}

export function activateConfig(id: number) {
  return request.put(`/config/${id}/activate`)
}

export function getSites() {
  return request.get('/config/site/') as unknown as Promise<{ code: number; data: any[] }>
}
