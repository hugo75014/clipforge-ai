import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Shield,
  Users,
  Film,
  Scissors,
  Download,
  Cpu,
  HardDrive,
  Activity,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react'

import { get } from '@/lib/api'
import { formatBytes, formatDuration, relTime } from '@/lib/utils'
import { JOB_STATUS_LABELS } from '@/lib/constants'
import type { AdminStats, AdminJob, HealthReport, User, Project } from '@/types'

export default function AdminPage() {
  const stats = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => get<AdminStats>('/api/v1/admin/stats'),
  })
  const health = useQuery({
    queryKey: ['admin', 'health'],
    queryFn: () => get<HealthReport>('/api/v1/admin/health-deep'),
    refetchInterval: 15000,
  })
  const jobs = useQuery({
    queryKey: ['admin', 'jobs'],
    queryFn: () => get<AdminJob[]>('/api/v1/admin/jobs?limit=50'),
    refetchInterval: 5000,
  })
  const config = useQuery({
    queryKey: ['admin', 'config'],
    queryFn: () => get<any>('/api/v1/admin/config'),
  })
  const users = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => get<User[]>('/api/v1/users'),
  })
  const projects = useQuery({
    queryKey: ['admin', 'projects'],
    queryFn: () => get<{ items: Project[] }>('/api/v1/projects?page=1&page_size=20'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Shield className="size-5 text-amber-300" /> Admin
          </h1>
          <p className="text-ink-400 text-sm mt-1">Platform overview, system health, and user management.</p>
        </div>
        <button onClick={() => { stats.refetch(); health.refetch(); jobs.refetch() }} className="btn-outline">
          <RefreshCw className="size-4" /> Refresh
        </button>
      </div>

      {/* Stats */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Users" value={stats.data?.users ?? 0} />
        <StatCard icon={Film} label="Projects" value={stats.data?.projects ?? 0} />
        <StatCard icon={Scissors} label="Clips" value={stats.data?.clips ?? 0} />
        <StatCard icon={Download} label="Exports" value={stats.data?.exports ?? 0} />
        <StatCard icon={Activity} label="Hours of clip" value={((stats.data?.total_clip_seconds ?? 0) / 3600).toFixed(1)} />
        <StatCard icon={HardDrive} label="Storage" value={formatBytes(stats.data?.total_storage_bytes ?? 0)} />
        <StatCard icon={Cpu} label="Jobs (done/total)" value={`${stats.data?.jobs.completed ?? 0}/${stats.data?.jobs.total ?? 0}`} />
        <StatCard icon={AlertCircle} label="Est. AI cost" value={`$${(stats.data?.total_estimated_cost_usd ?? 0).toFixed(4)}`} />
      </section>

      {/* System health */}
      <section className="card p-5">
        <h2 className="font-semibold tracking-tight mb-3 flex items-center gap-2">
          <Activity className="size-4 text-emerald-300" /> System health
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {health.data?.components && Object.entries(health.data.components).map(([name, info]: any) => (
            <div key={name} className="rounded-xl border border-white/10 p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium capitalize">{name.replace(/_/g, ' ')}</div>
                {info.status === 'up' ? (
                  <CheckCircle2 className="size-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="size-4 text-red-400" />
                )}
              </div>
              <div className="text-[11px] text-ink-400 mt-1">
                {info.provider || info.backend || info.ffmpeg || info.ffprobe || info.error || (info.status === 'up' ? 'Healthy' : 'Down')}
              </div>
              {info.latency_ms != null && (
                <div className="text-[10px] text-ink-500 mt-0.5">{info.latency_ms}ms</div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Recent jobs */}
      <section className="card p-5">
        <h2 className="font-semibold tracking-tight mb-3">Recent jobs</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-[10px] uppercase tracking-wider text-ink-400 border-b border-white/5">
              <tr>
                <th className="text-left py-2">Type</th>
                <th className="text-left py-2">Status</th>
                <th className="text-left py-2">Stage</th>
                <th className="text-left py-2">Message</th>
                <th className="text-left py-2">Provider</th>
                <th className="text-left py-2">Cost</th>
                <th className="text-left py-2">When</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {jobs.data?.slice(0, 30).map((j) => (
                <tr key={j.id} className="hover:bg-white/5">
                  <td className="py-2 font-mono text-xs">{j.type}</td>
                  <td className="py-2">
                    <JobStatusChip status={j.status} />
                  </td>
                  <td className="py-2 text-ink-400 text-xs">{j.current_stage || '—'}</td>
                  <td className="py-2 text-ink-300 text-xs max-w-xs truncate">{j.message || j.error || '—'}</td>
                  <td className="py-2 text-ink-400 text-xs">{j.provider || '—'}</td>
                  <td className="py-2 text-ink-400 text-xs">${(j.estimated_cost_usd ?? 0).toFixed(4)}</td>
                  <td className="py-2 text-ink-400 text-xs">{relTime(j.created_at)}</td>
                </tr>
              ))}
              {(!jobs.data || jobs.data.length === 0) && (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-sm text-ink-500">
                    No jobs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Config + Users */}
      <div className="grid lg:grid-cols-2 gap-4">
        <section className="card p-5">
          <h2 className="font-semibold tracking-tight mb-3">Configuration</h2>
          {config.data && (
            <pre className="text-[11px] text-ink-300 leading-relaxed bg-ink-900/60 rounded-xl p-3 overflow-x-auto">
              {JSON.stringify(config.data, null, 2)}
            </pre>
          )}
        </section>

        <section className="card p-5">
          <h2 className="font-semibold tracking-tight mb-3">Users</h2>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {users.data?.map((u) => (
              <div key={u.id} className="flex items-center gap-3 rounded-xl border border-white/5 p-2.5">
                <div className="size-8 rounded-full bg-gradient-to-br from-brand-500 to-pink-500 grid place-items-center text-[11px] font-semibold">
                  {(u.name?.[0] || u.email[0]).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{u.name || u.email}</div>
                  <div className="text-[11px] text-ink-400 truncate">{u.email}</div>
                </div>
                <span className="chip text-[10px] uppercase">{u.role}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Recent projects */}
      <section className="card p-5">
        <h2 className="font-semibold tracking-tight mb-3">Recent projects (all users)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-[10px] uppercase tracking-wider text-ink-400 border-b border-white/5">
              <tr>
                <th className="text-left py-2">Title</th>
                <th className="text-left py-2">Owner</th>
                <th className="text-left py-2">Status</th>
                <th className="text-left py-2">Duration</th>
                <th className="text-left py-2">Size</th>
                <th className="text-left py-2">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {projects.data?.items.map((p) => (
                <tr key={p.id} className="hover:bg-white/5">
                  <td className="py-2">
                    <Link to={`/projects/${p.id}`} className="text-brand-300 hover:text-brand-200">
                      {p.title}
                    </Link>
                  </td>
                  <td className="py-2 text-ink-300 text-xs">{p.owner_id.slice(0, 8)}…</td>
                  <td className="py-2 text-ink-300 text-xs">{p.status}</td>
                  <td className="py-2 text-ink-300 text-xs">{formatDuration(p.source_duration_sec, 0)}</td>
                  <td className="py-2 text-ink-300 text-xs">{formatBytes(p.source_size_bytes)}</td>
                  <td className="py-2 text-ink-400 text-xs">{relTime(p.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function StatCard({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: number | string }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
          <div className="text-2xl font-semibold tracking-tight mt-1">{value}</div>
        </div>
        <Icon className="size-4 text-ink-500" />
      </div>
    </div>
  )
}

function JobStatusChip({ status }: { status: string }) {
  const meta = JOB_STATUS_LABELS[status] || { label: status, tone: 'slate' as const }
  const map: Record<string, string> = {
    slate: 'chip',
    purple: 'chip-purple',
    green: 'chip-green',
    red: 'chip-red',
    amber: 'chip-amber',
  }
  return <span className={map[meta.tone]}>{meta.label}</span>
}
