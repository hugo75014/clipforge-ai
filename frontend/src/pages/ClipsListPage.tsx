import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Scissors, Download, Film, ChevronRight, Edit3 } from 'lucide-react'

import { get } from '@/lib/api'
import { formatDuration } from '@/lib/utils'
import type { Project } from '@/types'

export default function ClipsListPage() {
  const { data: projects } = useQuery({
    queryKey: ['projects', 'all-for-clips'],
    queryFn: () => get<{ items: Project[]; total: number }>('/api/v1/projects?page=1&page_size=100'),
  })

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">All clips</h1>
        <p className="text-ink-400 text-sm mt-1">
          Browse every clip generated across your projects.
        </p>
      </div>

      <div className="space-y-3">
        {projects?.items.map((p) => (
          <ProjectRow key={p.id} project={p} />
        ))}
      </div>
    </div>
  )
}

function ProjectRow({ project }: { project: Project }) {
  // We re-fetch the project detail to get the clips inline.
  const { data: detail } = useQuery({
    queryKey: ['project', project.id],
    queryFn: () => get<{ clips: any[] }>(`/api/v1/projects/${project.id}`),
  })
  const clips = detail?.clips ?? []
  if (clips.length === 0) return null
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <Link to={`/projects/${project.id}`} className="font-medium hover:text-white flex items-center gap-1.5">
            <Film className="size-4 text-ink-500" /> {project.title}
            <ChevronRight className="size-3.5 text-ink-500" />
          </Link>
          <div className="text-xs text-ink-400">{clips.length} clips</div>
        </div>
        <Link to={`/projects/${project.id}`} className="btn-ghost text-xs">
          Open project
        </Link>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {clips.map((c) => (
          <Link
            key={c.id}
            to={`/clips/${c.id}`}
            className="group block rounded-xl overflow-hidden border border-white/5 hover:border-white/10"
          >
            <div className="aspect-video bg-ink-900 relative">
              {c.thumbnail_url ? (
                <img src={c.thumbnail_url} alt={c.title || ''} className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform" />
              ) : (
                <div className="absolute inset-0 grid place-items-center bg-gradient-to-br from-brand-500/20 to-pink-500/20">
                  <Scissors className="size-6 text-ink-500" />
                </div>
              )}
              <div className="absolute top-1.5 right-1.5 text-[10px] px-1.5 py-0.5 rounded bg-black/60 backdrop-blur">
                {formatDuration(c.start_sec, 0)}
              </div>
              <div className="absolute bottom-1.5 left-1.5 text-[10px] px-1.5 py-0.5 rounded bg-gradient-to-r from-brand-500 to-pink-500 text-white font-medium">
                {Math.round(c.score_overall)}
              </div>
            </div>
            <div className="p-2">
              <div className="text-xs font-medium truncate">{c.title || 'Untitled clip'}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
