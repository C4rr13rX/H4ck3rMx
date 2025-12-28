# H4ck3rMx Trust Graph and Signing Architecture

## 1. Trust graph model
- **Adjacency (“hex”) rules:** Each app declares up to six trusted peers (`trusted_peers[<=6]`). Directional edges; reciprocity recommended but not required. Trust is scoped to package name + signing certificate digest.
- **Weight aggregation:** Each edge carries attestation metadata (`attestor_id`, `signature`, `timestamp`, `weight`). Weight defaults to count of independent attestations for the same edge. Reputation weighting optional (`attestor_score`) to bias cosigners/anchors.
- **Anchors:** First-party audited apps are bootstrap anchors. Anchors publish long-term keys and rotation schedule; all devices ship with the current anchor bundle.
- **Data format:**
  - `trust_manifest.json` embedded in APK `assets/` and mirrored in store metadata.
  - Fields:
    - `schema_version`, `app_id` (package), `app_cert_sha256`, `manifest_version`, `issued_at`, `expires_at`, `nonce`.
    - `trusted_peers`: array of up to six entries `{app_id, app_cert_sha256, purpose, expires_at}`.
    - `attestations`: array of `{attestor_id, attestor_cert_sha256, signature, issued_at, weight}` covering the manifest hash.
    - `anchors`: list of anchor IDs relied upon for reachability proofs.
    - `revocation_endpoints`: CRL/OCSP-like URIs.
  - Store metadata mirrors manifest plus store-level detached signature (`store_sig`) over manifest hash + APK digest.
  - Expiry must be <= 180 days; manifests with expired peers rejected.

## 2. Developer portal & review flow
- **Pipeline:** upload → static analysis → dynamic sandbox run → AI scan → 6-developer sponsorship queue → threshold signature issuance → publish.
- **Roles/permissions:**
  - Developer: upload builds, view results, request sponsorship.
  - Security analyst: triage static/dynamic/AI findings, issue holds.
  - Sponsor (cosigner): approve/deny sponsorship; contributes to threshold signature.
  - Release manager: final go/no-go, key rotation authority.
  - Auditor: read-only access to tamper-evident logs and reports.
- **Tamper-evident audit logs:** append-only (Merkle-linked) log per action; checkpoints signed by release manager key and periodically anchored to public transparency log.
- **Threshold signing:** 6-of-N cosigner policy. Cosigners use HSM-backed keys; signatures aggregated (e.g., BLS multi-signature or threshold ECDSA) into `cosignature`. All individual partial signatures logged.
- **Key distribution/rotation:** Cosigner public keys published in portal JWKS with `kid`, `role`, `not_before`, `expires_at`. Rotation uses overlapping validity and log checkpoints; devices fetch delta updates and pin issuer.

## 3. Signing & verification
- **Primitives:** APK Signature Scheme v4 (preferred) and v3 fallback. Detached store signature (Ed25519/threshold ECDSA/BLS) over `trust_manifest.json` hash + APK digest.
- **On-device verification steps:**
  1) Validate APK v4/v3 signature and certificate chain.
  2) Extract `trust_manifest.json`; verify store detached signature against pinned store key.
  3) Verify manifest expiry, nonce freshness, and that `trusted_peers` ≤ 6.
  4) Verify 6 cosignatures/threshold aggregate against current cosigner JWKS and policy (>=6 valid, non-expired cosigners, correct manifest hash).
  5) Build trust graph: ensure path from app to at least one anchor via declared peers within expiry windows; count independent attestations as weight.
  6) Check revocation via CRL/OCSP-like endpoint; honor stapled responses from store metadata if present.
  7) Cache validated manifest with monotonic versioning; pin to app certificate digest.

## 4. OS policy enforcement
- **Package manager:** rejects installs/enables when manifest invalid, cosignatures <6, or no path to an anchor hex. Provides UX message with failing condition and anchor names.
- **Runtime IPC constraints:**
  - Binder/Intent/foreground-service communication allowed only to declared trusted peers; enforced via package manager-maintained ACL derived from manifest.
  - SELinux policy auto-generated to confine app domains to declared peers; violations denied and logged with user-facing toast/notification (“Blocked IPC to undeclared app”).
  - Permissions hook rejects implicit intents targeting non-peers unless explicitly user-consented at runtime.
- **User UX:** Install failure dialog lists missing requirements (e.g., “Need connectivity to anchor X” or “Cosignatures <6”). Runtime blocks surface notification with “View trust manifest” deep link.

## 5. Networking & update paths
- **Metadata fetch:** device fetches trust metadata deltas from store using pinned TLS + key pinning (store root + cosigner JWKS pins). Supports binary deltas and ETags for efficiency.
- **Offline installs:** allow if manifest and store detached signature are bundled and not expired; revocation checked once online before first run. Preload anchor bundle and recent CRL snapshots in OTAs.
- **Manifest versioning:** monotonically increasing `manifest_version` per app; replay defenses require version > cached and signed timestamp > last seen.
- **Rollback protection:** reject manifests/APKs with lower `manifest_version` or older signing time; hardware-backed monotonic counter optionally recorded per app.

## 6. Revocation & incident response
- **CRL/OCSP:** short-lived (e.g., 6h) responses; stapling allowed in store metadata. Device caches but requires fresh after expiry.
- **Forced uninstall/quarantine:** policy allows server-pushed quarantine; package manager disables IPC and network, prompts user, and offers uninstall. Anchor-level emergency list can force removal.
- **Emergency key rotation:** store and cosigner keys carry `not_before`/`expires_at`; devices accept overlapping windows and require newest checkpoint signature from release manager. Anchors publish rotation manifests.
- **Developer dispute/appeal:** portal workflow to appeal revocation; requires new build with remediations and fresh 6 cosignatures; audit log records timeline.

## 7. Metrics & observability
- **Telemetry (opt-in, privacy-preserving):**
  - Install decisions (pass/fail reason codes), trust graph depth/degree (aggregated), IPC block counts.
  - All metrics pseudonymized with per-device rotating salt; no raw package names unless hashed with pepper stored server-side.
- **Redaction:** strip PII, bucket timestamps, and minimum aggregation thresholds before upload. Local logs retain full detail for user inspection only.

## 8. Threat model & abuse cases
- **Abuse vectors:** cosigner collusion (6 compromised), Sybil/puppet developer accounts, dormant-to-malicious updates, manifest replay/rollback, anchor compromise, offline sideloading without revocation check.
- **Mitigations:**
  - Reputation weights and staking/bonding for cosigners; slashing on abuse.
  - Cooldown periods and staged rollouts gated on real-user telemetry before wide availability.
  - Mandatory fresh 6 cosignatures per manifest version; enforced expiry windows and monotonic versions.
  - Transparency logs for manifests and cosignatures; public monitors.
  - Anchors audited with hardware-backed keys and separation of duties.
- **Assumptions/residual risks:** at least one honest anchor, device clock not massively skewed, users may disable telemetry, collusion beyond threshold remains possible, sophisticated on-device exploit may bypass IPC enforcement if kernel compromised.

## 9. Developer experience
- **SDK/CLI:**
  - Generate `trust_manifest.json` from `build.gradle` metadata and peer list; lint to block >6 peers or missing anchor references.
  - Commands: `hex init`, `hex add-peer --app-id ...`, `hex lint`, `hex sign --dev-key`, `hex request-sponsor`, `hex verify --local`.
  - Local adjacency tester simulates trust path to anchors using cached anchor bundle.
- **Sample hex graphs:** provided in SDK docs showing anchor + 3 peers with weighted attestations.
- **Lint rules:** enforce ≤6 peers, non-expired peers, unique app IDs, and manifest expiry <=180d.

## 10. Store UX
- **Trust chain view:** displays cosigners (names, reputations), timestamps, anchor paths count, and risk flags (recent cosigners, single anchor path, low weights).
- **Install rule messaging:** “Requires at least one anchor path; cosignatures >=6.” Weak trust surfaces yellow banner; strong trust green.
- **Post-install:** “View trust manifest” button shows peers, expiry, revocation status, and logs of blocked IPCs.

## 11. Device onboarding, connectivity, and driver provisioning
- **Host tooling prerequisites:** `adb`, `fastboot`, `avbtool`, `openssl`, and platform build tools; optional `uefi-firmware-parser`/`lsusb` for advanced diagnostics. Ship cross-platform installers with udev rules for Linux and signed drivers for Windows/macOS.
- **ADB/fastboot recognition:** wizard prompts user to enable OEM unlock/USB debugging; auto-pulls vendor IDs via `lsusb` and applies matching udev rule or Win/macOS driver package. For unknown vendors, fall back to generic WinUSB/CDC-ACM where permitted.
- **Connectivity bootstrap on device:** minimal initramfs includes hardware-probing agent (lightweight ML heuristic plus rules) to prioritize modems/5G cards → Wi‑Fi → Ethernet/USB tethering. Presents captive portal-style UI to select SSID/eSIM/APN; falls back to offline mode with cached driver bundles.
- **Dynamic driver fetch:** after basic IP connectivity, device fingerprinting (`ro.product.*`, modem baseband IDs, PCI/USB IDs) queries signed vendor bundle index. Driver packages are signed and integrity-checked; downloads happen over pinned TLS with resume and rate-limit/backoff.
- **Offline path:** recovery image can sideload a pre-signed “driver pack” zip via `adb sideload`; package manager validates signatures and manifest expiry before applying.
- **Safety rails:** driver installer runs in restricted SELinux domain; rollbacks available if new driver fails health checks. All installs logged to tamper-evident log with timestamps and package hashes.
- **APK signing readiness:** build system pre-installs keystore tooling, cosigner JWKS cache, and `trust_manifest.json` generator so that freshly built system apps/APKs can be signed (v4/v3) and cosigned before pushing via ADB/fastboot.
