# Waste City ABM

A Mesa-based agent-based model for the project **Waste in the City**.

**Course:** Symbolic AI and Rule-based Agents: Foundations  
**Lecturer:** Prof. Dr. Tatyana Ivanovska  
**University:** OTH Amberg-Weiden  

## Features
- Grid city with streets, walls, public areas, bins, and a disposal point
- Five required agent types: LocalHuman, Tourist, CleaningService, DustBin, DustTransporter
- BFS pathfinding for directed movement
- Cleaning strategies: random, nearest-waste, fixed route
- **Creative Extension:** Smart bins with fill-level sensor alerts
- Scenario experiments with CSV and PNG outputs

## Install
```bash
pip install -r requirements.txt
```

## Run
```bash
# Quick test
python run.py

# Full experiments
python experiments.py
```

## File Structure
```
waste-city-abm/
├── agents.py         All agent classes
├── model.py          Main WasteCityModel
├── pathfinding.py    BFS helpers
├── experiments.py    Scenario runner and plots
├── run.py            Quick entry point
├── requirements.txt  Dependencies
├── README.md         Project overview
└── REPORT.md         Full project documentation
```

## Agents
| Agent | Behaviour |
|---|---|
| LocalHuman | Regular daily pattern across zones; uses bins when nearby |
| Tourist | Attraction-biased movement; more waste in crowds |
| CleaningService | 3 strategies: random, nearest-waste (BFS), fixed route |
| DustBin | Fixed capacity; overflows to street; optional sensor alert |
| DustTransporter | Empties bins via BFS; reacts to sensor alerts in smart mode |

## Creative Extension: Smart Bins
When `smart_bins_enabled=True`, bins broadcast fill-level alerts.
Transporters respond reactively to these alerts instead of patrolling blindly.
