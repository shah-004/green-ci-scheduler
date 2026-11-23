import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.app import app
except (ImportError, ModuleNotFoundError):
    from app import app  # noqa: E402

from scheduler.decide import evaluate_mode, evaluate_mode_details  # noqa: E402
from scheduler.config_loader import parse_simple_yaml  # noqa: E402


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def test_evaluate_mode_standard():
    thresholds = {"green": 100, "amber": 250, "red": 250}
    assert evaluate_mode(50, thresholds) == "green"
    assert evaluate_mode(99.9, thresholds) == "green"
    assert evaluate_mode(100, thresholds) == "amber"
    assert evaluate_mode(180, thresholds) == "amber"
    assert evaluate_mode(249.9, thresholds) == "amber"
    assert evaluate_mode(250, thresholds) == "red"
    assert evaluate_mode(350, thresholds) == "red"


def test_evaluate_mode_details():
    green_info = evaluate_mode_details(80, {"green": 100, "amber": 250})
    assert green_info["mode"] == "green"
    assert green_info["execution_allowed"] is True

    amber_info = evaluate_mode_details(150, {"green": 100, "amber": 250})
    assert amber_info["mode"] == "amber"
    assert amber_info["execution_allowed"] is True

    red_info = evaluate_mode_details(320, {"green": 100, "amber": 250})
    assert red_info["mode"] == "red"
    assert red_info["execution_allowed"] is False


def test_simple_yaml_parser():
    sample_yaml = """
thresholds:
  green: 90
  amber: 220
max_wait_seconds: 180
assumed_power_kw: 0.08
provider: neso_uk
"""
    parsed = parse_simple_yaml(sample_yaml)
    assert parsed["thresholds"]["green"] == 90
    assert parsed["thresholds"]["amber"] == 220
    assert parsed["max_wait_seconds"] == 180
    assert parsed["assumed_power_kw"] == 0.08
    assert parsed["provider"] == "neso_uk"


def test_index_route(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"Carbon-Aware" in res.data
    assert b"GreenOps" in res.data


def test_api_status(client):
    res = client.get('/api/v1/status')
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "carbon_intensity_gco2_kwh" in data
    assert data["pipeline_mode"] in ["green", "amber", "red"]
    assert "thresholds" in data


def test_api_jobs_list_and_filter(client):
    res = client.get('/api/v1/jobs')
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["jobs"]) > 0

    # Test filtering by mode
    res_green = client.get('/api/v1/jobs?mode=green')
    assert res_green.status_code == 200
    green_jobs = res_green.get_json()["jobs"]
    assert all(j["mode"] == "green" for j in green_jobs)


def test_api_dispatch_green_vs_red(client):
    # 1. Dispatch with green intensity -> Should execute
    res_green = client.post('/api/v1/jobs/dispatch', json={
        "job_name": "Test PyTest Runner",
        "branch": "feature/green-test",
        "simulate_intensity": 65.0
    })
    assert res_green.status_code == 200
    data_green = res_green.get_json()
    assert data_green["executed"] is True
    assert data_green["job"]["mode"] == "green"
    assert "Executed" in data_green["job"]["status"]
    assert len(data_green["console_output"]) > 0

    # 2. Dispatch with red intensity -> Should defer
    res_red = client.post('/api/v1/jobs/dispatch', json={
        "job_name": "Test Heavy Docker Build",
        "branch": "feature/red-test",
        "simulate_intensity": 320.0,
        "force": False
    })
    assert res_red.status_code == 200
    data_red = res_red.get_json()
    assert data_red["executed"] is False
    assert data_red["job"]["mode"] == "red"
    assert "Deferred" in data_red["job"]["status"]

    # 3. Dispatch with red intensity but forced -> Should execute
    res_forced = client.post('/api/v1/jobs/dispatch', json={
        "job_name": "Test Emergency Hotfix",
        "branch": "hotfix/urgent",
        "simulate_intensity": 320.0,
        "force": True
    })
    assert res_forced.status_code == 200
    data_forced = res_forced.get_json()
    assert data_forced["executed"] is True
    assert "Executed" in data_forced["job"]["status"]


def test_api_simulation_override(client):
    # Enable simulation
    res_sim = client.post('/api/v1/simulate', json={
        "enabled": True,
        "intensity": 75.5
    })
    assert res_sim.status_code == 200
    data = res_sim.get_json()
    assert data["simulation_enabled"] is True
    assert data["current_intensity"] == 75.5
    assert data["mode"] == "green"

    # Verify status reflects simulation
    res_status = client.get('/api/v1/status')
    assert res_status.get_json()["carbon_intensity_gco2_kwh"] == 75.5

    # Disable simulation
    res_off = client.post('/api/v1/simulate', json={"enabled": False})
    assert res_off.status_code == 200
    assert res_off.get_json()["simulation_enabled"] is False


def test_api_analytics(client):
    res = client.get('/api/v1/analytics')
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "summary" in data["data"]
    assert "total_saved_kg" in data["data"]["summary"]
    assert "history_24h" in data["data"]
    assert len(data["data"]["history_24h"]["labels"]) == 24
    assert "breakdown" in data["data"]


def test_api_settings_update(client):
    res = client.post('/api/v1/settings', json={
        "thresholds": {"green": 95, "amber": 230},
        "assumed_power_kw": 0.06,
        "max_wait_seconds": 150
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["settings"]["thresholds"]["green"] == 95
    assert data["settings"]["thresholds"]["amber"] == 230
    assert data["settings"]["assumed_power_kw"] == 0.06
