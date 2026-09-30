# New-requirement kickoff meetings — what to ask

Why this note: first meeting on a new requirement, they presented, I understood
almost nothing, and to "any questions?" I only said "I'll review and get back to
you". That wastes the meeting. There are ALWAYS questions worth asking — the
ones below need zero understanding of the topic.

## Core insight

Ask for test artifacts first. "Do we already have test data / a sample file?"
is not about the data — if it exists, someone already ran something end-to-end
and the requirement is real. If it doesn't, you've just exposed that nobody has
verified anything yet (often including the people presenting). It is a maturity
check disguised as a data question.

## Always-ask checklist (no domain knowledge needed)

### Artifacts (the maturity check)
- Do we have test data already configured? In which environment/pod?
- Do we have a sample file/payload ready for testing (FBDI, CSV, JSON, XML)?
- Has anyone run this end-to-end already, even manually? What happened?

### Flow
- Which system produces the data and which consumes it?
- How does it get there (file drop, REST, event)? How often / what volume?
- What triggers it — schedule, user action, another integration?

### Failure & ops
- What should happen when it fails? Who gets notified?
- How is it reprocessed? Who owns it after go-live?

### Scope & done
- What is explicitly OUT of scope?
- What does "done" look like — what will you check to accept it?
- Who signs off (functional owner)?

### Logistics
- Which environment do we build/test against, and is it ready?
- Any hard deadline or dependency (quarterly Oracle update, another team's go-live)?

## The upgraded fallback line

Don't just say "I'll review and come back with questions". Ask the minimum set
on the spot, THEN say you'll review:

1. Do we have a sample file/payload and test data already?
2. Has anyone run this end-to-end before?
3. What does done look like for you?

## Example

Meeting: "new supplier invoice inbound integration".

- Q: "Do we have a sample FBDI file from the supplier?"
  → A: "No, the supplier hasn't sent one." → Nothing verified yet; the first
  dependency is getting that file — without it dev can't even start.
- Q: "Is there test data in the pod (supplier, POs, invoices to match)?"
  → A: "We think so." → "We think so" = no. Ask them to confirm it exists.
- Q: "What does a successful run look like — invoice created in AP and matched?"
  → Forces them to define acceptance instead of "make it work".
