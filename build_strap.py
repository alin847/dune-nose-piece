"""Build the flat-print TPU cheek strap and open ear hook, plus a STEP assembly.

The flexible strap is exported in its relaxed, flat manufacturing shape.
Its socket fits the existing nose piece. It bends to follow the face when worn.
"""
from pathlib import Path
import json
import math
import cadquery as cq
import trimesh
from build_model import build as build_nose, export_and_check

ROOT = Path(__file__).resolve().parent


def build_strap(s, reach):
    r = s['strap_radius_mm']
    z = s['strap_center_height_mm']
    rise = s['hook_entry_rise_mm']
    hook_r = s['hook_centerline_radius_mm']
    length = s['socket_length_mm']
    sr = s['socket_outer_radius_mm']
    bore_r = s['socket_bore_diameter_mm'] / 2
    assert hook_r > 2*r and sr > bore_r and reach > 60
    assert 0 < s['socket_bore_depth_mm'] < length
    # Negative local Y turns the cheek arm toward the back of the head after
    # alignment to the left-facing nose spigot. Z is the print thickness.
    points = [(length-1.5, 0, z), (.30*reach, -.017*rise, z),
              (.55*reach, -.12*rise, z), (.78*reach, -.38*rise, z),
              (.93*reach, -.71*rise, z), (reach, -rise, z)]
    cheek = cq.Edge.makeSpline([cq.Vector(*pt) for pt in points],
                              tangents=[cq.Vector(1, 0, 0), cq.Vector(0, -1, 0)])
    hook = cq.Edge.makeThreePointArc(cq.Vector(reach, -rise, z),
                                    cq.Vector(reach+hook_r, -rise-hook_r, z),
                                    cq.Vector(reach+2*hook_r, -rise, z))
    tip = cq.Vector(reach+2*hook_r, -rise+s['hook_return_length_mm'], z)
    tail = cq.Edge.makeLine(cq.Vector(reach+2*hook_r, -rise, z), tip)
    path = cq.Wire.assembleEdges([cheek, hook, tail])
    section = cq.Plane(origin=points[0], xDir=(0, 0, 1), normal=(1, 0, 0))
    arm = cq.Workplane(section).circle(r).sweep(path, isFrenet=False).val()
    cap = cq.Solid.makeSphere(r, tip, angleDegrees1=-90, angleDegrees2=90)
    arm = arm.fuse(cap)
    # A socket with a 2 mm solid end wall. The bore is cut after union, so the
    # strap root cannot block the opening. The nose barb stretches the TPU bore.
    socket = cq.Solid.makeCylinder(sr, length, cq.Vector(0, 0, sr), cq.Vector(1, 0, 0))
    body = arm.fuse(socket)
    bore = cq.Solid.makeCylinder(bore_r, s['socket_bore_depth_mm']+.5,
                                cq.Vector(-.5, 0, sr), cq.Vector(1, 0, 0))
    # Small lead-in chamfer molded into the opening.
    mouth = cq.Solid.makeCone(bore_r+.25, bore_r, .6,
                             cq.Vector(0, 0, sr), cq.Vector(1, 0, 0))
    body = body.cut(bore).cut(mouth)
    upper = cq.Workplane('XY').box(500, 500, 100,
                                   centered=(True, True, False)).val()
    body = body.intersect(upper).clean()
    return body, {
        'material_intent': 'flexible TPU',
        'configuration': 'relaxed flat printing shape',
        'cheek_reach_mm': reach,
        'hook_inner_width_mm': 2*(hook_r-r),
        'strap_nominal_width_mm': 2*r,
        'strap_flat_height_mm': z+r,
        'socket_bore_diameter_mm': 2*bore_r,
        'socket_bore_depth_mm': s['socket_bore_depth_mm'],
        'centerline_length_mm': path.Length()
    }


def main():
    p = json.loads((ROOT / 'parameters.json').read_text())
    s = json.loads((ROOT / 'strap_parameters.json').read_text())
    results = []
    standard = None
    for name, reach in [('dune_ear_strap_TPU', s['cheek_reach_mm']),
                        ('dune_ear_strap_TPU_short', s['short_cheek_reach_mm']),
                        ('dune_ear_strap_TPU_long', s['long_cheek_reach_mm'])]:
        shape, details = build_strap(s, reach)
        results.append(export_and_check(shape, name, p, details))
        if name == 'dune_ear_strap_TPU':
            standard = shape
    nose, _ = build_nose(p, p['default_spacing_mm'])
    half, bow = p['bar_half_span_mm'], p['bar_plan_bow_mm']
    cr = (half*half+bow*bow)/(2*bow)
    direction = cq.Vector(-(cr-bow), half, 0).normalized()
    angle = math.degrees(math.atan2(direction.y, direction.x))
    tip = cq.Vector(-half, bow, p['hose_spigot_radius_mm']) + direction*p['hose_spigot_length_mm']
    opening = tip - direction*s['nose_spigot_insertion_mm']
    shift = opening - cq.Vector(0, 0, s['socket_outer_radius_mm'])
    loc = cq.Location(shift, cq.Vector(0, 0, 1), angle)
    assembly = cq.Assembly(name='Dune costume - nose and TPU ear strap')
    assembly.add(nose, name='nose_piece', color=cq.Color(.18, .20, .22))
    assembly.add(standard, name='TPU_cheek_strap_and_ear_hook', loc=loc,
                 color=cq.Color(.08, .09, .10))
    file = ROOT / 'output/dune_complete_assembly.step'
    assembly.export(str(file))
    restored = cq.importers.importStep(str(file)).val()
    assert restored.isValid() and len(restored.Solids()) == 2
    expected = nose.Volume()+standard.Volume()
    # Sum component volumes: compound-level OCCT integration can use a looser
    # shared tolerance for transformed B-spline surfaces than each solid does.
    restored_volume = sum(part.Volume() for part in restored.Solids())
    relative_volume_error = abs(restored_volume-expected)/expected
    assert relative_volume_error < 1e-6
    # Check the actual engagement: modest overlap is the intentional TPU barb
    # interference, and the parts must meet rather than float apart.
    placed = standard.moved(loc)
    interference = nose.intersect(placed).Volume()
    assert 0 < interference < 8, f'Unexpected socket fit: {interference} mm3'
    bounds = cq.Compound.makeCompound([nose, placed]).BoundingBox()
    report = {
        'parts': results,
        'assembly': {'step': file.name, 'valid': True, 'solid_count': 2,
                     'configuration': 'relaxed flat strap fitted onto nose spigot',
                     'barb_interference_volume_mm3': interference,
                     'step_relative_component_volume_error': relative_volume_error,
                     'spigot_insertion_mm': s['nose_spigot_insertion_mm'],
                     'bounds_xyz_mm': [bounds.xlen, bounds.ylen, bounds.zlen],
                     'strap_rotation_z_degrees': angle,
                     'strap_translation_xyz_mm': shift.toTuple()}
    }
    (ROOT / 'output/strap_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    # Separate bodies laid on the bed: a convenience STL for viewing/slicing.
    # Only use one material for both if deliberately choosing a TPU nose piece.
    strap_mesh = trimesh.load_mesh(ROOT / 'output/dune_ear_strap_TPU.stl')
    nose_mesh = trimesh.load_mesh(ROOT / 'output/dune_nose_piece.stl')
    nose_mesh.apply_translation([25, 14, 0])
    plate = trimesh.util.concatenate([strap_mesh, nose_mesh])
    plate_path = ROOT / 'output/dune_complete_print_layout.stl'
    plate.export(plate_path)
    reloaded = trimesh.load_mesh(plate_path)
    assert reloaded.is_watertight and len(reloaded.split()) == 2
    print(f'Assembly: two valid STEP solids, socket interference {interference:.3f} mm3')
    print('Print layout: two separate watertight parts, both on Z=0')


if __name__ == '__main__':
    main()
