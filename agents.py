import random
import mesa


class WasteMixin:
    def deposit_waste(self, amount=1):
        nearby_bin = self.model.find_nearby_bin(self.pos, radius=2)
        if nearby_bin and not nearby_bin.is_full():
            nearby_bin.receive_waste(amount)
        else:
            self.model.add_ground_waste(self.pos, amount)


class LocalHuman(mesa.Agent, WasteMixin):
    def __init__(self, model, home_zone='NW', work_zone='SE'):
        super().__init__(model)
        self.home_zone = home_zone
        self.work_zone = work_zone
        self.waste_prob = 0.05

    def daily_target(self):
        phase = self.model.current_step % 40
        if phase < 10:
            return self.model.random_cell_in_zone(self.home_zone)
        if phase < 25:
            return self.model.random_cell_in_zone(self.work_zone)
        if phase < 35 and self.model.attraction_cells:
            return random.choice(self.model.attraction_cells)
        return self.model.random_cell_in_zone(self.home_zone)

    def step(self):
        self.model.move_agent_toward(self, self.daily_target())
        if random.random() < self.waste_prob:
            self.deposit_waste(1)


class Tourist(mesa.Agent, WasteMixin):
    def __init__(self, model):
        super().__init__(model)
        self.base_waste_prob = 0.10

    def tourist_target(self):
        if self.model.attraction_cells and random.random() < 0.75:
            return random.choice(self.model.attraction_cells)
        return None

    def step(self):
        target = self.tourist_target()
        if target is not None:
            self.model.move_agent_toward(self, target)
        else:
            self.model.move_agent_randomly(self)
        crowd = len(self.model.grid.get_cell_list_contents([self.pos]))
        waste_prob = self.base_waste_prob + (0.04 if crowd >= 3 else 0)
        if random.random() < waste_prob:
            self.deposit_waste(1)


class DustBin(mesa.Agent):
    def __init__(self, model, capacity=15, sensor_threshold=0.8, smart_enabled=False):
        super().__init__(model)
        self.capacity = capacity
        self.fill = 0
        self.sensor_threshold = sensor_threshold
        self.smart_enabled = smart_enabled

    def receive_waste(self, amount):
        accepted = min(amount, self.capacity - self.fill)
        self.fill += accepted
        overflow = amount - accepted
        if overflow > 0:
            self.model.add_ground_waste(self.pos, overflow)
        self.update_alert_state()

    def is_full(self):
        return self.fill >= self.capacity

    def empty(self):
        amount = self.fill
        self.fill = 0
        self.update_alert_state()
        return amount

    def update_alert_state(self):
        if not self.smart_enabled:
            return
        if self.fill / self.capacity >= self.sensor_threshold:
            self.model.sensor_alert_bins.add(self)
        else:
            self.model.sensor_alert_bins.discard(self)

    def step(self):
        self.update_alert_state()


class CleaningService(mesa.Agent):
    def __init__(self, model, strategy='nearest', patrol_route=None):
        super().__init__(model)
        self.strategy = strategy
        self.capacity = 10
        self.load = 0
        self.cleaned_total = 0
        self.patrol_route = patrol_route or []
        self.route_index = 0

    def collect_here(self):
        amount = self.model.ground_waste.get(self.pos, 0)
        if amount <= 0:
            return
        collected = min(amount, self.capacity - self.load)
        remaining = amount - collected
        if remaining > 0:
            self.model.ground_waste[self.pos] = remaining
        else:
            self.model.ground_waste.pop(self.pos, None)
        self.load += collected
        self.cleaned_total += collected

    def go_disposal(self):
        if self.pos == self.model.disposal_point:
            self.load = 0
        else:
            self.model.move_agent_toward(self, self.model.disposal_point)

    def step(self):
        if self.load >= self.capacity:
            self.go_disposal()
            return
        if self.strategy == 'random':
            self.model.move_agent_randomly(self)
        elif self.strategy == 'fixed' and self.patrol_route:
            target = self.patrol_route[self.route_index]
            if self.pos == target:
                self.route_index = (self.route_index + 1) % len(self.patrol_route)
                target = self.patrol_route[self.route_index]
            self.model.move_agent_toward(self, target)
        else:
            target, path = self.model.pathfinder.nearest_target(
                self.pos, self.model.ground_waste.keys()
            )
            if path and len(path) > 1:
                self.model.grid.move_agent(self, path[1])
            else:
                self.model.move_agent_randomly(self)
        self.collect_here()


class DustTransporter(mesa.Agent):
    def __init__(self, model, visit_threshold=0.8):
        super().__init__(model)
        self.capacity = 40
        self.load = 0
        self.visit_threshold = visit_threshold
        self.workload = 0
        self.pickups = 0

    def candidate_bins(self):
        if self.model.smart_bins_enabled and self.model.sensor_alert_bins:
            return list(self.model.sensor_alert_bins)
        return [b for b in self.model.bins if b.fill / b.capacity >= self.visit_threshold]

    def step(self):
        if self.load >= self.capacity:
            if self.pos == self.model.disposal_point:
                self.load = 0
            else:
                self.model.move_agent_toward(self, self.model.disposal_point)
            return
        bins = self.candidate_bins()
        if not bins:
            return
        target_positions = [b.pos for b in bins]
        target_pos, path = self.model.pathfinder.nearest_target(self.pos, target_positions)
        if not target_pos:
            return
        target_bin = next(b for b in bins if b.pos == target_pos)
        if self.pos == target_bin.pos:
            collected = target_bin.empty()
            self.load += collected
            self.workload += collected
            self.pickups += 1
        else:
            self.model.grid.move_agent(self, path[1])
