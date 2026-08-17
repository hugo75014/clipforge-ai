import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Wand2, Plus, Sparkles, Trash2, Copy } from 'lucide-react'
import toast from 'react-hot-toast'

import { get, post, del } from '@/lib/api'
import type { Template } from '@/types'
import { TEMPLATE_CATEGORIES, CAPTION_STYLES, CAPTION_POSITIONS, ASPECT_RATIOS } from '@/lib/constants'
import { cn } from '@/lib/utils'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'

export default function TemplatesPage() {
  const qc = useQueryClient()
  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => get<Template[]>('/api/v1/templates'),
  })
  const [showCreate, setShowCreate] = useState(false)
  const [category, setCategory] = useState<string>('')

  const createMut = useMutation({
    mutationFn: (payload: any) => post<Template>('/api/v1/templates', payload),
    onSuccess: () => {
      toast.success('Template created')
      setShowCreate(false)
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => del(`/api/v1/templates/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['templates'] }),
  })

  const filtered = (templates ?? []).filter((t) => !category || t.category === category)

  return (
    <div>
      <div className="flex items-end justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Templates</h1>
          <p className="text-ink-400 text-sm mt-1">
            Reusable editing presets for different content types.
          </p>
        </div>
        <Button variant="primary" icon={<Plus className="size-4" />} onClick={() => setShowCreate(true)}>
          New template
        </Button>
      </div>

      {/* Category filter */}
      <div className="card p-3 mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => setCategory('')}
          className={cn('chip', !category && 'chip-purple')}
        >
          All
        </button>
        {TEMPLATE_CATEGORIES.map((c) => (
          <button
            key={c.value}
            onClick={() => setCategory(c.value)}
            className={cn('chip', category === c.value && 'chip-purple')}
          >
            <span>{c.emoji}</span> {c.label}
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((t, i) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            className="card p-5 group"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="text-2xl">{TEMPLATE_CATEGORIES.find((c) => c.value === t.category)?.emoji || '✨'}</div>
              {t.is_builtin && <span className="chip-amber text-[10px]">Built-in</span>}
            </div>
            <h3 className="font-semibold tracking-tight">{t.name}</h3>
            <p className="text-xs text-ink-400 line-clamp-2 mt-1 min-h-[2.5rem]">{t.description}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {t.config?.caption_style && (
                <span className="chip text-[10px]">{t.config.caption_style}</span>
              )}
              {t.config?.aspect && <span className="chip text-[10px]">{t.config.aspect}</span>}
            </div>
            <div className="mt-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(t.config, null, 2))
                  toast.success('Config copied to clipboard')
                }}
                className="btn-ghost text-xs"
              >
                <Copy className="size-3" /> Copy config
              </button>
              {!t.is_builtin && (
                <button
                  onClick={() => deleteMut.mutate(t.id)}
                  className="btn-ghost text-xs text-red-300 hover:text-red-200"
                >
                  <Trash2 className="size-3" /> Delete
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create template">
        <CreateTemplateForm
          onSubmit={(payload) => createMut.mutate(payload)}
          loading={createMut.isPending}
        />
      </Modal>
    </div>
  )
}

function CreateTemplateForm({ onSubmit, loading }: { onSubmit: (p: any) => void; loading: boolean }) {
  const [name, setName] = useState('')
  const [category, setCategory] = useState('custom')
  const [description, setDescription] = useState('')
  const [captionStyle, setCaptionStyle] = useState('viral')
  const [captionPosition, setCaptionPosition] = useState('bottom')
  const [aspect, setAspect] = useState('9:16')

  function submit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      name: name.trim() || 'Untitled template',
      category,
      description: description.trim() || null,
      config: { aspect, caption_style: captionStyle, caption_position: captionPosition, burn_subtitles: true },
      is_public: false,
    })
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div>
        <div className="label">Name</div>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <div className="label">Category</div>
        <select className="input cursor-pointer" value={category} onChange={(e) => setCategory(e.target.value)}>
          {TEMPLATE_CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.emoji} {c.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <div className="label">Description</div>
        <textarea className="input min-h-[72px]" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div>
          <div className="label">Aspect</div>
          <select className="input cursor-pointer" value={aspect} onChange={(e) => setAspect(e.target.value)}>
            {ASPECT_RATIOS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <div>
          <div className="label">Caption</div>
          <select className="input cursor-pointer" value={captionStyle} onChange={(e) => setCaptionStyle(e.target.value)}>
            {CAPTION_STYLES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <div className="label">Position</div>
          <select className="input cursor-pointer" value={captionPosition} onChange={(e) => setCaptionPosition(e.target.value)}>
            {CAPTION_POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="submit" variant="primary" loading={loading} icon={<Sparkles className="size-4" />}>
          Create
        </Button>
      </div>
    </form>
  )
}
