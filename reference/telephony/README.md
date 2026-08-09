# Telephony Reference Catalog

This catalog is a local, normalized navigation layer for protocol-driven
telephony work. It is not a project architecture and it is not a substitute
for the cited standards.

## Purpose

The catalog gives RKX Scout and coverage slots a bounded set of references for:

- designing SIP, media, NAT traversal, security, interconnection and IMS
  behaviour;
- debugging a concrete SIP/SDP/ICE/DTLS/RTP symptom;
- reviewing an implementation against a documented profile or invariant;
- separating normative requirements from valid deployment choices.

An entry becomes relevant only when local code, configuration, trace or runtime
evidence connects it to the reported problem. A mismatch with a reference is
not automatically a defect.

## Layout

| Directory | Scope |
|---|---|
| `sip/` | Registration, transactions, dialogs, routing, authentication, failures and peering |
| `sdp/` | Offer/answer, media direction and session modification |
| `rtp/` | RTP/RTCP, payloads, ports, DTMF and media quality |
| `nat-traversal/` | ICE, STUN, TURN and candidate selection |
| `security/` | TLS, DTLS, SRTP, identity and fingerprints |
| `topology/` | SBC, proxy, media relay and PBX/provider interconnection |
| `call-flows/` | Establishment, cancellation, transfer, hold/resume and recovery |
| `deployment/` | Plane separation, redundancy, observability and recording |
| `ims/` | IMS control plane, media functions and interconnection |
| `sources/` | Small normalized source notes with exact official anchors |

The category names are the stable taxonomy. Entries are centralized in
`catalog.yaml` so Scout can retrieve a bounded record without scanning a
directory tree; category-specific notes can be split out later without
changing the entry IDs.

## Entry contract

Every entry has:

- a stable `reference_id` and one `reference_type`;
- source authority, pinned document revision and an exact local anchor;
- applicability and preconditions;
- normative expectations and explicitly allowed variants;
- observable evidence targets;
- failure modes, a bounded diagnostic branch and verification targets.

`call_flow` entries describe states, transitions, branches and timers. They do
not imply that every deployment uses one unconditional message sequence.

## Source policy

The catalog keeps metadata and normalized facts, not full third-party
repositories or PDFs. Official URLs and document revisions remain in
`catalog.yaml`, including each source `authority` and `status`
(`normative`, `industry_profile` or `reference_architecture`). Local source
notes preserve the exact anchors that Scout is allowed to read. Adding a
complete external document requires a separate license and repository-size
decision.
