import os
import csv
import yaml
from datetime import datetime

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def log_run(mode, intensity, runtime_minutes, is_baseline=False):
    config = load_config()
    power_kw = config.get("assumed_power_kw", 0.05)
    runtime_hours = runtime_minutes / 60.0
    energy_kwh = power_kw * runtime_hours
    co2_grams = energy_kwh * intensity
    
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, 'runs.csv')
    
    file_exists = os.path.exists(csv_path)
    with open(csv_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "mode", "intensity", "runtime_min", "co2_grams", "type"])
        timestamp = datetime.utcnow().isoformat()
        run_type = "baseline" if is_baseline else "actual"
        writer.writerow([timestamp, mode, intensity, runtime_minutes, round(co2_grams, 2), run_type])
    return co2_grams

if __name__ == "__main__":
    log_run("green", 100.0, 5.0, is_baseline=False)