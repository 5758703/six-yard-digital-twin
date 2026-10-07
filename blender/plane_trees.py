"""Pollarded roadside plane trees guided by the supplied street photograph.

Coordinates are campus X/elevation/Z. The same mesh calls work in Blender and
in the small GLB updater, so the editable generator and browser asset agree.
"""
import math
import random


def build_plane_trees(mesh, positions, mats):
    def segment(a, b, r0, r1, sides, material):
        dx, dy, dz = (b[i] - a[i] for i in range(3))
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        ux, uy, uz = dx / length, dy / length, dz / length
        # A stable perpendicular frame around each leaning branch.
        vx, vy, vz = -uz, 0, ux
        size = math.hypot(vx, vz)
        if size < .001:
            vx, vy, vz = 1, 0, 0
        else:
            vx, vz = vx / size, vz / size
        wx, wy, wz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        vertices = []
        for center, radius in ((a, r0), (b, r1)):
            for i in range(sides):
                angle = i * math.tau / sides
                px = math.cos(angle) * vx + math.sin(angle) * wx
                py = math.cos(angle) * vy + math.sin(angle) * wy
                pz = math.cos(angle) * vz + math.sin(angle) * wz
                vertices.append((center[0] + px * radius, center[1] + py * radius,
                                 center[2] + pz * radius))
        faces = [(i, i + sides, (i + 1) % sides + sides, (i + 1) % sides)
                 for i in range(sides)]
        mesh.shape(vertices, faces, material)
        mesh.shape(vertices, [tuple(range(sides * 2 - 1, sides - 1, -1))], mats['scar'])

    def crown_blob(rng, cx, cy, cz, rx, ry, rz, top_material):
        sides = 10
        phase = rng.random() * math.tau
        variation = [rng.uniform(.84, 1.16) for _ in range(sides)]
        rings = [(-.9, .30), (-.62, .82), (-.05, 1.0), (.55, .79), (1.0, .27)]
        vertices = []
        for y, radius in rings:
            for i in range(sides):
                angle = phase + i * math.tau / sides
                scale = radius * variation[i]
                vertices.append((cx + math.cos(angle) * rx * scale,
                                 cy + y * ry + rng.uniform(-.08, .08),
                                 cz + math.sin(angle) * rz * scale))
        for row in range(len(rings) - 1):
            faces = [(row * sides + i, (row + 1) * sides + i,
                      (row + 1) * sides + (i + 1) % sides, row * sides + (i + 1) % sides)
                     for i in range(sides)]
            material = mats['shade'] if row < 2 else top_material
            mesh.shape(vertices, faces, material)
        mesh.shape(vertices, [tuple(range(len(rings) * sides - 1, (len(rings) - 1) * sides - 1, -1))], top_material)

    for index, (x, z) in enumerate(positions):
        rng = random.Random(27000 + index)
        scale = rng.uniform(.91, 1.09)
        lean_x, lean_z = rng.uniform(-.30, .30), rng.uniform(-.26, .26)
        base_y = .23
        trunk_top = 3.95 * scale
        sides = 10
        paint_top = [1.25 + rng.uniform(-.13, .13) for _ in range(sides)]
        angles = [i * math.tau / sides for i in range(sides)]

        # Uneven whitewash follows the lowest part of each trunk, as on the
        # roadside trees in the photo. The wider base avoids a toy-like pole.
        for i in range(sides):
            j = (i + 1) % sides
            a, b = angles[i], angles[j]
            mesh.shape([(x + math.cos(a) * .59 * scale, base_y, z + math.sin(a) * .59 * scale),
                        (x + math.cos(b) * .59 * scale, base_y, z + math.sin(b) * .59 * scale),
                        (x + math.cos(b) * .47 * scale, paint_top[j] * scale,
                         z + math.sin(b) * .47 * scale),
                        (x + math.cos(a) * .47 * scale, paint_top[i] * scale,
                         z + math.sin(a) * .47 * scale)],
                       [(0, 3, 2, 1)], mats['whitewash'] if i % 4 else mats['whitewash_shadow'])
            mesh.shape([(x + math.cos(a) * .47 * scale, paint_top[i] * scale,
                         z + math.sin(a) * .47 * scale),
                        (x + math.cos(b) * .47 * scale, paint_top[j] * scale,
                         z + math.sin(b) * .47 * scale),
                        (x + lean_x + math.cos(b) * .41 * scale, trunk_top,
                         z + lean_z + math.sin(b) * .41 * scale),
                        (x + lean_x + math.cos(a) * .41 * scale, trunk_top,
                         z + lean_z + math.sin(a) * .41 * scale)],
                       [(0, 3, 2, 1)], mats['bark'][i % len(mats['bark'])])

        # Large, short forks and visible sawn ends identify a pruned plane tree.
        fork = (x + lean_x, trunk_top - .25, z + lean_z)
        for branch in range(4):
            angle = branch * math.tau / 4 + rng.uniform(-.28, .28)
            length = rng.uniform(.9, 1.55) * scale
            end = (fork[0] + math.cos(angle) * length,
                   trunk_top + rng.uniform(.58, 1.12) * scale,
                   fork[2] + math.sin(angle) * length)
            segment(fork, end, .27 * scale, .15 * scale, 7,
                    mats['bark'][(branch + index) % len(mats['bark'])])
            if branch % 2 == 0:
                twig_end = (end[0] + math.cos(angle + .5) * .52,
                            end[1] + .62 * scale,
                            end[2] + math.sin(angle + .5) * .52)
                segment(end, twig_end, .11 * scale, .055 * scale, 5, mats['bark'][1])

        # Interlocking, flattened masses make an irregular umbrella canopy;
        # shaded undersides and varied sunlit greens give it depth.
        crown_y = 6.24 * scale
        crown_x, crown_z = x + lean_x, z + lean_z
        crown_blob(rng, crown_x, crown_y, crown_z,
                   2.07 * scale, 1.48 * scale, 2.04 * scale, mats['foliage'][1])
        for clump in range(6):
            angle = clump * math.tau / 6 + rng.uniform(-.24, .24)
            reach = rng.uniform(1.16, 1.72) * scale
            crown_blob(rng, crown_x + math.cos(angle) * reach,
                       crown_y + rng.uniform(-.20, .30) * scale,
                       crown_z + math.sin(angle) * reach,
                       rng.uniform(1.32, 1.70) * scale,
                       rng.uniform(1.14, 1.44) * scale,
                       rng.uniform(1.31, 1.70) * scale,
                       mats['foliage'][(clump + index) % len(mats['foliage'])])

        # Small lobed leaf sprays break up the broad polygon outline in close
        # street views while adding only a few triangles to each tree.
        for leaf in range(12):
            angle = leaf * math.tau / 12 + rng.uniform(-.11, .11)
            reach = rng.uniform(2.63, 3.12) * scale
            center = (crown_x + math.cos(angle) * reach,
                      crown_y + rng.uniform(-.57, 1.00) * scale,
                      crown_z + math.sin(angle) * reach)
            size = rng.uniform(.26, .43) * scale
            tx, tz = -math.sin(angle), math.cos(angle)
            vertices = [center]
            for point in range(10):
                a = point * math.tau / 10
                radius = size * (1 if point % 2 == 0 else .53)
                vertices.append((center[0] + tx * math.cos(a) * radius,
                                 center[1] + math.sin(a) * radius,
                                 center[2] + tz * math.cos(a) * radius))
            faces = [(0, point + 1, (point + 1) % 10 + 1) for point in range(10)]
            mesh.shape(vertices, faces, mats['foliage'][(leaf + index) % len(mats['foliage'])])
