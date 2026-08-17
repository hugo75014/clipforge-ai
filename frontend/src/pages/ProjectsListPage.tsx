import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Film, Plus, Search, Filter } from 'lucide-react'

import { get } from '@/lib/api'
import { formatBytes, formatDuration, relTime } from '@/lib/utils'
import { PROJECT_STATUS_LABELS } from '@/lib/constants'
import type { ProjectList, Project } from '@/types'

export default function ProjectsListPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['projects', { search, status }],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (status) params.set('status', status)
      return get<ProjectList>(`/api/v1/projects?${params.toString()}`)
    },
  })

  return (
    <div>
      <div className="flex items-end justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">My projects</h1>
          <p className="text-ink-400 text-sm mt-1">
            {data?.total ?? 0} project{(data?.total ?? 0) === 1 ? '' : 's'}
          </p>
        </div>
        <Link to="/new" className="btn-primary">
          <Plus className="size-4" />
          New project
        </Link>
      </div>

      <div className="card p-3 mb-6 flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
          <input
            className="input pl-10"
            placeholder="Search projects…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
          <select
            className="input pl-9 pr-8 appearance-none cursor-pointer min-w-[160px]"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            {Object.entries(PROJECT_STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card aspect-[4/3] skeleton" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((p, i) => (
            <motion.div
              key={p.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <ProjectCard project={p} />
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState />
      )}
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
          <span className="truncate">{project.source_filename || '—'}</span>
          <span>{relTime(project.updated_at)}</span>
        </div>
        <div className="text-[11px] text-ink-500 mt-2">
          {formatBytes(project.source_size_bytes)} · {project.source_width}×{project.source_height}
        </div>
      </div>
    </Link>
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
  return <span className={map[tone] + ' backdrop-blur'}>{label}</span>
}

function EmptyState() {
  return (
    <div className="card p-12 text-center">
      <div className="mx-auto size-12 rounded-2xl bg-gradient-to-br from-brand-500/20 to-pink-500/20 grid place-items-center mb-4">
        <Film className="size-5 text-brand-300" />
      </div>
      <h3 className="text-lg font-semibold">No projects yet</h3>
      <p className="text-sm text-ink-400 mt-1 mb-5 max-w-sm mx-auto">
        Start by creating a new project. Drop a video, and we'll find the best moments for you.
      </p>
      <Link to="/new" className="btn-primary">
        <Plus className="size-4" /> New project
      </Link>
    </div>
  )
}
