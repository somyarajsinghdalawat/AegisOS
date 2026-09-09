# AegisOS

AI-Assisted Operating System Monitoring and Anomaly Detection System.

## 1. Clone the Repository

```bash
git clone https://github.com/somyarajsinghdalawat/AegisOS.git
cd AegisOS
```

## 2. Create a Virtual Environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` does not exist, install:

```bash
pip install psutil numpy scikit-learn joblib PySide6 pyqtgraph pytest
```

## 4. Run Tests

Run the automated test suite:

```bash
pytest -v
```

Expected result:

```text
13 passed
```

## 5. Run the AegisOS Dashboard

```bash
python -m dashboard.main
```

The dashboard provides:

* CPU monitoring
* Memory monitoring
* Process monitoring
* AI anomaly detection
* Risk scores
* Incident information

## 6. Run the Process Anomaly Detector

```bash
python -m ml.realtime_detector
```

The system will collect process history, train/load the anomaly model,
and continuously analyze process behavior.

## 7. Run the System Benchmark

```bash
python -m evaluation.benchmark
```

This generates:

```text
evaluation/system_benchmark.csv
```

## 8. Run the Evaluation Experiment

If the ML model already exists:

```bash
python -m evaluation.experiment_runner
```

This generates:

```text
evaluation/experiment_results.json
```

## 9. Generate the Evaluation Report

After the experiment finishes:

```bash
python -m evaluation.report_generator
```

This generates:

```text
evaluation/evaluation_report.md
```

## 10. Project Structure

```text
AegisOS/
│
├── collector/
│
├── detection/
│
├── ml/
│
├── recovery/
│
├── database/
│
├── dashboard/
│
├── evaluation/
│
├── tests/
│
├── docs/
│
├── requirements.txt
├── pytest.ini
└── README.md
```

## 11. Important Safety Notice

AegisOS is designed for monitoring and controlled security
experimentation.

Do not use autonomous recovery against arbitrary system processes.

Recovery experiments should use the provided controlled fault
simulation environment.

An ML anomaly does not automatically mean that a process is malicious.

## 12. Recommended First Run

After cloning, use this order:

```bash
git clone https://github.com/somyarajsinghdalawat/AegisOS.git
cd AegisOS
```

Create and activate the virtual environment:

```bash
python -m venv venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest -v
```

Run the dashboard:

```bash
python -m dashboard.main
```

Then perform the evaluation experiments.
