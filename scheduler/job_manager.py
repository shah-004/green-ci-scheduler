import os
import sys
import json
import uuid
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scheduler.decide import get_carbon_intensity_details, evaluate_mode_details  # noqa: E402
from scheduler.config_loader import load_config  # noqa: E402
from scheduler.estimate import log_run  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.json')

INITIAL_SEED_JOBS = [
    {
        "id": "job-1092",
        "name": "Build Backend & PyTest Suite",
        "branch": "main",
        "commit": "c8f2a91",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(minutes=14)).isoformat(),
        "duration_sec": 195,
        "intensity": 78.0,
        "mode": "green",
        "status": "Executed Successfully",
        "emissions_g": 1.27,
        "baseline_g": 3.74,
        "saved_g": 2.47,
        "runner_id": "runner-uk-green-01",
        "logs": [
            "[00:00:01] Initializing Carbon-Aware CI runner worker...",
            "[00:00:02] Querying National Grid ESO Carbon Intensity API...",
            "[00:00:02] Carbon intensity measured: 78 gCO2/kWh (LOW - Wind generation: 54.2%)",
            "[00:00:03] Policy check: Mode GREEN -> DISPATCH APPROVED immediately.",
            "[00:00:04] git checkout main @ c8f2a91",
            "[00:00:15] Setting up Python 3.11 environment with cached wheels",
            "[00:00:48] Running pytest test suite: 142 passed, 0 failed in 34.2s",
            "[00:02:15] Packaging artifacts and publishing test coverage report (98.4%)",
            "[00:03:15] Job completed cleanly. Estimated emissions: 1.27 gCO2 (Saved 2.47 gCO2 vs baseline)."
        ]
    },
    {
        "id": "job-1091",
        "name": "Docker Image Multi-Arch Push",
        "branch": "release/v2.4",
        "commit": "e43b17c",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(minutes=48)).isoformat(),
        "duration_sec": 380,
        "intensity": 94.0,
        "mode": "green",
        "status": "Executed Successfully",
        "emissions_g": 2.98,
        "baseline_g": 7.28,
        "saved_g": 4.30,
        "runner_id": "runner-uk-green-03",
        "logs": [
            "[00:00:01] Carbon Gate: Grid carbon intensity is 94 gCO2/kWh (GREEN).",
            "[00:00:03] Spawning multi-platform buildx daemon [linux/amd64, linux/arm64].",
            "[00:03:40] Docker build layers cached (8/12 layers hit cache).",
            "[00:05:50] Image digest sha256:77fa908 pushed to registry.internal/greenops:v2.4",
            "[00:06:20] Job finished. Total energy: 0.0317 kWh."
        ]
    },
    {
        "id": "job-1090",
        "name": "Nightly ML Benchmark & Retrain",
        "branch": "ml-pipeline",
        "commit": "80fd902",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(hours=2, minutes=10)).isoformat(),
        "duration_sec": 0,
        "intensity": 286.0,
        "mode": "red",
        "status": "Deferred / Paused",
        "emissions_g": 0.0,
        "baseline_g": 18.50,
        "saved_g": 18.50,
        "runner_id": "queue-pool-deferred",
        "deferral_reason": "Grid intensity 286 gCO2/kWh exceeds RED threshold (250 gCO2/kWh). Held for cleaner wind window.",
        "logs": [
            "[00:00:01] Trigger received for heavy batch workflow 'Nightly ML Benchmark & Retrain'.",
            "[00:00:02] Querying live UK grid intensity: 286 gCO2/kWh (RED ALERT - Gas Peakers online).",
            "[00:00:03] Evaluation Engine: Current grid emits 286 gCO2/kWh > Max limit 250 gCO2/kWh.",
            "[00:00:04] ACTION: Job deferred and queued. Scheduled re-evaluation in 15 minutes.",
            "[00:00:05] Projected carbon avoidance: ~18.50 gCO2."
        ]
    },
    {
        "id": "job-1089",
        "name": "Database Migration Dry-Run",
        "branch": "feature/user-auth",
        "commit": "1b5592e",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(hours=3, minutes=25)).isoformat(),
        "duration_sec": 110,
        "intensity": 165.0,
        "mode": "amber",
        "status": "Executed Successfully",
        "emissions_g": 1.51,
        "baseline_g": 2.11,
        "saved_g": 0.60,
        "runner_id": "runner-uk-amber-02",
        "logs": [
            "[00:00:01] Grid intensity is 165 gCO2/kWh (AMBER - Moderate).",
            "[00:00:02] Job 'Database Migration Dry-Run' marked as essential PR verification.",
            "[00:00:03] Execution permitted with constrained runner profile.",
            "[00:01:45] Migration rollback tests verified successfully against Postgres 16 replica.",
            "[00:01:50] Execution complete."
        ]
    },
    {
        "id": "job-1088",
        "name": "Frontend Next.js Static Export",
        "branch": "main",
        "commit": "05a74e3",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(hours=5, minutes=5)).isoformat(),
        "duration_sec": 240,
        "intensity": 82.0,
        "mode": "green",
        "status": "Executed Successfully",
        "emissions_g": 1.64,
        "baseline_g": 4.60,
        "saved_g": 2.96,
        "runner_id": "runner-uk-green-02",
        "logs": [
            "[00:00:01] Carbon intensity 82 gCO2/kWh (GREEN).",
            "[00:00:05] Running next build --turbo",
            "[00:03:50] Static pages generated (124 routes).",
            "[00:04:00] Artifacts synced to CDN edge."
        ]
    },
    {
        "id": "job-1087",
        "name": "End-to-End Cypress Integration Suite",
        "branch": "staging",
        "commit": "67da340",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(hours=7, minutes=15)).isoformat(),
        "duration_sec": 0,
        "intensity": 295.0,
        "mode": "red",
        "status": "Deferred / Paused",
        "emissions_g": 0.0,
        "baseline_g": 22.40,
        "saved_g": 22.40,
        "runner_id": "queue-pool-deferred",
        "deferral_reason": "Peak evening grid fossil load (295 gCO2/kWh). Paused until night-time green window.",
        "logs": [
            "[00:00:01] Carbon Gate evaluated: 295 gCO2/kWh.",
            "[00:00:02] Status: RED - Deferring non-blocking Cypress test matrix.",
            "[00:00:03] Job queued. Deferral timer: 45 min remaining."
        ]
    },
    {
        "id": "job-1086",
        "name": "Security SAST Scanning & Trivy",
        "branch": "main",
        "commit": "72199b0",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(hours=9, minutes=40)).isoformat(),
        "duration_sec": 130,
        "intensity": 145.0,
        "mode": "amber",
        "status": "Executed Successfully",
        "emissions_g": 1.31,
        "baseline_g": 2.07,
        "saved_g": 0.76,
        "runner_id": "runner-uk-amber-01",
        "logs": [
            "[00:00:01] Evaluated AMBER (145 gCO2/kWh).",
            "[00:00:02] Security policy overrides deferral for vulnerability scans.",
            "[00:02:10] Scanning complete: 0 Critical, 0 High vulnerabilities."
        ]
    },
    {
        "id": "job-1085",
        "name": "Helm Chart Package & Sign",
        "branch": "release/v2.4",
        "commit": "90e21bc",
        "trigger_time": (datetime.now(timezone.utc) - timedelta(hours=12, minutes=20)).isoformat(),
        "duration_sec": 75,
        "intensity": 68.0,
        "mode": "green",
        "status": "Executed Successfully",
        "emissions_g": 0.42,
        "baseline_g": 1.44,
        "saved_g": 1.02,
        "runner_id": "runner-uk-green-01",
        "logs": [
            "[00:00:01] Grid intensity: 68 gCO2/kWh (Optimal Green).",
            "[00:01:15] Helm package signed with Cosign key."
        ]
    }
]


def ensure_jobs_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(INITIAL_SEED_JOBS, f, indent=2)


def load_jobs():
    ensure_jobs_file()
    try:
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading jobs file: {e}")
        return INITIAL_SEED_JOBS


def save_jobs(jobs):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2)


def list_jobs(search=None, mode=None, status=None):
    jobs = load_jobs()
    filtered = jobs

    if search:
        s = search.lower()
        filtered = [
            j for j in filtered
            if s in j.get("name", "").lower() or s in j.get("branch", "").lower() or s in j.get("commit", "").lower()
        ]

    if mode and mode.lower() != "all":
        m = mode.lower()
        filtered = [j for j in filtered if j.get("mode", "").lower() == m]

    if status and status.lower() != "all":
        st = status.lower()
        if "defer" in st or "pause" in st:
            filtered = [j for j in filtered if "defer" in j.get("status", "").lower() or "pause" in j.get("status", "").lower()]
        elif "exec" in st or "success" in st:
            filtered = [j for j in filtered if "exec" in j.get("status", "").lower() or "success" in j.get("status", "").lower()]

    return filtered


def dispatch_job(job_name="Run PyTest Suite", branch="main", commit=None, simulate_intensity=None, force=False):
    """
    Executes or defers a CI/CD job based on live or simulated carbon intensity.
    Returns: { "job": dict, "console_output": list[str], "executed": bool }
    """
    config = load_config()
    thresholds = config.get("thresholds", {"green": 100, "amber": 250})

    if simulate_intensity is not None:
        intensity = float(simulate_intensity)
        details = {
            "intensity": intensity,
            "provider": "Simulation Input Override",
            "is_simulated": True
        }
    else:
        details = get_carbon_intensity_details()
        intensity = details["intensity"]

    mode_info = evaluate_mode_details(intensity, thresholds)
    mode = mode_info["mode"]

    now = datetime.now(timezone.utc)
    job_id = f"job-{random.randint(1100, 9999)}"
    commit_hash = commit or uuid.uuid4().hex[:7]
    duration_sec = random.randint(120, 260)
    runtime_min = round(duration_sec / 60.0, 1)

    power_kw = float(config.get("assumed_power_kw", 0.05))
    energy_kwh = round(power_kw * (duration_sec / 3600.0), 4)
    co2_grams = round(energy_kwh * intensity, 2)
    baseline_intensity = 230.0  # standard unmanaged grid average
    baseline_co2 = round(energy_kwh * baseline_intensity, 2)
    saved_co2 = max(0.0, round(baseline_co2 - co2_grams, 2))

    terminal_logs = []
    terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] >>> GREEN-CI DISPATCH INITIATED: '{job_name}' (branch: {branch} @ {commit_hash})")
    terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Connecting to Grid Telemetry ({details.get('provider')})...")
    terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Current Grid Carbon Intensity: {intensity:.1f} gCO2/kWh")
    terminal_logs.append(
        f"[{now.strftime('%H:%M:%S')}] Active Thresholds: Green < {thresholds.get('green', 100)} | "
        f"Amber < {thresholds.get('amber', 250)} | Red >= {thresholds.get('amber', 250)}"
    )
    terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Evaluated Decision Gate: [{mode.upper()}] Mode")

    if mode == "red" and not force:
        status = "Deferred / Paused"
        deferral_reason = (
            f"Grid carbon {intensity:.1f} gCO2/kWh exceeds RED threshold ({thresholds.get('amber', 250)} gCO2/kWh). "
            f"Pipeline deferred to prevent fossil-heavy emissions."
        )
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] [ALERT] Carbon gate closed! Job suspended and deferred to queue.")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] [POLICY] Non-essential workload paused. Estimated {baseline_co2:.2f} gCO2 avoided.")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Next scheduled grid re-evaluation: 5 minutes. Use 'Force Dispatch' to bypass.")

        job_record = {
            "id": job_id,
            "name": job_name,
            "branch": branch,
            "commit": commit_hash,
            "trigger_time": now.isoformat(),
            "duration_sec": 0,
            "intensity": intensity,
            "mode": mode,
            "status": status,
            "emissions_g": 0.0,
            "baseline_g": baseline_co2,
            "saved_g": baseline_co2,
            "runner_id": "queue-pool-deferred",
            "deferral_reason": deferral_reason,
            "logs": terminal_logs
        }
        executed = False
    else:
        if force and mode == "red":
            status = "Executed (Forced Bypass)"
            terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] [OVERRIDE] Manual override enabled: Proceeding despite RED grid status.")
        elif mode == "amber":
            status = "Executed Successfully"
            terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] [AMBER] Constrained runner provisioned. Proceeding with standard job execution.")
        else:
            status = "Executed Successfully"
            terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] [OPTIMAL] Green window active! Full parallel runner fleet allocated.")

        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Provisioning ephemeral runner instance (runner-uk-{mode}-01)...")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Fetching repository source code tree (git clone --depth 1)...")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Executing pipeline tasks: dependency hydration, linting, tests, package compile...")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Energy metrics: {energy_kwh:.4f} kWh consumed across {runtime_min} mins.")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] Carbon tally: {co2_grams:.2f} gCO2 emitted vs {baseline_co2:.2f} gCO2 baseline.")
        terminal_logs.append(f"[{now.strftime('%H:%M:%S')}] >>> PIPELINE COMPLETED SUCCESSFULLY [Exit Code: 0]")

        job_record = {
            "id": job_id,
            "name": job_name,
            "branch": branch,
            "commit": commit_hash,
            "trigger_time": now.isoformat(),
            "duration_sec": duration_sec,
            "intensity": intensity,
            "mode": mode,
            "status": status,
            "emissions_g": co2_grams,
            "baseline_g": baseline_co2,
            "saved_g": saved_co2,
            "runner_id": f"runner-uk-{mode}-01",
            "logs": terminal_logs
        }
        executed = True
        try:
            log_run(mode, intensity, runtime_min, is_baseline=False, job_name=job_name)
        except Exception as e:
            print(f"Error logging run: {e}")

    # Prepend new job to jobs list
    jobs = load_jobs()
    jobs.insert(0, job_record)
    save_jobs(jobs[:50])  # keep latest 50

    return {
        "job": job_record,
        "console_output": terminal_logs,
        "executed": executed
    }


def force_dispatch(job_id):
    """Bypasses red deferral for a previously paused job."""
    jobs = load_jobs()
    for j in jobs:
        if j.get("id") == job_id:
            now = datetime.now(timezone.utc)
            duration_sec = random.randint(110, 230)
            j["status"] = "Executed (Forced Bypass)"
            j["duration_sec"] = duration_sec
            j["emissions_g"] = round(0.05 * (duration_sec / 3600.0) * float(j.get("intensity", 250)), 2)
            log_msg = f"[{now.strftime('%H:%M:%S')}] Manual force dispatch executed by developer override."
            if "logs" not in j:
                j["logs"] = []
            j["logs"].append(log_msg)
            save_jobs(jobs)
            return {"success": True, "job": j}
    return {"success": False, "error": "Job not found"}


def get_analytics_data():
    """Generates analytics stats, 24h curve, and efficiency metrics."""
    jobs = load_jobs()
    config = load_config()
    thresholds = config.get("thresholds", {"green": 100, "amber": 250})

    total_saved_g = sum(float(j.get("saved_g", 0.0)) for j in jobs)
    total_emitted_g = sum(float(j.get("emissions_g", 0.0)) for j in jobs)
    total_baseline_g = sum(float(j.get("baseline_g", 0.0)) for j in jobs)

    base_historical_savings_kg = 48.7
    total_saved_kg = round(base_historical_savings_kg + (total_saved_g / 1000.0), 2)
    trees_equivalent = round(total_saved_kg * 0.045, 1)
    ev_miles_equivalent = round(total_saved_kg * 2.5, 1)

    total_jobs_count = len(jobs)
    green_jobs = sum(1 for j in jobs if j.get("mode") == "green")
    amber_jobs = sum(1 for j in jobs if j.get("mode") == "amber")
    red_jobs = sum(1 for j in jobs if j.get("mode") == "red")

    green_pct = round((green_jobs / total_jobs_count * 100), 1) if total_jobs_count else 0
    amber_pct = round((amber_jobs / total_jobs_count * 100), 1) if total_jobs_count else 0
    red_pct = round((red_jobs / total_jobs_count * 100), 1) if total_jobs_count else 0

    now = datetime.now(timezone.utc)
    hourly_labels = []
    hourly_intensity = []

    base_curve = [
        92, 85, 78, 72, 75, 88, 120, 165, 142, 110, 85, 76,
        70, 75, 95, 140, 195, 260, 285, 270, 220, 175, 130, 105
    ]

    current_hour = now.hour
    for i in range(24):
        h = (current_hour - 23 + i) % 24
        label = f"{h:02d}:00"
        hourly_labels.append(label)
        hourly_intensity.append(base_curve[h])

    return {
        "summary": {
            "total_saved_kg": total_saved_kg,
            "total_saved_g": round(total_saved_g, 2),
            "total_emitted_g": round(total_emitted_g, 2),
            "total_baseline_g": round(total_baseline_g, 2),
            "trees_equivalent": trees_equivalent,
            "ev_miles_equivalent": ev_miles_equivalent,
            "green_window_ratio_pct": green_pct,
            "total_jobs": total_jobs_count,
            "deferred_count": sum(1 for j in jobs if "defer" in j.get("status", "").lower() or "pause" in j.get("status", "").lower()),
            "executed_count": sum(1 for j in jobs if "exec" in j.get("status", "").lower())
        },
        "breakdown": {
            "green_count": green_jobs,
            "green_pct": green_pct,
            "amber_count": amber_jobs,
            "amber_pct": amber_pct,
            "red_count": red_jobs,
            "red_pct": red_pct
        },
        "history_24h": {
            "labels": hourly_labels,
            "intensity": hourly_intensity,
            "green_threshold": thresholds.get("green", 100),
            "amber_threshold": thresholds.get("amber", 250)
        }
    }
