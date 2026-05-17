export interface Product {
  id: number
  name: string
  category: string
  source: string
  total_score: number
  price: number | null
  active: boolean
  created_at: string
}

export interface Video {
  id: number
  product_id: number
  week: string
  status: string
  renderer: string
  total_cost: number
  created_at: string
}

export interface CreativePack {
  id: number
  video_id: number
  version: number
  hook: string
  caption: string
  compliance_status: string
  selected: boolean
}

export interface VideoEvent {
  id: number
  event_type: string
  actor: string
  details: Record<string, any> | null
  created_at: string
}
