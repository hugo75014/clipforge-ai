// Mirror of shared/constants/__init__.py — keep in sync.

export const ASPECT_RATIOS = ['9:16', '1:1', '16:9'] as const
export type AspectRatio = (typeof ASPECT_RATIOS)[number]

export const RESOLUTIONS = ['1080p', '720p', '480p'] as const
export type Resolution = (typeof RESOLUTIONS)[number]

export const CAPTION_STYLES = [
  'viral',
  'clean',
  'podcast',
  'cinematic',
  'bold',
  'karaoke',
] as const
export type CaptionStyle = (typeof CAPTION_STYLES)[number]

export const CAPTION_POSITIONS = ['top', 'center', 'bottom'] as const
export type CaptionPosition = (typeof CAPTION_POSITIONS)[number]

export const EXPORT_FORMATS = [
  { value: 'mp4_h264_1080p', label: 'MP4 · H.264 · 1080p' },
  { value: 'mp4_h264_720p', label: 'MP4 · H.264 · 720p' },
  { value: 'mp4_h264_480p', label: 'MP4 · H.264 · 480p' },
] as const

export const TEMPLATE_CATEGORIES = [
  { value: 'podcast', label: 'Podcast', emoji: '🎙️' },
  { value: 'interview', label: 'Interview', emoji: '🎤' },
  { value: 'business', label: 'Business', emoji: '💼' },
  { value: 'motivation', label: 'Motivation', emoji: '🔥' },
  { value: 'news', label: 'News', emoji: '📰' },
  { value: 'education', label: 'Education', emoji: '📚' },
  { value: 'gaming', label: 'Gaming', emoji: '🎮' },
  { value: 'storytelling', label: 'Storytelling', emoji: '📖' },
  { value: 'custom', label: 'Custom', emoji: '✨' },
] as const

export const JOB_STATUS_LABELS: Record<string, { label: string; tone: 'purple' | 'green' | 'red' | 'amber' | 'slate' }> = {
  pending: { label: 'Queued', tone: 'slate' },
  processing: { label: 'Processing', tone: 'amber' },
  completed: { label: 'Done', tone: 'green' },
  failed: { label: 'Failed', tone: 'red' },
  cancelled: { label: 'Cancelled', tone: 'slate' },
}

export const PROJECT_STATUS_LABELS: Record<string, { label: string; tone: 'purple' | 'green' | 'red' | 'amber' | 'slate' }> = {
  draft: { label: 'Draft', tone: 'slate' },
  uploading: { label: 'Uploading', tone: 'amber' },
  uploaded: { label: 'Uploaded', tone: 'slate' },
  analyzing: { label: 'Analyzing', tone: 'purple' },
  ready: { label: 'Ready', tone: 'green' },
  editing: { label: 'Editing', tone: 'purple' },
  rendering: { label: 'Rendering', tone: 'amber' },
  completed: { label: 'Completed', tone: 'green' },
  archived: { label: 'Archived', tone: 'slate' },
  failed: { label: 'Failed', tone: 'red' },
}

export const MAX_UPLOAD_MB = 2048
export const ALLOWED_VIDEO_EXT = ['mp4', 'mov', 'mkv', 'webm']
export const ALLOWED_VIDEO_MIME = ['video/mp4', 'video/quicktime', 'video/x-matroska', 'video/webm']

export const STORAGE_KEY_TOKEN = 'clipforge.token'
export const STORAGE_KEY_USER = 'clipforge.user'
