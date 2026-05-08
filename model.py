import random
import mesa
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from agents import LocalHuman, Tourist, CleaningService, DustBin, DustTransporter
from pathfinding import Pathfinder


class WasteCityModel(mesa.Model):
    def __init__(
        self,
        width=20,
        height=20,
        n_locals=20,
        n_tourists=10,
        n_cleaners=2,
        n_bins=8,
        n_transporters=1,
        cleaner_strategy='nearest',
        transporter_threshold=0.8,
        smart_bins_enabled=False,
        seed=None,
    ):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.current_step = 0
        self.disposal_point = (0, 0)
        self.ground_waste = {}
        self.smart_bins_enabled = smart_bins_enabled
        self.sensor_alert_bins = set()

        self.city_map = self.generate_city_map()
        self.pathfinder = Pathfinder(self.city_map)
        self.walkable = [
            (x, y)
            for x in range(width)
            for y in range(height)
            if self.city_map[x][y] != 'wall'
        ]
        self.attraction_cells = [
            p for p in self.walkable
            if self.city_map[p[0]][p[1]] == 'public' or self.is_central(p)
        ]

        self.bins = []
        self.cleaners = []
        self.transporters = []

        self.datacollector = DataCollector(model_reporters={
            'total_waste_on_streets': lambda m: sum(m.ground_waste.values()),
            'overflowing_bins': lambda m: sum(1 for b in m.bins if b.is_full()),
            'avg_waste_per_district': lambda m: m.average_waste_per_district(),
            'robot_cleaning_efficiency': lambda m: sum(c.cleaned_total for c in m.cleaners),
            'transporter_workload': lambda m: sum(t.workload for t in m.transporters),
            'sensor_alerted_bins': lambda m: len(m.sensor_alert_bins),
            'transporter_pickups': lambda m: sum(t.pickups for t in m.transporters),
        })

        self.place_bins(n_bins)
        self.place_people(n_locals, n_tourists)
        self.place_cleaners(n_cleaners, cleaner_strategy)
        self.place_transporters(n_transporters, transporter_threshold)

    def generate_city_map(self):
        city = [['street' for _ in range(self.height)] for _ in range(self.width)]
        for x in range(self.width):
            for y in range(self.height):
                if x % 5 in (1, 2) and y % 5 in (1, 2):
                    city[x][y] = 'wall'
                elif (x + y) % 7 == 0:
                    city[x][y] = 'public'
        city[0][0] = 'street'
        return city

    def is_central(self, pos):
        x, y = pos
        cx, cy = self.width // 2, self.height // 2
        return abs(x - cx) + abs(y - cy) <= 4

    def zone_of(self, pos):
        x, y = pos
        if x < self.width // 2 and y < self.height // 2:
            return 'NW'
        if x < self.width // 2:
            return 'NE'
        if y < self.height // 2:
            return 'SW'
        return 'SE'

    def random_walkable_cell(self):
        return random.choice(self.walkable)

    def random_cell_in_zone(self, zone):
        cells = [p for p in self.walkable if self.zone_of(p) == zone]
        return random.choice(cells) if cells else self.random_walkable_cell()

    def get_walkable_neighbors(self, pos):
        return self.pathfinder.neighbors(pos)

    def move_agent_randomly(self, agent):
        neighbors = self.get_walkable_neighbors(agent.pos)
        if neighbors:
            self.grid.move_agent(agent, random.choice(neighbors))

    def move_agent_toward(self, agent, target):
        path = self.pathfinder.bfs(agent.pos, target)
        if len(path) > 1:
            self.grid.move_agent(agent, path[1])
        else:
            self.move_agent_randomly(agent)

    def add_ground_waste(self, pos, amount):
        self.ground_waste[pos] = self.ground_waste.get(pos, 0) + amount

    def find_nearby_bin(self, pos, radius=2):
        x, y = pos
        candidates = [
            b for b in self.bins
            if not b.is_full() and abs(b.pos[0] - x) + abs(b.pos[1] - y) <= radius
        ]
        return min(candidates, key=lambda b: abs(b.pos[0] - x) + abs(b.pos[1] - y), default=None)

    def place_bins(self, n_bins):
        used = set()
        while len(self.bins) < n_bins:
            pos = self.random_walkable_cell()
            if pos == self.disposal_point or pos in used:
                continue
            used.add(pos)
            b = DustBin(self, capacity=15, sensor_threshold=0.8, smart_enabled=self.smart_bins_enabled)
            self.grid.place_agent(b, pos)
            self.bins.append(b)

    def place_people(self, n_locals, n_tourists):
        zones = [('NW', 'SE'), ('NE', 'SW'), ('SW', 'NE'), ('SE', 'NW')]
        for i in range(n_locals):
            home_zone, work_zone = zones[i % len(zones)]
            a = LocalHuman(self, home_zone=home_zone, work_zone=work_zone)
            self.grid.place_agent(a, self.random_cell_in_zone(home_zone))
        for _ in range(n_tourists):
            t = Tourist(self)
            self.grid.place_agent(
                t,
                random.choice(self.attraction_cells) if self.attraction_cells else self.random_walkable_cell()
            )

    def build_patrol_route(self):
        raw = [
            (self.width // 4, self.height // 4),
            (self.width // 4, 3 * self.height // 4),
            (3 * self.width // 4, 3 * self.height // 4),
            (3 * self.width // 4, self.height // 4),
        ]
        return [p for p in raw if self.city_map[p[0]][p[1]] != 'wall']

    def place_cleaners(self, n_cleaners, strategy):
        route = self.build_patrol_route()
        for _ in range(n_cleaners):
            c = CleaningService(self, strategy=strategy, patrol_route=route)
            self.grid.place_agent(c, self.random_walkable_cell())
            self.cleaners.append(c)

    def place_transporters(self, n_transporters, threshold):
        for _ in range(n_transporters):
            t = DustTransporter(self, visit_threshold=threshold)
            self.grid.place_agent(t, self.disposal_point)
            self.transporters.append(t)

    def average_waste_per_district(self):
        totals = {'NW': 0, 'NE': 0, 'SW': 0, 'SE': 0}
        counts = {'NW': 0, 'NE': 0, 'SW': 0, 'SE': 0}
        for pos, amount in self.ground_waste.items():
            zone = self.zone_of(pos)
            totals[zone] += amount
            counts[zone] += 1
        values = [totals[z] / counts[z] if counts[z] else 0 for z in totals]
        return sum(values) / len(values)

    @property
    def agents(self):
        return list(self.grid.agents)

    def step(self):
        agents = self.agents
        self.random.shuffle(agents)
        for agent in agents:
            agent.step()
        self.datacollector.collect(self)
        self.current_step += 1

    def run_model(self, steps=100):
        for _ in range(steps):
            self.step()
        return self.datacollector.get_model_vars_dataframe()
