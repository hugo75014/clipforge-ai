import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import { ArrowRight, Check, X } from 'lucide-react'

/**
 * Page publique. Seule page indexable qui porte du contenu : tout le reste de
 * l'application vit derrière l'authentification.
 *
 * Le motif conducteur est le recadrage lui-même — un cadre 9:16 qui se déplace
 * dans une image 16:9 — parce que c'est exactement ce que fait l'outil.
 */

const PIPELINE = [
  { tc: '00:00', title: 'Upload', body: 'Drop the file. Up to 2 GB, MP4, MOV, MKV or WebM.' },
  { tc: '00:12', title: 'Transcribe', body: 'The whole soundtrack becomes text with word-level timing.' },
  { tc: '01:04', title: 'Score', body: 'Every moment gets a score. The strongest ones become clips.' },
  { tc: '01:38', title: 'Reframe', body: 'The 9:16 window follows what matters instead of cropping the centre.' },
  { tc: '02:05', title: 'Caption', body: 'Captions are burned in, styled and timed to the words.' },
  { tc: '02:41', title: 'Render', body: 'Each clip renders on a worker. You get an MP4 and a thumbnail.' },
]

const DOES = [
  'Cuts a long video into several standalone vertical clips',
  'Keeps captions on-brand with reusable brand kits and templates',
  'Renders in the background — long videos do not tie up the page',
  'Gives every clip its own MP4 and thumbnail, ready to upload',
]

const DOES_NOT = [
  'Import from a YouTube or Vimeo link — upload the file itself',
  'Edit frame by frame on a timeline — cuts are per clip',
  'Post to your accounts for you',
]

export default function LandingPage() {
  const reduce = useReducedMotion()

  const rise = (delay: number) =>
    reduce
      ? {}
      : {
          initial: { opacity: 0, y: 16 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] as const },
        }

  return (
    <div className="min-h-full text-ink-100">
      {/* ---------------------------------------------------------------- nav */}
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-6">
        <span className="font-display text-lg font-semibold tracking-tight">
          ClipForge<span className="text-brand-400"> AI</span>
        </span>
        <nav className="flex items-center gap-2">
          <Link to="/login" className="btn-ghost">
            Sign in
          </Link>
          <Link to="/register" className="btn-primary">
            Create account
          </Link>
        </nav>
      </header>

      {/* -------------------------------------------------------------- hero */}
      <section className="mx-auto max-w-6xl px-5 pb-20 pt-10 lg:pt-16">
        <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_1fr]">
          <div>
            <motion.p
              {...rise(0)}
              className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-300/80"
            >
              16:9 in — 9:16 out
            </motion.p>

            <motion.h1
              {...rise(0.06)}
              className="mt-5 font-display text-[clamp(2.6rem,7vw,4.6rem)] font-semibold leading-[0.98] tracking-[-0.03em] text-balance"
            >
              One long video.
              <br />
              <span className="gradient-text">Six clips</span> that stand alone.
            </motion.h1>

            <motion.p {...rise(0.12)} className="mt-6 max-w-xl text-lg leading-relaxed text-ink-300">
              ClipForge listens to your video, scores every moment, and cuts the strongest ones into
              vertical clips — reframed, captioned and rendered, ready for Shorts, Reels and TikTok.
            </motion.p>

            <motion.div {...rise(0.18)} className="mt-9 flex flex-wrap items-center gap-3">
              <Link to="/register" className="btn-primary px-5 py-3 text-base">
                Start clipping
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/login" className="btn-outline px-5 py-3 text-base">
                I already have an account
              </Link>
            </motion.div>

            <motion.p {...rise(0.24)} className="mt-5 font-mono text-xs text-ink-500">
              Free account · no card · your files stay on the server that renders them
            </motion.p>
          </div>

          {/* Le dispositif : un cadre 9:16 qui balaye une image 16:9. */}
          <motion.div {...rise(0.1)} className="relative">
            <CropDevice reduce={!!reduce} />
          </motion.div>
        </div>
      </section>

      {/* --------------------------------------------------------- pipeline */}
      <section className="border-y border-white/5 bg-ink-950/40">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <SectionHead
            tc="Timeline"
            title="What happens to your video"
            lede="Six steps, in this order. You watch them tick by while the worker does the work."
          />

          <ol className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-white/5 bg-white/5 sm:grid-cols-2 lg:grid-cols-3">
            {PIPELINE.map((step) => (
              <li key={step.title} className="bg-ink-950/80 p-6 transition-colors hover:bg-ink-900/80">
                <span className="font-mono text-xs text-cyan-300/70">{step.tc}</span>
                <h3 className="mt-3 font-display text-xl font-semibold tracking-tight">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-400">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ------------------------------------------------------------ limits */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <SectionHead
          tc="Scope"
          title="Where it helps, where it stops"
          lede="Worth knowing before you upload an hour of footage."
        />

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <div className="card p-7">
            <h3 className="font-display text-lg font-semibold tracking-tight">It does</h3>
            <ul className="mt-5 space-y-4">
              {DOES.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-relaxed text-ink-300">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-brand-400" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="card border-white/[0.03] bg-ink-950/60 p-7">
            <h3 className="font-display text-lg font-semibold tracking-tight text-ink-300">It does not</h3>
            <ul className="mt-5 space-y-4">
              {DOES_NOT.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-relaxed text-ink-400">
                  <X className="mt-0.5 h-4 w-4 shrink-0 text-ink-600" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------- cta */}
      <section className="mx-auto max-w-6xl px-5 pb-24">
        <div className="card relative overflow-hidden p-10 text-center sm:p-14">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(600px_240px_at_50%_0%,rgba(139,92,246,0.18),transparent_70%)]"
          />
          <div className="relative">
            <h2 className="font-display text-[clamp(1.8rem,4vw,2.6rem)] font-semibold leading-tight tracking-[-0.02em]">
              Upload the video you already made.
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-ink-400">
              The clips are waiting inside it. Create an account and get them out.
            </p>
            <Link to="/register" className="btn-primary mt-8 px-6 py-3 text-base">
              Create account
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/5">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-8 text-sm text-ink-500 sm:flex-row sm:items-center sm:justify-between">
          <span className="font-display font-medium text-ink-300">ClipForge AI</span>
          <nav className="flex items-center gap-4 text-xs">
            <Link to="/legal" className="hover:text-ink-100">Legal notice</Link>
            <Link to="/terms" className="hover:text-ink-100">Terms</Link>
            <Link to="/privacy" className="hover:text-ink-100">Privacy</Link>
          </nav>
          <span className="font-mono text-xs">clip.viralcuts.live</span>
        </div>
      </footer>
    </div>
  )
}

function SectionHead({ tc, title, lede }: { tc: string; title: string; lede: string }) {
  return (
    <div className="max-w-2xl">
      <span className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-300/70">{tc}</span>
      <h2 className="mt-4 font-display text-[clamp(1.9rem,4vw,2.8rem)] font-semibold leading-[1.05] tracking-[-0.025em]">
        {title}
      </h2>
      <p className="mt-4 text-lg leading-relaxed text-ink-400">{lede}</p>
    </div>
  )
}

/**
 * Image 16:9 stylisée dans laquelle un cadre 9:16 se déplace d'un sujet à
 * l'autre, avec le ruban de timecodes correspondant. Tout est en CSS/SVG :
 * aucune image à charger, et le mouvement s'arrête si l'utilisateur a demandé
 * moins d'animation.
 */
function CropDevice({ reduce }: { reduce: boolean }) {
  const positions = ['12%', '52%', '30%']

  return (
    <div className="relative">
      <div className="relative aspect-video overflow-hidden rounded-2xl border border-white/10 bg-ink-900">
        {/* Fond : dégradé + grille, pour évoquer un plan filmé sans le mimer. */}
        <div className="absolute inset-0 bg-[radial-gradient(120%_100%_at_20%_0%,rgba(124,58,237,0.35),transparent_60%),radial-gradient(90%_80%_at_100%_100%,rgba(236,72,153,0.22),transparent_60%)]" />
        <div className="bg-grid absolute inset-0 opacity-40" />

        {/* Formes vagues qui tiennent lieu de sujets dans le plan. */}
        <div className="absolute bottom-0 left-[16%] h-[62%] w-[13%] rounded-t-full bg-white/10 blur-[1px]" />
        <div className="absolute bottom-0 left-[56%] h-[54%] w-[12%] rounded-t-full bg-white/[0.07] blur-[1px]" />

        {/* Le cadre 9:16 : la promesse du produit, en mouvement. Ce qu'il
            contient est ce que devient le clip — sujet cadré et sous-titre
            incrusté — pendant que le reste du plan s'assombrit. */}
        <motion.div
          className="absolute top-[6%] h-[88%] overflow-hidden rounded-lg border-2 border-cyan-300/80 shadow-[0_0_0_9999px_rgba(2,6,23,0.62)]"
          style={{ aspectRatio: '9 / 16' }}
          initial={{ left: positions[0] }}
          animate={reduce ? { left: positions[0] } : { left: positions }}
          transition={
            reduce
              ? undefined
              : { duration: 9, times: [0, 0.45, 1], repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut' }
          }
        >
          <span className="absolute -top-6 left-0 font-mono text-[10px] tracking-wider text-cyan-300/90">
            9:16
          </span>
          {/* Le sujet reste cadré : c'est le suivi, pas un recadrage centré. */}
          <span className="absolute bottom-0 left-1/2 h-[58%] w-[52%] -translate-x-1/2 rounded-t-full bg-white/25" />
          <span className="absolute bottom-[14%] left-1/2 w-[78%] -translate-x-1/2 rounded bg-ink-950/80 px-1 py-1 text-center font-display text-[9px] font-semibold leading-tight text-white">
            THIS IS THE PART
            <br />
            THEY REPLAY
          </span>
        </motion.div>

        <span className="absolute left-3 top-3 font-mono text-[10px] tracking-wider text-ink-400">
          SOURCE · 16:9
        </span>
      </div>

      {/* Ruban de timecodes : les segments retenus, en rose. */}
      <div className="mt-4 rounded-xl border border-white/5 bg-ink-950/60 p-3">
        <div className="flex h-8 items-stretch gap-[3px]">
          {Array.from({ length: 48 }).map((_, i) => {
            const picked = (i > 4 && i < 10) || (i > 19 && i < 26) || (i > 35 && i < 41)
            return (
              <span
                key={i}
                className={
                  picked
                    ? 'flex-1 rounded-[2px] bg-gradient-to-t from-pink-500/70 to-brand-400/80'
                    : 'flex-1 rounded-[2px] bg-white/[0.07]'
                }
                style={{ height: `${picked ? 100 : 30 + ((i * 37) % 45)}%`, alignSelf: 'flex-end' }}
              />
            )
          })}
        </div>
        <div className="mt-2 flex justify-between font-mono text-[10px] text-ink-500">
          <span>00:00:00</span>
          <span className="text-pink-300/80">3 moments picked</span>
          <span>00:47:12</span>
        </div>
      </div>
    </div>
  )
}
