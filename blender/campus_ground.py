"""Ground and joined road surfaces shared by Blender and the shipped GLB patcher."""
import math

SKIP_ROADS = {'international-north-link', 'shared-yard-service', 'factory-yard-connector'}
BOUNDS = (-330, 340, -285, 285)


def clip_segment(a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    lo, hi = 0., 1.
    for p, q in ((-dx, a[0] - BOUNDS[0]), (dx, BOUNDS[1] - a[0]),
                 (-dz, a[1] - BOUNDS[2]), (dz, BOUNDS[3] - a[1])):
        if abs(p) < 1e-10:
            if q < 0:
                return None
        elif p < 0:
            lo = max(lo, q / p)
        else:
            hi = min(hi, q / p)
    if lo >= hi:
        return None
    return ([a[0] + lo * dx, a[1] + lo * dz],
            [a[0] + hi * dx, a[1] + hi * dz])


def visible_chains(points):
    chains = []
    for a, b in zip(points, points[1:]):
        pair = clip_segment(a, b)
        if pair is None:
            continue
        start, end = pair
        if chains and math.dist(chains[-1][-1], start) < 1e-5:
            chains[-1].append(end)
        else:
            chains.append([start, end])
    return chains


def strip(mesh, points, width, height, material):
    """Use shared mitered edges, so bends have no triangular holes."""
    points = [p for i, p in enumerate(points)
              if i == 0 or math.dist(p, points[i - 1]) > 1e-5]
    if len(points) < 2:
        return
    normals = []
    for a, b in zip(points, points[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dz)
        normals.append((-dz / length, dx / length))
    edges = []
    for i, (x, z) in enumerate(points):
        before, after = normals[max(i - 1, 0)], normals[min(i, len(normals) - 1)]
        mx, mz = before[0] + after[0], before[1] + after[1]
        size = math.hypot(mx, mz)
        if size < .01:
            mx, mz, size = after[0], after[1], 1.
        mx, mz = mx / size, mz / size
        divisor = max(.4, mx * after[0] + mz * after[1])
        reach = width / 2 / divisor
        edges.append(((x + mx * reach, z + mz * reach),
                      (x - mx * reach, z - mz * reach)))
    for left, right in zip(edges, edges[1:]):
        mesh.shape([(left[0][0], height, left[0][1]),
                    (left[1][0], height, left[1][1]),
                    (right[1][0], height, right[1][1]),
                    (right[0][0], height, right[0][1])], [(3, 2, 1, 0)], material)


def junctions(roads):
    owners = {}
    for road in roads:
        for p in road['points']:
            key = (round(p[0], 2), round(p[1], 2))
            owners.setdefault(key, set()).add(road['id'])
    return {point for point, ids in owners.items()
            if len(ids) > 1 and BOUNDS[0] <= point[0] <= BOUNDS[1]
            and BOUNDS[2] <= point[1] <= BOUNDS[3]}


def disk(mesh, center, radius, height, material):
    x, z = center
    vertices = [(x + radius * math.cos(i * math.tau / 16), height,
                 z + radius * math.sin(i * math.tau / 16)) for i in range(16)]
    mesh.shape(vertices, [tuple(range(15, -1, -1))], material)


def build_ground(mesh, campus, mats):
    concrete, grass = mats['concrete'], mats['grass']
    asphalt, line = mats['asphalt'], mats['line']
    mesh.box(0, 0, -2.5, 680, 585, 5, concrete)
    mesh.box(0, 0, .02, 665, 570, .12, grass)
    mesh.box(-187, 155, .12, 160, 157, .16, mats['soil'])
    mesh.box(40, 198, .11, 36, 50, .14, mats['soil'])
    for green in campus.get('greens', []):
        mesh.box(green['x'], green['z'], .22, green['w'], green['d'], .14, grass)

    roads = [road for road in campus['roads'] if road['id'] not in SKIP_ROADS]
    crossings = junctions(roads)
    for road in roads:
        for chain in visible_chains(road['points']):
            strip(mesh, chain, road['width'] + 4, .205, concrete)
            strip(mesh, chain, road['width'], .24, asphalt)
            for a, b in zip(chain, chain[1:]):
                length = math.dist(a, b)
                for distance in range(0, int(length), 12):
                    start, stop = distance, min(distance + 5, length)
                    p = [a[i] + (b[i] - a[i]) * start / length for i in (0, 1)]
                    q = [a[i] + (b[i] - a[i]) * stop / length for i in (0, 1)]
                    # Keep the centre lines out of the turning area.
                    if any(math.dist(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2), j) < road['width']
                           for j in crossings):
                        continue
                    strip(mesh, [p, q], .20, .253, line)
    for center in crossings:
        widths = [road['width'] for road in roads
                  if any(math.dist(point, center) < .02 for point in road['points'])]
        radius = min(widths) / 2 + .35
        disk(mesh, center, radius + 2, .207, concrete)
        disk(mesh, center, radius, .242, asphalt)

    for parking in campus['parking']:
        x, z = parking['x'], parking['z']
        mesh.box(x, z, .2, 3.3, 6, .18, asphalt)
        for dx in (-1.6, 1.6):
            mesh.box(x + dx, z, .31, .10, 5.8, .035, line)
        mesh.box(x, z - 2.9, .31, 3.3, .12, .035, line)
        mesh.box(x, z - 2.15, .42, 1.4, .3, .2, concrete)
    for x in (-82, 165):
        for i in range(10):
            mesh.box(x - 6 + i * 1.3, 253, .265, .68, 7, .045, line)
