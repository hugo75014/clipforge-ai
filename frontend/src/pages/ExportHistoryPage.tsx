import { useQuery } from '@tanstack/react-query'
import { Download, ExternalLink, CheckCircle2, AlertCircle, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

import { get } from '@/lib/api'
import { formatBytes, formatDuration, relTime } from '@/lib/utils'
import type { ExportRecord, ExportProvider } from '@/types'

export default function ExportHistoryPage() {
  const { data: exports } = useQuery({
    queryKey: ['exports'],
    queryFn: () => get<ExportRecord[]>('/api/v1/exports'),
  })
  const { data: providers } = useQuery({
    queryKey: ['export-providers'],
    queryFn: () => get<ExportProvider[]>('/api/v1/exports/providers'),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Export history</h1>
        <p className="text-ink-400 text-sm mt-1">All your past renders, in one place.</p>
      </div>

      {/* Publish targets */}
      <div className="card p-5">
        <h2 className="font-semibold tracking-tight mb-1">Publish targets</h2>
        <p className="text-xs text-ink-400 mb-4">
          Connect your accounts to push clips directly. Configure each provider in your <code>.env</code>.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {providers?.map((p) => (
            <div key={p.name} className="rounded-xl border border-white/10 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium">{p.display}</div>
                {p.configured ? (
                  <span className="chip-green text-[10px]">Ready</span>
                ) : (
                  <span className="chip-amber text-[10px]">Not configured</span>
                )}
              </div>
              <div className="text-[11px] text-ink-400">
                {p.fields.length > 0 ? `Needs: ${p.fields.join(', ')}` : 'No setup required'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Exports list */}
      <div>
        <h2 className="font-semibold tracking-tight mb-3">Recent exports</h2>
        {exports && exports.length > 0 ? (
          <div className="space-y-2">
            {exports.map((e) => (
              <motion.div
                key={e.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="card p-4 flex items-center gap-3"
              >
                <div className="size-10 rounded-xl bg-gradient-to-br from-brand-500/30 to-pink-500/20 grid place-items-center">
                  <Download className="size-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">
                    {e.format} · {e.aspect_ratio} · {e.resolution}
                  </div>
                  <div className="text-[11px] text-ink-400 mt-0.5">
                    {formatBytes(e.file_size_bytes)} · {formatDuration(e.duration_sec ?? 0, 0)} · {relTime(e.created_at)}
                  </div>
                </div>
                <div>
                  {e.status === 'completed' ? (
                    <CheckCircle2 className="size-4 text-emerald-400" />
                  ) : e.status === 'failed' ? (
                    <AlertCircle className="size-4 text-red-400" />
                  ) : (
                    <Clock className="size-4 text-amber-400" />
                  )}
                </div>
                {e.file_url && (
                  <a href={e.file_url} target="_blank" rel="noopener" className="btn-outline text-xs">
                    <ExternalLink className="size-3" /> Open
                  </a>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="card p-10 text-center">
            <Download className="size-8 text-ink-500 mx-auto mb-3" />
            <h3 className="font-semibold">No exports yet</h3>
            <p className="text-sm text-ink-400 mt-1">Once you render a clip, it will appear here.</p>
          </div>
        )}
      </div>
    </div>
  )
}
