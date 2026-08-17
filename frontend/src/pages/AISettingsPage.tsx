import { useQuery } from '@tanstack/react-query'
import { Sparkles, Cpu, Wand2, AlertCircle, CheckCircle2, Eye, Mic } from 'lucide-react'

import { get } from '@/lib/api'
import { CAPTION_STYLES, CAPTION_POSITIONS, ASPECT_RATIOS, RESOLUTIONS } from '@/lib/constants'

export default function AISettingsPage() {
  const { data: info } = useQuery({
    queryKey: ['ai-info'],
    queryFn: () => get<any>('/api/v1/ai/info'),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">AI settings</h1>
        <p className="text-ink-400 text-sm mt-1">
          Defaults applied to every new project. Override per-clip in the editor.
        </p>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Cpu className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">Provider</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <Info label="AI provider" value={info?.provider || '—'} />
          <Info label="Model" value={info?.model || '—'} />
          <Info label="Transcription" value="Whisper (toggle in .env)" />
          <Info label="Demo mode" value={info?.demo_mode ? 'On' : 'Off'} />
        </div>
        {info?.demo_mode ? (
          <div className="mt-4 flex items-start gap-2 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2.5">
            <AlertCircle className="size-4 mt-0.5 shrink-0" />
            <div>
              <strong>Demo mode is on.</strong> AI completions return realistic mock data so you can
              exercise the whole pipeline without API keys. To use a real provider, set
              <code className="mx-1">AI_PROVIDER=openai</code>
              (or <code>anthropic</code>, <code>gemini</code>, <code>openrouter</code>, <code>local</code>)
              and provide the matching API key in your <code>.env</code>.
            </div>
          </div>
        ) : (
          <div className="mt-4 flex items-start gap-2 text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2.5">
            <CheckCircle2 className="size-4 mt-0.5 shrink-0" />
            <div>Connected to a real provider. Calls will be billed to your account.</div>
          </div>
        )}
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Wand2 className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">Defaults</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <SelectField label="Aspect ratio" value="9:16" options={ASPECT_RATIOS as unknown as string[]} />
          <SelectField label="Resolution" value="1080p" options={RESOLUTIONS as unknown as string[]} />
          <SelectField label="Caption style" value="viral" options={CAPTION_STYLES as unknown as string[]} />
          <SelectField label="Caption position" value="bottom" options={CAPTION_POSITIONS as unknown as string[]} />
        </div>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">AI Clip Finder weights</h2>
        </div>
        <p className="text-sm text-ink-400 mb-4">
          How the heuristic engine combines each axis into the final viral score.
        </p>
        <div className="space-y-2">
          <Weight label="Hook" value={25} />
          <Weight label="Emotion" value={20} />
          <Weight label="Curiosity" value={15} />
          <Weight label="Shareability" value={15} />
          <Weight label="Completion" value={10} />
          <Weight label="Information" value={8} />
          <Weight label="Story" value={7} />
        </div>
      </div>
    </div>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-ink-900/40 border border-white/5 p-3">
      <div className="text-[10px] uppercase tracking-wider text-ink-500">{label}</div>
      <div className="text-sm font-medium mt-0.5">{value}</div>
    </div>
  )
}

function SelectField({ label, value, options }: { label: string; value: string; options: string[] }) {
  return (
    <div>
      <div className="label">{label}</div>
      <select className="input cursor-pointer" defaultValue={value}>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  )
}

function Weight({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-ink-300 mb-1.5">
        <span>{label}</span>
        <span className="font-mono">{value}%</span>
      </div>
      <div className="progress-track">
        <div className="h-full bg-gradient-to-r from-brand-500 to-pink-500" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}
