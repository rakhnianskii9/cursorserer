# 3GPP IMS — normalized source note

Source authority: 3GPP
Primary architecture document: 3GPP TS 23.228, Release 18, version 18.11.0
Official source: <https://www.etsi.org/deliver/etsi_TS/123200_123299/123228/18.11.00_60/ts_123228v181100p.pdf>

This note is a navigation layer. The 3GPP specification is authoritative for
the normative architecture, reference points and procedures.

## Control-plane roles

The IMS reference model separates logical control functions:

- UE is the subscriber endpoint;
- P-CSCF is the first SIP contact point for the IMS domain;
- I-CSCF is an entry/routing function for the home network;
- S-CSCF performs subscriber session control and service invocation;
- application servers provide service logic;
- HSS/UDM and policy functions provide subscriber and policy data according
  to the selected release/profile.

The exact deployment may combine or distribute functions, but the logical
responsibilities and reference points must remain identifiable.

## Signaling and media

IMS separates signaling procedures from media and bearer handling. Media
resources, gateways, border functions and policy control may participate
without being the same component as the CSCF signaling functions.

## Procedures and interconnection

Registration, authentication, session establishment, modification, release,
NAT traversal and interconnection are distinct procedure families. A trace
review must state which procedure and release/profile it is checking.

## Evidence targets

Useful evidence includes UE/P-CSCF/I-CSCF/S-CSCF hop identity, SIP/SDP
messages, subscriber lookup and authentication outcomes, application-server
invocation, policy decisions, gateway/border routing and separate signaling
and media observations.
