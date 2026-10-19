"""Guard the PCR02 read-only runbook against stale historic TID reuse."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = (
    ROOT
    / "projects/xcrz-sigmastar-demo/current/runbooks/"
    "prog-pcr02-high-load-debug.md"
)


def test_runtime_followup_uses_live_process_tasks_instead_of_fixed_old_tids():
    doc = RUNBOOK.read_text(encoding="utf-8")
    section = doc.split("## Targeted Follow-Up", 1)[1].split(
        "## Source-Mapped Hot Thread Capture", 1
    )[0]
    assert "for tid in 807 785 735 820 781" not in section
    assert 'for task in /proc/"$pid"/task/[0-9]*' in section
    assert 'pid=$(pidof prog_pcr02) || exit 1' in section
    assert 'before=$(cat "$task/comm"' in section
    assert 'after=$(cat "$task/comm"' in section
    assert '[ "$before" = "$after" ] || continue' in section
    assert "AMBIGUOUS_PID" in section
    assert "NO_CURRENT_TARGET_THREADS" in section
    assert "历史 TID 不能作为新设备的可执行目标" in section
    assert "实际热点仍以" in section
