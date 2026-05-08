# Project Documentation
## ABM-Modeling: Waste in the City
**Course:** Symbolic AI and Rule-based Agents: Foundations  
**Lecturer:** Prof. Dr. Tatyana Ivanovska  
**University:** OTH Amberg-Weiden  
**Submission Date:** 01.06.2026  
**Team Members:** [Name 1] | [Name 2]

---

## 1. Problem Statement

The goal of this project is to study how different types of agents and infrastructure influence
the spatial and temporal distribution of waste in a city. The city is modelled as a discrete
grid world consisting of streets, walls (buildings), public areas, fixed waste bins, and a
disposal point.

**Main Research Question:**
> How do city structure, movement patterns, bin placement, cleaning strategies, and
> transporter frequency affect waste accumulation in a city?

The main interest is **not** the decision process of a single agent, but the **emergent
city-level waste distribution** that arises from many interacting agents over time. Waste
patterns are not programmed directly — they emerge from the collective behaviour of locals,
tourists, cleaners, bins, and transporters interacting on a shared grid.

---

## 2. System Design

### 2.1 Grid World

The city is represented as a 2D grid of size 20 × 20 cells. Each cell has one of three types:

| Cell Type   | Symbol   | Description                                        |
|-------------|----------|----------------------------------------------------|
| Street      | street   | Walkable; agents can move and waste can accumulate |
| Wall        | wall     | Non-walkable; represents buildings                 |
| Public Area | public   | Walkable; waste can accumulate; attracts tourists  |

Buildings are placed in a regular block pattern: every cell where both `x % 5 ∈ {1,2}`
and `y % 5 ∈ {1,2}` is a wall. Public areas are placed diagonally: any walkable cell
where `(x + y) % 7 == 0` is marked as public.

The city is divided into four **districts** by the centre lines:
- **NW** (x < 10, y < 10) — home zone for some locals
- **NE** (x < 10, y ≥ 10)
- **SW** (x ≥ 10, y < 10)
- **SE** (x ≥ 10, y ≥ 10)

The **central/attraction zone** is defined as all walkable cells with Manhattan distance ≤ 4
from the grid centre (10, 10). This zone overlaps all four districts and is the primary
tourist hotspot.

The disposal point is fixed at cell `(0, 0)` at the city edge. Cleaning robots and
transporters unload all collected waste here.

### 2.2 Waste Representation

Waste is modelled as a numeric quantity stored in a dictionary `ground_waste` keyed by
grid position. When a bin overflows or a human drops waste without a nearby bin, the
quantity is added to that cell's ground waste. Cleaning agents reduce this quantity by
collecting waste and transporting it to the disposal point.

---

## 3. Agent Types

### 3.1 Local Humans

Local humans represent residents who follow predictable daily routines. Their movement
is divided into four phases over a 40-step cycle:

| Steps 0–9   | Move toward home zone                |
|-------------|--------------------------------------|
| Steps 10–24 | Move toward work zone                |
| Steps 25–34 | Move toward leisure / public area    |
| Steps 35–39 | Return to home zone                  |

At each step, a local human generates waste with probability 0.05. If a bin within
radius 2 is available and not full, the waste goes into the bin. Otherwise, it is
dropped on the street as ground waste.

**Design rationale:** Local humans are assigned to opposing zone pairs (e.g., home=NW,
work=SE) to simulate realistic cross-city commuting patterns that distribute waste
unevenly across districts.

### 3.2 Tourists

Tourists move less predictably. With probability 0.75 per step, they move toward a
randomly chosen attraction cell (central or public area). Otherwise, they move randomly.

Tourists generate waste with base probability 0.10. In crowded cells (3+ agents), an
extra 0.04 probability is added, reflecting the real-world observation that crowded
public areas accumulate waste faster.

**Design rationale:** Tourists create emergent waste hotspots around central and
public zones. This is one of the key phenomena the model is designed to study — the
central zone accumulates disproportionately more waste than peripheral districts
because multiple tourists independently converge there.

### 3.3 Cleaning Service

Cleaning agents move through streets and collect ground waste. They support three
rule-based strategies:

| Strategy  | Behaviour                                                              |
|-----------|------------------------------------------------------------------------|
| random    | Moves to a random walkable neighbour at each step                      |
| nearest   | Uses BFS to find the closest cell with ground waste and moves toward it |
| fixed     | Follows a predefined rectangular patrol route around the city          |

When a cleaning agent's load reaches capacity (10 units), it returns to the disposal
point via BFS, deposits its load, and resumes its strategy.

### 3.4 Dust Bins

Bins are fixed infrastructure placed on walkable cells at model initialisation. Each bin
has a capacity of 15 units. When a human deposits waste:

1. The bin accepts as much as it can (up to capacity).
2. Any excess becomes ground waste on the bin's cell (overflow).

Bins can also be equipped with **fill-level sensors** (see Section 6: Creative Extension).

**Bin Placement Strategy (3-step priority):**
1. **2 bins per district** (NW, NE, SW, SE) — ensures even city-wide coverage (8 bins)
2. **Remaining bins go to the central/attraction zone** — highest tourist density and
   primary waste hotspot
3. **Fallback** to random walkable cells if zones run out of space

The default `n_bins=10` gives 8 district bins + 2 central bins. This is the baseline.
The placement is deterministic given the same seed, which makes experiment results
reproducible and directly comparable across runs.

### 3.5 Dust Transporters

Transporters collect waste from bins and carry it to the disposal point. They follow
walkable street paths and cannot pass through buildings. At each step, a transporter:

1. Checks for candidate bins (those above the visit threshold, or sensor-alerted bins).
2. Uses BFS to find the nearest candidate bin.
3. Moves one step along that BFS path.
4. When it reaches the bin, it empties it and adds to its load.
5. When load reaches capacity (40 units), it navigates to the disposal point and unloads.

---

## 4. Emergent Behaviour

The research question specifically asks about **emergent** city-level waste distribution —
patterns that no single agent causes, but that arise from interactions.

### 4.1 Tourist Waste Hotspot
Tourists independently choose to move toward central and public cells. No agent is told
to "create a hotspot". Yet collectively, their convergence on the same zone causes
disproportionate bin fill-up and street overflow in the central area. This hotspot emerges
from the interaction of the tourist movement rule and the city's spatial structure.

### 4.2 District Waste Imbalance
Local humans commuting between opposing districts (NW↔SE, NE↔SW) deposit waste along
their travel paths. Over time, zones with more commuter traffic accumulate more street
waste than quiet zones. The `avg_waste_per_district` metric captures this imbalance
emerging from movement patterns alone.

### 4.3 Bin Overflow Cascade
When a bin fills up and overflows, waste spills to the street. Cleaners must then travel
further to collect it. This slows cleanup, allowing even more waste to accumulate before
the next collection. The cascade effect amplifies local waste peaks — it is a positive
feedback loop that is not programmed but emerges from the interaction of bin capacity,
overfill logic, and cleaner capacity.

### 4.4 Cleaner Convergence
Two cleaning agents using the `nearest` strategy can independently navigate toward the
same waste hotspot, leaving other parts of the city unserviced. This emergent inefficiency
is visible in the `robot_cleaning_efficiency` metric and contrasts with the `fixed`
patrol strategy that distributes coverage more evenly.

---

## 5. Graph Search

All directed movement in the model uses **Breadth-First Search (BFS)** on the walkable
street graph. Buildings act as non-traversable nodes.

BFS was chosen because:
- The grid is unweighted (every street step costs the same).
- BFS always finds the shortest path in an unweighted graph.
- It is simpler to implement correctly than A* while achieving the same result here.
- DFS was not considered because it does not guarantee shortest paths.

Two BFS variants are implemented in `pathfinding.py`:

| Function                          | Purpose                                                      |
|-----------------------------------|--------------------------------------------------------------|
| `bfs(start, goal)`                | Returns shortest path from start to a specific goal cell     |
| `nearest_target(start, targets)`  | Single BFS from start; stops at the first target cell reached, returning that cell and the path |

The `nearest_target()` function is significantly more efficient than running separate BFS
calls for every possible target. It explores the grid once in expanding rings and stops
as soon as any target is encountered, which guarantees the nearest is found first.

---

## 6. Experiments

We ran 11 scenarios, each repeated 5 times with different random seeds to reduce variance.
Each run lasted 120 steps. Results were averaged across runs before plotting.

| Scenario               | Variable changed                                              |
|------------------------|---------------------------------------------------------------|
| few_bins               | n_bins = 6 (district-only, no central coverage)              |
| baseline_bins          | n_bins = 10 (8 district + 2 central) ← **default**          |
| many_bins              | n_bins = 16 (8 district + 8 central, saturated)              |
| low_tourists           | n_tourists = 5                                               |
| high_tourists          | n_tourists = 20                                              |
| random_cleaning        | cleaner_strategy = random                                    |
| nearest_cleaning       | cleaner_strategy = nearest                                   |
| fixed_cleaning         | cleaner_strategy = fixed route                               |
| rare_transporter       | transporter_threshold = 1.0 (visits only full bins)          |
| frequent_transporter   | transporter_threshold = 0.5 (visits half-full bins)          |
| smart_bins             | smart_bins_enabled = True (creative extension)               |

### 6.1 Metrics Collected

| Metric                     | Description                                           |
|----------------------------|-------------------------------------------------------|
| total_waste_on_streets     | Sum of all ground_waste values across the grid        |
| overflowing_bins           | Number of bins at full capacity                       |
| avg_waste_per_district     | Average ground waste per NW/NE/SW/SE district         |
| robot_cleaning_efficiency  | Cumulative total waste collected by all cleaning agents |
| transporter_workload       | Cumulative waste emptied from bins by transporters    |
| sensor_alerted_bins        | Number of bins currently broadcasting a sensor alert  |
| transporter_pickups        | Total number of bin-emptying events by transporters   |

### 6.2 Expected Findings

Based on the model design, we expect the following outcomes:

**Bin placement:**
- `few_bins` (6, district-only) → highest street waste, most overflows, especially in
  the central tourist zone which has no bin coverage
- `baseline_bins` (10) → balanced performance; central zone is covered
- `many_bins` (16) → lowest street waste; overflow nearly eliminated in central zone

**Tourist density:**
- `high_tourists` → significantly more street waste in the central zone and public areas;
  more bin overflows; higher transporter workload
- `low_tourists` → waste more evenly distributed across districts from local commuters

**Cleaning strategy:**
- `nearest` → most efficient at reducing total street waste; reacts to hotspots
- `fixed` → more even spatial coverage but slower to respond to sudden waste peaks
- `random` → lowest cleaning efficiency; highest residual street waste

**Transporter frequency:**
- `frequent_transporter` (threshold=0.5) → fewer overflowing bins; lower street waste
  from overflow; higher transporter pickups
- `rare_transporter` (threshold=1.0) → more overflowing bins; more street spillage;
  less transporter activity

**Smart bins (creative extension):**
- Smart bins should reduce transporter workload by eliminating redundant trips
- Overflow count should decrease because transporters respond faster to critical bins
- Transporter pickups should be more targeted and efficient

---

## 7. Creative Extension: Smart Bins with Fill-Level Alerts

### 7.1 Motivation

In the baseline model, transporters visit bins whenever their fill level crosses a fixed
threshold, regardless of urgency. In real cities, smart waste infrastructure uses
IoT sensors to broadcast alerts only when a bin needs attention. This reduces unnecessary
transporter trips and prioritises the most critical bins.

### 7.2 Implementation

When `smart_bins_enabled=True`, each DustBin monitors its own fill ratio. When
`fill / capacity >= sensor_threshold` (default 0.8), the bin adds itself to the model's
`sensor_alert_bins` set. When it is emptied, it removes itself from that set.

The DustTransporter checks `sensor_alert_bins` first. If any bins are alerting, it uses
BFS to navigate to the nearest one. This means:
- The transporter is reactive, not probing.
- It prioritises genuinely critical bins.
- When no alerts exist, it falls back to threshold-based selection.

### 7.3 Connection to Research Question

Smart bins represent an infrastructure-level answer to the research question on
transporter frequency. Rather than changing how often the transporter checks bins,
smart bins change **which bins trigger a response**. This is a more realistic model
of modern city waste management and demonstrates how infrastructure intelligence
affects emergent waste distribution at the city level.

---

## 8. Assumptions and Limitations

| Assumption / Limitation          | Explanation                                               |
|----------------------------------|-----------------------------------------------------------|
| Simplified city layout           | Grid is procedurally generated, not based on real GIS data |
| No waste type differentiation    | All waste is modelled as a single numeric quantity        |
| Simplified human behaviour       | No social influence, mood, or economic factors            |
| No learning agents               | All agents follow fixed rule-based strategies             |
| Uniform grid cost                | BFS assumes equal movement cost per cell                  |
| Static bin positions             | Bins do not move or adapt to waste hotspots dynamically   |
| Single transporter               | Real cities operate fleets; scaling not modelled          |

---

## 9. How to Run

### Install dependencies
```
pip install -r requirements.txt
```

### Quick test (50 steps, smart bins enabled)
```
python run.py
```

### Full experiments (generates output/scenario_results.csv and 7 PNG charts)
```
python experiments.py
```

---

## 10. File Structure

```
waste-city-abm/
├── agents.py         All agent classes
├── model.py          Main WasteCityModel (default n_bins=10)
├── pathfinding.py    BFS pathfinding
├── experiments.py    Scenario runner and plots
├── run.py            Quick entry point
├── requirements.txt  Dependencies
├── README.md         Project overview
└── REPORT.md         This document
```

---

## 11. References

- Mesa: Agent-Based Modeling in Python. https://mesa.readthedocs.io
- Wilensky, U., & Rand, W. (2015). *An Introduction to Agent-Based Modeling*. MIT Press.
- Ivanovska, T. (2026). Symbolic AI and Rule-based Agents: Foundations (Lecture Slides). OTH Amberg-Weiden.
