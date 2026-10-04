from pathlib import Path

R=Path(__file__).resolve().parents[1]
PS=(R/'app'/'FreeNetHub.ps1').read_text(encoding='utf-8-sig')
ENG=(R/'app'/'engine.py').read_text(encoding='utf-8-sig')

def test_ui_marks_test_running_and_timeout_in_dashboard():
    assert "function Paint-TestState" in PS
    assert "Paint-TestState 'DIRECT' 'RUNNING'" in PS
    assert "Paint-TestState $mode 'RUNNING'" in PS
    assert "'TIMEOUT'" in PS and "'N/A'" in PS
    assert "if($failMode){Paint-TestState" in PS

def test_engine_result_records_mode_for_failure_attribution():
    assert "'action':ns.action,'mode':ns.mode,'exit':code" in ENG

def test_direct_route_avoids_slow_nettcpip_aggregate_probe():
    block=ENG.split('def direct_route():',1)[1].split('def ping_direct(',1)[0]
    assert "route.exe','print','-4" in block
    assert "_windows_ipv4_ifindex" in block
    assert "_windows_if_row2" in block
    assert "Get-NetAdapter" not in block
    assert "Get-NetRoute" not in block
    assert "Get-CimInstance" not in block
    assert "ROUTE_EXE+WINDOWS_IPHELPER" in block

def test_direct_speed_exposes_stage_progress():
    block=ENG.split('def direct_speed():',1)[1].split('def direct_adapter_snapshot',1)[0]
    for stage in ('verifying physical default route','verifying HTTPS exit','measuring Ping','measuring Download','measuring Upload'):
        assert stage in block
