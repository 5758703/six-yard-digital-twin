"""Shared factory entrance and precinct boundary geometry (X east, Z south)."""
import math


def build_factory(mesh, building, mats):
    x, z = building['x'], building['z']
    w, d, h = building['w'], building['d'], building['height']
    wall_top = h * .72
    eave = wall_top + .18
    rise = h * .33
    mesh.box(x, z, .18, w + .25, d + .25, .36, mats['concrete'])
    mesh.box(x, z, wall_top / 2, w, d, wall_top, mats['factory_wall'])
    # Fine panel joints and irregular vertical staining seen on the east wall.
    for zz in range(math.ceil(z - d / 2 + 4), math.floor(z + d / 2), 4):
        for sign in (-1, 1):
            wall_x = x + sign * (w / 2 + .014)
            mesh.box(wall_x, zz, wall_top / 2, .025, .025, wall_top - .12, mats['factory_joint'])
        if zz % 3 == 0:
            mesh.box(x + w / 2 + .023, zz + .35, 2.4, .015, .34, 3.7, mats['factory_stain'])
    for yy in (2.15, 4.35):
        mesh.box(x + w / 2 + .018, z, yy, .025, d, .025, mats['factory_joint'])
    mesh.box(x + w / 2 + .07, z, .48, .10, d, .52, mats['factory_stain'])
    mesh.box(x + w / 2 + .10, z, wall_top - .06, .2, d + .4, .22, mats['factory_trim'])
    mesh.box(x - w / 2 - .10, z, wall_top - .06, .2, d + .4, .22, mats['factory_trim'])

    # Corrugated, barrel-vaulted roof: arch across the short span, ribs run north-south.
    roof_w, roof_d = w + .8, d + .8
    segments = 32
    def roof_y(t):
        return eave + rise * (1 - (2 * t - 1) ** 2)
    for i in range(segments):
        t0, t1 = i / segments, (i + 1) / segments
        xa, xb = x - roof_w / 2 + roof_w * t0, x - roof_w / 2 + roof_w * t1
        ya, yb = roof_y(t0), roof_y(t1)
        mesh.shape([(xa, ya, z - roof_d / 2), (xb, yb, z - roof_d / 2),
                    (xb, yb, z + roof_d / 2), (xa, ya, z + roof_d / 2)],
                   [(3, 2, 1, 0)], mats['factory_roof'])
    for i in range(1, segments):
        t = i / segments
        xx = x - roof_w / 2 + roof_w * t
        mesh.box(xx, z, roof_y(t) + .035, .055, roof_d, .07,
                 mats['factory_roof_rib'])
    for end in (-1, 1):
        zz = z + end * (roof_d / 2)
        for i in range(segments):
            t0, t1 = i / segments, (i + 1) / segments
            xa, xb = x - roof_w / 2 + roof_w * t0, x - roof_w / 2 + roof_w * t1
            mesh.shape([(xa, eave - .16, zz), (xb, eave - .16, zz),
                        (xb, roof_y(t1), zz), (xa, roof_y(t0), zz)],
                       [(0, 1, 2, 3) if end == 1 else (3, 2, 1, 0)], mats['factory_roof'])

    east_x = x + w / 2
    for index, door_z in enumerate(building['eastDoors']):
        mesh.box(east_x + .08, door_z, 1.65, .16, 1.65, 3.04, mats['factory_trim'])
        mesh.box(east_x + .18, door_z, 1.62, .06, 1.38, 2.84, mats['factory_door'])
        mesh.box(east_x + .225, door_z + .47, 1.62, .025, .055, 2.1, mats['factory_joint'])
        mesh.box(east_x + .25, door_z + .43, 1.25, .07, .06, .12, mats['steel'])
        mesh.box(east_x + .2, door_z, 3.26, .12, 2.15, .12, mats['factory_trim'])
        mesh.box(east_x + 1.2, door_z, .22, 2.1, 2.2, .15, mats['concrete'])
    door_positions = building['eastDoors']
    for i, zz in enumerate(range(math.ceil(z - d / 2 + 3), math.floor(z + d / 2 - 1), 4)):
        if min(abs(zz - door_z) for door_z in door_positions) < 2.6:
            continue
        mesh.box(east_x + .08, zz, 3.7, .12, 1.65, 2.0, mats['frame'])
        mesh.box(east_x + .16, zz, 3.7, .05, 1.47, 1.83, mats['glass'])
        mesh.box(east_x + .2, zz, 3.7, .035, .06, 1.85, mats['frame'])
        mesh.box(east_x + .2, zz, 3.68, .035, 1.46, .06, mats['frame'])
        if i % 2 == 0:
            mesh.box(east_x + .18, zz - 1.5, 3.28, .06, .9, 1.25, mats['factory_sign'])
        else:
            mesh.box(east_x + .27, zz - 1.35, 5.3, .42, .7, .38, mats['steel'])
            mesh.box(east_x + .18, zz + 1.5, 1.05, .4, .72, .54, mats['frame'])
    # Simple dark high windows on the end walls.
    for end in (-1, 1):
        for xx in (x - w * .28, x, x + w * .28):
            mesh.box(xx, z + end * (d / 2 + .06), 4.2, 1.1, .1, 1.55, mats['glass'])


def build_factory_courtyard(mesh, feature, mats):
    """Photo-guided hardstand, badminton markings, portable cabins and crate stacks."""
    west, east, north, south = (feature[key] for key in ('west', 'east', 'north', 'south'))
    mesh.box((west + east) / 2, (north + south) / 2, .235,
             east - west, south - north, .07, mats['concrete'])
    # Large, slightly varied concrete slabs with thin expansion joints.
    for zz in range(math.ceil(north / 8) * 8, math.floor(south / 8) * 8 + 1, 8):
        mesh.box((west + east) / 2, zz, .276, east - west, .035, .014, mats['factory_joint'])
    for xx in (west + 7.4, west + 14.8):
        mesh.box(xx, (north + south) / 2, .276, .035, south - north, .014, mats['factory_joint'])

    def court(cx, cz):
        width, length = 6.1, 13.4
        for xx in (cx - width / 2, cx + width / 2):
            mesh.box(xx, cz, .29, .055, length, .014, mats['court_line'])
        for zz in (cz - length / 2, cz, cz + length / 2):
            mesh.box(cx, zz, .29, width, .055, .014, mats['court_line'])
        for zz in (cz - 2, cz + 2):
            mesh.box(cx, zz, .29, width, .045, .014, mats['court_line'])
        mesh.box(cx, cz, .29, .045, length, .014, mats['court_line'])

    for cz in feature['badmintonCourtCenters']:
        court(feature['badmintonCourtX'], cz)

    def cabin(cx, cz, green_roof=False):
        width, length = 5.55, 7.25
        mesh.box(cx, cz, 1.55, width, length, 2.55, mats['cabin_white'])
        if green_roof:
            awning_width, awning_length = width + .55, length + .9
            for i in range(12):
                def canopy_point(t, end_z):
                    return (cx - awning_width / 2 + awning_width * t,
                            2.94 + .48 * (1 - (2 * t - 1) ** 2), end_z)
                a, b = i / 12, (i + 1) / 12
                mesh.shape([canopy_point(a, cz - awning_length / 2),
                            canopy_point(b, cz - awning_length / 2),
                            canopy_point(b, cz + awning_length / 2),
                            canopy_point(a, cz + awning_length / 2)],
                           [(3, 2, 1, 0)], mats['canopy_green'])
            for i in range(1, 12, 2):
                t = i / 12
                mesh.box(cx - awning_width / 2 + awning_width * t, cz,
                         3.0 + .48 * (1 - (2 * t - 1) ** 2), .045, awning_length, .04,
                         mats['factory_joint'])
        else:
            mesh.box(cx, cz, 2.89, width + .26, length + .23, .14, mats['cabin_roof'])
        for end in (-1, 1):
            face = cz + end * (length / 2 + .045)
            mesh.box(cx - 1.1, face, 1.75, .95, .06, .77, mats['glass'])
            mesh.box(cx + 1.25, face, 1.46, 1.05, .065, 2.0, mats['cabin_roof'])
            mesh.box(cx + 1.25, face + end * .055, 1.98, .45, .02, .40, mats['glass'])
            mesh.box(cx + 1.25, face + end * .57, .29, 1.3, .9, .12, mats['concrete'])
        for offset in (-1.65, 1.65):
            mesh.box(cx + width / 2 + .045, cz + offset, 1.77, .06, 1.12, .85, mats['glass'])
        for zz in (cz - length / 2 + .4, cz + length / 2 - .4):
            mesh.box(cx, zz, 2.86, width + .26, .05, .07, mats['factory_joint'])

    for i, cz in enumerate(feature['cabinCenters']):
        # The green shelters sit beyond the nearer white cabins in the north-to-south photo.
        cabin(feature['cabinX'], cz,
              i >= len(feature['cabinCenters']) - feature['greenCanopyCount'])
    for item in feature['crateStacks']:
        cx, cz, columns, rows = (item[key] for key in ('x', 'z', 'columns', 'rows'))
        for col in range(columns):
            for row in range(rows):
                xx, zz = cx + col * .67, cz + row * .72
                for tier in range(item['height']):
                    bottom = .31 + tier * .38
                    mesh.box(xx, zz, bottom + .18, .56, .60, .36, mats['crate_blue'])
                    mesh.box(xx, zz, bottom + .36, .59, .63, .045, mats['crate_rim'])
                    for side in (-1, 1):
                        mesh.box(xx + side * .287, zz, bottom + .19,
                                 .012, .43, .11, mats['crate_shadow'])
                    mesh.box(xx, zz + .307, bottom + .19,
                             .40, .012, .11, mats['crate_shadow'])


def build_independent_boundary(mesh, boundary, mats):
    west, east = boundary['west'], boundary['east']
    north, south = boundary['north'], boundary['south']

    def segment(a, b, fixed, horizontal):
        if b - a < .2:
            return
        center = (a + b) / 2
        if horizontal:
            mesh.box(center, fixed, .48, b - a, .28, .96, mats['concrete'])
            for height in (1.24, 1.82):
                mesh.box(center, fixed, height, b - a, .09, .07, mats['steel'])
            for offset in range(math.ceil((b - a) / 3) + 1):
                xx = a + min(offset * 3, b - a)
                mesh.box(xx, fixed, 1.5, .12, .12, 1.15, mats['steel'])
        else:
            mesh.box(fixed, center, .48, .28, b - a, .96, mats['concrete'])
            for height in (1.24, 1.82):
                mesh.box(fixed, center, height, .09, b - a, .07, mats['steel'])
            for offset in range(math.ceil((b - a) / 3) + 1):
                zz = a + min(offset * 3, b - a)
                mesh.box(fixed, zz, 1.5, .12, .12, 1.15, mats['steel'])

    for side, z in (('north', north), ('south', south)):
        openings = sorted((gate['x'] - gate['width'] / 2, gate['x'] + gate['width'] / 2)
                          for gate in boundary['gates'] if gate['side'] == side)
        cursor = west
        for start, end in openings:
            segment(cursor, start, z, True)
            for xx in (start, end):
                mesh.box(xx, z, 1.25, .72, .72, 2.5, mats['ivory'])
                mesh.box(xx, z, 2.55, .88, .88, .18, mats['steel'])
            cursor = end
        segment(cursor, east, z, True)
    segment(north, south, west, False)
    segment(north, south, east, False)


def build_service_lane(mesh, road, mats):
    x = road['points'][0][0]
    north, south = sorted((road['points'][0][1], road['points'][-1][1]))
    # The photo shows a continuous concrete hardstand, not an asphalt road.
    mesh.box(x, (north + south) / 2, .215, road['width'], south - north, .05, mats['concrete'])


def build_factory_yard_gate(mesh, gate, mats):
    """South-west opening into the yard shared with the equipment building."""
    z = gate['z']
    opening_west = gate['x'] - gate['width'] / 2
    opening_east = gate['x'] + gate['width'] / 2
    for west, east in ((21.5, opening_west), (opening_east, 68)):
        middle = (west + east) / 2
        mesh.box(middle, z, .48, east - west, .28, .96, mats['concrete'])
        for height in (1.24, 1.82):
            mesh.box(middle, z, height, east - west, .09, .07, mats['steel'])
        for xx in (west, east):
            mesh.box(xx, z, 1.48, .12, .12, 1.12, mats['steel'])
    for xx in (opening_west, opening_east):
        mesh.box(xx, z, 1.25, .72, .72, 2.5, mats['ivory'])
        mesh.box(xx, z, 2.55, .88, .88, .18, mats['steel'])


def build_yard_connector(mesh, road, mats):
    for (ax, az), (bx, bz) in zip(road['points'], road['points'][1:]):
        if ax == bx:
            center_z = (az + bz) / 2
            mesh.box(ax, center_z, .17, road['width'] + 2, abs(az - bz), .06, mats['concrete'])
            mesh.box(ax, center_z, .225, road['width'], abs(az - bz), .05, mats['concrete'])
        elif az == bz:
            center_x = (ax + bx) / 2
            mesh.box(center_x, az, .17, abs(ax - bx), road['width'] + 2, .06, mats['concrete'])
            mesh.box(center_x, az, .225, abs(ax - bx), road['width'], .05, mats['concrete'])
        else:
            raise ValueError('The yard connector must use axis-aligned segments')


def build_north_walkway(mesh, road, mats):
    x = road['points'][0][0]
    north, south = sorted((road['points'][0][1], road['points'][-1][1]))
    mesh.box(x, (north + south) / 2, .2, road['width'], south - north, .07, mats['concrete'])
    for z in range(math.ceil(north / 8) * 8, math.floor(south / 8) * 8, 8):
        mesh.box(x, z, .245, road['width'], .04, .015, mats['line'])


def cover_old_yard_overlap(mesh, mats):
    # The older GLB's bare-ground pocket extended into the independent office.
    mesh.box(14.75, 198, .205, 13.5, 50, .035, mats['grass'])
