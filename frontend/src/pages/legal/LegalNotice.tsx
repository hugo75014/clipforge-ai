import { LegalList, LegalPage, LegalSection, PUBLISHER } from './LegalPage'

/**
 * Legal notice — required for any site accessible to the French public
 * (art. 6-III of the LCEN).
 */
export default function LegalNotice() {
  return (
    <LegalPage title="Legal notice" subtitle="Who publishes this site, and who hosts it.">
      <LegalSection title="Publisher">
        <LegalList
          items={[
            <>Trade name: {PUBLISHER.name}</>,
            <>Legal name: {PUBLISHER.legalName}</>,
            <>Legal form: {PUBLISHER.legalForm}</>,
            <>Registered address: {PUBLISHER.address}</>,
            <>SIREN: {PUBLISHER.siren}</>,
            <>SIRET: {PUBLISHER.siret}</>,
            <>
              Contact: {PUBLISHER.email} — {PUBLISHER.phone}
            </>,
            <>Publication director: {PUBLISHER.publicationDirector}</>,
          ]}
        />
      </LegalSection>

      <LegalSection title="Hosting">
        <p>
          {PUBLISHER.host.name} — {PUBLISHER.host.address}
        </p>
      </LegalSection>

      <LegalSection title="What this service does">
        <p>
          ClipForge AI turns a long video into several standalone vertical clips: transcription,
          scoring of the strongest moments, automatic 9:16 reframing, burned-in captions, and
          rendering on a background worker. The videos you upload and the clips produced from
          them are yours; ClipForge AI provides the tool, not the source footage.
        </p>
      </LegalSection>

      <LegalSection title="Intellectual property">
        <p>
          The site's interface, code and design are protected. The videos you upload and the
          clips generated from them remain your property; you are responsible for having the
          rights to any footage you process here.
        </p>
      </LegalSection>

      <LegalSection title="Report an issue">
        <p>
          Infringing content, a bug, an abuse of the service: write to {PUBLISHER.email}. Reported
          content is reviewed and removed if unlawful.
        </p>
      </LegalSection>
    </LegalPage>
  )
}
