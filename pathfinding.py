from collections import deque


class Pathfinder:
    def __init__(self, city_map):
        self.city_map = city_map
        self.width = len(city_map)
        self.height = len(city_map[0]) if city_map else 0

    def is_walkable(self, pos):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height and self.city_map[x][y] != 'wall'

    def neighbors(self, pos):
        x, y = pos
        candidates = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        return [p for p in candidates if self.is_walkable(p)]

    def bfs(self, start, goal):
        if start == goal:
            return [start]
        queue = deque([start])
        parents = {start: None}
        while queue:
            current = queue.popleft()
            for nxt in self.neighbors(current):
                if nxt in parents:
                    continue
                parents[nxt] = current
                if nxt == goal:
                    return self._reconstruct(parents, goal)
                queue.append(nxt)
        return []

    def nearest_target(self, start, targets):
        targets = set(targets)
        if not targets:
            return None, []
        if start in targets:
            return start, [start]
        queue = deque([start])
        parents = {start: None}
        while queue:
            current = queue.popleft()
            for nxt in self.neighbors(current):
                if nxt in parents:
                    continue
                parents[nxt] = current
                if nxt in targets:
                    return nxt, self._reconstruct(parents, nxt)
                queue.append(nxt)
        return None, []

    def _reconstruct(self, parents, goal):
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = parents[current]
        return list(reversed(path))
