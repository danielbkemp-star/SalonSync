import { useState } from 'react'
import { GlassCard } from '@/components/ui'
import { Button } from '@/components/ui'
import { Textarea, Select } from '@/components/ui'
import { mediaApi, MediaSet, CaptionResult } from '@/api/media'
import {
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Hash,
  Clock,
  Wand2,
} from 'lucide-react'

interface CaptionGeneratorProps {
  mediaSet: MediaSet
  onSave?: (caption: string, hashtags: string[]) => void
}

const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional' },
  { value: 'playful', label: 'Playful & Fun' },
  { value: 'luxurious', label: 'Luxurious' },
  { value: 'educational', label: 'Educational' },
]

export function CaptionGenerator({ mediaSet, onSave }: CaptionGeneratorProps) {
  const [tone, setTone] = useState<string>('professional')
  const [includeHashtags, setIncludeHashtags] = useState(true)
  const [includeCTA, setIncludeCTA] = useState(true)
  const [customInstructions, setCustomInstructions] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<CaptionResult | null>(null)
  const [selectedCaption, setSelectedCaption] = useState<string>('')
  const [selectedHashtags, setSelectedHashtags] = useState<string[]>([])
  const [copiedCaption, setCopiedCaption] = useState(false)
  const [copiedHashtags, setCopiedHashtags] = useState(false)

  const generateCaption = async () => {
    setIsGenerating(true)
    try {
      const captionResult = await mediaApi.generateCaption(mediaSet.id, {
        tone: tone as 'professional' | 'playful' | 'luxurious' | 'educational',
        include_hashtags: includeHashtags,
        include_call_to_action: includeCTA,
        custom_instructions: customInstructions || undefined,
      })
      setResult(captionResult)
      setSelectedCaption(captionResult.caption)
      setSelectedHashtags(captionResult.hashtags)
    } catch (error) {
      console.error('Failed to generate caption:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = async (text: string, type: 'caption' | 'hashtags') => {
    await navigator.clipboard.writeText(text)
    if (type === 'caption') {
      setCopiedCaption(true)
      setTimeout(() => setCopiedCaption(false), 2000)
    } else {
      setCopiedHashtags(true)
      setTimeout(() => setCopiedHashtags(false), 2000)
    }
  }

  const selectAltCaption = (caption: string) => {
    setSelectedCaption(caption)
  }

  const toggleHashtag = (hashtag: string) => {
    setSelectedHashtags((prev) =>
      prev.includes(hashtag)
        ? prev.filter((h) => h !== hashtag)
        : [...prev, hashtag]
    )
  }

  const handleSave = () => {
    onSave?.(selectedCaption, selectedHashtags)
  }

  return (
    <div className="space-y-6">
      {/* Generation Options */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Wand2 className="w-5 h-5 text-brand-plum-400" />
          Caption Settings
        </h3>

        <div className="space-y-4">
          <Select
            label="Tone"
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            options={TONE_OPTIONS}
          />

          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeHashtags}
                onChange={(e) => setIncludeHashtags(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-white/10 text-brand-plum-500 focus:ring-brand-plum-500"
              />
              <span className="text-white/80 text-sm">Include hashtags</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeCTA}
                onChange={(e) => setIncludeCTA(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-white/10 text-brand-plum-500 focus:ring-brand-plum-500"
              />
              <span className="text-white/80 text-sm">Include call-to-action</span>
            </label>
          </div>

          <Textarea
            label="Custom Instructions (optional)"
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="e.g., Mention our summer promotion, focus on the color technique..."
            rows={2}
          />

          <Button
            variant="primary"
            className="w-full"
            onClick={generateCaption}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Caption
              </>
            )}
          </Button>
        </div>
      </GlassCard>

      {/* Generated Result */}
      {result && (
        <>
          {/* Main Caption */}
          <GlassCard glow="plum">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                Generated Caption
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(selectedCaption, 'caption')}
              >
                {copiedCaption ? (
                  <>
                    <Check className="w-4 h-4 mr-1 text-green-400" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-1" />
                    Copy
                  </>
                )}
              </Button>
            </div>

            <Textarea
              value={selectedCaption}
              onChange={(e) => setSelectedCaption(e.target.value)}
              rows={4}
              className="mb-4"
            />

            {/* Alternative Captions */}
            {result.alt_captions && result.alt_captions.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/10">
                <p className="text-sm text-white/60 mb-2">
                  Alternative options:
                </p>
                <div className="space-y-2">
                  {result.alt_captions.map((alt, index) => (
                    <button
                      key={index}
                      onClick={() => selectAltCaption(alt)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        selectedCaption === alt
                          ? 'bg-brand-plum-500/30 border border-brand-plum-500/50'
                          : 'bg-white/5 border border-white/10 hover:bg-white/10'
                      }`}
                    >
                      <p className="text-white/80 text-sm line-clamp-2">{alt}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </GlassCard>

          {/* Hashtags */}
          {result.hashtags.length > 0 && (
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Hash className="w-5 h-5 text-brand-rose-400" />
                  Hashtags
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    copyToClipboard(
                      selectedHashtags.map((h) => `#${h}`).join(' '),
                      'hashtags'
                    )
                  }
                >
                  {copiedHashtags ? (
                    <>
                      <Check className="w-4 h-4 mr-1 text-green-400" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-1" />
                      Copy All
                    </>
                  )}
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {result.hashtags.map((hashtag) => (
                  <button
                    key={hashtag}
                    onClick={() => toggleHashtag(hashtag)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                      selectedHashtags.includes(hashtag)
                        ? 'bg-brand-rose-500 text-white'
                        : 'bg-white/10 text-white/50 hover:bg-white/20 line-through'
                    }`}
                  >
                    #{hashtag}
                  </button>
                ))}
              </div>

              <p className="text-xs text-white/40 mt-3">
                Click to toggle hashtags. {selectedHashtags.length} selected.
              </p>
            </GlassCard>
          )}

          {/* Best Time to Post */}
          {result.suggested_post_time && (
            <GlassCard>
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <Clock className="w-5 h-5 text-brand-gold-400" />
                Best Time to Post
              </h3>
              <p className="text-white/80">{result.suggested_post_time}</p>
              <p className="text-xs text-white/40 mt-1">
                Based on your audience engagement patterns
              </p>
            </GlassCard>
          )}

          {/* Save Button */}
          {onSave && (
            <Button variant="primary" className="w-full" onClick={handleSave}>
              <Check className="w-4 h-4 mr-2" />
              Save Caption & Hashtags
            </Button>
          )}
        </>
      )}
    </div>
  )
}
