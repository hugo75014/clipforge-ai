// Mirror of backend Pydantic schemas. Keep in sync with backend/app/schemas/.

export type UserRole = 'admin' | 'editor' | 'viewer'

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
  avatar_url?: string | null
  preferences?: string | null
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface Project {
  id: string
  owner_id: string
  title: string
  description?: string | null
  source_url?: string | null
  source_filename?: string | null
  source_size_bytes?: number | null
  source_duration_sec?: number | null
  source_width?: number | null
  source_height?: number | null
  source_fps?: number | null
  source_codec?: string | null
  source_thumbnail_url?: string | null
  status: string
  language?: string | null
  error?: string | null
  created_at: string
  updated_at: string
}

export interface ProjectList {
  items: Project[]
  total: number
  page: number
  page_size: number
}

export interface ClipScores {
  hook: number
  emotion: number
  information: number
  story: number
  curiosity: number
  shareability: number
  completion: number
  overall: number
}

export interface Clip {
  id: string
  project_id: string
  start_sec: number
  end_sec: number
  edit_start_sec?: number | null
  edit_end_sec?: number | null
  title?: string | null
  hook?: string | null
  description?: string | null
  hashtags?: string[] | null
  keywords?: string[] | null
  reason?: string | null
  transcript?: string | null
  score_hook: number
  score_emotion: number
  score_information: number
  score_story: number
  score_curiosity: number
  score_shareability: number
  score_completion: number
  score_overall: number
  status: string
  selected: boolean
  sort_order: number
  render_path?: string | null
  render_url?: string | null
  thumbnail_url?: string | null
  render_duration_sec?: number | null
  render_size_bytes?: number | null
  render_error?: string | null
  config?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface Job {
  id: string
  type: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  project_id?: string | null
  clip_id?: string | null
  user_id?: string | null
  progress: number
  current_stage?: string | null
  message?: string | null
  error?: string | null
  celery_task_id?: string | null
  started_at?: string | null
  finished_at?: string | null
  duration_ms?: number | null
  provider?: string | null
  model?: string | null
  estimated_cost_usd?: number | null
  created_at: string
  updated_at: string
}

export interface TranscriptWord {
  word: string
  start: number
  end: number
  confidence?: number
  speaker?: string | null
}

export interface TranscriptSegment {
  id: string
  idx: number
  start_sec: number
  end_sec: number
  text: string
  speaker?: string | null
  confidence?: number | null
  words: TranscriptWord[]
}

export interface Transcript {
  language: string
  duration: number
  provider: string
  segments: TranscriptSegment[]
}

export interface ProjectDetail extends Project {
  clips: Clip[]
  transcript: Transcript | null
  jobs: Job[]
}

export interface BrandKit {
  id: string
  owner_id: string
  name: string
  is_default: boolean
  logo_url?: string | null
  primary_color?: string | null
  secondary_color?: string | null
  accent_color?: string | null
  font_family?: string | null
  caption_style?: string | null
  intro_url?: string | null
  outro_url?: string | null
  watermark_url?: string | null
  music_url?: string | null
  extras?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface Template {
  id: string
  owner_id?: string | null
  name: string
  category: string
  description?: string | null
  thumbnail_url?: string | null
  is_builtin: boolean
  is_public: boolean
  config: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ExportRecord {
  id: string
  project_id?: string | null
  clip_id?: string | null
  user_id?: string | null
  format: string
  aspect_ratio: string
  resolution: string
  file_path: string
  file_url: string
  file_size_bytes?: number | null
  duration_sec?: number | null
  target?: string | null
  external_id?: string | null
  external_url?: string | null
  status: string
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface ExportProvider {
  name: string
  display: string
  configured: boolean
  fields: string[]
}

export interface AdminStats {
  users: number
  projects: number
  clips: number
  exports: number
  jobs: { total: number; completed: number; processing: number; failed: number }
  total_clip_seconds: number
  total_storage_bytes: number
  total_estimated_cost_usd: number
}

export interface AdminJob {
  id: string
  type: string
  status: string
  project_id?: string | null
  clip_id?: string | null
  user_id?: string | null
  progress: number
  current_stage?: string | null
  message?: string | null
  error?: string | null
  provider?: string | null
  model?: string | null
  estimated_cost_usd?: number | null
  duration_ms?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface HealthReport {
  status: string
  version: string
  env: string
  components: Record<
    string,
    { status: 'up' | 'down'; [key: string]: any }
  >
}
