"""Photo-guided six-storey residential elevations in the campus coordinate system.

The four supplied photographs establish the palette and visible details, but do
not establish exact dimensions or the unseen sides of every OSM footprint.
"""
import math
import pathlib
import random
import struct
import zlib


def make_textures(directory):
    """Create small tileable painted plaster and roof textures without a dependency."""
    directory = pathlib.Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    textures = {}
    for kind, base in [('wall', (223, 217, 199)),
                       ('wall-aged', (205, 196, 175)),
                       ('plinth', (180, 153, 119)),
                       ('roof', (91, 65, 56))]:
        rng = random.Random({'wall': 991, 'wall-aged': 994, 'plinth': 992, 'roof': 993}[kind])
        size = 256
        rows = []
        streaks = [rng.randint(-6, 5) for _ in range(size)]
        for y in range(size):
            pixels = bytearray()
            for x in range(size):
                grain = rng.randint(-5, 5)
                stain = streaks[x] * (y / size) if kind != 'roof' else 0
                if kind == 'roof':
                    # Offset roof tile courses, as seen on the lower homes in photo 3.
                    seam = y % 28 < 2 or (x + (y // 28 % 2) * 28) % 56 < 2
                    grain += -15 if seam else 0
                else:
                    grain += -3 if y % 64 < 2 else 0
                pixels.extend(max(0, min(255, round(c + grain + stain))) for c in base)
                pixels.append(255)
            rows.append(b'\0' + pixels)
        raw = zlib.compress(b''.join(rows), 9)
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        image = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
                 + chunk(b'IDAT', raw) + chunk(b'IEND', b''))
        path = directory / f'residential-{kind}.png'
        path.write_bytes(image)
        textures[kind] = path
    return textures


def build_residential(mesh, building, mats):
    x, z, w, d, h = (building[key] for key in ('x', 'z', 'w', 'd', 'height'))
    outline = [tuple(point) for point in building['polygon']]
    mesh.polygon(outline, h, mats['wall'])

    # The street photographs show a warm ochre ground floor, thin storey joints
    # and a shallow, dark red roof edge on the six-storey blocks.
    mesh.box(x, z, h + .15, w + .5, d + .5, .30, mats['roof'])
    mesh.box(x, z, h + .36, w + .2, d + .2, .18, mats['coping'])
    for side in (-1, 1):
        mesh.box(x, z + side * (d / 2 - .18), h + .53, w + .2, .24, .30, mats['wall'])
    for side in (-1, 1):
        mesh.box(x + side * (w / 2 - .16), z, h + .53, .24, d + .2, .30, mats['wall'])

    center = (x, z)
    edges = sorted(((a, b) for a, b in zip(outline, outline[1:] + outline[:1])),
                   key=lambda edge: math.dist(*edge), reverse=True)[:2]

    def panel(edge, t, y, width, height, material, offset=.08):
        a, b = edge
        length = math.dist(a, b)
        ux, uz = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        nx, nz = -uz, ux
        px, pz = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        if (px + nx - center[0]) ** 2 + (pz + nz - center[1]) ** 2 < (px - nx - center[0]) ** 2 + (pz - nz - center[1]) ** 2:
            nx, nz = -nx, -nz
        px, pz = px + nx * offset, pz + nz * offset
        mesh.shape([(px - ux * width / 2, y - height / 2, pz - uz * width / 2),
                    (px + ux * width / 2, y - height / 2, pz + uz * width / 2),
                    (px + ux * width / 2, y + height / 2, pz + uz * width / 2),
                    (px - ux * width / 2, y + height / 2, pz - uz * width / 2)],
                   [(0, 1, 2, 3), (3, 2, 1, 0)], material)

    entrance_edge = max(edges, key=lambda edge: (edge[0][1] + edge[1][1]) / 2)
    for edge in edges:
        length = math.dist(*edge)
        bays = max(3, round(length / 4.0))
        for level in range(1, building['floors']):
            panel(edge, .5, level * h / building['floors'], length, .055, mats['joint'], .12)
        panel(edge, .5, 1.45, length, 2.9, mats['plinth'], .095)
        for bay in range(bays):
            t = (bay + .5) / bays
            for floor in range(building['floors']):
                y = floor * h / building['floors'] + 1.72
                entrance = edge == entrance_edge and floor == 0 and bay % 6 == 2
                if entrance:
                    panel(edge, t, 1.35, 2.24, 2.65, mats['entry_shadow'], .15)
                    panel(edge, t, 1.35, 1.76, 2.42, mats['door'], .18)
                    panel(edge, t, 1.78, 1.05, .70, mats['glass'], .20)
                    for k in range(5):
                        panel(edge, t + (k - 2) * .0034, 1.78, .025, .69, mats['grille'], .23)
                    panel(edge, t, 2.92, 3.35, .42, mats['canopy'], .33)
                    panel(edge, t, 2.72, .72, .22, mats['sign'], .36)
                    continue

                # Dark individual windows with light frames and some enclosed
                # bay windows match the photographs better than a curtain wall.
                wide = bay % 5 == 0
                win_w = 2.02 if wide else 1.54
                panel(edge, t, y, win_w + .23, 1.88, mats['frame'], .145)
                panel(edge, t, y, win_w, 1.64,
                      mats['glass'] if (bay * 13 + floor * 7) % 9 else mats['curtain'], .16)
                panel(edge, t, y, .055, 1.62, mats['mullion'], .185)
                panel(edge, t, y - .23, win_w, .045, mats['mullion'], .19)
                panel(edge, t, y - .98, win_w + .30, .10, mats['sill'], .16)
                if wide:
                    for side in (-1, 1):
                        panel(edge, t + side * (win_w / 2 + .04) / length, y,
                              .10, 2.06, mats['bay_edge'], .22)
                if floor < 2 and bay % 3 == 0:
                    for k in range(-2, 3):
                        panel(edge, t + k * (win_w / 6) / length, y,
                              .025, 1.74, mats['grille'], .24)
                    for dy in (-.52, .52):
                        panel(edge, t, y + dy, win_w + .08, .025, mats['grille'], .25)
                if floor > 0 and (bay + 2 * floor) % 3 == 1:
                    ac_t = t + (win_w / 2 + .38) / length
                    panel(edge, ac_t, y - .32, .72, .58, mats['ac'], .29)
                    for dy in (-.16, -.055, .05, .155):
                        panel(edge, ac_t, y - .32 + dy, .53, .022, mats['ac_vent'], .32)
        for bay in range(0, bays, 6):
            panel(edge, (bay + .1) / bays, h / 2, .07, h - .6, mats['pipe'], .22)

    # Two restrained roof service elements, visible from the overview camera.
    mesh.box(x - w * .20, z, h + 1.12, 2.5, 2.2, 1.55, mats['wall'])
    mesh.box(x - w * .20, z, h + 1.94, 2.9, 2.6, .15, mats['roof'])
    mesh.box(x + w * .24, z, h + .64, 1.3, 1.3, .9, mats['coping'])
