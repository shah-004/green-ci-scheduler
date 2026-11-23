import os
import sys
import csv
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scheduler.config_loader import load_config
except ImportError:
    from config_loader import load_config


def log_run(mode, intensity, runtime_minutes, is_baseline=False, job_name="ci-pipeline-job"):
    config = load_config()
    power_kw = float(config.get("assumed_power_kw", 0.05))
    runtime_hours = float(runtime_minutes) / 60.0
    energy_kwh = power_kw * runtime_hours
    co2_grams = energy_kwh * float(intensity)

    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, 'runs.csv')

    file_exists = os.path.exists(csv_path)
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "job_name", "mode", "intensity", "runtime_min", "energy_kwh", "co2_grams", "type"])
        timestamp = datetime.now(timezone.utc).isoformat()
        run_type = "baseline" if is_baseline else "actual"
        writer.writerow([timestamp, job_name, mode, intensity, runtime_minutes, round(energy_kwh, 4), round(co2_grams, 2), run_type])
    return {
        "co2_grams": round(co2_grams, 2),
        "energy_kwh": round(energy_kwh, 4),
        "power_kw": power_kw
    }


if __name__ == "__main__":
    res = log_run("green", 92.0, 4.5, is_baseline=False, job_name="test-run")
    print("Logged run:", res)
