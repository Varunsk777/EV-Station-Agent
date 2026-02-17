# ⚡ Intelligent EV Charging Station Agent using Reinforcement Learning

## 📌 Overview
This project presents a Reinforcement Learning-based intelligent scheduling agent for EV charging stations. The system dynamically allocates charging slots based on vehicle priority, arrival patterns, state-of-charge (SOC), and queue dynamics.

The objective is to improve:
- Queue stability
- Fairness
- Throughput
- Priority-aware servicing
- System efficiency under varying arrival rates

---

## 🚗 Priority Classification

Vehicles are categorized into:

- **Priority 1** – Emergency Vehicles (Ambulance, Fire, Police)
- **Priority 2** – Government / VIP Vehicles
- **Priority 3** – Normal Civilian Vehicles

The agent ensures fairness while prioritizing critical vehicles.

---

## 🧠 Methodology

The system is modeled as a Markov Decision Process (MDP):

- **State Space**:
  - Queue lengths
  - Remaining charging time
  - Vehicle priority
  - Arrival rate
  - Charging demand
  - Station utilization

- **Action Space**:
  - Assign vehicle to charger
  - Defer vehicle
  - Switch scheduling strategy (if enabled)

- **Reward Function**:
  - Positive reward for serving high-priority vehicles
  - Penalty for long waiting times
  - Penalty for queue instability
  - Throughput-based reward component

---

## 📊 Metrics Evaluated

- Average waiting time
- Maximum queue length
- Throughput
- Stability Index
- Priority fairness score
- Time spent in critical mode
  


