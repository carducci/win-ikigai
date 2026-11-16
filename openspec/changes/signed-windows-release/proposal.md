## Why

Arlo is joining ikigai natively on Windows 11 (`carducci#1715`), and Smart App Control on his
machine refuses unsigned executables: `cargo install ikigai-cli` fails at the first build script
(serde, os error 4551), and ikigai-cli has no releases. ikigai-cli belongs to ikigai-rs, where we
can't publish, so this repository builds a pinned upstream version, signs it as Michael's company
through Azure Artifact Signing, and releases it. Windows users get a signed binary; building from
source on Windows becomes a contributor's path. Decided with Michael in pax-explore, 2026-11-15.

## What Changes

- A pinned upstream version (`upstream.toml`) is built for `x86_64-pc-windows-msvc` with
  `--features quic`, the C runtime linked statically, so the release carries no DLL.
- Each release is one zip (`ikigai.exe`, ikigai-cli's licence files and `NOTICE`, a README) and
  a `SHA256SUMS` file, published as a GitHub release when a tag matching the pinned version is
  pushed.
- The packaged binary is smoke-tested on Windows before release: `--version`, a local `-c`
  with no `HOME`, and a client reaching a QUIC door on loopback.
- `ikigai.exe` is signed through Artifact Signing by the release job, authenticated by OIDC
  to a protected `release` environment, with no signing secret in the repository.
- A gate refuses to publish unless every executable in the zip has a valid, timestamped
  Authenticode signature from the expected publisher.
- A winget manifest is generated for each release, and the first signed release is submitted
  to `microsoft/winget-pkgs`.
- The README tells Windows users to install the signed binary and how to check its checksum.

## Resource map

Not needed: a build and release pipeline for an existing binary. It names no new resources and
holds no state; ikigai's own resources are unchanged.

## Impact

- Artifacts: `release`, `winget`
- Also `.github/workflows/`, `upstream.toml` and `README.md` at the root.
- Michael: the Artifact Signing account and identity validation in his company's Azure tenant,
  the federated credential, the `release` environment, and pushing the release tag.
- Arlo: installs the first release on a machine with Smart App Control in enforce mode.
- Brian's side: Michael tells Brian the binary of his code goes out under the company's
  signature. Nothing changes in ikigai-rs.

## Variances

None.

## Out of scope

- A Windows local transport for ikigai (`carducci#1719`) and Arlo's face (`carducci#1718`).
- ikigai-cli's own Windows defects (its `docs/windows.md` W2 to W6) and its docs: Brian's side.
- Following new upstream versions automatically: a bump is a one-line change to `upstream.toml`
  and a new tag.
- Re-releasing the same upstream version with a packaging fix, ARM64 builds, and the `web`
  feature.
- An installer (MSI or MSIX): the release is a portable zip.
