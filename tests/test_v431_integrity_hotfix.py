from pathlib import Path
import json, hashlib

ROOT=Path(__file__).resolve().parents[1]

def test_app_manifest_matches_actual_runtime_bytes():
    m=json.loads((ROOT/"app/manifest.json").read_text(encoding="utf-8-sig"))
    assert m["version"]=="4.3.6"
    release=json.loads((ROOT/"RELEASE.json").read_text(encoding="utf-8-sig"))
    assert m["coreVersion"]==release["releaseRevision"]
    for e in m["code"]:
        p=ROOT/"app"/e["file"]
        assert p.is_file(), e["file"]
        b=p.read_bytes()
        assert e["bytes"]==len(b), e["file"]
        assert e["sha256"]==hashlib.sha256(b).hexdigest().upper(), e["file"]
        assert e["sourceSha256"]==e["sha256"], e["file"]

def test_known_v43_stale_entries_match_raw_build_source_bytes():
    m=json.loads((ROOT/"app/manifest.json").read_text(encoding="utf-8-sig"))
    entries={e["file"]:e for e in m["code"]}
    for rel in ("View.xaml","directdpi/hosts.txt"):
        raw=(ROOT/"app"/rel).read_bytes()
        assert entries[rel]["sha256"]==hashlib.sha256(raw).hexdigest().upper()
        assert entries[rel]["bytes"]==len(raw)
    assert entries["View.xaml"]["sha256"]!="E2CDE4A12279AB12B37AB76772D569AA117207A17357C3ECD043CCBB7BF41708"
    assert b"\r\n" not in (ROOT/"app/directdpi/hosts.txt").read_bytes()

def test_ci_fresh_install_launches_ui_and_rejects_ui_error():
    w=(ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "build_v436_installer.ps1" in w
    assert "V436_UI_CHILD_PWSH_MISSING" in w
    assert "V436_UI_ERROR_" in w
    assert "FreeNetHub_4.3.6_R50_Setup.exe" in w

def test_build_fails_closed_on_raw_source_manifest_drift():
    script=(ROOT/"tests/build_v436_installer.ps1").read_text(encoding="utf-8-sig")
    assert "V436_BUILD_SOURCE_MANIFEST_MISMATCH_" in script
    assert "PASS_RAW_BYTES_MATCH_APP_MANIFEST" in script
    assert "Get-FileHash -LiteralPath $src" in script

def test_node_grid_remains_visible_at_minimum_window_height():
    x=(ROOT/"app/View.xaml").read_text(encoding="utf-8")
    node=x.split('Name="NodeList"',1)[1]
    assert 'MinHeight="190"' in node[:900]
    assert 'RowHeight="32"' in node[:1200]
    assert 'ColumnHeaderHeight="34"' in node[:1200]
    assert 'ElementStyle="{StaticResource NodeGridText}"' in node
    assert 'Header="مشخصات پیشرفته نود"' in x
    assert 'IsExpanded="False"' in x
