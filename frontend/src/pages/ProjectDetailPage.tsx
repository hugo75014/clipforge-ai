import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Film,
  Scissors,
  RefreshCw,
  Sparkles,
  Download,
  Edit3,
  ChevronRight,
  ChevronLeft,
  Star,
  Eye,
  Clock,
  Hash,
  Wand2,
  Volume2,
  Trash2,
  Copy,
  Archive,
  Loader2,
  CheckCircle2,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { get, post, patch, del } from '@/lib/api'
import type { ProjectDetail, Clip, Job } from '@/types'
import { formatDuration, formatBytes, relTime, cn, clamp } from '@/lib/utils'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import Modal from '@/components/ui/Modal'
import ScoreBar from '@/components/ui/ScoreBar'

export default function ProjectDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [analyzing, setAnalyzing] = useState(false)
  const [activeClip, setActiveClip] = useState<Clip | null>(null)
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false)

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => get<ProjectDetail>(`/api/v1/projects/${id}`),
    refetchInterval: (query) => {
      const data = query.state.data as ProjectDetail | undefined
      if (!data) return false
      if (['analyzing', 'rendering'].includes(data.status)) return 3000
      return false
    },
  })

  // Le projet repasse en 'ready' (ou 'failed') quand le worker a fini : c'est
  // lui qui fait foi, pas la mutation, qui rend la main immédiatement.
  useEffect(() => {
    if (project && project.status !== 'analyzing') setAnalyzing(false)
  }, [project?.status])

  const analyze = useMutation({
    mutationFn: () => post<Job>(`/api/v1/projects/${id}/analyze`),
    onSuccess: () => {
      setAnalyzing(true)
      toast.success('Analysis started')
      qc.invalidateQueries({ queryKey: ['project', id] })
    },
  })

  const renderClip = useMutation({
    mutationFn: (clip: Clip) =>
      post<Job>(`/api/v1/clips/${clip.id}/render`, null, {
        params: { aspect: '9:16', resolution: '1080p', burn_subtitles: true },
      }),
    onSuccess: (job) => {
      toast.success('Render started')
      qc.invalidateQueries({ queryKey: ['project', id] })
    },
  })

  const aiEdit = useMutation({
    mutationFn: ({ clip, instruction }: { clip: Clip; instruction: string }) =>
      post(`/api/v1/clips/${clip.id}/ai-edit`, { instruction }),
    onSuccess: () => {
      toast.success('AI edit applied')
      qc.invalidateQueries({ queryKey: ['project', id] })
      setActiveClip(null)
    },
  })

  const deleteMut = useMutation({
    mutationFn: () => del(`/api/v1/projects/${id}`),
    onSuccess: () => {
      toast.success('Project deleted')
      navigate('/projects')
    },
  })

  const archiveMut = useMutation({
    mutationFn: () => post(`/api/v1/projects/${id}/archive`),
    onSuccess: () => {
      toast.success('Project archived')
      qc.invalidateQueries({ queryKey: ['project', id] })
      setShowArchiveConfirm(false)
    },
  })

  const duplicateMut = useMutation({
    mutationFn: () => post(`/api/v1/projects/${id}/duplicate`),
    onSuccess: (p: any) => {
      toast.success('Project duplicated')
      navigate(`/projects/${p.id}`)
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-64 skeleton rounded" />
        <div className="h-64 skeleton rounded-2xl" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="card p-12 text-center">
        <h3 className="text-lg font-semibold">Project not found</h3>
        <Link to="/projects" className="text-sm text-brand-300 mt-2 inline-block">
          Back to projects →
        </Link>
      </div>
    )
  }

  const clipCount = project.clips?.length ?? 0
  const topClips = (project.clips ?? []).slice().sort((a, b) => b.score_overall - a.score_overall)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row gap-4 lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs text-ink-400 mb-1">
            <Link to="/projects" className="hover:text-ink-200">Projects</Link>
            <ChevronRight className="size-3" />
            <span>{project.title}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{project.title}</h1>
            <StatusChip status={project.status} />
          </div>
          {project.description && (
            <p className="text-ink-400 text-sm mt-1 max-w-2xl">{project.description}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => analyze.mutate()}
            disabled={analyzing || !project.source_filename}
            className="btn-outline"
          >
            {analyzing ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            {analyzing ? 'Analyzing…' : 'Re-analyze'}
          </button>
          <button
            onClick={() => setShowArchiveConfirm(true)}
            className="btn-ghost"
            title="Archive"
          >
            <Archive className="size-4" />
          </button>
          <button
            onClick={() => duplicateMut.mutate()}
            disabled={duplicateMut.isPending}
            className="btn-ghost"
            title="Duplicate"
          >
            <Copy className="size-4" />
          </button>
          <button
            onClick={() => {
              if (confirm('Delete this project? This cannot be undone.')) {
                deleteMut.mutate()
              }
            }}
            className="btn-ghost text-red-300 hover:text-red-200"
            title="Delete"
          >
            <Trash2 className="size-4" />
          </button>
        </div>
      </div>

      {/* Source video info */}
      <div className="card overflow-hidden">
        <div className="grid md:grid-cols-[280px,1fr] gap-0">
          <div className="aspect-video md:aspect-auto md:min-h-[200px] bg-ink-900 relative overflow-hidden">
            {project.source_thumbnail_url ? (
              <img src={project.source_thumbnail_url} alt={project.title} className="absolute inset-0 w-full h-full object-cover" />
            ) : (
              <div className="absolute inset-0 grid place-items-center bg-gradient-to-br from-ink-800 to-ink-900">
                <Film className="size-12 text-ink-600" />
              </div>
            )}
            {project.source_url && (
              <a
                href={project.source_url}
                target="_blank"
                rel="noopener"
                className="absolute bottom-2 right-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-black/60 backdrop-blur"
              >
                Source
              </a>
            )}
          </div>
          <div className="p-5 space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <InfoCell label="Duration" value={formatDuration(project.source_duration_sec, 0) || '—'} />
              <InfoCell label="Resolution" value={project.source_width ? `${project.source_width}×${project.source_height}` : '—'} />
              <InfoCell label="FPS" value={project.source_fps ? project.source_fps.toFixed(1) : '—'} />
              <InfoCell label="Size" value={formatBytes(project.source_size_bytes)} />
            </div>
            <div className="text-xs text-ink-400 leading-relaxed">
              <span className="text-ink-500">Filename:</span> {project.source_filename || '—'}
              {project.language && (
                <> · <span className="text-ink-500">Language:</span> {project.language}</>
              )}
              {' · '}
              <span className="text-ink-500">Updated:</span> {relTime(project.updated_at)}
            </div>
          </div>
        </div>
      </div>

      {/* AI analysis status */}
      {project.status === 'analyzing' || analyzing ? (
        <AnalyzingBanner />
      ) : null}

      {/* Clips */}
      <section>
        <div className="flex items-end justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Detected clips</h2>
            <p className="text-sm text-ink-400">
              {clipCount > 0
                ? `${clipCount} candidate${clipCount === 1 ? '' : 's'} ranked by viral score.`
                : 'Run an analysis to detect the best moments.'}
            </p>
          </div>
          {clipCount > 0 && (
            <div className="flex gap-2">
              <button
                onClick={() => topClips.forEach((c) => c.render_url || renderClip.mutate(c))}
                className="btn-primary"
                disabled={renderClip.isPending}
              >
                <Sparkles className="size-4" />
                Render all top picks
              </button>
            </div>
          )}
        </div>

        {clipCount > 0 ? (
          <div className="grid lg:grid-cols-2 gap-4">
            {topClips.map((c) => (
              <ClipCard
                key={c.id}
                clip={c}
                onOpen={() => setActiveClip(c)}
                onRender={() => renderClip.mutate(c)}
                rendering={renderClip.isPending}
              />
            ))}
          </div>
        ) : (
          <div className="card p-10 text-center">
            <Scissors className="size-8 text-ink-500 mx-auto mb-3" />
            <h3 className="font-semibold">No clips yet</h3>
            <p className="text-sm text-ink-400 mt-1 mb-4">
              {project.source_filename
                ? 'Run the AI analysis to detect the best moments.'
                : 'Upload a source video first.'}
            </p>
            {project.source_filename && (
              <button onClick={() => analyze.mutate()} disabled={analyzing} className="btn-primary">
                {analyzing ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
                Analyze now
              </button>
            )}
          </div>
        )}
      </section>

      {/* Transcript */}
      {project.transcript && project.transcript.segments.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold tracking-tight mb-3">Transcript</h2>
          <div className="card p-5 max-h-[480px] overflow-y-auto space-y-3">
            {project.transcript.segments.map((s) => (
              <div key={s.id} className="flex gap-3">
                <div className="text-[11px] text-ink-500 font-mono mt-0.5 w-14 shrink-0">
                  {formatDuration(s.start_sec, 0)}
                </div>
                <p className="text-sm text-ink-200 leading-relaxed">{s.text}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Archive confirmation */}
      <Modal open={showArchiveConfirm} onClose={() => setShowArchiveConfirm(false)} title="Archive project?">
        <p className="text-sm text-ink-300 mb-5">
          Archived projects are hidden from the main list. You can still find them by searching.
        </p>
        <div className="flex justify-end gap-2">
          <button onClick={() => setShowArchiveConfirm(false)} className="btn-ghost">Cancel</button>
          <button
            onClick={() => archiveMut.mutate()}
            disabled={archiveMut.isPending}
            className="btn-primary"
          >
            Archive
          </button>
        </div>
      </Modal>

      {/* Clip modal */}
      {activeClip && (
        <ClipEditModal
          clip={activeClip}
          onClose={() => setActiveClip(null)}
          onAiEdit={(instruction) => aiEdit.mutate({ clip: activeClip, instruction })}
        />
      )}
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-ink-900/40 border border-white/5 p-3">
      <div className="text-[10px] uppercase tracking-wider text-ink-500">{label}</div>
      <div className="text-sm font-medium mt-0.5">{value}</div>
    </div>
  )
}

function StatusChip({ status }: { status: string }) {
  const tone = PROJECT_STATUS_LABELS[status]?.tone || 'slate'
  const label = PROJECT_STATUS_LABELS[status]?.label || status
  const map: Record<string, string> = {
    slate: 'chip',
    purple: 'chip-purple',
    green: 'chip-green',
    red: 'chip-red',
    amber: 'chip-amber',
  }
  return <span className={map[tone]}>{label}</span>
}

function AnalyzingBanner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-4 flex items-center gap-3"
    >
      <Loader2 className="size-5 animate-spin text-brand-300" />
      <div>
        <div className="text-sm font-medium">AI analysis in progress</div>
        <div className="text-xs text-ink-400">
          Transcribing audio, detecting scenes, scoring moments… this page will update automatically.
        </div>
      </div>
    </motion.div>
  )
}

function ClipCard({
  clip,
  onOpen,
  onRender,
  rendering,
}: {
  clip: Clip
  onOpen: () => void
  onRender: () => void
  rendering: boolean
}) {
  return (
    <div className="card overflow-hidden hover:border-white/10 transition-colors">
      <div className="grid sm:grid-cols-[180px,1fr]">
        <div className="relative aspect-video sm:aspect-auto bg-ink-900">
          {clip.thumbnail_url ? (
            <img src={clip.thumbnail_url} alt={clip.title || ''} className="absolute inset-0 w-full h-full object-cover" />
          ) : (
            <div className="absolute inset-0 grid place-items-center bg-gradient-to-br from-brand-500/20 via-ink-900 to-pink-500/20">
              <Scissors className="size-8 text-ink-500" />
            </div>
          )}
          <div className="absolute top-2 left-2">
            <div className="px-2 py-0.5 rounded-full bg-black/60 backdrop-blur text-[10px] font-medium">
              {formatDuration(clip.edit_start_sec ?? clip.start_sec, 0)} → {formatDuration(clip.edit_end_sec ?? clip.end_sec, 0)}
            </div>
          </div>
          {clip.render_url ? (
            <div className="absolute bottom-2 left-2">
              <div className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-[10px] font-medium backdrop-blur flex items-center gap-1">
                <CheckCircle2 className="size-3" /> Rendered
              </div>
            </div>
          ) : null}
        </div>
        <div className="p-4">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h3 className="font-medium leading-tight line-clamp-2">{clip.title || 'Untitled clip'}</h3>
            <div className="text-right shrink-0">
              <div className="text-2xl font-bold leading-none gradient-text">{Math.round(clip.score_overall)}</div>
              <div className="text-[10px] uppercase tracking-wider text-ink-500">viral</div>
            </div>
          </div>
          {clip.hook && <p className="text-xs text-ink-400 italic line-clamp-2">"{clip.hook}"</p>}

          <div className="mt-3 space-y-1.5">
            <ScoreBar label="Hook" value={clip.score_hook} />
            <ScoreBar label="Emotion" value={clip.score_emotion} />
            <ScoreBar label="Curiosity" value={clip.score_curiosity} />
            <ScoreBar label="Share" value={clip.score_shareability} />
          </div>

          <div className="mt-4 flex items-center gap-2">
            <button onClick={onOpen} className="btn-outline flex-1">
              <Edit3 className="size-4" /> Edit
            </button>
            {clip.render_url ? (
              <a
                href={clip.render_url}
                target="_blank"
                rel="noopener"
                download
                className="btn-primary"
              >
                <Download className="size-4" /> Download
              </a>
            ) : (
              <button onClick={onRender} disabled={rendering} className="btn-primary">
                {rendering ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
                Render
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ClipEditModal({
  clip,
  onClose,
  onAiEdit,
}: {
  clip: Clip
  onClose: () => void
  onAiEdit: (instruction: string) => void
}) {
  const [instruction, setInstruction] = useState('')
  return (
    <Modal open onClose={onClose} title="Edit clip" wide>
      <div className="space-y-5">
        <div>
          <h3 className="text-sm font-medium mb-1">{clip.title || 'Untitled clip'}</h3>
          <p className="text-xs text-ink-400">{clip.reason}</p>
        </div>

        <div className="grid sm:grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-ink-900/40 p-3">
            <div className="text-[10px] uppercase tracking-wider text-ink-500">Start</div>
            <div className="font-mono mt-0.5">{formatDuration(clip.start_sec)}</div>
          </div>
          <div className="rounded-xl bg-ink-900/40 p-3">
            <div className="text-[10px] uppercase tracking-wider text-ink-500">End</div>
            <div className="font-mono mt-0.5">{formatDuration(clip.end_sec)}</div>
          </div>
        </div>

        {clip.transcript && (
          <div className="rounded-xl bg-ink-900/40 p-4 max-h-40 overflow-y-auto">
            <div className="text-[10px] uppercase tracking-wider text-ink-500 mb-1.5">Transcript</div>
            <p className="text-sm text-ink-200 leading-relaxed">{clip.transcript}</p>
          </div>
        )}

        <div>
          <div className="label flex items-center gap-1.5">
            <Wand2 className="size-3" /> Edit with AI
          </div>
          <div className="flex gap-2">
            <input
              className="input"
              placeholder="e.g. Make it more engaging, Remove silence, Add dynamic captions…"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
            />
            <button
              disabled={!instruction.trim()}
              onClick={() => onAiEdit(instruction)}
              className="btn-primary"
            >
              <Sparkles className="size-4" /> Apply
            </button>
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
                onClick={() => setInstruction(s)}
                className="chip hover:bg-white/10"
                type="button"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-white/5">
          <Link to={`/clips/${clip.id}`} className="btn-outline">
            Open full editor
          </Link>
          <button onClick={onClose} className="btn-ghost">Close</button>
        </div>
      </div>
    </Modal>
  )
}
