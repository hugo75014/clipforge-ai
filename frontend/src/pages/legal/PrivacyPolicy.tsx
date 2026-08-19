import { LegalList, LegalPage, LegalSection, PUBLISHER } from './LegalPage'

/**
 * Privacy policy — describes what the product actually stores (users,
 * uploaded videos, transcripts, clips, exports), not a generic template.
 */
export default function PrivacyPolicy() {
  return (
    <LegalPage
      title="Privacy policy"
      subtitle="What we store, why, for how long, and how to take it back."
    >
      <LegalSection title="What we store">
        <LegalList
          items={[
            'Your account: name, email address, hashed password.',
            'The videos you upload, and the clips, thumbnails and exports generated from them.',
            'The transcript of your videos, with word-level timing, produced to score moments and place captions.',
            'Your brand kits and templates, if you create any.',
            'Basic technical logs needed to run and debug the rendering pipeline.',
          ]}
        />
        <p>No payment card data is collected or stored by ClipForge AI directly.</p>
      </LegalSection>

      <LegalSection title="Why, and on what basis">
        <LegalList
          items={[
            'Running the service you asked for — transcribing, scoring, reframing and rendering your videos — under the contract formed when you create an account.',
            'Keeping your account secure and preventing abuse of the service: legitimate interest.',
          ]}
        />
        <p>Your data is never sold, rented, or used for targeted advertising.</p>
      </LegalSection>

      <LegalSection title="Who has access">
        <LegalList
          items={[
            "The operator of ClipForge AI, for support and security.",
            'Our technical providers — hosting and, where you configure one, the AI provider used for transcription or scoring — acting on instruction, with no use of your data for their own purposes.',
          ]}
        />
      </LegalSection>

      <LegalSection title="How long">
        <LegalList
          items={[
            'Your account: kept as long as you keep it. Delete it at any time from Settings.',
            'Uploaded videos, clips and exports: kept until you delete them or your account.',
            'Technical logs: kept for as long as needed to debug an issue, twelve months at most.',
          ]}
        />
      </LegalSection>

      <LegalSection title="Your rights">
        <p>
          You can access, correct, or delete your data, or ask for a copy of it, at any time from
          Settings, or by writing to {PUBLISHER.email}. If unresolved, you can contact the CNIL
          (www.cnil.fr).
        </p>
      </LegalSection>

      <LegalSection title="Cookies">
        <p>
          This site uses a session cookie to keep you signed in, and nothing else — no
          advertising cookie, no third-party audience measurement.
        </p>
      </LegalSection>

      <LegalSection title="Security">
        <p>
          Traffic is encrypted. Passwords are stored as an irreversible hash, never in clear
          text.
        </p>
      </LegalSection>
    </LegalPage>
  )
}
