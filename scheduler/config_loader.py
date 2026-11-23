"""
Configuration loader supporting YAML and JSON, with built-in lightweight
YAML parser fallback if PyYAML is not installed.
"""
import os
import json

DEFAULT_CONFIG = {
    "thresholds": {
        "green": 100,
        "amber": 250,
        "red": 250
    },
    "max_wait_seconds": 120,
    "assumed_power_kw": 0.05,
    "provider": "neso_uk",  # 'neso_uk' or 'custom_webhook'
    "custom_webhook_url": "https://api.internal-grid.io/v1/carbon",
    "webhook_token": "",
    "simulated_intensity": None,
    "simulation_enabled": False
}


def parse_simple_yaml(text: str) -> dict:
    result = {}
    current_section = None

    for line in text.splitlines():
        line_clean = line.split('#')[0].rstrip()
        if not line_clean.strip():
            continue

        indent = len(line_clean) - len(line_clean.lstrip())
        trimmed = line_clean.strip()

        if ':' in trimmed:
            key, val = trimmed.split(':', 1)
            key = key.strip()
            val = val.strip()

            if indent > 0 and current_section is not None:
                # Nested property
                result[current_section][key] = _cast_value(val)
            elif not val:
                # New section header
                current_section = key
                if key not in result:
                    result[key] = {}
            else:
                current_section = None
                result[key] = _cast_value(val)

    return result


def _cast_value(val: str):
    if not val:
        return ""
    val_lower = val.lower()
    if val_lower in ("true", "yes", "on"):
        return True
    if val_lower in ("false", "no", "off"):
        return False
    if val_lower in ("null", "none", "~"):
        return None
    try:
        if '.' in val:
            return float(val)
        return int(val)
    except ValueError:
        return val.strip('"\'')


def dump_simple_yaml(data: dict) -> str:
    lines = []
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for sub_k, sub_v in v.items():
                lines.append(f"  {sub_k}: {sub_v}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) + "\n"


def get_config_path() -> str:
    return os.path.join(os.path.dirname(__file__), 'config.yaml')


def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    config_path = get_config_path()

    if os.path.exists(config_path):
        try:
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
            except ImportError:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = parse_simple_yaml(f.read())
            if isinstance(loaded, dict):
                # Deep merge top-level and thresholds
                for k, v in loaded.items():
                    if k == "thresholds" and isinstance(v, dict):
                        if "thresholds" not in config:
                            config["thresholds"] = {}
                        config["thresholds"].update(v)
                    else:
                        config[k] = v
        except Exception as e:
            print(f"Error loading config.yaml: {e}")

    # Also check runtime state file if present
    state_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'runtime_state.json')
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                if isinstance(state, dict):
                    config.update(state)
        except Exception:
            pass

    return config


def save_config(config_data: dict) -> bool:
    try:
        config_path = get_config_path()
        yaml_str = dump_simple_yaml({
            "thresholds": config_data.get("thresholds", {"green": 100, "amber": 250}),
            "max_wait_seconds": config_data.get("max_wait_seconds", 120),
            "assumed_power_kw": config_data.get("assumed_power_kw", 0.05),
            "provider": config_data.get("provider", "neso_uk"),
            "custom_webhook_url": config_data.get("custom_webhook_url", ""),
            "simulated_intensity": config_data.get("simulated_intensity"),
            "simulation_enabled": config_data.get("simulation_enabled", False)
        })
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(yaml_str)

        # Also mirror to data/runtime_state.json
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        state_path = os.path.join(data_dir, 'runtime_state.json')
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
