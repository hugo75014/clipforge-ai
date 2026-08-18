import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Upload,
  Link as LinkIcon,
  ArrowRight,
  Loader2,
  CheckCircle2,
  X,
  FileVideo,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { api, post, waitForJob } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import { formatBytes, cn } from '@/lib/utils'
import { ALLOWED_VIDEO_EXT, MAX_UPLOAD_MB } from '@/lib/constants'
import type { Project, Job } from '@/types'

const STAGES = [
  { key: 'upload', label: 'Upload' },
  { key: 'extract_audio', label: 'Extract audio' },
  { key: 'transcribe', label: 'Transcribe' },
  { key: 'analyze', label: 'Analyze content' },
  { key: 'detect_scenes', label: 'Detect scenes' },
  { key: 'detect_faces', label: 'Detect faces' },
  { key: 'score', label: 'Score moments' },
  { key: 'clips', label: 'Generate clips' },
]

export default function NewProjectPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [phase, setPhase] = useState<'compose' | 'uploading' | 'analyzing' | 'done' | 'error'>('compose')
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState(STAGES[0].key)
  const [stageIdx, setStageIdx] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const cancelRef = useRef<(() => void) | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: {
      'video/mp4': ['.mp4'],
      'video/quicktime': ['.mov'],
      'video/x-matroska': ['.mkv'],
      'video/webm': ['.webm'],
    },
    maxSize: MAX_UPLOAD_MB * 1024 * 1024,
    multiple: false,
    noClick: true,
    noKeyboard: true,
  })

  function startOver() {
    setPhase('compose')
    setFile(null)
    setProgress(0)
    setStageIdx(0)
    setStage(STAGES[0].key)
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!file && !sourceUrl) {
      setError('Please upload a file or paste a URL.')
      return
    }
    if (!title.trim()) {
      setError('Please give your project a name.')
      return
    }

    try {
      setPhase('uploading')
      setProgress(2)
      setStage('upload')
      setStageIdx(0)

      // 1) Create project
      const project = await post<Project>('/api/v1/projects', {
        title: title.trim(),
        description: description.trim() || null,
        source_url: sourceUrl.trim() || null,
      })

      // 2) Upload
      if (file) {
        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest()
          xhr.open('POST', `/api/v1/projects/${project.id}/upload`)
          xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('clipforge.token') || ''}`)

          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              setProgress(Math.round((e.loaded / e.total) * 50)) // 0-50 for upload
            }
          }
          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve()
            } else {
              try {
                const body = JSON.parse(xhr.responseText)
                reject(new Error(body?.detail || 'Upload failed'))
              } catch {
                reject(new Error('Upload failed'))
              }
            }
          }
          xhr.onerror = () => reject(new Error('Network error'))
          xhr.onabort = () => reject(new Error('Upload aborted'))

          cancelRef.current = () => xhr.abort()

          const form = new FormData()
          form.append('file', file)
          xhr.send(form)
        })
      }

      // 3) Analyze
      setPhase('analyzing')
      setStage('extract_audio')
      setStageIdx(1)
      setProgress(55)

      // Stage animation: walk through stages while the worker analyzes.
      let stageTimer = window.setInterval(() => {
        setStageIdx((prev) => {
          const next = Math.min(prev + 1, STAGES.length - 1)
          setStage(STAGES[next].key)
          return next
        })
        setProgress((p) => {
          if (p >= 95) return p
          return Math.min(95, p + 2 + Math.random() * 3)
        })
      }, 700)

      try {
        // Route asynchrone : le worker fait le travail, on suit le job.
        // La variante /sync tenait la requête ouverte le temps du traitement
        // et expirait sur les vidéos longues.
        const job = await post<Job>(`/api/v1/projects/${project.id}/analyze`)
        await waitForJob(job.id, {
          onTick: (j) => {
            if (typeof j.progress === 'number' && j.progress > 0) {
              setProgress(Math.min(95, 55 + j.progress * 0.4))
            }
          },
        })
      } finally {
        clearInterval(stageTimer)
      }

      setProgress(100)
      setStage('clips')
      setStageIdx(STAGES.length - 1)
      setPhase('done')
      toast.success('Analysis complete — generating clips!')
      setTimeout(() => navigate(`/projects/${project.id}`), 700)
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || err?.message || 'Something went wrong')
      setPhase('error')
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">New project</h1>
        <p className="text-ink-400 text-sm mt-1">
          Drop a long video. We'll transcribe, detect the best moments, and produce ready-to-publish clips.
        </p>
      </div>

      {phase === 'compose' && (
        <motion.form
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="grid lg:grid-cols-2 gap-6"
        >
          {/* Left: project info */}
          <div className="card p-6 space-y-4">
            <h2 className="font-semibold tracking-tight">Project info</h2>
            <div>
              <label className="label">Project name</label>
              <input
                className="input"
                placeholder="e.g. Founder podcast #4"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={120}
              />
            </div>
            <div>
              <label className="label">Description (optional)</label>
              <textarea
                className="input min-h-[96px] resize-y"
                placeholder="A short note to help you remember this project."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Source URL (optional)</label>
              <div className="relative">
                <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
                <input
                  className="input pl-10"
                  placeholder="https://… (YouTube, Vimeo, S3, …)"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                />
              </div>
              <div className="text-[11px] text-ink-500 mt-1.5">
                Direct file URLs only — we'll fetch and analyze them. For YouTube/Vimeo, please upload
                the file directly.
              </div>
            </div>
          </div>

          {/* Right: dropzone */}
          <div className="card p-6">
            <h2 className="font-semibold tracking-tight">Source video</h2>
            <div
              {...getRootProps()}
              className={cn(
                'mt-4 border-2 border-dashed rounded-2xl p-8 text-center transition-colors',
                isDragActive
                  ? 'border-brand-400 bg-brand-500/10'
                  : 'border-white/10 hover:border-white/20 bg-ink-900/40'
              )}
            >
              <input {...getInputProps()} />
              {file ? (
                <div className="flex items-center gap-3 text-left">
                  <div className="size-10 rounded-xl bg-brand-500/20 grid place-items-center">
                    <FileVideo className="size-5 text-brand-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{file.name}</div>
                    <div className="text-xs text-ink-400">
                      {formatBytes(file.size)} · {file.type || 'video/*'}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      setFile(null)
                    }}
                    className="p-2 text-ink-400 hover:text-white"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              ) : (
                <>
                  <div className="mx-auto size-12 rounded-2xl bg-gradient-to-br from-brand-500/20 to-pink-500/20 grid place-items-center mb-3">
                    <Upload className="size-5 text-brand-300" />
                  </div>
                  <div className="text-sm font-medium">Drop your video here</div>
                  <div className="text-xs text-ink-400 mt-1 mb-3">
                    MP4, MOV, MKV, WEBM · up to {Math.round(MAX_UPLOAD_MB / 1024)} GB
                  </div>
                  <button type="button" onClick={open} className="btn-outline">
                    Choose a file
                  </button>
                </>
              )}
            </div>

            {error && (
              <div className="mt-4 flex items-start gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5">
                <AlertCircle className="size-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="mt-6 flex items-center justify-between">
              <div className="text-xs text-ink-500">
                Signed in as <span className="text-ink-300">{user?.email}</span>
              </div>
              <button
                type="submit"
                disabled={!file && !sourceUrl.trim()}
                className="btn-primary"
              >
                Start analysis <ArrowRight className="size-4" />
              </button>
            </div>
          </div>
        </motion.form>
      )}

      {(phase === 'uploading' || phase === 'analyzing' || phase === 'done' || phase === 'error') && (
        <div className="card p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold tracking-tight flex items-center gap-2">
              {phase === 'done' ? (
                <>
                  <CheckCircle2 className="size-5 text-emerald-400" />
                  Analysis complete
                </>
              ) : phase === 'error' ? (
                <>
                  <AlertCircle className="size-5 text-red-400" />
                  Something went wrong
                </>
              ) : (
                <>
                  <Loader2 className="size-5 animate-spin text-brand-300" />
                  Analyzing video…
                </>
              )}
            </h2>
            {phase === 'error' && (
              <button onClick={startOver} className="btn-outline">
                Start over
              </button>
            )}
          </div>

          <div className="progress-track mb-3">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
          <div className="flex items-center justify-between text-xs text-ink-400 mb-6">
            <span>{Math.round(progress)}%</span>
            <span className="capitalize">{STAGES[stageIdx]?.label || stage}</span>
          </div>

          <ol className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {STAGES.map((s, i) => {
              const done = i < stageIdx || (phase === 'done' && i <= stageIdx)
              const active = i === stageIdx && phase !== 'done' && phase !== 'error'
              return (
                <li
                  key={s.key}
                  className={cn(
                    'rounded-xl border p-3 text-sm transition',
                    done
                      ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-200'
                      : active
                        ? 'border-brand-500/40 bg-brand-500/10 text-brand-100'
                        : 'border-white/5 bg-ink-900/40 text-ink-400'
                  )}
                >
                  <div className="flex items-center gap-2">
                    {done ? <CheckCircle2 className="size-4" /> : active ? <Loader2 className="size-4 animate-spin" /> : <span className="size-4 rounded-full border border-white/20" />}
                    <span className="font-medium">{s.label}</span>
                  </div>
                </li>
              )
            })}
          </ol>

          {phase === 'error' && error && (
            <div className="mt-6 flex items-start gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5">
              <AlertCircle className="size-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
