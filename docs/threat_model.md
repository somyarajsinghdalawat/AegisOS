# AegisOS Threat Model

## 1. Objective

AegisOS is designed to identify unusual process behavior and provide
risk-based responses.

The system focuses primarily on process-level behavioral indicators.

## 2. Assets

The main assets considered by AegisOS are:

- System availability
- System resources
- Running processes
- Monitoring information
- Incident information

## 3. Threats

### 3.1 Resource Exhaustion

A process may consume excessive system resources.

Examples:

- Extremely high CPU usage
- Excessive memory consumption
- Rapid thread creation

Possible impact:

- System slowdown
- Application instability
- Denial of service

### 3.2 Abnormal Process Behavior

A process may suddenly behave differently from its historical baseline.

Examples:

- Sudden CPU increase
- Rapid memory growth
- Increasing thread count
- High resource volatility

### 3.3 Monitoring Evasion

A malicious process could attempt to avoid detection by changing its
behavior or reducing its resource usage during monitoring.

## 4. False Positives

Legitimate applications may also produce unusual behavior.

Examples include:

- Software compilation
- Gaming
- Large data processing
- Software updates
- Development workloads

Therefore:

Anomaly does not automatically mean malware.

## 5. Safety Requirements

AegisOS should not automatically terminate arbitrary operating-system
processes.

System-critical and unknown processes should be protected.

Recovery testing should initially use controlled fault simulations.

## 6. Recovery Safety

The recovery subsystem follows:

Detection
→ Risk
→ Policy
→ Safety Check
→ Action
→ Verification

This prevents the ML detector from directly controlling potentially
dangerous recovery operations.

## 7. Future Threat Coverage

Future versions may investigate:

- Process injection
- Persistence
- Privilege escalation
- Malicious child processes
- Cryptomining behavior
- Ransomware-related behavior
- Network-based indicators

## 8. Limitation

AegisOS currently focuses on behavioral anomaly detection.

An anomaly score alone cannot prove that a process is malicious.