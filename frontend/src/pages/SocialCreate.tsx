import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { GlassCard } from '@/components/ui'
import { Button } from '@/components/ui'
import { CaptionGenerator } from '@/components/social/CaptionGenerator'
import { mediaApi, MediaSet } from '@/api/media'
import { socialApi, SocialPostCreate } from '@/api/social'
import {
  ArrowLeft,
  Instagram,
  Facebook,
  Music2,
  Send,
  Calendar,
  Clock,
} from 'lucide-react'

const PLATFORMS = [
  { value: 'instagram', label: 'Instagram Post', icon: Instagram },
  { value: 'instagram_stories', label: 'Instagram Stories', icon: Instagram },
  { value: 'instagram_reels', label: 'Instagram Reels', icon: Instagram },
  { value: 'facebook', label: 'Facebook', icon: Facebook },
  { value: 'tiktok', label: 'TikTok', icon: Music2 },
]

export function SocialCreatePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const mediaSetId = searchParams.get('mediaSetId')

  const [mediaSet, setMediaSet] = useState<MediaSet | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [platform, setPlatform] = useState<string>('instagram')
  const [caption, setCaption] = useState('')
  const [hashtags, setHashtags] = useState<string[]>([])
  const [scheduleMode, setScheduleMode] = useState<'now' | 'schedule'>('now')
  const [scheduledTime, setScheduledTime] = useState('')
  const [isPublishing, setIsPublishing] = useState(false)

  useEffect(() => {
    if (mediaSetId) {
      loadMediaSet(parseInt(mediaSetId))
    } else {
      setIsLoading(false)
    }
  }, [mediaSetId])

  const loadMediaSet = async (id: number) => {
    try {
      const data = await mediaApi.get(id)
      setMediaSet(data)
      if (data.ai_generated_caption) {
        setCaption(data.ai_generated_caption)
      }
      if (data.suggested_hashtags) {
        setHashtags(data.suggested_hashtags)
      }
    } catch (error) {
      console.error('Failed to load media set:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCaptionSave = (newCaption: string, newHashtags: string[]) => {
    setCaption(newCaption)
    setHashtags(newHashtags)
  }

  const handlePublish = async () => {
    if (!mediaSet) return

    setIsPublishing(true)
    try {
      const postData: SocialPostCreate = {
        media_set_id: mediaSet.id,
        platform,
        caption,
        hashtags,
        image_urls: [
          mediaSet.comparison_photo_url ||
            mediaSet.after_photo_url ||
            mediaSet.before_photo_url,
        ].filter(Boolean) as string[],
        scheduled_time:
          scheduleMode === 'schedule' ? scheduledTime : undefined,
      }

      const post = await socialApi.create(mediaSet.salon_id, postData)

      if (scheduleMode === 'now') {
        await socialApi.publish(post.id)
      } else if (scheduledTime) {
        await socialApi.schedule(post.id, scheduledTime)
      }

      navigate('/social')
    } catch (error) {
      console.error('Failed to publish:', error)
    } finally {
      setIsPublishing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen relative overflow-hidden">
        <SalonBackground />
        <div className="relative z-10 min-h-screen flex items-center justify-center">
          <div className="text-white">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      <SalonBackground />

      <div className="relative z-10 min-h-screen">
        {/* Header */}
        <header className="sticky top-0 z-20 backdrop-blur-xl bg-brand-dark-900/80 border-b border-white/10">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-white/70 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back</span>
            </button>

            <h1 className="text-lg font-semibold text-white">Create Post</h1>

            <div className="w-20" />
          </div>
        </header>

        {/* Content */}
        <main className="max-w-6xl mx-auto px-4 py-8">
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Column - Preview & Platform */}
            <div className="space-y-6">
              {/* Media Preview */}
              {mediaSet && (
                <GlassCard>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    Media Preview
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    {mediaSet.before_photo_url && (
                      <div>
                        <p className="text-xs text-white/40 mb-2">Before</p>
                        <img
                          src={mediaSet.before_photo_url}
                          alt="Before"
                          className="w-full aspect-square object-cover rounded-lg"
                        />
                      </div>
                    )}
                    {mediaSet.after_photo_url && (
                      <div>
                        <p className="text-xs text-white/40 mb-2">After</p>
                        <img
                          src={mediaSet.after_photo_url}
                          alt="After"
                          className="w-full aspect-square object-cover rounded-lg"
                        />
                      </div>
                    )}
                  </div>
                  {mediaSet.comparison_photo_url && (
                    <div className="mt-4">
                      <p className="text-xs text-white/40 mb-2">
                        Comparison (will be posted)
                      </p>
                      <img
                        src={mediaSet.comparison_photo_url}
                        alt="Comparison"
                        className="w-full rounded-lg"
                      />
                    </div>
                  )}
                </GlassCard>
              )}

              {/* Platform Selection */}
              <GlassCard>
                <h3 className="text-lg font-semibold text-white mb-4">
                  Platform
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {PLATFORMS.map(({ value, label, icon: Icon }) => (
                    <button
                      key={value}
                      onClick={() => setPlatform(value)}
                      className={`flex items-center gap-3 p-3 rounded-xl transition-colors ${
                        platform === value
                          ? 'bg-brand-plum-500 text-white'
                          : 'bg-white/5 text-white/70 hover:bg-white/10'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-sm">{label}</span>
                    </button>
                  ))}
                </div>
              </GlassCard>

              {/* Schedule Options */}
              <GlassCard>
                <h3 className="text-lg font-semibold text-white mb-4">
                  When to Post
                </h3>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <button
                      onClick={() => setScheduleMode('now')}
                      className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl transition-colors ${
                        scheduleMode === 'now'
                          ? 'bg-brand-plum-500 text-white'
                          : 'bg-white/5 text-white/70 hover:bg-white/10'
                      }`}
                    >
                      <Send className="w-4 h-4" />
                      Post Now
                    </button>
                    <button
                      onClick={() => setScheduleMode('schedule')}
                      className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl transition-colors ${
                        scheduleMode === 'schedule'
                          ? 'bg-brand-plum-500 text-white'
                          : 'bg-white/5 text-white/70 hover:bg-white/10'
                      }`}
                    >
                      <Calendar className="w-4 h-4" />
                      Schedule
                    </button>
                  </div>

                  {scheduleMode === 'schedule' && (
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                      <Clock className="w-5 h-5 text-white/40" />
                      <input
                        type="datetime-local"
                        value={scheduledTime}
                        onChange={(e) => setScheduledTime(e.target.value)}
                        className="flex-1 bg-transparent text-white focus:outline-none"
                      />
                    </div>
                  )}
                </div>
              </GlassCard>

              {/* Publish Button */}
              <Button
                variant="primary"
                className="w-full"
                onClick={handlePublish}
                disabled={!caption || isPublishing}
              >
                {isPublishing ? (
                  'Publishing...'
                ) : scheduleMode === 'now' ? (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Publish Now
                  </>
                ) : (
                  <>
                    <Calendar className="w-4 h-4 mr-2" />
                    Schedule Post
                  </>
                )}
              </Button>
            </div>

            {/* Right Column - Caption Generator */}
            <div>
              {mediaSet ? (
                <CaptionGenerator
                  mediaSet={mediaSet}
                  onSave={handleCaptionSave}
                />
              ) : (
                <GlassCard>
                  <p className="text-white/60 text-center py-8">
                    No media set selected. Start by capturing photos.
                  </p>
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={() => navigate('/capture')}
                  >
                    Go to Capture
                  </Button>
                </GlassCard>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
