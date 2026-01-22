import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { SalonBackground } from '@/components/dashboard/CommandCenter/SalonBackground'
import { GlassCard, GlassCardCompact } from '@/components/ui'
import { Button } from '@/components/ui'
import { Input, Textarea, Select } from '@/components/ui'
import { mediaApi, MediaSetCreate, ColorFormula } from '@/api/media'
import {
  Camera,
  Upload,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Check,
  X,
  Plus,
  Trash2,
  Image as ImageIcon,
} from 'lucide-react'

type CaptureStep = 'before' | 'after' | 'details' | 'preview'

const COMMON_SERVICES = [
  'Haircut',
  'Balayage',
  'Highlights',
  'Color Correction',
  'Root Touch-up',
  'Keratin Treatment',
  'Blowout',
  'Extensions',
]

const COMMON_TECHNIQUES = [
  'Foilayage',
  'Hand-painted',
  'Babylights',
  'Shadow Root',
  'Toner',
  'Gloss',
  'Olaplex',
  'Deep Condition',
]

export function CapturePage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState<CaptureStep>('before')
  const [isLoading, setIsLoading] = useState(false)
  const [currentPhotoType, setCurrentPhotoType] = useState<'before' | 'after'>('before')

  const [beforePhoto, setBeforePhoto] = useState<string | null>(null)
  const [afterPhoto, setAfterPhoto] = useState<string | null>(null)
  const [beforeFile, setBeforeFile] = useState<File | null>(null)
  const [afterFile, setAfterFile] = useState<File | null>(null)

  const [formData, setFormData] = useState<Partial<MediaSetCreate>>({
    title: '',
    services_performed: [],
    techniques_used: [],
    starting_level: '',
    achieved_level: '',
    tags: [],
    notes: '',
    client_photo_consent: true,
    client_social_consent: false,
    is_portfolio_piece: true,
  })

  const [colorFormulas, setColorFormulas] = useState<ColorFormula[]>([])
  const [newFormula, setNewFormula] = useState<ColorFormula>({
    brand: '',
    line: '',
    color: '',
    developer: '',
    ratio: '',
    processing_time_mins: undefined,
    notes: '',
  })

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      if (currentPhotoType === 'before') {
        setBeforePhoto(dataUrl)
        setBeforeFile(file)
      } else {
        setAfterPhoto(dataUrl)
        setAfterFile(file)
      }
    }
    reader.readAsDataURL(file)
  }

  const triggerFileSelect = (type: 'before' | 'after') => {
    setCurrentPhotoType(type)
    fileInputRef.current?.click()
  }

  const toggleArrayItem = (
    field: 'services_performed' | 'techniques_used',
    item: string
  ) => {
    const current = formData[field] || []
    const updated = current.includes(item)
      ? current.filter((i) => i !== item)
      : [...current, item]
    setFormData((prev) => ({ ...prev, [field]: updated }))
  }

  const addFormula = () => {
    if (newFormula.brand && newFormula.color) {
      setColorFormulas((prev) => [...prev, newFormula])
      setNewFormula({
        brand: '',
        line: '',
        color: '',
        developer: '',
        ratio: '',
        processing_time_mins: undefined,
        notes: '',
      })
    }
  }

  const removeFormula = (index: number) => {
    setColorFormulas((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    setIsLoading(true)
    try {
      // Upload photos first
      let beforeUrl: string | undefined
      let afterUrl: string | undefined

      if (beforeFile) {
        const result = await mediaApi.uploadPhoto(beforeFile, 'before')
        beforeUrl = result.url
      }
      if (afterFile) {
        const result = await mediaApi.uploadPhoto(afterFile, 'after')
        afterUrl = result.url
      }

      // Create media set
      const mediaSet = await mediaApi.create(1, {
        ...formData,
        before_photo_url: beforeUrl,
        after_photo_url: afterUrl,
        color_formulas: colorFormulas,
        salon_id: 1, // TODO: Get from auth context
      } as MediaSetCreate)

      // Navigate to caption generator
      navigate(`/social/create?mediaSetId=${mediaSet.id}`)
    } catch (error) {
      console.error('Failed to create media set:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const canProceed = () => {
    switch (step) {
      case 'before':
        return !!beforePhoto
      case 'after':
        return !!afterPhoto
      case 'details':
        return (formData.services_performed?.length || 0) > 0
      case 'preview':
        return true
      default:
        return false
    }
  }

  const nextStep = () => {
    const steps: CaptureStep[] = ['before', 'after', 'details', 'preview']
    const currentIndex = steps.indexOf(step)
    if (currentIndex < steps.length - 1) {
      setStep(steps[currentIndex + 1])
    }
  }

  const prevStep = () => {
    const steps: CaptureStep[] = ['before', 'after', 'details', 'preview']
    const currentIndex = steps.indexOf(step)
    if (currentIndex > 0) {
      setStep(steps[currentIndex - 1])
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      <SalonBackground />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileSelect}
      />

      <div className="relative z-10 min-h-screen">
        {/* Header */}
        <header className="sticky top-0 z-20 backdrop-blur-xl bg-brand-dark-900/80 border-b border-white/10">
          <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-white/70 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Dashboard</span>
            </button>

            <div className="flex items-center gap-2">
              {['before', 'after', 'details', 'preview'].map((s, i) => (
                <div
                  key={s}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    step === s
                      ? 'bg-brand-plum-500'
                      : ['before', 'after', 'details', 'preview'].indexOf(step) > i
                      ? 'bg-brand-plum-500/50'
                      : 'bg-white/20'
                  }`}
                />
              ))}
            </div>

            <div className="w-20" /> {/* Spacer for alignment */}
          </div>
        </header>

        {/* Content */}
        <main className="max-w-4xl mx-auto px-4 py-8">
          {/* Before Photo Step */}
          {step === 'before' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white mb-2">
                  Capture Before Photo
                </h1>
                <p className="text-white/60">
                  Start by taking a photo of your client before the service
                </p>
              </div>

              <GlassCard className="aspect-[4/3] flex items-center justify-center">
                {beforePhoto ? (
                  <div className="relative w-full h-full">
                    <img
                      src={beforePhoto}
                      alt="Before"
                      className="w-full h-full object-cover rounded-xl"
                    />
                    <button
                      onClick={() => {
                        setBeforePhoto(null)
                        setBeforeFile(null)
                      }}
                      className="absolute top-4 right-4 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                ) : (
                  <div className="text-center space-y-4">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white/10">
                      <Camera className="w-10 h-10 text-white/60" />
                    </div>
                    <p className="text-white/60">No photo yet</p>
                    <div className="flex gap-3 justify-center">
                      <Button
                        variant="primary"
                        onClick={() => triggerFileSelect('before')}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Photo
                      </Button>
                    </div>
                  </div>
                )}
              </GlassCard>
            </div>
          )}

          {/* After Photo Step */}
          {step === 'after' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white mb-2">
                  Capture After Photo
                </h1>
                <p className="text-white/60">
                  Now capture the stunning transformation
                </p>
              </div>

              {/* Side by side preview */}
              <div className="grid grid-cols-2 gap-4">
                <GlassCardCompact className="aspect-square">
                  <p className="text-xs text-white/40 mb-2">Before</p>
                  <img
                    src={beforePhoto!}
                    alt="Before"
                    className="w-full h-full object-cover rounded-lg"
                  />
                </GlassCardCompact>

                <GlassCard className="aspect-square flex items-center justify-center">
                  {afterPhoto ? (
                    <div className="relative w-full h-full">
                      <p className="text-xs text-white/40 mb-2">After</p>
                      <img
                        src={afterPhoto}
                        alt="After"
                        className="w-full h-full object-cover rounded-lg"
                      />
                      <button
                        onClick={() => {
                          setAfterPhoto(null)
                          setAfterFile(null)
                        }}
                        className="absolute top-4 right-4 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ) : (
                    <div className="text-center space-y-4">
                      <Camera className="w-10 h-10 text-white/40 mx-auto" />
                      <Button
                        variant="primary"
                        onClick={() => triggerFileSelect('after')}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload After
                      </Button>
                    </div>
                  )}
                </GlassCard>
              </div>
            </div>
          )}

          {/* Details Step */}
          {step === 'details' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white mb-2">
                  Service Details
                </h1>
                <p className="text-white/60">
                  Add information to help generate the perfect caption
                </p>
              </div>

              <GlassCard>
                <div className="space-y-6">
                  <Input
                    label="Title (optional)"
                    value={formData.title || ''}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, title: e.target.value }))
                    }
                    placeholder="e.g., Summer Balayage Transformation"
                  />

                  {/* Services */}
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-3">
                      Services Performed
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {COMMON_SERVICES.map((service) => (
                        <button
                          key={service}
                          onClick={() =>
                            toggleArrayItem('services_performed', service)
                          }
                          className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                            formData.services_performed?.includes(service)
                              ? 'bg-brand-plum-500 text-white'
                              : 'bg-white/10 text-white/70 hover:bg-white/20'
                          }`}
                        >
                          {service}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Techniques */}
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-3">
                      Techniques Used
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {COMMON_TECHNIQUES.map((technique) => (
                        <button
                          key={technique}
                          onClick={() =>
                            toggleArrayItem('techniques_used', technique)
                          }
                          className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                            formData.techniques_used?.includes(technique)
                              ? 'bg-brand-rose-500 text-white'
                              : 'bg-white/10 text-white/70 hover:bg-white/20'
                          }`}
                        >
                          {technique}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Color Levels */}
                  <div className="grid grid-cols-2 gap-4">
                    <Select
                      label="Starting Level"
                      value={formData.starting_level || ''}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          starting_level: e.target.value,
                        }))
                      }
                      options={[
                        { value: '', label: 'Select level' },
                        ...Array.from({ length: 10 }, (_, i) => ({
                          value: String(i + 1),
                          label: `Level ${i + 1}`,
                        })),
                      ]}
                    />
                    <Select
                      label="Achieved Level"
                      value={formData.achieved_level || ''}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          achieved_level: e.target.value,
                        }))
                      }
                      options={[
                        { value: '', label: 'Select level' },
                        ...Array.from({ length: 10 }, (_, i) => ({
                          value: String(i + 1),
                          label: `Level ${i + 1}`,
                        })),
                      ]}
                    />
                  </div>

                  {/* Color Formulas */}
                  <div>
                    <label className="block text-sm font-medium text-white/80 mb-3">
                      Color Formulas
                    </label>
                    {colorFormulas.length > 0 && (
                      <div className="space-y-2 mb-4">
                        {colorFormulas.map((formula, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10"
                          >
                            <span className="text-white/80">
                              {formula.brand} {formula.line} - {formula.color}
                              {formula.developer && ` + ${formula.developer}`}
                            </span>
                            <button
                              onClick={() => removeFormula(index)}
                              className="p-1 text-red-400 hover:text-red-300"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="grid grid-cols-3 gap-3">
                      <Input
                        placeholder="Brand"
                        value={newFormula.brand}
                        onChange={(e) =>
                          setNewFormula((prev) => ({
                            ...prev,
                            brand: e.target.value,
                          }))
                        }
                      />
                      <Input
                        placeholder="Color"
                        value={newFormula.color}
                        onChange={(e) =>
                          setNewFormula((prev) => ({
                            ...prev,
                            color: e.target.value,
                          }))
                        }
                      />
                      <Button variant="secondary" onClick={addFormula}>
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Notes */}
                  <Textarea
                    label="Notes"
                    value={formData.notes || ''}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, notes: e.target.value }))
                    }
                    placeholder="Any additional details about the service..."
                    rows={3}
                  />

                  {/* Consent */}
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.client_social_consent}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            client_social_consent: e.target.checked,
                          }))
                        }
                        className="w-5 h-5 rounded border-white/20 bg-white/10 text-brand-plum-500 focus:ring-brand-plum-500"
                      />
                      <span className="text-white/80">
                        Client consents to social media posting
                      </span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_portfolio_piece}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            is_portfolio_piece: e.target.checked,
                          }))
                        }
                        className="w-5 h-5 rounded border-white/20 bg-white/10 text-brand-plum-500 focus:ring-brand-plum-500"
                      />
                      <span className="text-white/80">Add to portfolio</span>
                    </label>
                  </div>
                </div>
              </GlassCard>
            </div>
          )}

          {/* Preview Step */}
          {step === 'preview' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white mb-2">
                  Ready to Create
                </h1>
                <p className="text-white/60">
                  Review your media set before generating captions
                </p>
              </div>

              {/* Photos Preview */}
              <div className="grid grid-cols-2 gap-4">
                <GlassCard className="overflow-hidden">
                  <p className="text-xs text-white/40 mb-2 font-medium uppercase tracking-wider">
                    Before
                  </p>
                  <img
                    src={beforePhoto!}
                    alt="Before"
                    className="w-full aspect-square object-cover rounded-xl"
                  />
                </GlassCard>
                <GlassCard className="overflow-hidden">
                  <p className="text-xs text-white/40 mb-2 font-medium uppercase tracking-wider">
                    After
                  </p>
                  <img
                    src={afterPhoto!}
                    alt="After"
                    className="w-full aspect-square object-cover rounded-xl"
                  />
                </GlassCard>
              </div>

              {/* Details Summary */}
              <GlassCard>
                <h3 className="text-lg font-semibold text-white mb-4">
                  Service Summary
                </h3>
                <div className="space-y-4">
                  {formData.title && (
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-wider">
                        Title
                      </p>
                      <p className="text-white">{formData.title}</p>
                    </div>
                  )}

                  {(formData.services_performed?.length || 0) > 0 && (
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-wider mb-2">
                        Services
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {formData.services_performed?.map((service) => (
                          <span
                            key={service}
                            className="px-2 py-1 rounded-full text-xs bg-brand-plum-500/30 text-brand-plum-300"
                          >
                            {service}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {(formData.techniques_used?.length || 0) > 0 && (
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-wider mb-2">
                        Techniques
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {formData.techniques_used?.map((technique) => (
                          <span
                            key={technique}
                            className="px-2 py-1 rounded-full text-xs bg-brand-rose-500/30 text-brand-rose-300"
                          >
                            {technique}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {colorFormulas.length > 0 && (
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-wider mb-2">
                        Color Formulas
                      </p>
                      <div className="space-y-1">
                        {colorFormulas.map((formula, i) => (
                          <p key={i} className="text-white/80 text-sm">
                            {formula.brand} {formula.line} - {formula.color}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-4 pt-2">
                    {formData.client_social_consent && (
                      <span className="flex items-center gap-1 text-green-400 text-sm">
                        <Check className="w-4 h-4" /> Social consent
                      </span>
                    )}
                    {formData.is_portfolio_piece && (
                      <span className="flex items-center gap-1 text-brand-gold-400 text-sm">
                        <ImageIcon className="w-4 h-4" /> Portfolio piece
                      </span>
                    )}
                  </div>
                </div>
              </GlassCard>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <Button
              variant="ghost"
              onClick={prevStep}
              disabled={step === 'before'}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            {step === 'preview' ? (
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={isLoading}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                {isLoading ? 'Creating...' : 'Create & Generate Caption'}
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={nextStep}
                disabled={!canProceed()}
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
