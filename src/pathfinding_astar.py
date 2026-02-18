import heapq

def manhattan_distance(a, b):
    """Heuristic: Manhattan mesafesi"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def find_path_astar(start, goal, level):
    """
    A* algoritması ile grid tabanlı yol bulma.
    start, goal: (x, y) koordinatları
    level: level nesnesi, is_walkable(x, y) fonksiyonu içermeli
    """
    open_set = []
    heapq.heappush(open_set, (0 + manhattan_distance(start, goal), 0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while open_set:
        _, current_cost, current = heapq.heappop(open_set)

        if current == goal:
            break

        x, y = current
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            next_pos = (x + dx, y + dy)

            if not level.is_walkable(x, y, next_pos[0], next_pos[1]):

                continue

            new_cost = current_cost + 1
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + manhattan_distance(next_pos, goal)
                heapq.heappush(open_set, (priority, new_cost, next_pos))
                came_from[next_pos] = current

    # Yol oluşturuluyor
    path = []
    curr = goal
    while curr != start:
        if curr not in came_from:
            return []  # Ulaşılamıyor
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    print(f"[A*] path from {start} to {goal} → {path}")
    return path
