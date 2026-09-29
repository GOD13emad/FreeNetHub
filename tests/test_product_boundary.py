from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOTS = [
    ROOT / "app",
    ROOT / "windows" / "installer",
    ROOT / "crossplatform",
    ROOT / "android",
    ROOT / "ios",
]
TEXT_SUFFIXES = {".py", ".ps1", ".xaml", ".json", ".sh", ".iss", ".md", ".txt", ".xml", ".kt", ".swift"}
# OpenVPN may be named defensively when detecting/excluding a foreign VPN adapter.
# What is forbidden is absorbing OIG's actual VPN Gate/OpenVPN backend.
FORBIDDEN_BACKEND_MARKERS = (
    "vpn gate",
    "vpngate",
    "ovpnconnector",
    "openvpn connect",
    "udp-cache",
    ".ovpn",
)


def test_freenethub_does_not_absorb_oig_vpngate_openvpn_backend():
    violations = []
    for base in PRODUCTION_ROOTS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            rel = path.relative_to(ROOT).as_posix()
            # Third-party notice/license material is not product implementation.
            if "/docs/" in f"/{rel.lower()}/" or "third_party" in rel.lower():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            hits = [term for term in FORBIDDEN_BACKEND_MARKERS if term in text]
            if hits:
                violations.append((rel, hits))
    assert not violations, (
        "FreeNetHub must not absorb the OIG VPN Gate/OpenVPN backend: "
        + repr(violations)
    )
