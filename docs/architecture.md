# AegisOS Architecture

## 1. Overview

AegisOS is an AI-assisted operating system monitoring and security
system designed to monitor process behavior, detect unusual activity,
calculate risk, generate alerts, and support controlled recovery.

## 2. System Architecture

The main AegisOS pipeline is:

Process Monitoring
→ Process History
→ Feature Engineering
→ ML Anomaly Detection
→ Risk Engine
→ Alert Engine
→ Recovery Policy
→ Safe Recovery
→ Recovery Verification
→ Incident Logging
→ Dashboard

## 3. Process Monitoring

The Process Monitor collects information about running processes.

The monitored attributes include:

- Process ID
- Process name
- Process status
- CPU usage
- Memory usage
- Thread count

## 4. Process History

AegisOS maintains historical observations for processes.

Historical data allows the system to understand how a process normally
behaves instead of relying only on a single observation.

## 5. Feature Engineering

Historical process data is converted into numerical features.

Examples include:

- CPU mean
- CPU maximum
- CPU standard deviation
- Recent CPU usage
- Memory mean
- Memory maximum
- Memory standard deviation
- Recent memory usage
- Thread statistics
- CPU slope
- Memory slope
- Thread slope
- CPU change
- Memory change
- Thread change
- CPU volatility
- Memory volatility

## 6. Machine Learning

AegisOS uses Isolation Forest for unsupervised anomaly detection.

The ML pipeline is:

Historical Data
→ Feature Engineering
→ StandardScaler
→ Isolation Forest
→ Anomaly Prediction

The model produces:

- Normal prediction
- Anomaly prediction
- Anomaly score

## 7. Risk Engine

The Risk Engine combines process behavior and the ML result to
calculate a risk score.

Risk levels are:

- NORMAL
- LOW
- MEDIUM
- HIGH
- CRITICAL

The risk score ranges from 0 to 100.

## 8. Alert Engine

The Alert Engine generates alerts when abnormal behavior reaches the
configured alert conditions.

A cooldown mechanism prevents repeated alerts for the same process.

## 9. Recovery

Recovery is separated from detection.

The recovery pipeline is:

Detection
→ Risk Assessment
→ Recovery Policy
→ Safety Check
→ Recovery Action
→ Verification

Recovery actions must be restricted to controlled and safe targets.

## 10. Incident Logging

Security events and recovery events can be stored for later analysis.

This provides an audit trail of system activity.

## 11. Dashboard

The AegisOS dashboard provides a graphical interface for:

- CPU monitoring
- Memory monitoring
- Process monitoring
- AI anomaly status
- Risk scores
- Incident information

## 12. Design Principle

AegisOS separates:

Detection
→ Risk
→ Decision
→ Action
→ Verification

This separation reduces the possibility of an incorrect ML prediction
directly causing a dangerous system action.