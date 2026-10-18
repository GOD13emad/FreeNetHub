#!/usr/bin/env python3
"""Fail-closed selector for the R57 *R53-baseline-only* disposable installer job.

A private R55 Native integration uses a distinct release line and must use its
own acceptance job; skipping R57's R53-only job is not R57 acceptance.
"""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R53_ID = ("4.3.9", "4.3.9-r53-inno-root-guard", "R53_UNSIGNED_INSTALLER_RELEASE_LINE")


def eligible_for_r57_r53_fixture(release, app):
    return bool(
        isinstance(release, dict)
        and isinstance(app, dict)
        and (release.get("version"), release.get("releaseRevision"), release.get("status")) == R53_ID
        and (app.get("version"), app.get("coreVersion")) == R53_ID[:2]
    )


def selftest():
    accepted = {"version": R53_ID[0], "releaseRevision": R53_ID[1], "status": R53_ID[2]}
    app = {"version": R53_ID[0], "coreVersion": R53_ID[1]}
    assert eligible_for_r57_r53_fixture(accepted, app)
    for wrong in (
        {"version": "4.3.11", "releaseRevision": "4.3.11-r55-native-status-review", "status": "R55_PRIVATE_CANDIDATE_NOT_FOR_RELEASE"},
        dict(accepted, status="R53_PUBLIC_OVERRIDE"),
        dict(accepted, version="4.3.11"),
        dict(accepted, releaseRevision="4.3.9-r53-other"),
        {},
        None,
    ):
        assert not eligible_for_r57_r53_fixture(wrong, app)
    assert not eligible_for_r57_r53_fixture(accepted, dict(app, coreVersion="4.3.11-r55-native-status-review"))
    assert not eligible_for_r57_r53_fixture(accepted, None)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--github-output", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    selftest()
    if args.self_test:
        print("R57_R53_ONLY_ELIGIBILITY_MATRIX_PASS")
        return
    release = json.loads((ROOT / "RELEASE.json").read_text(encoding="utf-8-sig"))
    app = json.loads((ROOT / "app/manifest.json").read_text(encoding="utf-8-sig"))
    allowed = eligible_for_r57_r53_fixture(release, app)
    row = "eligible=" + str(allowed).lower() + "\n"
    if args.github_output:
        output = os.environ.get("GITHUB_OUTPUT")
        if not output:
            raise RuntimeError("GITHUB_OUTPUT_NOT_CONFIGURED")
        with open(output, "a", encoding="utf-8") as f:
            f.write(row)
    print("R57_R53_ONLY_FIXTURE_" + ("ELIGIBLE" if allowed else "NOT_APPLICABLE"))


if __name__ == "__main__":
    main()
