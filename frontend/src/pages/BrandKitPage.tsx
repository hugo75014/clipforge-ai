import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Palette, Plus, Save, Trash2, Image as ImageIcon, Music, Type, Star } from 'lucide-react'
import toast from 'react-hot-toast'

import { get, post, patch, del } from '@/lib/api'
import type { BrandKit } from '@/types'
import { cn } from '@/lib/utils'
import { CAPTION_STYLES } from '@/lib/constants'
import Button from '@/components/ui/Button'

export default function BrandKitPage() {
  const qc = useQueryClient()
  const { data: kits } = useQuery({
    queryKey: ['brand-kits'],
    queryFn: () => get<BrandKit[]>('/api/v1/brand-kits'),
  })
  const [editing, setEditing] = useState<BrandKit | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const createMut = useMutation({
    mutationFn: (payload: any) => post<BrandKit>('/api/v1/brand-kits', payload),
    onSuccess: (k) => {
      toast.success('Brand kit created')
      qc.invalidateQueries({ queryKey: ['brand-kits'] })
      setShowCreate(false)
      setEditing(k)
    },
  })
  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => patch<BrandKit>(`/api/v1/brand-kits/${id}`, payload),
    onSuccess: () => {
      toast.success('Brand kit saved')
      qc.invalidateQueries({ queryKey: ['brand-kits'] })
    },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => del(`/api/v1/brand-kits/${id}`),
    onSuccess: () => {
      toast.success('Brand kit deleted')
      qc.invalidateQueries({ queryKey: ['brand-kits'] })
      setEditing(null)
    },
  })

  return (
    <div>
      <div className="flex items-end justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Brand kit</h1>
          <p className="text-ink-400 text-sm mt-1">
            Reusable logo, colors, fonts and intro/outro applied to every clip.
          </p>
        </div>
        <Button variant="primary" icon={<Plus className="size-4" />} onClick={() => setShowCreate(true)}>
          New brand kit
        </Button>
      </div>

      <div className="grid lg:grid-cols-[260px,1fr] gap-4">
        {/* Sidebar list */}
        <div className="space-y-2">
          {kits?.length === 0 && (
            <div className="card p-4 text-sm text-ink-400">
              No brand kits yet. Create one to get started.
            </div>
          )}
          {kits?.map((k) => (
            <button
              key={k.id}
              onClick={() => setEditing(k)}
              className={cn(
                'w-full text-left card p-4 flex items-center gap-3 transition',
                editing?.id === k.id ? 'border-brand-500/40 bg-brand-500/5' : 'hover:border-white/10'
              )}
            >
              <div
                className="size-10 rounded-xl border border-white/10"
                style={{ background: k.primary_color || '#8b5cf6' }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate flex items-center gap-1.5">
                  {k.name}
                  {k.is_default && <Star className="size-3 text-amber-400 fill-amber-400" />}
                </div>
                <div className="text-[11px] text-ink-400 truncate">{k.caption_style || 'default captions'}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Editor */}
        <div>
          {showCreate ? (
            <CreateForm
              onSubmit={(payload) => createMut.mutate(payload)}
              onCancel={() => setShowCreate(false)}
            />
          ) : editing ? (
            <EditForm
              key={editing.id}
              kit={editing}
              onSubmit={(payload) => updateMut.mutate({ id: editing.id, payload })}
              onDelete={() => deleteMut.mutate(editing.id)}
              loading={updateMut.isPending}
            />
          ) : (
            <div className="card p-12 text-center">
              <Palette className="size-10 text-ink-500 mx-auto mb-3" />
              <h3 className="font-semibold">Pick or create a brand kit</h3>
              <p className="text-sm text-ink-400 mt-1">
                Your brand assets will be auto-applied to new clips.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function CreateForm({ onSubmit, onCancel }: { onSubmit: (p: any) => void; onCancel: () => void }) {
  const [name, setName] = useState('')
  return (
    <div className="card p-5">
      <div className="label">Brand kit name</div>
      <input
        className="input"
        placeholder="e.g. My main brand"
        value={name}
        onChange={(e) => setName(e.target.value)}
        autoFocus
      />
      <div className="flex justify-end gap-2 mt-4">
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button variant="primary" onClick={() => onSubmit({ name: name.trim() || 'New brand kit' })} icon={<Plus className="size-4" />}>
          Create
        </Button>
      </div>
    </div>
  )
}

function EditForm({
  kit,
  onSubmit,
  onDelete,
  loading,
}: {
  kit: BrandKit
  onSubmit: (p: any) => void
  onDelete: () => void
  loading: boolean
}) {
  const [name, setName] = useState(kit.name)
  const [primary, setPrimary] = useState(kit.primary_color || '#8b5cf6')
  const [secondary, setSecondary] = useState(kit.secondary_color || '#ec4899')
  const [accent, setAccent] = useState(kit.accent_color || '#22d3ee')
  const [font, setFont] = useState(kit.font_family || 'Inter')
  const [captionStyle, setCaptionStyle] = useState(kit.caption_style || 'viral')
  const [logo, setLogo] = useState(kit.logo_url || '')
  const [intro, setIntro] = useState(kit.intro_url || '')
  const [outro, setOutro] = useState(kit.outro_url || '')
  const [watermark, setWatermark] = useState(kit.watermark_url || '')
  const [music, setMusic] = useState(kit.music_url || '')
  const [isDefault, setIsDefault] = useState(kit.is_default)

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold tracking-tight">Edit "{kit.name}"</h2>
        <Button variant="primary" onClick={() => onSubmit({
          name, primary_color: primary, secondary_color: secondary, accent_color: accent,
          font_family: font, caption_style: captionStyle,
          logo_url: logo || null, intro_url: intro || null, outro_url: outro || null,
          watermark_url: watermark || null, music_url: music || null, is_default: isDefault,
        })} icon={<Save className="size-4" />} loading={loading}>
          Save
        </Button>
      </div>

      <div className="space-y-5">
        <div>
          <div className="label">Name</div>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
        </div>

        <div>
          <div className="label">Colors</div>
          <div className="grid grid-cols-3 gap-3">
            <ColorField label="Primary" value={primary} onChange={setPrimary} />
            <ColorField label="Secondary" value={secondary} onChange={setSecondary} />
            <ColorField label="Accent" value={accent} onChange={setAccent} />
          </div>
        </div>

        <div>
          <div className="label">Caption style</div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {CAPTION_STYLES.map((s) => (
              <button
                key={s}
                onClick={() => setCaptionStyle(s)}
                className={cn(
                  'rounded-xl border px-2 py-2 text-xs uppercase tracking-wider',
                  captionStyle === s ? 'border-brand-500 bg-brand-500/15 text-brand-200' : 'border-white/10 text-ink-300 hover:border-white/20'
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="label">Font family</div>
          <input className="input" value={font} onChange={(e) => setFont(e.target.value)} placeholder="Inter, Poppins, …" />
        </div>

        <div>
          <div className="label">Assets (paste URLs)</div>
          <div className="space-y-2">
            <AssetField icon={ImageIcon} label="Logo" value={logo} onChange={setLogo} placeholder="https://…" />
            <AssetField icon={ImageIcon} label="Intro" value={intro} onChange={setIntro} placeholder="https://…" />
            <AssetField icon={ImageIcon} label="Outro" value={outro} onChange={setOutro} placeholder="https://…" />
            <AssetField icon={ImageIcon} label="Watermark" value={watermark} onChange={setWatermark} placeholder="https://…" />
            <AssetField icon={Music} label="Background music" value={music} onChange={setMusic} placeholder="https://…" />
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-white/5">
          <label className="flex items-center gap-2 text-sm text-ink-200 cursor-pointer">
            <input
              type="checkbox"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="size-4 rounded border-white/20 bg-ink-900 text-brand-500 focus:ring-brand-500"
            />
            Set as default brand kit
          </label>
          <button onClick={onDelete} className="btn-ghost text-red-300 hover:text-red-200 text-sm">
            <Trash2 className="size-4" /> Delete
          </button>
        </div>
      </div>
    </div>
  )
}

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-ink-400 mb-1.5">{label}</div>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="size-10 rounded-lg border border-white/10 bg-transparent cursor-pointer"
        />
        <input className="input flex-1 font-mono text-xs" value={value} onChange={(e) => onChange(e.target.value)} />
      </div>
    </div>
  )
}

function AssetField({
  icon: Icon,
  label,
  value,
  onChange,
  placeholder,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="size-4 text-ink-500 shrink-0" />
      <div className="text-xs text-ink-300 w-32 shrink-0">{label}</div>
      <input
        className="input flex-1"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  )
}
