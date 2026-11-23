import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scheduler.config_loader import load_config
except ImportError:
    from config_loader import load_config


def get_grid_intensity():
    config = load_config()

    # 1. Environment Variable override
    sim_intensity = os.getenv("SIMULATE_INTENSITY")
    if sim_intensity is not None:
        try:
            return float(sim_intensity)
        except ValueError:
            pass

    # 2. Config simulation override
    if config.get("simulation_enabled") and config.get("simulated_intensity") is not None:
        try:
            return float(config.get("simulated_intensity"))
        except (ValueError, TypeError):
            pass

    # 3. Check sim file
    try:
        sim_file = os.path.join(os.path.dirname(__file__), '../data/sim_intensity.json')
        if os.path.exists(sim_file):
            with open(sim_file, 'r', encoding='utf-8') as sf:
                data = json.load(sf)
                if data.get("enabled", True) and "intensity" in data:
                    return float(data.get("intensity"))
    except Exception:
        pass

    return 142.0


if __name__ == "__main__":
    print(f"CURRENT_INTENSITY={get_grid_intensity()}")
