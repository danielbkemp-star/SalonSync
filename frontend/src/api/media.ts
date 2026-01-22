import { api } from './client'

export interface ColorFormula {
  brand: string
  line?: string
  color: string
  developer?: string
  ratio?: string
  processing_time_mins?: number
  notes?: string
}

export interface MediaSet {
  id: number
  salon_id: number
  staff_id: number
  client_id?: number
  appointment_id?: number
  title?: string
  before_photo_url?: string
  after_photo_url?: string
  comparison_photo_url?: string
  color_formulas?: ColorFormula[]
  products_used?: { name: string; brand?: string }[]
  services_performed?: string[]
  techniques_used?: string[]
  starting_level?: string
  achieved_level?: string
  tags?: string[]
  notes?: string
  ai_generated_caption?: string
  suggested_hashtags?: string[]
  client_photo_consent: boolean
  client_social_consent: boolean
  client_website_consent: boolean
  is_portfolio_piece: boolean
  is_private: boolean
  service_date?: string
  created_at: string
  updated_at?: string
}

export interface MediaSetCreate {
  salon_id: number
  client_id?: number
  appointment_id?: number
  title?: string
  before_photo_url?: string
  after_photo_url?: string
  color_formulas?: ColorFormula[]
  products_used?: { name: string; brand?: string }[]
  services_performed?: string[]
  techniques_used?: string[]
  starting_level?: string
  achieved_level?: string
  tags?: string[]
  notes?: string
  client_photo_consent?: boolean
  client_social_consent?: boolean
  client_website_consent?: boolean
  is_portfolio_piece?: boolean
  service_date?: string
}

export interface CaptionResult {
  caption: string
  hashtags: string[]
  alt_captions?: string[]
  suggested_post_time?: string
  confidence_score?: number
}

export const mediaApi = {
  // List media sets for a salon
  list: async (salonId: number, params?: {
    skip?: number
    limit?: number
    staff_id?: number
    client_id?: number
  }) => {
    const response = await api.get(`/salons/${salonId}/media-sets`, { params })
    return response.data
  },

  // Get single media set
  get: async (mediaSetId: number): Promise<MediaSet> => {
    const response = await api.get(`/media-sets/${mediaSetId}`)
    return response.data
  },

  // Create media set
  create: async (salonId: number, data: MediaSetCreate): Promise<MediaSet> => {
    const response = await api.post(`/salons/${salonId}/media-sets`, data)
    return response.data
  },

  // Update media set
  update: async (mediaSetId: number, data: Partial<MediaSetCreate>): Promise<MediaSet> => {
    const response = await api.put(`/media-sets/${mediaSetId}`, data)
    return response.data
  },

  // Delete media set
  delete: async (mediaSetId: number): Promise<void> => {
    await api.delete(`/media-sets/${mediaSetId}`)
  },

  // Generate comparison image
  generateComparison: async (mediaSetId: number, layout: string = 'side_by_side') => {
    const response = await api.post(`/media-sets/${mediaSetId}/generate-comparison`, { layout })
    return response.data
  },

  // Generate AI caption
  generateCaption: async (
    mediaSetId: number,
    options?: {
      tone?: 'professional' | 'playful' | 'luxurious' | 'educational'
      include_hashtags?: boolean
      include_call_to_action?: boolean
      custom_instructions?: string
    }
  ): Promise<CaptionResult> => {
    const response = await api.post(`/media-sets/${mediaSetId}/generate-caption`, {
      tone: options?.tone || 'professional',
      include_hashtags: options?.include_hashtags ?? true,
      include_call_to_action: options?.include_call_to_action ?? true,
      custom_instructions: options?.custom_instructions,
    })
    return response.data
  },

  // Add formula to media set
  addFormula: async (mediaSetId: number, formula: ColorFormula) => {
    const response = await api.post(`/media-sets/${mediaSetId}/add-formula`, formula)
    return response.data
  },

  // Search media sets
  search: async (salonId: number, filters: {
    tags?: string[]
    techniques?: string[]
    has_before_after?: boolean
    is_portfolio_piece?: boolean
    can_post_to_social?: boolean
    date_from?: string
    date_to?: string
  }) => {
    const response = await api.post(`/salons/${salonId}/media-sets/search`, filters)
    return response.data
  },

  // Upload photo (returns URL)
  uploadPhoto: async (file: File, folder: string = 'media') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder', folder)

    const response = await api.post('/upload/photo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}
