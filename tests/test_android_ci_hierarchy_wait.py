from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

def test_android_runtime_uses_bounded_ui_hierarchy_wait():
    assert "dump_until_contains() {" in WORKFLOW
    assert "for attempt in $(seq 1 15); do" in WORKFLOW
    assert "UI hierarchy deadline exceeded:" in WORKFLOW
    assert '"$ADB" wait-for-device' in WORKFLOW
    assert '"$ADB" get-state' in WORKFLOW

def test_android_runtime_waits_for_each_state_transition():
    for marker in (
        "initial app fail-closed state",
        "VPN consent dialog",
        "app state after VPN consent cancel",
        "VPN consent dialog after cancel",
        "app state after VPN consent grant",
        "persisted VPN permission state",
    ):
        assert marker in WORKFLOW

def test_android_runtime_no_longer_relies_on_one_shot_ui_dump_for_lifecycle_states():
    lifecycle_files = (
        "fnh-window.xml",
        "fnh-vpn-consent.xml",
        "fnh-after-cancel.xml",
        "fnh-vpn-consent2.xml",
        "fnh-after-ok.xml",
        "fnh-after-grant.xml",
    )
    for name in lifecycle_files:
        assert f' shell uiautomator dump /sdcard/{name}' not in WORKFLOW
