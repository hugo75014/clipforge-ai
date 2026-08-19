import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

/**
 * Shared shell for legal pages. Same dark surface and type scale as the rest
 * of the app — a legal document does not need its own visual language.
 *
 * PUBLISHER is declared once: it is the identity that stands behind ClipForge
 * AI, and copying it into three pages is the fastest way to let one go stale.
 */
export const PUBLISHER = {
  name: 'ClipForge AI',
  legalName: 'BELLEVUE HUGUES',
  legalForm: 'Sole trader (entrepreneur individuel), France',
  address: '8 rue Maurice Bouchor, 75014 Paris, France',
  siren: '839 385 499 RCS Paris',
  siret: '839 385 499 00018',
  email: 'hello@atlasflash.com',
  phone: '+33 6 59 80 24 91',
  publicationDirector: 'Hugues Bellevue',
  host: {
    name: 'Contabo GmbH',
    address: 'Aschauer Straße 32a, 81549 Munich, Germany',
  },
}

export function LegalPage({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <div className="min-h-full px-5 py-10 text-ink-100">
      <div className="mx-auto w-full max-w-3xl space-y-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs text-ink-500 transition-colors hover:text-ink-100"
        >
          <ArrowLeft className="h-4 w-4" />
          Back home
        </Link>

        <div className="space-y-6 rounded-2xl border border-white/10 bg-ink-900/60 p-8">
          <div className="space-y-2">
            <h1 className="font-display text-2xl text-ink-100">{title}</h1>
            {subtitle && <p className="text-xs text-ink-500">{subtitle}</p>}
          </div>
          <div className="space-y-6 text-sm leading-relaxed text-ink-300">{children}</div>
        </div>
      </div>
    </div>
  )
}

export function LegalSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="font-display text-base text-ink-100">{title}</h2>
      {children}
    </section>
  )
}

export function LegalList({ items }: { items: ReactNode[] }) {
  return (
    <ul className="list-disc space-y-1 pl-5">
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  )
}
