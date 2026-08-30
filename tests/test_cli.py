import sys
import os
import yaml
import pytest
from unittest.mock import patch
from cli.main import main, handle_check
from risk_engine import RiskLevel

def test_cli_help(capsys):
    with patch("sys.argv", ["ripple", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Ripple — See how far your changes travel." in captured.out
    assert "scan" in captured.out
    assert "impact" in captured.out

def test_cli_version(capsys):
    with patch("sys.argv", ["ripple", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # Check for __version__ that is passed down
    from cli.main import __version__
    assert f"Ripple {__version__}" in (captured.out + captured.err)

def test_cli_executable_availability():
    # If the package is installed properly, the 'ripple' executable should be available in the path,
    # or at least the entrypoint should map correctly. We can test that the entry point functions.
    import importlib.metadata
    eps = importlib.metadata.entry_points()
    
    # Modern importlib.metadata handling
    if hasattr(eps, 'select'):
        console_scripts = eps.select(group='console_scripts')
    else:
        console_scripts = eps.get('console_scripts', [])
        
    ripple_script = next((ep for ep in console_scripts if ep.name == 'ripple'), None)
    assert ripple_script is not None, "ripple entry point not found in console_scripts"
    assert ripple_script.value == "cli.main:main", "ripple entry point does not point to cli.main:main"

def test_workflow_file_validity():
    wf_path = os.path.join(".github", "workflows", "ripple-check.yml")
    assert os.path.exists(wf_path)
    with open(wf_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["name"] == "Ripple Change Impact & Risk Analysis"
    assert "pull_request" in data["on"]

def test_cli_invalid_path_returns_exit_code_2():
    with patch("sys.argv", ["ripple", "scan", "non_existent_folder_123"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

def test_cli_scan_command(capsys):
    with patch("sys.argv", ["ripple", "scan", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Repository Scan" in captured.out
    assert "Files" in captured.out

def test_cli_impact_command(capsys):
    with patch("sys.argv", ["ripple", "impact", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Impact Analysis" in captured.out
    assert "Risk:" in captured.out

def test_cli_runtime_command(capsys):
    with patch("sys.argv", ["ripple", "runtime", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Runtime Analysis" in captured.out

def test_cli_drift_command(capsys):
    with patch("sys.argv", ["ripple", "drift", "demo_services"]):
        main()
    captured = capsys.readouterr()
    assert "Ripple Architecture Drift" in captured.out

def test_cli_check_low_risk_passes_exit_0(capsys):
    from risk_engine.models import RiskReport, RiskLevel
    low_report = RiskReport(
        total_score=10,
        risk_level=RiskLevel.LOW,
        factors=[],
        directly_changed_files=["utils.py"],
        directly_changed_nodes=["utils.py"],
        impacted_nodes=[],
        affected_services=["utils"],
        affected_endpoints=[],
        recommendations=[]
    )
    with patch("risk_engine.service.RiskEngine.evaluate_risk", return_value=low_report):
        with patch("sys.argv", ["ripple", "check", "demo_services", "--fail-on", "high"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Ripple CI Check" in captured.out
    assert "PASSED" in captured.out

def test_cli_check_threshold_triggers_failure_exit_1(capsys):
    # Setting threshold to low forces check to fail
    with patch("sys.argv", ["ripple", "check", "demo_services", "--fail-on", "low"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "FAILED" in captured.out
