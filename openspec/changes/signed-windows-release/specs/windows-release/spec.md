## ADDED Requirements

### Requirement: Pinned upstream build
The build SHALL compile ikigai-cli at exactly the version named in `upstream.toml`, from its
published crate with its own lockfile (`--locked`), with `--features quic`, for
`x86_64-pc-windows-msvc`.

#### Scenario: The binary reports the pinned version
- **WHEN** `upstream.toml` names version `0.5.2` and the Windows build job runs
- **THEN** the built `ikigai.exe --version` prints `ikigai 0.5.2`

#### Scenario: The QUIC client is compiled in
- **WHEN** the built `ikigai.exe` is asked to connect to a `quic://` door
- **THEN** it does not refuse for want of the `quic` feature

### Requirement: No runtime DLLs
The executable SHALL link the C runtime statically, and the build SHALL fail if it depends on
any DLL outside the Windows system set.

#### Scenario: A static build passes
- **WHEN** `dumpbin /dependents ikigai.exe` lists only system DLLs
- **THEN** the dependency check passes

#### Scenario: A C runtime dependency fails the build
- **WHEN** the dependents include `vcruntime140.dll`, `msvcp140.dll`, `ucrtbase.dll` or any `api-ms-win-crt-*` DLL
- **THEN** the dependency check fails and names each such DLL

### Requirement: Release contents
Each release SHALL be one zip named `ikigai-<version>-x86_64-pc-windows-msvc.zip` holding
exactly `ikigai.exe`, ikigai-cli's `LICENSE-MIT`, `LICENSE-APACHE` and `NOTICE`, and a
`README.txt`, plus a `SHA256SUMS` file listing the zip.

#### Scenario: The zip holds exactly the five files
- **WHEN** the packaging step runs for version `0.5.2`
- **THEN** `ikigai-0.5.2-x86_64-pc-windows-msvc.zip` holds exactly `ikigai.exe`, `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE` and `README.txt`

#### Scenario: The checksum matches the zip
- **WHEN** a user computes `Get-FileHash -Algorithm SHA256` over the downloaded zip
- **THEN** it equals the zip's line in `SHA256SUMS`, in lowercase hex

#### Scenario: An extra file fails packaging
- **WHEN** the staging directory holds any file beyond the five
- **THEN** packaging fails and names the extra file

### Requirement: Packaged binary runs
The binary taken out of the zip SHALL be smoke-tested on a Windows runner before anything is
released.

#### Scenario: Version and a local command with no HOME
- **WHEN** PowerShell runs the unzipped `ikigai.exe --version` and `ikigai.exe --quiet -c 'source urn:host:identity'` with `HOME` unset
- **THEN** both exit 0 and the second answers `identity root (full authority)`

#### Scenario: A client reaches a QUIC door on loopback
- **WHEN** the unzipped binary serves `quic://127.0.0.1:0` with throwaway certificates and a second run of it connects through `--override urn:host:=quic://127.0.0.1:<port> --cert-dir <certs>`
- **THEN** the client's `source urn:host:identity` answers with a principal minted by the door

### Requirement: Every executable signed and timestamped
Nothing SHALL be published unless every PE file (`.exe`, `.dll`) in the zip has an Authenticode
signature with status `Valid`, a timestamp countersignature, and a signer whose subject CN equals
the expected publisher name.

#### Scenario: An unsigned executable is refused
- **WHEN** the gate checks a zip whose `ikigai.exe` is unsigned
- **THEN** it fails and names `ikigai.exe` and the status it found

#### Scenario: A signature without a timestamp is refused
- **WHEN** the gate checks an executable signed without a timestamp
- **THEN** it fails and says the timestamp is missing

#### Scenario: The wrong publisher is refused
- **WHEN** the gate checks an executable validly signed by a subject other than the expected publisher name
- **THEN** it fails and names both subjects

#### Scenario: A correctly signed zip passes
- **WHEN** every PE file is validly signed, timestamped, by the expected publisher
- **THEN** the gate passes and lists each file it checked

### Requirement: Signed through Artifact Signing
The release job SHALL sign `ikigai.exe` through Azure Artifact Signing as Michael's company,
authenticated by OIDC federation to the GitHub environment `release`, with no signing secret
stored in the repository.

#### Scenario: A tag build is signed
- **WHEN** the release job runs for a tag in the `release` environment
- **THEN** `ikigai.exe` is signed and timestamped before packaging, and the gate passes with the publisher from the `PUBLISHER_NAME` variable

#### Scenario: A pull request cannot sign
- **WHEN** CI runs for a pull request
- **THEN** no job enters the `release` environment, the build is packaged unsigned, and only the gate's self-tests run

### Requirement: Release on tag
Pushing a tag `v<version>` SHALL publish a GitHub release holding the zip and `SHA256SUMS`, only
when `<version>` equals the version in `upstream.toml` and every earlier check passed.

#### Scenario: A matching tag publishes
- **WHEN** `v0.5.2` is pushed and `upstream.toml` names `0.5.2`
- **THEN** a release `v0.5.2` is published with the zip and `SHA256SUMS`, and its notes name the upstream crate version and the upstream repository commit it was built from

#### Scenario: A mismatched tag publishes nothing
- **WHEN** `v0.5.3` is pushed and `upstream.toml` names `0.5.2`
- **THEN** the release job fails before building, naming both versions, and no release is created

### Requirement: Install instructions
The README SHALL tell Windows users to install the signed release, show how to check its
checksum, and say that building from source on Windows is a contributor's path.

#### Scenario: A user installs from the README alone
- **WHEN** a Windows user follows the README's install section in PowerShell
- **THEN** the steps download the zip, compare its SHA-256 with `SHA256SUMS`, unzip it, put `ikigai.exe` on the user's PATH, and run `ikigai --version`

### Requirement: Runs under Smart App Control
The signed release SHALL run on Windows 11 with Smart App Control in enforce mode.

#### Scenario: Smart App Control lets it run
- **WHEN** a person unzips the first signed release on a Windows 11 machine with Smart App Control on and runs `ikigai --version`
- **THEN** it prints the version, and Smart App Control shows no block

### Requirement: Winget manifest
Each release SHALL have a generated winget manifest (portable install from the zip) whose
installer URL and SHA-256 are the release's own.

#### Scenario: The manifest validates
- **WHEN** the manifest generator runs for release `v0.5.2`
- **THEN** the manifest passes winget's schema validation

#### Scenario: The manifest's hash is the release's
- **WHEN** the manifest is generated for a release
- **THEN** its `InstallerSha256` equals the zip's entry in that release's `SHA256SUMS`, and its `InstallerUrl` is the zip's download URL
