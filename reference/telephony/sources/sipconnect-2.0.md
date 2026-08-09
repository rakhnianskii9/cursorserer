# SIPconnect 2.0 — normalized source note

Source authority: SIP Forum
Document: SIPconnect 2.0 Technical Recommendation
Revision: 2.0, ratified December 2016
Official source: <https://www.sipforum.org/download/sipconnect-technical-recommendation-version-2-0/?wpdmdl=2818>

This file contains normalized navigation facts. The official recommendation is
the authority for the normative wording.

## Reference architecture

SIPconnect models direct interoperability between an enterprise SIP-PBX
network and a service-provider network. It separates:

- a signaling reference point carrying SIP signaling;
- a media reference point carrying RTP/RTCP;
- enterprise and provider media endpoints, which may be placed in an SBC,
  PBX, gateway, media server or other media-capable element.

The two reference points form the SIPconnect interface. Signaling and media
endpoints are related, but the model does not require them to be the same
physical component.

## Registration and static modes

The provider can locate the enterprise SIP-PBX through:

- registration mode, where the PBX registers with the provider;
- static mode, where the provider uses configured or discoverable signaling
  reachability.

An implementation must make the selected mode, authentication contract,
address discovery and failure behaviour observable.

## Call origination and termination

The profile covers the minimum interoperability behaviour for calls originated
from the enterprise toward the provider and calls terminated toward the
enterprise. A review must identify the direction, dialog role, routing
decision, media endpoints and response handling instead of treating
“connected” as a sufficient result.

## Protocol profile and negotiation

SIPconnect narrows implementation choices left open by the underlying IETF
specifications. Codec support, packetization, DTMF, media handling, identity,
security and IPv6 behaviour are profile concerns and must be checked against
the selected recommendation revision.

## Security and interconnection

The reference architecture permits border elements such as an SBC to enforce
signaling and media policy at the enterprise/provider boundary. Security,
topology exposure, address handling and media anchoring are separate checks;
passing SIP signaling does not prove that the media or security contract is
correct.

## Evidence targets

Useful local evidence includes SIP messages and response codes, registration
state, Contact/Via/Route data, SDP offer/answer, selected media endpoints,
FreeSWITCH/SBC configuration, TLS/DTLS state and RTP/RTCP counters.
