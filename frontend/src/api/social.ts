import { api } from './client'

export interface SocialPost {
  id: number
  salon_id: number
  media_set_id?: number
  platform: 'instagram' | 'instagram_stories' | 'instagram_reels' | 'tiktok' | 'facebook'
  status: 'draft' | 'scheduled' | 'published' | 'failed'
  caption?: string
  hashtags?: string[]
  image_urls?: string[]
  scheduled_time?: string
  published_time?: string
  platform_post_id?: string
  platform_post_url?: string
  likes_count?: number
  comments_count?: number
  shares_count?: number
  saves_count?: number
  reach_count?: number
  impressions_count?: number
  engagement_rate?: number
  created_at: string
  updated_at?: string
}

export interface SocialPostCreate {
  media_set_id?: number
  platform: string
  caption?: string
  hashtags?: string[]
  image_urls?: string[]
  scheduled_time?: string
}

export interface SocialAnalytics {
  salon_id: number
  total_posts: number
  total_likes: number
  total_comments: number
  total_shares: number
  total_reach: number
  avg_engagement_rate: number
  posts_this_week: number
  best_performing_post?: SocialPost
}

export interface BestTimeToPost {
  platform: string
  best_hours: number[]
  best_days: string[]
  data_source: string
  note?: string
}

export const socialApi = {
  // List social posts for a salon
  list: async (salonId: number, params?: {
    skip?: number
    limit?: number
    platform?: string
    status?: string
  }) => {
    const response = await api.get(`/salons/${salonId}/social-posts`, { params })
    return response.data
  },

  // Get single post
  get: async (postId: number): Promise<SocialPost> => {
    const response = await api.get(`/social-posts/${postId}`)
    return response.data
  },

  // Create post
  create: async (salonId: number, data: SocialPostCreate): Promise<SocialPost> => {
    const response = await api.post(`/salons/${salonId}/social-posts`, data)
    return response.data
  },

  // Update post
  update: async (postId: number, data: Partial<SocialPostCreate>): Promise<SocialPost> => {
    const response = await api.put(`/social-posts/${postId}`, data)
    return response.data
  },

  // Delete post
  delete: async (postId: number): Promise<void> => {
    await api.delete(`/social-posts/${postId}`)
  },

  // Schedule post
  schedule: async (postId: number, scheduledTime: string): Promise<SocialPost> => {
    const response = await api.post(`/social-posts/${postId}/schedule`, {
      scheduled_time: scheduledTime,
    })
    return response.data
  },

  // Publish post immediately
  publish: async (postId: number) => {
    const response = await api.post(`/social-posts/${postId}/publish`)
    return response.data
  },

  // Generate caption for a post
  generateCaption: async (
    postId: number,
    options?: {
      tone?: string
      custom_instructions?: string
    }
  ) => {
    const response = await api.post(`/social-posts/${postId}/generate-caption`, options)
    return response.data
  },

  // Get post insights
  getInsights: async (postId: number) => {
    const response = await api.get(`/social-posts/${postId}/insights`)
    return response.data
  },

  // Get salon analytics
  getAnalytics: async (salonId: number): Promise<SocialAnalytics> => {
    const response = await api.get(`/salons/${salonId}/social-analytics`)
    return response.data
  },

  // Get best times to post
  getBestTimes: async (salonId: number): Promise<BestTimeToPost[]> => {
    const response = await api.get(`/salons/${salonId}/best-times-to-post`)
    return response.data
  },
}
