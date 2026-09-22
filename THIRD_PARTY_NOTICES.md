# Third-Party Notices

FreeNet Hub uses or can provision third-party software. Third-party components remain subject to their own license terms.

## sing-box

- Upstream project: SagerNet/sing-box
- Pinned runtime version used by the Console Gateway setup: 1.14.0
- Upstream license: GNU General Public License, version 3 or (at your option) any later version (GPL-3.0-or-later)
- Integration model: `gateway/Setup-GatewayCore.ps1` downloads the pinned upstream Windows release at setup time, verifies the archive and binary SHA-256 values, and installs the validated binary into the local FreeNet Hub runtime directory.
- Distribution boundary: the current FreeNet Hub installer source manifest does not embed the sing-box binary; it provisions the binary from the upstream release when needed.

Refer to the upstream SagerNet/sing-box repository and its LICENSE file for the complete license text and current upstream terms.

## FreeNet Hub project license

This notice does not grant a license to FreeNet Hub's own source code. The repository currently does not declare a project-wide software license.
