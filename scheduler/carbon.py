import os
import yaml

def get_grid_intensity():
    sim_intensity = os.getenv("SIMULATE_INTENSITY")
    if sim_intensity is not None:
        return float(sim_intensity)
    try:
        sim_file = os.path.join(os.path.dirname(__file__), '../data/sim_intensity.json')
        if os.path.exists(sim_file):
            import json
            with open(sim_file, 'r') as sf:
                data = json.load(sf)
                return float(data.get("intensity", 200))
        return 200.0
    except Exception:
        return 200.0

if __name__ == "__main__":
    print(f"CURRENT_INTENSITY={get_grid_intensity()}")