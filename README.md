# 🌿 GreenOps CI — Carbon-Aware CI/CD Scheduler

> **Shift your software builds to cleaner electricity windows. Cut Scope 2 emissions by up to 60% with an average delay of only ~18 minutes.**

A full-stack Python + Flask web application that monitors real-time UK electrical grid carbon intensity and intelligently gates CI/CD pipeline execution — running builds when the grid is clean, deferring them when it's dirty.

---

## 🧠 The Problem It Solves

Software CI/CD pipelines run 24/7 — blindly, without any awareness of whether the electricity powering them is clean or dirty. During windy days the grid runs mostly on renewables; during cold evenings gas and coal peaker plants dominate. Every build that runs at the wrong time emits unnecessary carbon.

**GreenOps CI fixes this.** It watches the UK National Grid's live carbon intensity number (gCO₂/kWh), evaluates it against configurable thresholds, and makes a real-time decision on every pipeline trigger:

- 🟢 **Green** — grid is clean → run everything immediately at full speed
- 🟡 **Amber** — mixed grid → run essential jobs, throttle heavy ones  
- 🔴 **Red** — fossil fuels dominant → pause non-urgent pipelines until the grid clears

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔴🟡🟢 **Live Carbon Gate** | Fetches real-time gCO₂/kWh from NESO UK API and evaluates Green / Amber / Red mode |
| 📊 **5-View Dashboard** | Full SPA with sidebar navigation across Overview, Jobs, Analytics, Simulation, and Settings |
| 🖥️ **Live Terminal Console** | Streams carbon gate decisions and runner logs line-by-line with an interactive CLI |
| 🧪 **Simulation Room** | Slider + presets to inject any carbon value and preview scheduler behavior in real time |
| 📈 **Analytics & Savings** | Charts, CO₂ saved (kg), tree equivalents, EV miles, and green window ratios |
| ⚙️ **Configurable Thresholds** | Set your own Green / Red boundaries; supports NESO UK API or custom webhook providers |
| 🔁 **Auto-Polling** | Dashboard refreshes live telemetry every 5 seconds automatically |
| 💾 **Persistent Job Log** | All dispatches recorded with intensity, mode, emissions, and baseline savings |
| 🧪 **Test Suite** | 10 pytest tests covering all API endpoints and decision logic |

---

## 🖼️ Dashboard Views

### 1. Dashboard / Overview
Real-time large-number carbon intensity display, animated traffic-light pulse indicator, policy banner, and an interactive terminal console that streams live dispatch logs. Click **"Run Test CI Job Now"** to see the carbon gate evaluate instantly.

### 2. Pipelines & Jobs Manager
Full data table of all recent CI/CD pipeline jobs with job name, branch, commit hash, trigger time, carbon intensity at execution, evaluated mode badge, and status (`Executed Successfully` / `Deferred / Paused`). Supports search, mode filter, and status filter. Force-dispatch any paused job for emergency hotfixes.

### 3. Analytics & Carbon Savings
KPI summary cards (total CO₂ saved in kg, trees equivalent, EV miles), a 24-hour grid intensity line chart with threshold markers, an execution distribution donut chart, and a side-by-side comparison table between standard always-on CI and GreenOps CI.

### 4. Simulation & Control Room
Interactive slider (30–500 gCO₂/kWh), one-click scenario presets (High Offshore Wind 65, Midday Solar 85, Mixed Grid 175, Evening Gas Surge 310), an instant preview card showing what the scheduler would do, and a simulated test dispatch button.

### 5. Settings & Threshold Configuration
Form inputs for Green/Red thresholds, runner power consumption, max deferral buffer, and provider selection (NESO UK API or custom webhook with bearer token). All settings persist to `scheduler/config.yaml`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.1 |
| **Decision Engine** | Custom Python (`scheduler/decide.py`) |
| **Data Source** | [NESO UK Carbon Intensity API](https://carbonintensity.org.uk) (free, no key needed) |
| **Frontend** | Vanilla HTML5 + Tailwind CSS (CDN) + Chart.js |
| **Icons** | Font Awesome 6 |
| **Storage** | JSON flat files (`data/jobs.json`) + CSV (`data/runs.csv`) |
| **Testing** | pytest |
| **Linting** | flake8 |
| **CI/CD** | GitHub Actions (`.github/workflows/green-ci.yml`) |

---

## 📂 Project Structure

```
green-ci-scheduler/
├── app/
│   ├── app.py                    # Flask server — 10 REST API routes
│   ├── test_app.py               # pytest test suite (10 tests)
│   ├── __init__.py
│   ├── static/
│   │   ├── css/style.css         # Dark theme, glowing pulse lights, terminal styles
│   │   └── js/app.js             # SPA router, 5s polling, terminal streaming, Chart.js
│   └── templates/
│       └── index.html            # Responsive 5-view single-page dashboard
├── scheduler/
│   ├── carbon.py                 # Grid intensity query interface
│   ├── config.yaml               # Thresholds and runner configuration
│   ├── config_loader.py          # YAML/JSON loader (zero-dependency fallback parser)
│   ├── decide.py                 # Carbon gate decision engine (Green/Amber/Red)
│   ├── estimate.py               # Energy (kWh) and emissions (gCO₂) calculation
│   └── job_manager.py            # Job store, dispatch engine, seed data, analytics
├── data/
│   ├── jobs.json                 # Pipeline job records (auto-generated)
│   ├── runs.csv                  # Emissions audit log (auto-generated)
│   └── runtime_state.json        # Active simulation state (auto-generated)
├── docs/
│   ├── explainer.txt             # Plain-English project explainer
│   └── HOW_TO_RUN.txt            # Step-by-step setup guide
├── .github/workflows/
│   └── green-ci.yml              # GitHub Actions carbon-gated pipeline
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or newer — check with `python --version`
- No Docker, database, or cloud account needed

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd green-ci-scheduler
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the dashboard
**Windows:**
```powershell
.\venv\Scripts\python app\app.py
```

**Mac / Linux:**
```bash
python app/app.py
```

### 5. Open in your browser
```
http://localhost:5000
```

---

## 🕹️ How to Operate

### Triggering a CI Job
1. Click **"Run Test CI Job Now"** on the Dashboard (or **"Trigger New Pipeline"** in the Jobs view)
2. Select a job type, set a branch, and click **Dispatch Job**
3. Watch the terminal stream the live carbon gate evaluation
4. Result: `Executed Successfully` (Green/Amber) or `Deferred / Paused` (Red)

### Using the Simulation Room
1. Navigate to **Simulation Room** in the sidebar
2. Drag the slider or use a preset scenario button
3. Click **"Apply Simulation Override"** — a purple **SIMULATION ACTIVE** badge appears
4. Trigger a job from the Dashboard to see the gate respond to your fake value
5. Click **"Reset to Live"** to reconnect to real grid data

### Force-Dispatching a Paused Job
In **Pipelines & Jobs**, find any job with a red `Deferred (Paused)` badge and click the **Force Run** button to bypass the carbon gate (simulates an emergency hotfix).

### Terminal CLI Commands
Type commands directly into the terminal input bar on the Dashboard:

| Command | Action |
|---|---|
| `help` | List all available commands |
| `green-ci status` | Print current intensity and active mode |
| `green-ci run <name>` | Dispatch a named pipeline job |
| `sim 80` | Quickly apply a 80 gCO₂/kWh simulation override |
| `sim 320` | Quickly apply a 320 gCO₂/kWh (Red) simulation |
| `clear` | Clear the terminal log buffer |

### Resetting to Defaults
In **Settings**, click **"Reset to Defaults"** to restore original thresholds, clear simulation state, and reload the demo job data.

---

## 📡 API Reference

All endpoints are served at `http://localhost:5000`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the dashboard SPA |
| `GET` | `/api/v1/status` | Live carbon intensity, mode, thresholds, and summary stats |
| `POST` | `/api/v1/jobs/dispatch` | Evaluate carbon gate and dispatch or defer a pipeline job |
| `GET` | `/api/v1/jobs` | List recent jobs (supports `?search=`, `?mode=`, `?status=` filters) |
| `POST` | `/api/v1/jobs/<id>/force` | Force-execute a previously deferred job |
| `POST` | `/api/v1/simulate` | Enable or disable a simulated intensity override |
| `GET` | `/api/v1/analytics` | Carbon savings summary, 24h history curve, efficiency breakdown |
| `GET` / `POST` | `/api/v1/settings` | Read or update threshold and provider configuration |
| `POST` | `/api/v1/reset` | Reset all data and settings to defaults |

### Example: Check live status
```bash
curl http://localhost:5000/api/v1/status
```
```json
{
  "carbon_intensity_gco2_kwh": 142.0,
  "pipeline_mode": "amber",
  "is_simulated": false,
  "provider": "UK Grid Baseline (142 gCO2/kWh Offline Fallback)",
  "thresholds": { "green": 100, "amber": 250 }
}
```

### Example: Dispatch a job
```bash
curl -X POST http://localhost:5000/api/v1/jobs/dispatch \
  -H "Content-Type: application/json" \
  -d '{"job_name": "Run PyTest Suite", "branch": "main"}'
```

### Example: Apply a simulation override
```bash
curl -X POST http://localhost:5000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "intensity": 65}'
```

---

## ⚙️ Configuration

Edit `scheduler/config.yaml` directly, or use the **Settings** screen in the dashboard:

```yaml
thresholds:
  green: 100      # Jobs run freely below this value (gCO₂/kWh)
  amber: 250      # Jobs are deferred above this value (gCO₂/kWh)
max_wait_seconds: 120       # Max queue wait before fallback dispatch
assumed_power_kw: 0.05      # Runner power draw (standard 2-core VM ≈ 50W)
provider: neso_uk           # 'neso_uk' or 'custom_webhook'
```

### Simulating carbon intensity locally (without the dashboard)
```powershell
# Windows
$env:SIMULATE_INTENSITY = "80"
.\venv\Scripts\python scheduler\decide.py

# Mac / Linux
SIMULATE_INTENSITY=80 python scheduler/decide.py
```

---

## 🧪 Running Tests

```bash
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run linting
flake8 app scheduler --max-line-length=160
```

Expected output:
```
10 passed in 0.89s
```

The test suite covers:
- `evaluate_mode()` logic across all threshold boundaries
- `evaluate_mode_details()` metadata and `execution_allowed` flag
- YAML parser correctness
- All 7 REST API endpoints
- Green dispatch (simulate intensity 65 → executes)
- Red deferral (simulate intensity 320 → defers)
- Forced bypass (simulate intensity 320 + force=True → executes)
- Simulation enable/disable and status reflection
- Analytics data shape and 24-hour curve length
- Settings update and persistence

---

## 🌍 Carbon Intensity — What Does the Number Mean?

| Range (gCO₂/kWh) | Grid State | Pipeline Mode |
|---|---|---|
| < 80 | Very clean — offshore wind dominant | 🟢 Green |
| 80 – 100 | Clean — mixed renewables | 🟢 Green |
| 100 – 200 | Moderate — gas backup active | 🟡 Amber |
| 200 – 250 | High — significant fossil generation | 🟡 Amber |
| > 250 | Very high — coal/gas peakers online | 🔴 Red |

Data sourced from [carbonintensity.org.uk](https://carbonintensity.org.uk) — the official UK National Grid ESO open API (free, no key required, updates every 30 minutes).

---

## 🔄 GitHub Actions Integration

The workflow at `.github/workflows/green-ci.yml` runs automatically on every push to `main`. It:

1. Checks out the code and installs Python
2. Runs `scheduler/decide.py` to evaluate the live grid intensity
3. Outputs the mode (`green`, `amber`, or `red`) as a GitHub Actions step output
4. Conditionally runs the test suite (Green or Amber mode)
5. **Skips the deploy step** if mode is `red` — avoiding fossil-heavy deployment emissions

To trigger manually with a custom intensity value:
```
GitHub → Actions → GreenOps CI/CD Pipeline → Run workflow → Enter intensity value
```

---

## 📁 Additional Documentation

| File | Contents |
|---|---|
| [`docs/explainer.txt`](docs/explainer.txt) | Plain-English explanation of the whole project — no jargon |
| [`docs/HOW_TO_RUN.txt`](docs/HOW_TO_RUN.txt) | Step-by-step setup and configuration guide |

---

## 📄 License

MIT License — free to use, fork, and adapt.
