#!/usr/bin/env python3
"""Fetch only upstream HEV 2.18.0 Android AAR, verify immutable digest and contents."""
from __future__ import annotations
import hashlib
import io
import os
import pathlib
import tempfile
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
AAR = ROOT / "libs" / "hev-socks5-tunnel-2.18.0.aar"
UPSTREAM = (
    "https://github.com/heiher/hev-socks5-tunnel/releases/download/"
    "2.18.0/hev-socks5-tunnel.aar"
)
EXPECTED_SIZE = 590342
EXPECTED_SHA256 = "15ec8ed121663b562c99caa5bb602d1009f24e5b09e733438b81988f12feaaab"
ABIS = ("arm64-v8a", "armeabi-v7a", "x86", "x86_64")
REQUIRED = {"classes.jar"} | {
    "jni/" + abi + "/libhev-socks5-tunnel.so" for abi in ABIS
}

def check(data: bytes) -> None:
    if len(data) != EXPECTED_SIZE:
        raise ValueError("HEV_AAR_SIZE_NOT_PINNED")
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("HEV_AAR_SHA256_NOT_PINNED")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or not REQUIRED.issubset(set(z.namelist())):
            raise ValueError("HEV_AAR_MISSING_JNI_OR_CLASSES")
        with zipfile.ZipFile(io.BytesIO(z.read("classes.jar"))) as jar:
            if "hev/htproxy/TProxyService.class" not in jar.namelist():
                raise ValueError("HEV_AAR_JNI_BINDING_MISSING")

def main() -> None:
    if AAR.is_file():
        check(AAR.read_bytes())
        print("PINNED_HEV_AAR_ALREADY_VERIFIED", EXPECTED_SHA256)
        return
    if AAR.exists():
        raise SystemExit("HEV_AAR_PATH_NOT_REGULAR")
    AAR.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(UPSTREAM, headers={
        "User-Agent": "FreeNetHub-Private-ReproducibleAndroidBuild/1.0"
    })
    with urllib.request.urlopen(req, timeout=40) as stream:
        if not stream.geturl().startswith("https://"):
            raise ValueError("HEV_AAR_NOT_HTTPS")
        data = stream.read(EXPECTED_SIZE + 1)
    check(data)
    fd, part = tempfile.mkstemp(prefix=".fnh-hev-aar-", dir=AAR.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(part, 0o644)
        if AAR.exists():
            raise ValueError("HEV_AAR_CONCURRENT_WRITER")
        os.replace(part, AAR)
    finally:
        if os.path.exists(part):
            os.unlink(part)
    check(AAR.read_bytes())
    print("PINNED_HEV_AAR_DOWNLOAD_VERIFIED", EXPECTED_SHA256)

if __name__ == "__main__":
    main()
