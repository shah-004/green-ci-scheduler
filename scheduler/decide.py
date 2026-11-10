import os
import yaml
from carbon import get_grid_intensity

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def decide_mode(intensity):
    config = load_config()
    thresholds = config.get("thresholds", {"amber": 150, "red": 250})
    if intensity < thresholds["amber"]:
        return "green"
    elif intensity <= thresholds["red"]:
        return "amber"
    else:
        return "red"

if __name__ == "__main__":
    intensity = get_grid_intensity()
    mode = decide_mode(intensity)
    print(f"INTENSITY: {intensity} -> MODE: {mode}")
    
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"mode={mode}\n")
            f.write(f"intensity={intensity}\n")