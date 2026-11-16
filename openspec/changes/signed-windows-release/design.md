## Context

Smart App Control (SAC) in enforce mode refuses unsigned executables. On Arlo's Windows 11
machine that stops `cargo install ikigai-cli` at its first build script, and ikigai-cli has no
releases (`carducci#1715`; Arlo's log, 2026-11-15). ikigai-cli is Apache-2.0 or MIT, in the
ikigai-rs organisation, where Michael has triage rights only. Its non-gating `windows-probe` CI
job already builds `ikigai-cli` on `windows-latest` (about 18 minutes cold) and smoke-tests the
binary; `docs/windows.md` there maps what does and doesn't work natively. What's missing is
signing, packaging and a release. Decided with Michael in pax-explore on 2026-11-15.

## Decisions

### D1. Release from Michael's own repository, signed as his company
A repository of Michael's (`carducci/win-ikigai`, no `ikigai-` prefix, by Brian's naming rule)
builds a pinned upstream version and signs it. Michael tells Brian before the first release.
- Alternative rejected: a signed-release job in ikigai-cli. It's the right long-term home, but
  it needs Brian's side to obtain a signing identity, and their timeline. The workflow here can
  be offered upstream as a PR later.

### D2. Azure Artifact Signing, organisation identity, in the company's tenant
Michael's company (a US corporation since 2010, an Azure customer for a decade) validates as a
public-trust organisation, and the signing account lives in that company's tenant, so the
certificate names the entity that validated. Its certificates chain to Microsoft's root.
- Alternative rejected: an OV certificate in a CA's cloud key store. It costs a few hundred
  dollars a year and is the fallback if validation fails.
- Alternative rejected: self-signed. SAC refuses it.
- Trade-off: Artifact Signing certificates live about three days, so every signature must be
  timestamped, and the gate checks that (D6).
- The publisher users see is the validated legal name. Before submitting, Michael checks that
  his D&B profile and Secretary of State record carry the same legal name and address, and that
  the company is in good standing. A failed validation is hard to retry.

### D3. Pin a published crate version
`upstream.toml` names one ikigai-cli version from crates.io, and the build uses
`cargo install ikigai-cli --version <v> --locked --features quic`. A published crate is
immutable, carries its own lockfile, and is the version `ikigai --version` reports.
- Alternative rejected: building a git commit of ikigai-cli. It's harder to name, and its
  version string doesn't say which commit it was. If a published version doesn't build on
  Windows, the task that finds out records it and proposes a `rev` field instead.

### D4. `--features quic` only
That's what Arlo needs: the client path to a layer door, and `ikigai mcp`.
- Alternative rejected: `quic,web`, which is what upstream's probe builds. `web` adds an
  inbound HTTP face that nobody on Windows has asked for. Adding it later is a one-line change.

### D5. Static C runtime, no DLLs in the zip
`RUSTFLAGS=-C target-feature=+crt-static`, checked with `dumpbin /dependents` (the `cc` crate
follows the flag for RocksDB's C++).
- Alternative rejected: shipping `vcruntime140.dll` or relying on the VC++ redistributable. A
  DLL in the zip is one more file SAC checks and we sign. A missing redistributable fails
  silently on a clean machine.
- If RocksDB's C++ doesn't link statically, the task stops and hands back. It doesn't ship a DLL.

### D6. A signature gate on every PE file
A PowerShell script, `artifacts/release/Test-ReleaseSignatures.ps1`, opens the zip and refuses
unless every `.exe` and `.dll` has a valid Authenticode signature, a timestamp, and a signer
whose subject CN equals `PUBLISHER_NAME`. It runs in the release job before publishing. Pester
tests prove it refuses an unsigned file, an untimestamped one and a wrong publisher. They
sign fixtures with a throwaway self-signed certificate trusted only inside the test, and they
run on every pull request.

### D7. Sign in CI through OIDC, in a protected environment
The release job runs in the GitHub environment `release`, which only `v*` tags can enter. It
logs in to Azure through a federated credential whose subject is
`repo:carducci/win-ikigai:environment:release`, and signs with Microsoft's Artifact Signing
GitHub action. No secret is stored. Repository variables hold the endpoint, account,
certificate profile, client, tenant and subscription IDs, and `PUBLISHER_NAME`.
- Alternative rejected: a client secret in repository secrets. It's long-lived and would be
  readable by any workflow edit.
- Pull request CI builds, packages and smoke-tests unsigned. It never reaches the environment.

### D8. The tag is the upstream version
`v<version>` must equal `upstream.toml`'s version, or the release job stops before building.
Re-releasing one upstream version with a packaging fix is out of scope until it's needed.

### D9. A public repository, winget after the first release
winget needs a public download URL, and Arlo then needs no access grant. The winget manifest
(a portable install, nested in the zip) is generated from the release. The first submission
to `microsoft/winget-pkgs` is Michael's, since it goes out under his name. Its review takes days
and gates nothing else.

## Constraints

- Private keys never leave Azure: signing happens in Artifact Signing's HSM. The runner holds
  only a short-lived OIDC token.
- Agents never push a release tag or submit to winget-pkgs. Both are outward-facing, so they
  are human tasks.
- Workers can't sign. Their pull requests never enter `release`.

## Sensors (fitness functions for CI)

| requirement | sensor | proof it fires |
| --- | --- | --- |
| Every executable signed and timestamped | `Test-ReleaseSignatures.ps1` in the release job | Pester: unsigned, untimestamped and wrong-publisher fixtures each fail it (every PR) |
| No runtime DLLs | the dependency check after the build | its test feeds it a `dumpbin` listing that holds `vcruntime140.dll` and expects a failure |
| Release contents | the packaging step's exact-file check | its test stages an extra file and expects a failure |
| Release on tag | the tag check, first step of the release job | its test passes a mismatched tag and version and expects a failure |
| Signed through Artifact Signing | environment protection on `release` (`v*` tags only) | 3.1 records the rule; a PR run's log shows no job in `release` |

## Open

- **Michael's identity validation** (Michael, in the Azure portal). Only 3.2 waits on it.
- **Whether SAC accepts the signature** (Arlo, task 3.4). If it refuses, the fallback is an OV
  certificate (D2).
- **Whether the static CRT links with RocksDB's C++** (task 1.2 finds out, and hands back if not).
- **Whether `winget` runs on the GitHub runner.** If not, 2.1 validates against winget's
  published JSON schemas instead.
- **Whether `microsoft/winget-pkgs` review accepts the package** (Michael, task 4.1).
- **Seed runs in file order.** 2.1 waits on 1.7, which it needn't. That's accepted for this
  change, since both are short.
