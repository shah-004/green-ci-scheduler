import os
import sys
from flask import Flask, jsonify, request, render_template

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scheduler.decide import get_carbon_intensity_details, evaluate_mode_details  # noqa: E402
from scheduler.config_loader import load_config, save_config  # noqa: E402
from scheduler.job_manager import (  # noqa: E402
    list_jobs, dispatch_job, force_dispatch, get_analytics_data,
    save_jobs, INITIAL_SEED_JOBS
)

app = Flask(__name__, template_folder='templates', static_folder='static')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/v1/status', methods=['GET'])
def get_status():
    config = load_config()
    thresholds = config.get("thresholds", {"green": 100, "amber": 250})
    details = get_carbon_intensity_details()
    intensity = details["intensity"]
    mode_info = evaluate_mode_details(intensity, thresholds)

    analytics = get_analytics_data()

    return jsonify({
        "status": "success",
        "carbon_intensity_gco2_kwh": intensity,
        "pipeline_mode": mode_info["mode"],
        "mode_details": mode_info,
        "source": details.get("source", "unknown"),
        "is_simulated": details.get("is_simulated", False),
        "provider": details.get("provider", "NESO UK Grid"),
        "index": details.get("index", "moderate"),
        "timestamp": details.get("timestamp"),
        "thresholds": thresholds,
        "simulation_enabled": config.get("simulation_enabled", False),
        "simulated_intensity": config.get("simulated_intensity"),
        "summary": analytics["summary"]
    })


@app.route('/api/v1/schedule', methods=['POST'])
def schedule():
    """Compatibility endpoint for existing CI/CD webhook callers."""
    data = request.get_json() or {}
    job_name = data.get("job_name", "ci-scheduled-build")
    branch = data.get("branch", "main")
    force = data.get("force", False)

    result = dispatch_job(job_name=job_name, branch=branch, force=force)
    job = result["job"]

    return jsonify({
        "job_name": job["name"],
        "carbon_intensity": job["intensity"],
        "mode": job["mode"],
        "status": job["status"],
        "execution_allowed": result["executed"],
        "message": f"Job '{job_name}' evaluated under {job['mode'].upper()} mode.",
        "job_id": job["id"],
        "console_output": result["console_output"]
    })


@app.route('/api/v1/simulate', methods=['POST'])
def set_simulation():
    data = request.get_json() or {}
    enabled = data.get("enabled", False)
    intensity = data.get("intensity")

    config = load_config()
    config["simulation_enabled"] = bool(enabled)
    if enabled and intensity is not None:
        try:
            config["simulated_intensity"] = float(intensity)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid intensity value"}), 400
    elif not enabled:
        config["simulated_intensity"] = None

    save_config(config)

    # Return updated status
    thresholds = config.get("thresholds", {"green": 100, "amber": 250})
    details = get_carbon_intensity_details()
    mode_info = evaluate_mode_details(details["intensity"], thresholds)

    return jsonify({
        "status": "success",
        "simulation_enabled": config.get("simulation_enabled", False),
        "simulated_intensity": config.get("simulated_intensity"),
        "current_intensity": details["intensity"],
        "mode": mode_info["mode"],
        "mode_details": mode_info
    })


@app.route('/api/v1/jobs', methods=['GET'])
def get_jobs():
    search = request.args.get('search')
    mode = request.args.get('mode')
    status = request.args.get('status')
    jobs = list_jobs(search=search, mode=mode, status=status)
    return jsonify({
        "status": "success",
        "count": len(jobs),
        "jobs": jobs
    })


@app.route('/api/v1/jobs/dispatch', methods=['POST'])
def dispatch_new_job():
    data = request.get_json() or {}
    job_name = data.get("job_name", "Test CI Job")
    branch = data.get("branch", "main")
    commit = data.get("commit")
    force = data.get("force", False)
    simulate_intensity = data.get("simulate_intensity")

    result = dispatch_job(
        job_name=job_name,
        branch=branch,
        commit=commit,
        simulate_intensity=simulate_intensity,
        force=force
    )
    return jsonify({
        "status": "success",
        "job": result["job"],
        "console_output": result["console_output"],
        "executed": result["executed"]
    })


@app.route('/api/v1/jobs/<job_id>/force', methods=['POST'])
def force_job(job_id):
    res = force_dispatch(job_id)
    if res["success"]:
        return jsonify({"status": "success", "job": res["job"]})
    return jsonify({"status": "error", "message": res.get("error", "Failed")}), 404


@app.route('/api/v1/analytics', methods=['GET'])
def analytics():
    data = get_analytics_data()
    return jsonify({
        "status": "success",
        "data": data
    })


@app.route('/api/v1/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        config = load_config()
        return jsonify({
            "status": "success",
            "settings": config
        })
    else:
        data = request.get_json() or {}
        config = load_config()

        # Update thresholds
        if "thresholds" in data:
            if "green" in data["thresholds"]:
                config["thresholds"]["green"] = float(data["thresholds"]["green"])
            if "amber" in data["thresholds"]:
                config["thresholds"]["amber"] = float(data["thresholds"]["amber"])
                config["thresholds"]["red"] = float(data["thresholds"]["amber"])

        if "assumed_power_kw" in data:
            config["assumed_power_kw"] = float(data["assumed_power_kw"])

        if "max_wait_seconds" in data:
            config["max_wait_seconds"] = int(data["max_wait_seconds"])

        if "provider" in data:
            config["provider"] = str(data["provider"])

        if "custom_webhook_url" in data:
            config["custom_webhook_url"] = str(data["custom_webhook_url"])

        if "webhook_token" in data:
            config["webhook_token"] = str(data["webhook_token"])

        saved = save_config(config)
        if saved:
            return jsonify({
                "status": "success",
                "message": "Configuration saved successfully",
                "settings": config
            })
        return jsonify({"status": "error", "message": "Failed to persist configuration"}), 500


@app.route('/api/v1/reset', methods=['POST'])
def reset_demo():
    config = load_config()
    config["simulation_enabled"] = False
    config["simulated_intensity"] = None
    config["thresholds"] = {"green": 100, "amber": 250, "red": 250}
    save_config(config)
    save_jobs(INITIAL_SEED_JOBS)
    return jsonify({"status": "success", "message": "Demo data and thresholds reset."})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Carbon-Aware CI/CD Scheduler running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
