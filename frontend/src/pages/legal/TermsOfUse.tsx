import { LegalList, LegalPage, LegalSection, PUBLISHER } from './LegalPage'

/**
 * Terms of use. Describes what the product does as it is actually built:
 * upload, transcribe, score, reframe, caption, render. Nothing promised that
 * the product does not hold.
 */
export default function TermsOfUse() {
  return (
    <LegalPage
      title="Terms of use"
      subtitle="What the service does, what it does not, and what everyone agrees to."
    >
      <LegalSection title="Purpose">
        <p>
          These terms govern the use of ClipForge AI. Using the service means accepting them.
        </p>
      </LegalSection>

      <LegalSection title="What the service does">
        <LegalList
          items={[
            'Cuts a long video you upload into several standalone vertical clips.',
            'Transcribes the soundtrack, scores moments, and reframes to 9:16 automatically.',
            'Burns in captions styled from reusable templates and brand kits.',
            'Renders clips in the background and gives you an MP4 and thumbnail for each.',
          ]}
        />
      </LegalSection>

      <LegalSection title="What it does not do">
        <LegalList
          items={[
            'Import from a YouTube or Vimeo link — you upload the file itself.',
            'Edit frame by frame on a timeline — cuts are per clip.',
            'Post to your social accounts for you.',
          ]}
        />
      </LegalSection>

      <LegalSection title="Your account">
        <p>
          You are responsible for the accuracy of the information you provide and for keeping
          your credentials secret. You are responsible for having the rights to any video you
          upload and process.
        </p>
      </LegalSection>

      <LegalSection title="Prohibited use">
        <LegalList
          items={[
            'Uploading content you do not have the rights to process.',
            'Attempting to access another account or another user’s data.',
            'Disrupting the service or extracting its content at scale.',
          ]}
        />
        <p>An account used this way is suspended.</p>
      </LegalSection>

      <LegalSection title="Availability">
        <p>
          The service is provided as-is, without guarantee of uninterrupted availability.
          Maintenance is scheduled to minimise impact on rendering jobs in progress.
        </p>
      </LegalSection>

      <LegalSection title="Changes and governing law">
        <p>
          These terms may change; the version shown here is the one in force. French law
          applies. In case of dispute, an amicable solution is sought first by writing to{' '}
          {PUBLISHER.email}.
        </p>
      </LegalSection>
    </LegalPage>
  )
}
