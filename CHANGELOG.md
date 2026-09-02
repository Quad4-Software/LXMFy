# Changelog

## [Unreleased]

### CI/CD
- GitHub Actions for lint, typecheck, tests, live-local Alice/Bob, and build
- Secure defaults: SHA-pinned actions, least-privilege token, Dependabot, dependency review, Scorecard, CODEOWNERS
- OIDC publish to PyPI on GitHub release (or confirmed manual run)

### Updates
- Dropped former self-hosted package registry publish targets
- Project links point at GitHub

## [2.0.4] - 2026-09-02

### Fixes
- Always drop inbound LXMF messages with an invalid signature

### Tests
- Alice/Bob local live LXMF test over TCP loopback (LXMFY_LIVE_LOCAL=1)

## [2.0.3] - 2026-09-01

### Fixes
- Outbound stamp cost comes from the peer announce or an explicit send override
- Config stamp_cost is inbound-only again
- Outbound messages include reply tickets by default

### Updates
- RNS >=1.5.2, LXMF >=1.1.1
- Debugger covers stamp, ticket, and ratchet send blockers more clearly

## [2.0.2] - 2026-07-23

### Features
- Debugger CLI and helpers for send/receive diagnosis
- Privacy-redacted shareable reports and blocker lists

### Fixes
- Delivery hash no longer registers lxmf/delivery on Transport

### Updates
- Color output respects NO_COLOR / FORCE_COLOR and adds --no-color

## [2.0.1] - 2026-07-21

### Fixes
- Prefer existing user/system Reticulum config over the bot config path
- Isolated bots force share_instance = No to avoid shared-instance digest rejection
- opportunistic_sending now selects LXMF OPPORTUNISTIC delivery

### Tests
- Config discovery and isolated share_instance coverage
- Opt-in live LXMF ping/pong (LXMFY_LIVE_LXMF=1)

### Updates
- RNS >=1.3.9

## [2.0.0] - 2026-07-10

Final feature release of LXMFy.

### Features
- RRC client support for hub chat ([RRC spec](https://rrc.kc1awv.net/))
- RRCBot template and session persistence options

### Fixes
- Crash-safe outgoing queue restore and flush
- Corrupt persisted destinations dropped on restore

### Updates
- RNS >=1.3.8, LXMF >=1.0.1, cbor2 >=5.4.0
- Message persistence enabled by default
- Bounded queues and RRC resource caps

### Tests
- RRC/CBOR unit and integration tests
- Opt-in live rrcd smoke test (LXMFY_LIVE_RRC=1)

## [1.6.5] - 2026-07-04

### Features
- Optional Landlock filesystem sandbox on Linux
- External cog sandbox prefers Landlock, then bwrap, then firejail
- Static type checking with pyright

### Fixes
- Removed invalid enforce_stamps from enable_propagation()
- Cog permission checks delegate to bot.permissions

### Updates
- LXMF 1.0.1+, RNS 1.3.5+
- Docs and README updated for sandboxing

## [1.6.4] - 2026-05-30

### Updates
- LXMF 1.0.0, RNS 1.3.4

## [1.6.3] - 2026-05-08

### Features
- Structured LXMF field commands and results (FIELD_COMMANDS / FIELD_RESULTS)
- Field commands use the same registry, permissions, and middleware as text commands
- lxmf_commands_enabled config option (default on)

## [1.6.2] - 2026-04-15

### Features
- reticulum_config_dir / LXMFY_RETICULUM_CONFIG_DIR for shared Reticulum config
- Announce display name refreshed from bot name or config files
- announce_now() for library callers

### Updates
- RNS 1.1.5

## [1.6.1] - 2026-03-11

### Updates
- License switched from MIT to BSD-0-Clause

## [1.6.0] - 2026-02-27

### Updates
- RNS 1.1.3
- Cryptography 46.0.5

## [1.5.0] - 2026-01-15

### Features
- In-memory storage backend
- Reliability suite: chaos, temporal drift, leak detection, manifold NLP tests
- Optional outgoing message persistence across restarts
- Optional identity pinning against hash collisions
- Runtime cog remove/reload
- Cross-language script cogs with optional sandboxing
- Local offline Tiny-NLP intent classification
- RNS link support
- Type-hinted command argument parsing
- Hypothesis property-based tests

### Fixes
- Identity persistence works in test mode

## [1.4.0] - 2026-01-05

### Features
- require_stamps inbound stamp enforcement toggle
- Optional identity fetch for unknown senders
- Performance and memory stress tests

### Fixes
- Cleanup stops hanging Reticulum background threads between tests
- More stable propagation and signature path-request tests

## [1.3.0] - 2026-01-04

### Features
- Version shown in lxmfy help

### Updates
- Twine-based publish flow and README install notes
- SHA256 checksums for release assets
- RNS 1.1.0

## [1.2.1] - 2025-11-30

### Fixes
- Actions pinning settings on the project repo

## [1.2.0] - 2025-11-30

### Features
- Dedicated colors module for CLI

### Fixes
- Interactive CLI color support on Windows 10/11

### Updates
- RNS 1.0.4, ruff 0.14.7
- Moved from safety to bearer for security scanning
- Actions pinned to full-length commit SHAs

## [1.1.0] - 2025-11-21

### Features
- Direct delivery with retries and propagation fallback
- Configurable stamp cost for bots

### Updates
- Poetry-only tooling and codebase cleanup
- LXMF 0.9.3, RNS 1.0.3

## [1.0.3] - 2025-11-03

### Updates
- LXMF 0.9.1

## [1.0.2] - 2025-11-03

### Updates
- LXMF 0.9.0, RNS 1.0.1
- Docker files moved under docker/

## [1.0.1] - 2025-09-28

### Fixes
- Signature canonicalization format and matching tests

## [1.0.0] - 2025-09-27

### Features
- Stable 1.0 release
- Broad pytest coverage and Actions CI
- Type hint and code quality cleanup

## [0.8.0] - 2025-09-27

### Features
- Cryptographic message signing and verification
- Optional require_message_signatures
- CLI helpers for signature testing and toggling

## [0.7.8] - 2025-09-13

### Updates
- Dependency refresh and Makefile added

## [0.7.7] - 2025-07-14

### Updates
- Arm64 Docker support
- RNS 1.0.0, LXMF 0.8.0
- General cleanup

## [0.7.6] - 2025-07-05

### Features
- Threaded command option for long-running callbacks

### Updates
- Dependency maintenance

## [0.7.5] - 2025-06-22

### Features
- More robust cog command loading
- CogTest template for regression checks

## [0.7.4] - 2025-06-22

### Fixes
- Cog command binding preserved metadata correctly

## [0.7.3] - 2025-05-15

### Updates
- LXMF 0.7.1, RNS 0.9.6

## [0.7.2] - 2025-05-13

### Updates
- LXMF 0.7.0
- Python 3.13 required

## [0.7.1] - 2025-05-09

### Fixes
- Workflow fix

## [0.7.0] - 2025-05-09

### Features
- LXMF fields support

### Updates
- Dependencies and docs

## [0.6.9] - 2025-05-07

### Updates
- Opencontainers metadata
- Removed bot scan/verification paths
- Performance and cog loading hardening

## [0.6.8] - 2025-04-29

### Features
- CLI colors and interactive mode
- Dockerfile.Build added

## [0.6.7] - 2025-04-29

### Fixes
- Workflow fix

## [0.6.6] - 2025-04-29

### Updates
- Basic tests, docs, cleanup
- ARMv7 and ARM64 builds
- Removed Bandit, meme bot, and requests

## [0.6.5] - 2025-04-07

### Fixes
- Attachment system
- Storage error handling

## [0.6.4] - 2025-04-06

### Updates
- Security and performance refactoring

## [0.6.3] - 2025-04-06

### Fixes
- Syntax errors
- Manual publish workflow

## [0.6.0] - 2025-04-06

### Features
- Run bot templates directly (lxmfy run echo)
- LXMF attachment support
- Basic tests and docker-compose

### Updates
- LXMF 0.6.3, RNS 0.9.3

## [0.5.1] - 2025-02-14

### Fixes
- Unused variables and version bump

## [0.5.0] - 2025-02-14

### Fixes
- Config, CLI, core, and announce system

## [0.4.9] - 2025-02-14

### Features
- Disable announces on start and configure announce interval

### Fixes
- Duplicate responses
- LXMF 0.6.2

## [0.4.8] - 2025-01-25

### Fixes
- Storage serialization
- SQLite storage backend

## [0.4.7] - 2025-01-25

### Fixes
- Storage serialization
- Event attribute handling

## [0.4.6] - 2025-01-25

### Features
- Middleware system
- Task scheduler

### Updates
- LXMF 0.6.1

## [0.4.5] - 2025-01-20

### Features
- Event system with priorities and middleware

### Updates
- RNS and LXMF bumps

## [0.4.4] - 2025-01-17

### Features
- Bot analysis CLI (lxmfy analyze)

### Updates
- RNS 0.9.0

## [0.4.3] - 2025-01-04

### Features
- First-message handler
- SQLite storage backend
- EchoBot, ReminderBot, NoteBot templates (FullBot removed)

## [0.4.2] - 2025-01-01

### Features
- Role-based permission system with persistent roles and command checks

## [0.4.1] - 2024-12-31

### Features
- Auto-generated help command

## [0.4.0] - 2024-12-29

### Features
- CLI templates (basic and full)
- Wheel verification via lxmfy verify
- Stronger rate limiting and spam protection for banned senders

## [0.3.3] - 2024-12-28

### Features
- Simplified lxmfy create CLI
- Transport layer path discovery and link caching
- JSON storage system
- Initial docs and website polish

### Fixes
- Mobile navigation and docs link accessibility
