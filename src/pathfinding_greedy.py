import heapq

def manhattan_distance(a, b):
    """Heuristic: Manhattan mesafesi"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def find_path_greedy(start, goal, level):
    """
    Greedy Best-First Search ile yol bulur.
    start: (x, y)
    goal: (x, y)
    level: Level nesnesi (level.is_walkable(x, y) fonksiyonuna sahip olmalı)
    """
    frontier = []
    heapq.heappush(frontier, (manhattan_distance(start, goal), start))
    came_from = {start: None}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal:
            break

        x, y = current
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:  # yukarı, sağ, aşağı, sol
            next_pos = (x + dx, y + dy)
            if level.is_walkable(*next_pos) and next_pos not in came_from:
                heapq.heappush(frontier, (manhattan_distance(next_pos, goal), next_pos))
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
    print(f"[GREEDY] path from {start} to {goal} → {path}")
    return path