# SPEERMINT — normalized source note

Source authority: IETF
Primary documents:

- RFC 5486: <https://www.rfc-editor.org/rfc/rfc5486.html>
- RFC 6406: <https://www.rfc-editor.org/rfc/rfc6406.html>

The RFCs are authoritative for the reference architecture and terminology.

## Session peering model

SPEERMINT describes Layer 5 session peering between SIP Service Provider
domains. The peering model is about inter-domain session routing and does not
assume that the signaling and media paths are identical.

## Functional components

The reference model names logical functions such as:

- Lookup Function (LUF) and Location Routing Function (LRF);
- Signaling Function (SF);
- Signaling Path Border Element (SBE);
- Data Path Border Element (DBE);
- originating, terminating and indirect provider domains.

These are logical responsibilities, not a demand that every deployment use a
separate process for every function.

## Routing and interconnection checks

A peering review should identify the domain boundary, target discovery method,
session-routing data, signaling border policy and media-border policy. Direct
and indirect peering are different paths and must not be collapsed into one
generic “provider route” check.

## Evidence targets

Useful evidence includes SIP URI and E.164 routing inputs, DNS/ENUM or other
lookup results, selected provider path, SBE/DBE policy, topology hiding,
inter-domain response codes and media-path observations.
