import { cn } from '@/lib/utils'
import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-white/80"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full px-4 py-2.5 rounded-xl',
            'bg-white/5 border border-white/10',
            'text-white placeholder:text-white/40',
            'focus:outline-none focus:ring-2 focus:ring-brand-plum-500/50 focus:border-brand-plum-500/50',
            'transition-colors duration-200',
            error && 'border-red-500/50 focus:ring-red-500/50 focus:border-red-500/50',
            className
          )}
          {...props}
        />
        {hint && !error && (
          <p className="text-xs text-white/50">{hint}</p>
        )}
        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

// Textarea variant
interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
  charCount?: boolean
  maxLength?: number
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, hint, charCount, maxLength, value, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-')
    const currentLength = typeof value === 'string' ? value.length : 0

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-white/80"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          value={value}
          maxLength={maxLength}
          className={cn(
            'w-full px-4 py-3 rounded-xl resize-none',
            'bg-white/5 border border-white/10',
            'text-white placeholder:text-white/40',
            'focus:outline-none focus:ring-2 focus:ring-brand-plum-500/50 focus:border-brand-plum-500/50',
            'transition-colors duration-200',
            'scrollbar-thin',
            error && 'border-red-500/50 focus:ring-red-500/50 focus:border-red-500/50',
            className
          )}
          {...props}
        />
        <div className="flex justify-between items-center">
          <div>
            {hint && !error && (
              <p className="text-xs text-white/50">{hint}</p>
            )}
            {error && (
              <p className="text-xs text-red-400">{error}</p>
            )}
          </div>
          {charCount && maxLength && (
            <p className={cn(
              'text-xs',
              currentLength > maxLength * 0.9 ? 'text-yellow-400' : 'text-white/40'
            )}>
              {currentLength}/{maxLength}
            </p>
          )}
        </div>
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

// Select component
interface SelectProps extends InputHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: { value: string; label: string }[]
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, id, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-white/80"
          >
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'w-full px-4 py-2.5 rounded-xl appearance-none',
            'bg-white/5 border border-white/10',
            'text-white',
            'focus:outline-none focus:ring-2 focus:ring-brand-plum-500/50 focus:border-brand-plum-500/50',
            'transition-colors duration-200 cursor-pointer',
            'bg-[url("data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 fill=%27none%27 viewBox=%270 0 20 20%27%3e%3cpath stroke=%27%23a3a3a3%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%271.5%27 d=%27M6 8l4 4 4-4%27/%3e%3c/svg%3e")]',
            'bg-[length:1.5em_1.5em] bg-[right_0.5rem_center] bg-no-repeat pr-10',
            error && 'border-red-500/50',
            className
          )}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-gray-800">
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'
