# FDE Ecosystem and Domain Ontology Page Design

**Date:** 2026-08-27  
**Status:** Approved design, pending written-spec review  
**Target pages:** `portal/fde.html`, `portal/zh/fde.html`

## 1. Purpose

Replace the existing three-project FDE story with a current, evidence-aware explanation of the VLSC ecosystem. The page will explain how field engineering produced multiple product families, how engineering assets move between them, and what stable domain concepts can now be extracted across the portfolio.

The page is both:

1. an FDE case study grounded in shipped systems and field findings; and
2. a lightweight, modular domain ontology for remote amateur-radio operation.

It is not an OWL/RDF knowledge graph and will not claim formal machine reasoning.

## 2. Correct Portfolio Model

The page must describe **three engineering tracks and five product families**. Repositories and client applications must not be counted as independent top-level products.

### 2.1 Radio-control track

#### MRRC Universal product family

A general CAT-controlled radio path based on Hamlib/rigctld. Its system includes the authoritative server, desktop/mobile Web clients, bidirectional audio, WDSP, PTT safety, memory channels, recording, optional RTL-SDR panadapter, ATR-1000 integration, and operational tooling.

#### MRRC Direct USB product family

This is an explicit product lineage:

```text
MRRC FT-710 vertical implementation
    -> abstraction and capability extraction
MRRC Modern multi-radio platform
```

MRRC FT-710 remains visible as the single-radio vertical proof. MRRC Modern is the platformized result, with a `RadioBackend` abstraction, `RadioCapabilities`, FT-710 and IC-7300/IC-7300MK2 backends, capability-driven UI, CAT/CI-V protocol adapters, and backend-specific spectrum/audio handling.

Clients belong inside this family:

- Web/PWA client
- FT710Mobile iOS client
- FT710Android client

Client maturity must be stated separately. In particular, the iOS audit records unresolved P0 PTT-safety issues, while Android implementation/test status and physical-device acceptance are distinct claims.

### 2.2 Direct-IQ SDR track

#### SunMRRC product family

SunMRRC is the authoritative SunSDR2 DX server/system. It includes proprietary UDP protocol integration, IQ receive and transmit paths, server-side DSP, Web control, and stable WebSocket interfaces.

Clients belong inside the product family:

- SunMRRC Web client
- SunsdrMobile native iOS client

SunsdrMobile is not a separate top-level system. It is a client implementation that consumes SunMRRC's service contract and demonstrates protocol reuse with no required server redesign.

### 2.3 Workflow and RF-edge track

#### MRRC-FT8 product family

A headless FT8/FT4 operating system containing the supervised WSJT-X Improved DSP worker, FastAPI control plane, rigctld boundary, UTC slot orchestration, QSO state machine, control lease, PTT safety controller, SQLite/ADIF persistence, mobile PWA, and desktop FT8web-derived client.

#### EFHW product family

A combined knowledge and cyber-physical product family containing the EFHW research base, Fuchs ATU V3.0 hardware design, ESP32-S3 firmware, Bias-T power architecture, servo actuator, NVS tuning cache, and MRRC/ATR-1000 integration.

Its maturity must be explicit: the design and firmware are complete, while PCB manufacture and bench/field verification remain pending. Design targets and simulations must not be presented as measured production results.

## 3. Page Information Architecture

The English and Chinese pages use the same section order and equivalent content.

1. **Hero — One Field, Three Tracks, Five Product Families**
   - Replace the obsolete "three projects" framing.
   - Summarize the ecosystem without unstable vanity metrics.
   - Mention Web, PWA, iOS, Android, and desktop clients as delivery surfaces, not product families.

2. **Two Coupled Loops**
   - FDE delivery loop: Echo -> Delta -> Product.
   - Ontology engineering loop: Scope -> Terms -> Relations -> Constraints -> Validation.
   - Show bidirectional feedback: products provide evidence to the ontology; the ontology gives later projects a shared vocabulary, boundaries, and competency questions.

3. **Three Engineering Tracks**
   - Radio control.
   - Direct-IQ SDR.
   - Workflow and RF edge.
   - Use explicit relationship labels instead of implying a single linear inheritance chain.

4. **Five Product-Family Deep Dives**
   - MRRC Universal.
   - MRRC Direct USB, including FT-710 -> Modern evolution and all client implementations.
   - SunMRRC, including Web and SunsdrMobile.
   - MRRC-FT8.
   - EFHW.

5. **Cross-Product Leverage Graph**
   - Control plane.
   - Media plane.
   - Device plane.
   - Safety plane.
   - Workflow plane.
   - Experience plane.

6. **VLSC Remote Amateur Radio Domain Ontology**
   - Human-readable vocabulary, class partitions, typed relations, constraints, and product profiles.
   - Explicitly describe it as lightweight and modular.

7. **Capability and Maturity Matrix**
   - Compare responsibilities and implementation boundaries.
   - Keep product capability separate from evidence maturity.

8. **Expandable Appendix**
   - Evidence/version ledger.
   - Bilingual glossary.
   - Competency questions.
   - Detailed timelines where evidence is reliable.
   - References to relevant project documentation and ontology standards.

## 4. Product-Family Analysis Template

Each deep dive uses the same fields:

1. **Field Problem** — the operator or engineering problem observed in context.
2. **Echo Evidence** — captures, logs, operational failures, protocol traces, or user feedback.
3. **Delta Breakthrough** — the smallest working technical breakthrough.
4. **Product Boundary** — what became a maintained system and what remains outside it.
5. **Reused Assets** — inherited implementation, consumed contract, or reused engineering pattern.
6. **New Assets** — reusable contracts, modules, workflows, tests, or safety rules created by the product.
7. **Ontology Contribution** — stable concepts or relations exposed by the work.
8. **Maturity/Evidence** — design, simulation, automated test, bench test, field validation, or released operation.

The page must not reproduce seven README files. Long version histories belong in the appendix.

## 5. Ontology Position

### 5.1 Definition

The page uses "ontology" in the applied knowledge-engineering sense: an explicit specification of concepts, relationships, vocabulary, and coherent-use constraints for a domain.

The deliverable is a **lightweight modular domain ontology**, not merely a taxonomy and not a formal OWL implementation.

It must include:

- stable bilingual preferred terms;
- classes for entities, activities, and information objects;
- typed relationships with defined direction;
- domain/range descriptions where useful;
- safety and state-ownership constraints;
- product-family profiles;
- competency questions that validate scope.

### 5.2 Separation from FDE

Ontology is not a fourth FDE phase. The two processes are coupled:

```text
FDE:       Echo -> Delta -> Product
                         |       ^
                         v       |
Ontology: Scope -> Terms -> Relations -> Constraints -> Validate
```

Project results create evidence for ontology revisions. The ontology accelerates later projects by providing shared language, boundaries, and reusable questions.

### 5.3 Top-Level Partitions

The ontology distinguishes:

- **Agent** — operator or software agent bearing responsibility.
- **Physical Entity** — station, radio, tuner, antenna, sensor, actuator, audio interface.
- **Software System** — service, adapter, DSP worker, client application.
- **Activity/Process** — observation, actuation, demodulation, decoding, transmission, QSO, tuning.
- **Information Object** — command intent, state report, sample, frame, configuration, log record.
- **Capability/Function** — control, sensing, actuation, media processing, workflow execution.
- **Policy/Constraint** — authority, ownership, safety interlock, timeout, retry, fail-safe behavior.
- **Evidence/Provenance Record** — test result, field observation, release, design target, simulation.

`ProductFamily`, `Repository`, `Commit`, and `Release` belong to portfolio/provenance views, not the radio operational core.

## 6. Ontology Modules

### 6.1 Identity and Authority

Core concepts:

- Operator
- SoftwareAgent
- Credential
- Session
- ControlLease
- TransmissionAuthority

Key relations:

- `usesClient`
- `opensSession`
- `holdsLease`
- `authorizesIntent`
- `mayStopTransmission`

### 6.2 Station and Equipment

Core concepts:

- Station
- Radio / Transceiver
- Tuner / MatchingNetwork
- Antenna
- Sensor
- Actuator
- AudioDevice
- ComputeNode

Key relations:

- `containsDevice`
- `connectedTo`
- `hosts`
- `feeds`
- `matchesImpedanceFor`

### 6.3 Function, Capability, and Service

Core concepts:

- Function
- Capability
- Command
- State
- Service
- InteractionAffordance

Key relations:

- `hasFunction`
- `supportsCapability`
- `exposesService`
- `acceptsCommand`
- `reportsState`

This follows the useful separation in SAREF and W3C WoT: devices perform functions; services expose discoverable interactions; protocol bindings describe how an interaction is reached.

### 6.4 Command, Actuation, Observation, and State

These must remain distinct:

```text
CommandIntent (information object)
    -> requests
Actuation (activity)
    -> changes
FeatureOfInterest / DeviceState
    -> observed by
Observation (activity)
    -> yields
ObservationResult / StateReport (information object)
```

This module aligns conceptually with SOSA/SSN while adding radio-specific command authority and state ownership.

### 6.5 Protocol and Transport

Core concepts:

- DeviceAdapter
- DeviceProtocol
- InteractionProtocol
- ProtocolBinding
- Transport
- Endpoint

Examples:

- Hamlib/rigctld
- Yaesu CAT
- Icom CI-V
- SunSDR proprietary binary UDP
- FT4222 SPI
- USB Audio
- HTTP/WebSocket

WebSocket, USB, UDP, serial, and SPI are bindings/transports, not domain capabilities.

### 6.6 Signal, Media, and Measurement

The model distinguishes physical phenomena from digital representations:

```text
RFSignal -> sampledAs -> IQSample / AudioSample
Sample sequence -> representedAs -> Stream
Stream -> packetizedAs -> Frame
DSP activity -> derives -> SpectrumEstimate / DecodedMessage
```

Measurements use explicit quantity kind, value, unit, timestamp, and source. Examples include frequency in Hz, power in W, signal level in dB/dBm, temperature in degrees Celsius, latency in milliseconds, and dimensionless SWR.

### 6.7 Time and Workflow

Core concepts:

- Instant
- Interval
- Duration
- UTC Slot
- Deadline
- QSO
- QsoState
- Candidate
- DecodeBatch
- TuneCycle
- RetryBudget

OWL-Time supplies the general instant/interval vocabulary. VLSC-specific concepts define FT8 slots, QSO transitions, tuning phases, and deadlines.

### 6.8 Safety and Reliability

Core concepts:

- TransmissionContext
- PttState
- SafetyPolicy
- Interlock
- Watchdog
- Timeout
- RetryPolicy
- FailSafeAction
- Rollback
- HealthState

Core invariants:

1. A mutable state has one authoritative owner.
2. `PttState == TX` requires a live transmission context and valid authority.
3. Disconnect, lease expiry, timeout, or unrecoverable error converges to RX-safe state.
4. A sent PTT command is not equivalent to confirmed TX state.
5. Control intent and device observation remain separate.
6. A client mirror is not authoritative server/device state.
7. Safety claims must name their detection path and response path.
8. Undetectable faults must not be presented as firmware-detected faults.

### 6.9 Evidence and Provenance

Use a lightweight pattern based on PROV-O:

- EvidenceArtifact
- EngineeringActivity
- ResponsibleAgent
- `used`
- `generated`
- `derivedFrom`
- `attributedTo`

Every volatile claim should carry an evidence status:

- Design target
- Simulation result
- Automated test
- Bench verified
- Field verified
- Released/operational
- Deferred or known issue

## 7. Product Profiles

Each product family is a profile that selects and specializes ontology concepts.

### MRRC Universal profile

Emphasizes Hamlib-based device abstraction, browser control, bidirectional audio, WDSP, multi-instance operation, memory/recording, ATR integration, and PTT recovery.

### MRRC Direct USB profile

Emphasizes direct device adapters, real hardware scope sources, backend-specific audio clock domains, capability-driven UI, and native clients. The profile contains an explicit lineage from the FT-710 vertical implementation to MRRC Modern.

### SunMRRC profile

Emphasizes proprietary device protocol, IQ streams, server-side demodulation/modulation, FFT products, stable service contracts, and Web/native client implementations.

### MRRC-FT8 profile

Emphasizes time, workflow, DSP worker isolation, control lease, universal STOP, audit history, QSO persistence, and digital-message semantics.

### EFHW profile

Emphasizes antenna/matching-network entities, remote observations, physical actuation, tuning workflow, NVS tune profiles, health state, RF safety boundaries, and explicit undetectable-fault declarations.

## 8. Competency Questions

The ontology section must demonstrate that it can answer at least these questions:

1. Which product family supports a given radio model?
2. Which device adapter and protocol binding control that model?
3. Which service is the authoritative owner of radio/PTT state?
4. Which clients consume the service contract, and which capabilities do they expose?
5. Can a given client initiate TX, and which safety policies constrain it?
6. What happens when that client disconnects during TX?
7. Is a displayed spectrum derived from IQ, FT4222 SPI, CI-V, or S-meter synthesis?
8. Which sensor produced a given SWR/power/temperature value, at what time and unit?
9. Which activity transforms an IQ or audio stream into a spectrum or decoded message?
10. Which workflow owns a UTC slot, retry budget, QSO state, or tune cycle?
11. Which implementation directly inherited an asset, consumed a contract, independently implemented a concept, or was only inspired by a prior design?
12. Is a capability a design target, simulation result, automated-test result, bench result, field result, or released feature?

## 9. Reuse Semantics

Project relationships use four distinct labels:

- **inherits** — directly inherits implementation or structure.
- **consumes** — consumes a stable external contract.
- **implements** — independently realizes the same ontology concept.
- **inspired-by** — reuses an engineering lesson or pattern without direct implementation inheritance.

This avoids unsupported claims such as treating shared PTT principles as shared source code.

## 10. Capability Matrix

The matrix compares product-family responsibilities, not repository popularity. Columns include:

- supported equipment;
- device-control protocol;
- control service;
- RX/TX media path;
- spectrum source;
- DSP location;
- workflow automation;
- RF actuation;
- Web/PWA/native clients;
- safety model;
- persistence;
- deployment targets;
- evidence maturity.

On narrow screens the table scrolls horizontally and retains row labels.

## 11. Visual and Interaction Design

The page retains the portal's existing dark Octen visual language and requires no new framework or build step.

- Hero uses the five-product-family framing.
- Main ecosystem map visually separates three tracks and nests clients inside product families.
- Relationship diagrams use text labels and line styles in addition to color.
- Product-family cards use a consistent field order.
- Ontology uses a compact overview followed by readable module cards.
- Long timelines, evidence tables, glossary, and references are collapsible.
- Expand/collapse controls use native buttons with `aria-expanded` and keyboard operation.
- SVG diagrams include `<title>` and `<desc>`.
- Mobile layouts stack cards; wide tables use contained horizontal scrolling.
- Inline diagrams and HTML/CSS are preferred over external image-generation or build tooling.

## 12. Evidence and Content Rules

1. Current project documents and code-adjacent SDDs take precedence over old marketing copy.
2. Published release, source-tree version, SDD version, and deployment status are separate fields.
3. Automated tests do not imply physical hardware acceptance.
4. Simulation does not imply bench verification.
5. Design targets use future/target language.
6. Historical commit counts are only stated with repository scope and as-of date.
7. Unverifiable legacy numbers such as broad commit/cycle totals are removed or explicitly marked historical estimates.
8. Known safety gaps are not hidden by aggregate feature claims.

Current facts to reflect include:

- MRRC FT-710 source history through v1.8.1; v1.8.0 published Windows package; 439-test current documented suite.
- MRRC Modern v1.12.0; FT-710, IC-7300, and IC-7300MK2 backends; 633 automated tests; physical IC acceptance remains separate.
- MRRC-FT8 public release history and SDD evolution are separate; the SDD records field iterations through V1.8.
- EFHW Fuchs ATU V3.0 firmware/design complete; PCB and bench validation pending.
- SunsdrMobile belongs to SunMRRC and consumes its service contract.
- FT710Mobile and FT710Android belong to the Direct USB family; their safety/test/device-acceptance maturity differs.

## 13. Verification

Before completion:

1. Validate both HTML files for balanced structure and duplicate IDs.
2. Check all local links and referenced assets.
3. Verify EN/ZH section parity and equivalent facts.
4. Confirm no remaining "three projects" or "seven top-level projects" claims on FDE pages.
5. Confirm SunsdrMobile is nested under SunMRRC.
6. Confirm iOS/Android clients are nested under the Direct USB family.
7. Check every maturity badge against the cited local source.
8. Test desktop and mobile viewport layout.
9. Test keyboard operation and `aria-expanded` updates for appendices.
10. Run project diagnostics and a lightweight local HTTP smoke check.

## 14. Out of Scope

- RDF, OWL, JSON-LD, SHACL, triple stores, or automated reasoning.
- A new JavaScript framework or build system.
- Rewriting individual product websites or SDDs.
- Resolving product implementation defects discovered during content research.
- Automatically deriving project metrics at page runtime.

## 15. Research Basis

- Tom Gruber, *Ontology*: explicit specification of a conceptualization and coherent representational vocabulary.
- Stanford, *Ontology Development 101*: domain/scope, reuse, iterative development, classes/properties/instances, and competency questions.
- W3C OWL 2 Primer: formal classes, properties, individuals, axioms, and open-world semantics.
- W3C SKOS Primer: lightweight concept schemes, labels, broader/narrower, and associative relations.
- W3C SOSA/SSN: sensors, observations, actuators, actuations, systems, platforms, procedures, and features of interest.
- W3C Web of Things Thing Description: properties, actions, events, and protocol bindings.
- W3C PROV-O: entities, activities, agents, generation, use, derivation, and attribution.
- W3C OWL-Time: instants, intervals, duration, and temporal relations.
- ETSI SAREF: device, function, command, state, service, property, and measurement separation.
- QUDT: quantity kinds, quantity values, units, and dimensional semantics.
