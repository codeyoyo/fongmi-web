export interface ConfigInfo {
  id: string
  name: string
  site_count: number
  updated_at: string
  active: boolean
}

export interface SiteInfo {
  id: string
  name: string
  type: string
  key: string
}
