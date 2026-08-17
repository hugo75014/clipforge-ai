import { cn } from '@/lib/utils'

interface Props {
  label: string
  value: number
  className?: string
  showValue?: boolean
}

export default function ScoreBar({ label, value, className, showValue = true }: Props) {
  const v = Math.max(0, Math.min(100, value))
  const tone =
    v >= 80 ? 'from-emerald-400 to-cyan-400' : v >= 60 ? 'from-amber-400 to-pink-400' : 'from-ink-500 to-ink-600'
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="text-[10px] uppercase tracking-wider text-ink-400 w-16 shrink-0">{label}</div>
      <div className="flex-1 progress-track h-1">
        <div className={cn('h-full bg-gradient-to-r', tone)} style={{ width: `${v}%` }} />
      </div>
      {showValue && <div className="text-[10px] tabular-nums text-ink-300 w-7 text-right">{Math.round(v)}</div>}
    </div>
  )
}
