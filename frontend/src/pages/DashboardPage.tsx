import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Film,
  Scissors,
  Clock,
  Download,
  Plus,
  ArrowRight,
  Sparkles,
} from 'lucide-react'

import { get } from '@/lib/api'
import type { Project, ProjectList } from '@/types'
import { formatDuration, formatBytes, relTime } from '@/lib/utils'

export default function DashboardPage() {
  const { data: projects } = useQuery({
    queryKey: ['projects', 'recent'],
    queryFn: () => get<ProjectList>('/api/v1/projects?page=1&page_size=6'),
  })

  const stats = useMemo(() => {
    const totalProjects = projects?.total ?? 0
    const totalClips = projects?.items.reduce((acc, p) => acc + ((p as any).clip_count ?? 0), 0) ?? 0
    return {
      totalProjects,
      totalClips,
      hoursSaved: Math.max(0, totalClips * 0.4),
      exports: 0,
    }
  }, [projects])

  return (
    <div className="space-y-8">
      {/* Hero */}
      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-ink-900 via-ink-900 to-ink-950 p-8 lg:p-10"
      >
        <div className="absolute -top-20 -right-20 size-72 bg-brand-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-20 -left-20 size-72 bg-pink-500/15 rounded-full blur-3xl" />

        <div className="relative max-w-2xl">
          <div className="inline-flex chip-purple mb-4">
            <Sparkles className="size-3" /> AI studio
          </div>
          <h1 className="text-3xl lg:text-4xl font-semibold tracking-tight mb-3 text-balance">
            Turn long videos into <span className="gradient-text">viral Shorts</span>.
          </h1>
          <p className="text-ink-300 mb-6 leading-relaxed">
            Drop a video. ClipForge finds the best moments, reframes to 9:16, burns dynamic captions
            and exports clips ready for TikTok, Reels, and YouTube Shorts.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/new" className="btn-primary">
              <Plus className="size-4" />
              Create a new project
            </Link>
            <Link to="/projects" className="btn-outline">
              View all projects
              <ArrowRight className="size-4" />
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Stats */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Film} label="Projects" value={stats.totalProjects} accent="from-brand-500 to-pink-500" />
        <StatCard icon={Scissors} label="Clips generated" value={stats.totalClips} accent="from-cyan-400 to-brand-500" />
        <StatCard icon={Clock} label="Hours saved" value={stats.hoursSaved.toFixed(1)} accent="from-amber-400 to-pink-500" />
        <StatCard icon={Download} label="Exports" value={stats.exports} accent="from-emerald-400 to-cyan-400" />
      </section>

      {/* Recent projects */}
      <section>
        <div className="flex items-end justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Recent projects</h2>
            <p className="text-sm text-ink-400">Pick up where you left off.</p>
          </div>
          <Link to="/projects" className="text-sm text-brand-300 hover:text-brand-200">
            View all →
          </Link>
        </div>

        {projects && projects.items.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.items.map((p) => (
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </section>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number | string
  accent: string
}) {
  return (
    <div className="card p-5 relative overflow-hidden">
      <div className={`absolute -top-10 -right-10 size-32 rounded-full bg-gradient-to-br ${accent} opacity-10 blur-2xl`} />
      <div className="relative flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-wider text-ink-400 mb-1">{label}</div>
          <div className="text-2xl font-semibold tracking-tight">{value}</div>
        </div>
        <div className={`size-9 rounded-xl grid place-items-center bg-gradient-to-br ${accent} bg-opacity-20`}>
          <Icon className="size-4 text-white" />
        </div>
      </div>
    </div>
  )
}

function ProjectCard({ project }: { project: Project }) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="group card overflow-hidden hover:border-white/10 transition-all"
    >
      <div className="aspect-video bg-ink-900 relative overflow-hidden">
        {project.source_thumbnail_url ? (
          <img
            src={project.source_thumbnail_url}
            alt={project.title}
            className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="absolute inset-0 grid place-items-center bg-gradient-to-br from-ink-800 to-ink-900">
            <Film className="size-10 text-ink-600" />
          </div>
        )}
        <div className="absolute top-2 right-2">
          <StatusChip status={project.status} />
        </div>
        {project.source_duration_sec != null && (
          <div className="absolute bottom-2 right-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-black/60 backdrop-blur">
            {formatDuration(project.source_duration_sec, 0)}
          </div>
        )}
      </div>
      <div className="p-4">
        <div className="font-medium truncate">{project.title}</div>
        <div className="flex items-center justify-between text-xs text-ink-400 mt-1">
          <span>{project.source_filename || '—'}</span>
          <span>{relTime(project.updated_at)}</span>
        </div>
        {project.source_size_bytes != null && (
          <div className="text-[11px] text-ink-500 mt-2">
            {formatBytes(project.source_size_bytes)} · {project.source_width}×{project.source_height}
          </div>
        )}
      </div>
    </Link>
  )
}

function StatusChip({ status }: { status: string }) {
  const map: Record<string, string> = {
    draft: 'chip',
    uploaded: 'chip',
    analyzing: 'chip-amber',
    ready: 'chip-green',
    rendering: 'chip-amber',
    completed: 'chip-green',
    failed: 'chip-red',
    archived: 'chip',
  }
  const cls = map[status] || 'chip'
  return <span className={cls + ' backdrop-blur'}>{status}</span>
}

function EmptyState() {
  return (
    <div className="card p-12 text-center">
      <div className="mx-auto size-12 rounded-2xl bg-gradient-to-br from-brand-500/20 to-pink-500/20 grid place-items-center mb-4">
        <Film className="size-5 text-brand-300" />
      </div>
      <h3 className="text-lg font-semibold">No projects yet</h3>
      <p className="text-sm text-ink-400 mt-1 mb-5 max-w-sm mx-auto">
        Create your first project by uploading a long video. ClipForge will handle the rest.
      </p>
      <Link to="/new" className="btn-primary">
        <Plus className="size-4" /> New project
      </Link>
    </div>
  )
}
