import os
import sys
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from scheduler.config_loader import load_config
except ImportError:
    from config_loader import load_config


def get_carbon_intensity_details():
    """
    Fetches real-time carbon intensity (gCO2/kWh) and metadata.
    Priority order:
    1. Environment Variable override (SIMULATE_INTENSITY)
    2. Config simulation override (simulation_enabled = True)
    3. Active Provider: 'neso_uk' or 'custom_webhook'
    4. Fallback baseline (142 gCO2/kWh)
    """
    config = load_config()

    # 1. Environment Variable override
    sim_env = os.getenv("SIMULATE_INTENSITY")
    if sim_env is not None and sim_env.strip() != "":
        try:
            val = float(sim_env)
            return {
                "intensity": val,
                "source": "env_override",
                "is_simulated": True,
                "provider": "Environment Variable (SIMULATE_INTENSITY)",
                "index": _intensity_to_index(val),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except ValueError:
            pass

    # 2. Config simulation override
    if config.get("simulation_enabled") and config.get("simulated_intensity") is not None:
        try:
            val = float(config["simulated_intensity"])
            return {
                "intensity": val,
                "source": "simulation_room",
                "is_simulated": True,
                "provider": "Simulation & Control Room Override",
                "index": _intensity_to_index(val),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except (ValueError, TypeError):
            pass

    # 3. Provider query
    provider = config.get("provider", "neso_uk")

    if provider == "custom_webhook":
        webhook_url = config.get("custom_webhook_url")
        token = config.get("webhook_token", "")
        if webhook_url:
            try:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                res = requests.get(webhook_url, headers=headers, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    val = float(data.get("intensity") or data.get("carbon_intensity") or 142.0)
                    return {
                        "intensity": val,
                        "source": "custom_webhook",
                        "is_simulated": False,
                        "provider": f"Custom Webhook ({webhook_url})",
                        "index": _intensity_to_index(val),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
            except Exception as ex:
                print(f"Custom Webhook Error: {ex}. Falling back to default.")

    # Default provider: NESO UK
    try:
        url = "https://api.carbonintensity.org.uk/intensity"
        res = requests.get(url, timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            entry = data["data"][0]
            actual = entry["intensity"]["actual"]
            forecast = entry["intensity"]["forecast"]
            index_str = entry["intensity"].get("index", "")
            intensity = actual if actual is not None else forecast
            return {
                "intensity": float(intensity),
                "source": "neso_uk_api",
                "is_simulated": False,
                "provider": "NESO National Grid UK (Live API)",
                "forecast": forecast,
                "actual": actual,
                "index": index_str or _intensity_to_index(float(intensity)),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception:
        # Offline or sandbox network isolation
        pass

    # 4. Fallback default
    fallback_val = 142.0
    return {
        "intensity": fallback_val,
        "source": "fallback_baseline",
        "is_simulated": False,
        "provider": "UK Grid Baseline (142 gCO2/kWh Offline Fallback)",
        "index": _intensity_to_index(fallback_val),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_carbon_intensity():
    """Convenience helper returning just the numeric value."""
    details = get_carbon_intensity_details()
    return details["intensity"]


def evaluate_mode(intensity, thresholds=None):
    """
    Evaluates execution mode based on thresholds.
    Green mode: intensity < green_limit
    Amber mode: intensity < amber_limit
    Red mode: intensity >= amber_limit
    """
    if thresholds is None:
        config = load_config()
        thresholds = config.get("thresholds", {})

    green_limit = float(thresholds.get("green", 100))
    amber_limit = float(thresholds.get("amber", 250))

    if intensity < green_limit:
        return "green"
    elif intensity < amber_limit:
        return "amber"
    else:
        return "red"


def evaluate_mode_details(intensity, thresholds=None):
    mode = evaluate_mode(intensity, thresholds)
    if thresholds is None:
        config = load_config()
        thresholds = config.get("thresholds", {})

    green_limit = float(thresholds.get("green", 100))
    amber_limit = float(thresholds.get("amber", 250))

    if mode == "green":
        return {
            "mode": "green",
            "name": "OPTIMAL (GREEN)",
            "title": "Optimal Green Window - Full Dispatch",
            "description": "Grid carbon intensity is very low. All CI/CD jobs, heavy Docker builds, test matrices, and deployments execute immediately.",
            "execution_allowed": True,
            "badge_color": "emerald",
            "hex": "#10B981",
            "bg_color": "rgba(16, 185, 129, 0.15)",
            "border_color": "#10B981",
            "threshold_context": f"Current: {intensity} gCO2/kWh (Below green threshold of {green_limit} gCO2/kWh)"
        }
    elif mode == "amber":
        return {
            "mode": "amber",
            "name": "MODERATE (AMBER)",
            "title": "Moderate Intensity - Constrained Dispatch",
            "description": (
                "Grid emissions are moderate. Critical path unit tests & lightweight linters proceed; "
                "large multi-arch builds are throttled."
            ),
            "execution_allowed": True,
            "badge_color": "amber",
            "hex": "#F59E0B",
            "bg_color": "rgba(245, 158, 11, 0.15)",
            "border_color": "#F59E0B",
            "threshold_context": f"Current: {intensity} gCO2/kWh (Between {green_limit} and {amber_limit} gCO2/kWh)"
        }
    else:
        return {
            "mode": "red",
            "name": "CRITICAL (RED)",
            "title": "High Carbon Alert - Non-Urgent Jobs Deferred",
            "description": (
                "Fossil fuel generation dominates the grid. Non-critical CI/CD pipelines are held "
                "in queue until cleaner renewable energy is available."
            ),
            "execution_allowed": False,
            "badge_color": "red",
            "hex": "#EF4444",
            "bg_color": "rgba(239, 68, 68, 0.15)",
            "border_color": "#EF4444",
            "threshold_context": f"Current: {intensity} gCO2/kWh (Exceeds alert threshold of {amber_limit} gCO2/kWh)"
        }


def _intensity_to_index(intensity):
    if intensity < 80:
        return "very low"
    elif intensity < 140:
        return "low"
    elif intensity < 200:
        return "moderate"
    elif intensity < 280:
        return "high"
    else:
        return "very high"


if __name__ == "__main__":
    details = get_carbon_intensity_details()
    intensity = details["intensity"]
    mode_info = evaluate_mode_details(intensity)

    print(f"Measured Grid Carbon Intensity: {intensity} gCO2/kWh ({details['provider']})")
    print(f"Evaluated Pipeline Mode: {mode_info['name']}")
    print(f"Policy: {mode_info['title']}")

    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"mode={mode_info['mode']}\n")
            f.write(f"intensity={intensity}\n")
