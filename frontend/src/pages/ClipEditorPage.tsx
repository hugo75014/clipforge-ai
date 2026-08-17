import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  ChevronLeft,
  Play,
  Pause,
  Scissors,
  Wand2,
  Download,
  Loader2,
  Sparkles,
  Type,
  Crop,
  Music,
  Volume2,
  Settings2,
  Image as ImageIcon,
  Save,
  RefreshCw,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { get, post, patch } from '@/lib/api'
import type { Clip } from '@/types'
import { formatDuration, cn, clamp } from '@/lib/utils'
import { ASPECT_RATIOS, CAPTION_POSITIONS, CAPTION_STYLES, RESOLUTIONS } from '@/lib/constants'
import ScoreBar from '@/components/ui/ScoreBar'
import Button from '@/components/ui/Button'

export default function ClipEditorPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const videoRef = useRef<HTMLVideoElement | null>(null)

  const { data: clip, isLoading } = useQuery({
    queryKey: ['clip', id],
    queryFn: () => get<Clip>(`/api/v1/clips/${id}`),
  })

  // The clip's source video is the project file.
  const { data: project } = useQuery({
    queryKey: ['clip', id, 'project'],
    queryFn: async () => {
      const c = await get<Clip>(`/api/v1/clips/${id}`)
      return get<any>(`/api/v1/projects/${c.project_id}`)
    },
    enabled: !!clip,
  })

  const [tab, setTab] = useState<'captions' | 'crop' | 'text' | 'audio' | 'effects'>('captions')
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)

  // Editable state
  const [start, setStart] = useState(0)
  const [end, setEnd] = useState(0)
  const [title, setTitle] = useState('')
  const [hook, setHook] = useState('')
  const [description, setDescription] = useState('')
  const [hashtags, setHashtags] = useState<string[]>([])
  const [aspect, setAspect] = useState<typeof ASPECT_RATIOS[number]>('9:16')
  const [resolution, setResolution] = useState<typeof RESOLUTIONS[number]>('1080p')
  const [captionStyle, setCaptionStyle] = useState<typeof CAPTION_STYLES[number]>('viral')
  const [captionPosition, setCaptionPosition] = useState<typeof CAPTION_POSITIONS[number]>('bottom')
  const [burnSubtitles, setBurnSubtitles] = useState(true)
  const [aiInstruction, setAiInstruction] = useState('')

  useEffect(() => {
    if (!clip) return
    setStart(clip.edit_start_sec ?? clip.start_sec)
    setEnd(clip.edit_end_sec ?? clip.end_sec)
    setTitle(clip.title || '')
    setHook(clip.hook || '')
    setDescription(clip.description || '')
    setHashtags(clip.hashtags || [])
    if (clip.config) {
      const cfg = clip.config as any
      if (cfg.aspect && (ASPECT_RATIOS as readonly string[]).includes(cfg.aspect)) setAspect(cfg.aspect as any)
      if (cfg.caption_style && (CAPTION_STYLES as readonly string[]).includes(cfg.caption_style)) setCaptionStyle(cfg.caption_style as any)
      if (cfg.caption_position && (CAPTION_POSITIONS as readonly string[]).includes(cfg.caption_position)) setCaptionPosition(cfg.caption_position as any)
      if (typeof cfg.burn_subtitles === 'boolean') setBurnSubtitles(cfg.burn_subtitles)
    }
  }, [clip?.id])

  const sourceUrl = project?.source_url as string | undefined
  const duration = end - start

  const saveMut = useMutation({
    mutationFn: () =>
      patch<Clip>(`/api/v1/clips/${id}`, {
        start_sec: clip?.start_sec,
        end_sec: clip?.end_sec,
        edit_start_sec: start,
        edit_end_sec: end,
        title,
        hook,
        description,
        hashtags,
        config: { aspect, resolution, caption_style: captionStyle, caption_position: captionPosition, burn_subtitles: burnSubtitles },
      }),
    onSuccess: () => {
      toast.success('Clip saved')
      qc.invalidateQueries({ queryKey: ['clip', id] })
    },
  })

  const renderMut = useMutation({
    mutationFn: () =>
      post(`/api/v1/clips/${id}/render/sync`, null, {
        params: { aspect, resolution, burn_subtitles: burnSubtitles, caption_style: captionStyle, caption_position: captionPosition },
      }),
    onSuccess: (data: any) => {
      toast.success('Render complete')
      qc.invalidateQueries({ queryKey: ['clip', id] })
      if (data?.result?.render_url) window.open(data.result.render_url, '_blank')
    },
  })

  const aiEditMut = useMutation({
    mutationFn: (instruction: string) => post(`/api/v1/clips/${id}/ai-edit`, { instruction }),
    onSuccess: () => {
      toast.success('AI edit applied')
      qc.invalidateQueries({ queryKey: ['clip', id] })
    },
  })

  // Playback
  function togglePlay() {
    const v = videoRef.current
    if (!v) return
    if (v.paused) {
      v.play()
      setPlaying(true)
    } else {
      v.pause()
      setPlaying(false)
    }
  }

  function onTimeUpdate() {
    const v = videoRef.current
    if (!v) return
    setCurrentTime(v.currentTime)
    setProgress(((v.currentTime - start) / Math.max(0.1, end - start)) * 100)
    if (v.currentTime >= end) {
      v.pause()
      v.currentTime = start
      setPlaying(false)
    }
  }

  if (isLoading) {
    return <div className="h-64 skeleton rounded-2xl" />
  }
  if (!clip) {
    return (
      <div className="card p-12 text-center">
        <h3 className="text-lg font-semibold">Clip not found</h3>
        <Link to="/projects" className="text-sm text-brand-300 mt-2 inline-block">
          Back to projects
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <Link to={`/projects/${clip.project_id}`} className="btn-ghost text-sm">
          <ChevronLeft className="size-4" />
          Back to project
        </Link>
        <div className="flex items-center gap-2">
          <Button onClick={() => saveMut.mutate()} variant="outline" icon={<Save className="size-4" />} loading={saveMut.isPending}>
            Save
          </Button>
          <Button onClick={() => renderMut.mutate()} variant="primary" icon={<Sparkles className="size-4" />} loading={renderMut.isPending}>
            Render
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr,360px] gap-4">
        {/* Left: preview + timeline */}
        <div className="space-y-4">
          <div className="card overflow-hidden">
            <div className="relative aspect-video bg-black">
              {sourceUrl ? (
                <video
                  ref={videoRef}
                  src={sourceUrl}
                  className="absolute inset-0 w-full h-full"
                  onTimeUpdate={onTimeUpdate}
                  onPlay={() => setPlaying(true)}
                  onPause={() => setPlaying(false)}
                  preload="metadata"
                />
              ) : (
                <div className="absolute inset-0 grid place-items-center text-ink-500">
                  Source video unavailable
                </div>
              )}

              {/* Captions overlay (preview, simple white text) */}
              {clip.transcript && burnSubtitles && (
                <div
                  className={cn(
                    'absolute left-0 right-0 px-6 text-center pointer-events-none',
                    captionPosition === 'top' && 'top-4',
                    captionPosition === 'center' && 'top-1/2 -translate-y-1/2',
                    captionPosition === 'bottom' && 'bottom-6'
                  )}
                >
                  <span
                    className={cn(
                      'inline-block px-3 py-1.5 rounded-md font-semibold',
                      captionStyle === 'viral' && 'text-2xl text-white bg-black/40',
                      captionStyle === 'bold' && 'text-3xl text-yellow-300 bg-black/40',
                      captionStyle === 'clean' && 'text-base text-white bg-black/50',
                      captionStyle === 'podcast' && 'text-lg text-white bg-black/30',
                      captionStyle === 'cinematic' && 'text-base text-white tracking-wide',
                      captionStyle === 'karaoke' && 'text-2xl text-cyan-300 bg-black/40'
                    )}
                  >
                    {clip.transcript.length > 80 ? clip.transcript.slice(0, 80) + '…' : clip.transcript}
                  </span>
                </div>
              )}

              <button
                onClick={togglePlay}
                className="absolute inset-0 grid place-items-center group"
                aria-label={playing ? 'Pause' : 'Play'}
              >
                <span className="size-14 rounded-full bg-black/40 backdrop-blur grid place-items-center group-hover:scale-110 transition">
                  {playing ? <Pause className="size-6 text-white" /> : <Play className="size-6 text-white translate-x-0.5" />}
                </span>
              </button>
            </div>

            {/* Timeline */}
            <div className="p-4 space-y-3">
              <div className="relative h-10 rounded-lg bg-ink-900/60 overflow-hidden">
                <div
                  className="absolute inset-y-0 bg-gradient-to-r from-brand-500/40 to-pink-500/40"
                  style={{ left: `${((start / Math.max(0.1, project?.source_duration_sec || end)) * 100)}%`, width: `${((duration / Math.max(0.1, project?.source_duration_sec || end)) * 100)}%` }}
                />
                <div
                  className="absolute inset-y-0 w-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.6)]"
                  style={{ left: `${((currentTime / Math.max(0.1, project?.source_duration_sec || end)) * 100)}%` }}
                />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="label">Start: {formatDuration(start)}</div>
                  <input
                    type="range"
                    min={clip.start_sec}
                    max={end - 0.5}
                    step={0.1}
                    value={start}
                    onChange={(e) => setStart(clamp(parseFloat(e.target.value), 0, end - 0.5))}
                    className="w-full accent-brand-500"
                  />
                </div>
                <div>
                  <div className="label">End: {formatDuration(end)}</div>
                  <input
                    type="range"
                    min={start + 0.5}
                    max={clip.end_sec}
                    step={0.1}
                    value={end}
                    onChange={(e) => setEnd(clamp(parseFloat(e.target.value), start + 0.5, project?.source_duration_sec || clip.end_sec))}
                    className="w-full accent-brand-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-ink-400">
                <span>Duration: <span className="text-ink-200 font-medium">{formatDuration(duration, 0)}</span></span>
                <span>{Math.round(progress)}%</span>
              </div>
            </div>
          </div>

          {/* AI Edit bar */}
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Wand2 className="size-4 text-brand-300" />
              <div className="text-sm font-medium">Edit with AI</div>
            </div>
            <div className="flex gap-2">
              <input
                className="input"
                placeholder="e.g. Remove silence, Make it punchier, Add dynamic captions…"
                value={aiInstruction}
                onChange={(e) => setAiInstruction(e.target.value)}
              />
              <Button
                variant="primary"
                icon={<Sparkles className="size-4" />}
                loading={aiEditMut.isPending}
                disabled={!aiInstruction.trim()}
                onClick={() => aiEditMut.mutate(aiInstruction)}
              >
                Apply
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              {[
                'Remove silence',
                'Make it faster',
                'Add dynamic captions',
                'Focus on the speaker',
                'Make it TikTok style',
                'Make it professional',
              ].map((s) => (
                <button
                  key={s}
                  onClick={() => aiEditMut.mutate(s)}
                  className="chip hover:bg-white/10"
                  type="button"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Scores */}
          <div className="card p-5">
            <div className="text-sm font-medium mb-3">AI scores</div>
            <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
              <ScoreBar label="Hook" value={clip.score_hook} />
              <ScoreBar label="Emotion" value={clip.score_emotion} />
              <ScoreBar label="Information" value={clip.score_information} />
              <ScoreBar label="Story" value={clip.score_story} />
              <ScoreBar label="Curiosity" value={clip.score_curiosity} />
              <ScoreBar label="Shareability" value={clip.score_shareability} />
              <ScoreBar label="Completion" value={clip.score_completion} />
            </div>
            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
              <div className="text-xs text-ink-400">Viral score</div>
              <div className="text-3xl font-bold gradient-text">{Math.round(clip.score_overall)}<span className="text-base text-ink-500">/100</span></div>
            </div>
          </div>
        </div>

        {/* Right: editor tabs */}
        <div className="card overflow-hidden">
          <div className="grid grid-cols-5 border-b border-white/5">
            {[
              { k: 'captions', label: 'Captions', icon: Type },
              { k: 'crop', label: 'Crop', icon: Crop },
              { k: 'text', label: 'Text', icon: Settings2 },
              { k: 'audio', label: 'Audio', icon: Music },
              { k: 'effects', label: 'Effects', icon: Wand2 },
            ].map((t) => (
              <button
                key={t.k}
                onClick={() => setTab(t.k as any)}
                className={cn(
                  'flex flex-col items-center gap-1 py-3 text-[11px] uppercase tracking-wider transition',
                  tab === t.k
                    ? 'text-brand-300 border-b-2 border-brand-400 bg-brand-500/5'
                    : 'text-ink-400 hover:text-ink-200'
                )}
              >
                <t.icon className="size-4" />
                {t.label}
              </button>
            ))}
          </div>

          <div className="p-4 space-y-4">
            {tab === 'captions' && (
              <div className="space-y-4">
                <div>
                  <div className="label">Style</div>
                  <div className="grid grid-cols-3 gap-2">
                    {CAPTION_STYLES.map((s) => (
                      <button
                        key={s}
                        onClick={() => setCaptionStyle(s)}
                        className={cn(
                          'rounded-xl border px-2 py-3 text-xs uppercase tracking-wider transition',
                          captionStyle === s
                            ? 'border-brand-500 bg-brand-500/15 text-brand-200'
                            : 'border-white/10 text-ink-300 hover:border-white/20'
                        )}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="label">Position</div>
                  <div className="grid grid-cols-3 gap-2">
                    {CAPTION_POSITIONS.map((p) => (
                      <button
                        key={p}
                        onClick={() => setCaptionPosition(p)}
                        className={cn(
                          'rounded-xl border px-2 py-2 text-xs uppercase tracking-wider',
                          captionPosition === p
                            ? 'border-brand-500 bg-brand-500/15 text-brand-200'
                            : 'border-white/10 text-ink-300 hover:border-white/20'
                        )}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm text-ink-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={burnSubtitles}
                    onChange={(e) => setBurnSubtitles(e.target.checked)}
                    className="size-4 rounded border-white/20 bg-ink-900 text-brand-500 focus:ring-brand-500"
                  />
                  Burn captions into the video
                </label>
              </div>
            )}

            {tab === 'crop' && (
              <div className="space-y-4">
                <div>
                  <div className="label">Aspect ratio</div>
                  <div className="grid grid-cols-3 gap-2">
                    {ASPECT_RATIOS.map((a) => (
                      <button
                        key={a}
                        onClick={() => setAspect(a)}
                        className={cn(
                          'rounded-xl border px-2 py-3 text-xs uppercase tracking-wider',
                          aspect === a
                            ? 'border-brand-500 bg-brand-500/15 text-brand-200'
                            : 'border-white/10 text-ink-300 hover:border-white/20'
                        )}
                      >
                        {a}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="label">Resolution</div>
                  <div className="grid grid-cols-3 gap-2">
                    {RESOLUTIONS.map((r) => (
                      <button
                        key={r}
                        onClick={() => setResolution(r)}
                        className={cn(
                          'rounded-xl border px-2 py-2 text-xs uppercase tracking-wider',
                          resolution === r
                            ? 'border-brand-500 bg-brand-500/15 text-brand-200'
                            : 'border-white/10 text-ink-300 hover:border-white/20'
                        )}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-ink-500 leading-relaxed">
                  Face-aware smart crop is enabled. The crop window follows the speaker's face
                  throughout the clip.
                </p>
              </div>
            )}

            {tab === 'text' && (
              <div className="space-y-3">
                <div>
                  <div className="label">Title</div>
                  <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={120} />
                </div>
                <div>
                  <div className="label">Hook (1-liner)</div>
                  <input className="input" value={hook} onChange={(e) => setHook(e.target.value)} maxLength={140} />
                </div>
                <div>
                  <div className="label">Description</div>
                  <textarea className="input min-h-[80px]" value={description} onChange={(e) => setDescription(e.target.value)} />
                </div>
                <div>
                  <div className="label">Hashtags</div>
                  <input
                    className="input"
                    value={hashtags.join(' ')}
                    onChange={(e) => setHashtags(e.target.value.split(/\s+/).filter(Boolean))}
                    placeholder="#shorts #viral #topic"
                  />
                </div>
              </div>
            )}

            {tab === 'audio' && (
              <div className="space-y-4 text-sm text-ink-300">
                <div className="rounded-xl border border-white/10 p-4 space-y-3">
                  <div className="text-xs uppercase tracking-wider text-ink-400">Audio mix</div>
                  <label className="flex items-center justify-between">
                    <span>Original voice</span>
                    <input type="range" defaultValue={100} className="w-32 accent-brand-500" />
                  </label>
                  <label className="flex items-center justify-between">
                    <span>Background music</span>
                    <input type="range" defaultValue={15} className="w-32 accent-brand-500" />
                  </label>
                  <label className="flex items-center justify-between">
                    <span>Fade in / out</span>
                    <input type="range" defaultValue={20} className="w-32 accent-brand-500" />
                  </label>
                </div>
                <p className="text-xs text-ink-500">
                  Voice always stays at the top of the mix. Music auto-ducks when speech is present.
                </p>
              </div>
            )}

            {tab === 'effects' && (
              <div className="space-y-3 text-sm text-ink-300">
                <Toggle label="Auto zoom on speaker" defaultChecked />
                <Toggle label="Punch-in on key moments" defaultChecked />
                <Toggle label="Smooth transitions" defaultChecked />
                <Toggle label="Color enhancement" />
                <Toggle label="Background blur" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function Toggle({ label, defaultChecked }: { label: string; defaultChecked?: boolean }) {
  const [on, setOn] = useState(!!defaultChecked)
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <span>{label}</span>
      <button
        type="button"
        onClick={() => setOn(!on)}
        className={cn(
          'w-10 h-6 rounded-full transition-colors relative',
          on ? 'bg-brand-500' : 'bg-ink-700'
        )}
      >
        <span
          className={cn(
            'absolute top-1 size-4 rounded-full bg-white transition-all',
            on ? 'left-5' : 'left-1'
          )}
        />
      </button>
    </label>
  )
}
