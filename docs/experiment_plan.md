# AegisOS Experiment Plan

## 1. Objective

The objective is to evaluate whether AegisOS can identify unusual
process behavior while maintaining an acceptable false-positive rate.

## 2. Experiment 1 — Normal System Behavior

Run AegisOS during normal computer usage.

Record:

- CPU usage
- Memory usage
- Process count
- Process behavior
- Anomaly scores
- Risk scores
- Alerts

Expected result:

Most normal observations should remain classified as normal.

## 3. Experiment 2 — CPU Fault

Use the controlled fault simulator to create sustained CPU activity.

Measure:

- CPU usage
- CPU trend
- Anomaly score
- Risk score
- Alert generation

Expected result:

The controlled fault should produce increased behavioral risk.

## 4. Experiment 3 — Memory Fault

Use the controlled memory fault simulator.

Measure:

- Memory usage
- Memory trend
- Anomaly score
- Risk score
- Alert generation

Expected result:

The controlled memory fault should produce increased behavioral
risk.

## 5. Experiment 4 — Recovery

Use only the controlled fault simulator.

Test:

Detection
→ Risk Assessment
→ Recovery Policy
→ Safe Recovery
→ Verification

Measure:

- Detection success
- Recovery success
- Verification success
- Recovery time

## 6. Experiment 5 — False Positives

Run legitimate workloads such as:

- Browser usage
- Compilation
- Development tools
- File compression
- Python workloads

Record cases where legitimate processes are classified as anomalous.

## 7. Metrics

### Detection Rate

Percentage of controlled anomalies detected by AegisOS.

### False Positive Rate

Percentage of normal observations incorrectly classified as anomalous.

### Alert Rate

Number of alerts generated during an experiment.

### Detection Latency

Time between abnormal behavior and detection.

### Recovery Success

Percentage of approved recovery actions that successfully resolve
the controlled fault.

### Verification Success

Percentage of recovery operations correctly verified.

## 8. Reproducibility

Each experiment should record:

- Date
- Operating system
- Python version
- Model version
- Dataset size
- Model parameters
- Experiment duration
- Workload
- Results

## 9. Important Limitation

The experiments should not be presented as proof of real-world malware
detection unless the system is evaluated using appropriately labeled
malicious datasets.

## 10. Future Evaluation

Future experiments should include:

- Larger datasets
- Labeled malicious processes
- Precision
- Recall
- F1 score
- False-positive analysis
- False-negative analysis
- Detection latency
- System overhead
- Recovery performance