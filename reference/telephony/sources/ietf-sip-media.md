# IETF SIP and media stack — normalized source note

This note maps the core IETF documents used by the telephony catalog. Each
RFC remains the authority for its normative requirements.

## RFC 3261 — SIP

Official source: <https://www.rfc-editor.org/rfc/rfc3261.html>
Anchor: SIP transactions, dialogs, methods and response handling

SIP transactions and dialogs are related but distinct state machines. A
transaction handles a request/response exchange; a dialog represents a
longer-lived peer relationship established by dialog-forming methods. A
diagnosis must identify the transaction and dialog state rather than inferring
call state from one HTTP-like response.

## RFC 3263 — SIP server location

Official source: <https://www.rfc-editor.org/rfc/rfc3263.html>
Anchor: locating SIP servers with URI transport, NAPTR, SRV and address records

SIP reachability can depend on URI transport, DNS service discovery and
address resolution. A routing check must preserve the selected transport,
target and fallback path.

## RFC 3264 and RFC 4566 — SDP offer/answer

Official sources:

- <https://www.rfc-editor.org/rfc/rfc3264.html>
- <https://www.rfc-editor.org/rfc/rfc4566.html>

An offer/answer exchange establishes compatible session and media parameters.
The review surface includes media sections, payload types, direction
attributes, addresses, ports, codecs and format parameters. Hold, resume,
re-INVITE and UPDATE are session modifications, not new independent calls.

## RFC 3550 and RFC 3551 — RTP/RTCP

Official sources:

- <https://www.rfc-editor.org/rfc/rfc3550.html>
- <https://www.rfc-editor.org/rfc/rfc3551.html>

RTP carries timed media packets and exposes sequence, timestamp and SSRC
identity. RTCP supplies control and quality information. Payload type and
profile negotiation must agree with the SDP contract; a successful SIP dialog
does not prove bidirectional media.

## RFC 8445, RFC 5389 and RFC 5766 — ICE, STUN and TURN

Official sources:

- <https://www.rfc-editor.org/rfc/rfc8445.html>
- <https://www.rfc-editor.org/rfc/rfc5389.html>
- <https://www.rfc-editor.org/rfc/rfc5766.html>

ICE gathers candidates, performs connectivity checks and nominates a usable
candidate pair. STUN supports discovery/checks and TURN provides relaying when
direct connectivity is unavailable. Candidate gathering, checklist progress,
nomination and selected pair are separate observable states.

## RFC 5763, RFC 5764 and RFC 8827 — secure media

Official sources:

- <https://www.rfc-editor.org/rfc/rfc5763.html>
- <https://www.rfc-editor.org/rfc/rfc5764.html>
- <https://www.rfc-editor.org/rfc/rfc8827.html>

DTLS-SRTP uses the authenticated DTLS exchange and the SDP fingerprint to
establish keys for protected RTP. The fingerprint, certificate/DTLS state and
SRTP context are distinct evidence points.

## RFC 8834 — WebRTC RTP requirements

Official source: <https://www.rfc-editor.org/rfc/rfc8834.html>

WebRTC media transport has additional profile and signaling requirements,
including secure RTP profiles, ICE-provided transport addresses and explicit
payload/format signaling. A WebRTC gateway may interwork with a non-WebRTC
media profile, but that adaptation must be explicit.

## Evidence targets

Useful evidence includes SIP transaction/dialog traces, SDP offers and
answers, DNS resolution, ICE candidate/check state, selected pair, DTLS
fingerprint and handshake state, SRTP counters, RTP/RTCP loss/jitter and
client WebRTC telemetry.
