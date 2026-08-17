import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number | null | undefined, precision: 0 | 1 = 1): string {
  if (seconds == null || isNaN(seconds) || seconds < 0) return '00:00'
  const s = Math.floor(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const frac = seconds - s
  if (h) {
    return `${pad(h)}:${pad(m)}:${pad(sec)}`
  }
  if (precision === 0) return `${pad(m)}:${pad(sec)}`
  return `${pad(m)}:${pad(sec)}.${Math.floor(frac * 10 ** precision)
    .toString()
    .padStart(precision, '0')}`
}

export function pad(n: number, w = 2): string {
  return n.toString().padStart(w, '0')
}

export function formatTimestamp(seconds: number): string {
  if (seconds == null || isNaN(seconds) || seconds < 0) return '00:00:00,000'
  const ms = Math.round((seconds - Math.floor(seconds)) * 1000)
  const total = Math.floor(seconds) + (ms === 1000 ? 1 : 0)
  const msec = ms === 1000 ? 0 : ms
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  return `${pad(h)}:${pad(m)}:${pad(s)},${msec.toString().padStart(3, '0')}`
}

export function formatBytes(bytes: number | null | undefined, decimals = 1): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(sizes.length - 1, Math.floor(Math.log(bytes) / Math.log(k)))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`
}

export function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value))
}

export function relTime(date: string | Date | null | undefined): string {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return d.toLocaleDateString()
}

export function downloadFile(url: string, filename: string): void {
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.target = '_blank'
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard?.writeText(text) ?? Promise.resolve()
}

export function safeNumber(value: unknown, fallback = 0): number {
  const n = typeof value === 'string' ? Number(value) : (value as number)
  return Number.isFinite(n) ? (n as number) : fallback
}

export function pickFirst<T>(...vals: (T | null | undefined)[]): T | undefined {
  for (const v of vals) if (v != null) return v
  return undefined
}
