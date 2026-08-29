import sys
import os
import yaml
import pytest
from unittest.mock import patch
from cli.main import main, handle_check
from risk_engine import RiskLevel

def test_workflow_file_validity():
    wf_path = os.path.join(".github", "workflows", "ripple-check.yml")
    assert os.path.exists(wf_path)
    with open(wf_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["name"] == "Ripple Change Impact & Risk Analysis"
    assert "pull_request" in data["on"]

def test_cli_invalid_path_returns_exit_code_2():
    with patch("sys.argv", ["cli.main", "scan", "non_existent_folder_123"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

def test_cli_scan_command(capsys):
    with patch("sys.argv", ["cli.main", "scan", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Repository Scan" in captured.out
    assert "Files" in captured.out

def test_cli_impact_command(capsys):
    with patch("sys.argv", ["cli.main", "impact", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Impact Analysis" in captured.out
    assert "Risk:" in captured.out

def test_cli_runtime_command(capsys):
    with patch("sys.argv", ["cli.main", "runtime", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Runtime Analysis" in captured.out

def test_cli_drift_command(capsys):
    with patch("sys.argv", ["cli.main", "drift", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Architecture Drift" in captured.out

def test_cli_check_low_risk_passes_exit_0(capsys):
    with patch("sys.argv", ["cli.main", "check", "demo_services", "--fail-on", "high"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Ripple CI Check" in captured.out
    assert "PASSED" in captured.out

def test_cli_check_threshold_triggers_failure_exit_1(capsys):
    # Setting threshold to low forces check to fail
    with patch("sys.argv", ["cli.main", "check", "demo_services", "--fail-on", "low"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "FAILED" in captured.out
