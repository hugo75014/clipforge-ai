import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Save, User, KeyRound, Bell, Shield } from 'lucide-react'
import toast from 'react-hot-toast'

import { api, patch } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import Button from '@/components/ui/Button'

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [name, setName] = useState(user?.name || '')
  const [email] = useState(user?.email || '')
  const [password, setPassword] = useState('')
  const [emailNotif, setEmailNotif] = useState(true)

  const saveMut = useMutation({
    mutationFn: () =>
      patch('/api/v1/users/' + user?.id, {
        name,
        password: password || undefined,
      }),
    onSuccess: async () => {
      toast.success('Saved')
      setPassword('')
      try {
        const me = await api.get<any>('/api/v1/auth/me')
        setUser(me.data)
      } catch {}
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-ink-400 text-sm mt-1">Manage your account and preferences.</p>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <User className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">Profile</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <div className="label">Name</div>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <div className="label">Email</div>
            <input className="input" value={email} disabled />
          </div>
        </div>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <KeyRound className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">Password</h2>
        </div>
        <div className="max-w-md">
          <div className="label">New password</div>
          <input
            type="password"
            className="input"
            placeholder="Leave blank to keep current"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="text-[11px] text-ink-500 mt-1">At least 8 characters.</div>
        </div>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">Notifications</h2>
        </div>
        <label className="flex items-center justify-between max-w-md">
          <span className="text-sm">Email me when a render completes</span>
          <button
            onClick={() => setEmailNotif(!emailNotif)}
            className={`w-10 h-6 rounded-full transition-colors relative ${emailNotif ? 'bg-brand-500' : 'bg-ink-700'}`}
          >
            <span
              className={`absolute top-1 size-4 rounded-full bg-white transition-all ${emailNotif ? 'left-5' : 'left-1'}`}
            />
          </button>
        </label>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="size-4 text-brand-300" />
          <h2 className="font-semibold tracking-tight">Account</h2>
        </div>
        <div className="text-sm text-ink-300 space-y-1">
          <div>Role: <span className="text-ink-100 font-medium uppercase">{user?.role}</span></div>
          <div>Created: <span className="text-ink-100">{user?.created_at?.slice(0, 10)}</span></div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={() => saveMut.mutate()}
          loading={saveMut.isPending}
          icon={<Save className="size-4" />}
        >
          Save changes
        </Button>
      </div>
    </div>
  )
}
