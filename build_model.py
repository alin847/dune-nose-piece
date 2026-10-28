"""Build an original, reference-inspired costume nose piece in millimeters.

Run: .venv/bin/python build_model.py
Editable parameters: parameters.json. STEP output is analytic B-rep geometry.
X = left/right; +Y = toward the face; +Z = up toward the nose.
The underside is on Z=0, ready for slicing without a rotation.
"""
from pathlib import Path
import json
import math
import argparse
import cadquery as cq
import trimesh

ROOT = Path(__file__).resolve().parent


def build(p, spacing):
    half = p['bar_half_span_mm']
    bow = p['bar_plan_bow_mm']
    radius = p['bar_radius_mm']
    z = p['bar_center_height_mm']
    if not 0 < spacing < 2 * (half - p['prong_radius_mm']):
        raise ValueError('Prong spacing is outside the bar. Increase bar_half_span_mm.')
    if not 0 < bow < half:
        raise ValueError('bar_plan_bow_mm must be positive and less than the half span.')
    curve_radius = (half * half + bow * bow) / (2 * bow)
    start = cq.Vector(-half, bow, z)
    end = cq.Vector(half, bow, z)
    arc = cq.Edge.makeThreePointArc(start, cq.Vector(0, 0, z), end)
    path = cq.Wire.assembleEdges([arc])
    tangent = cq.Vector(curve_radius - bow, -half, 0).normalized()
    section = cq.Plane(origin=start, xDir=(0, 0, 1), normal=tangent)
    body = cq.Workplane(section).circle(radius).sweep(path, isFrenet=True).val()
    # Full spheres (CadQuery's low-level sphere default is a hemisphere).
    def sphere(r, center):
        return cq.Solid.makeSphere(r, center, angleDegrees1=-90, angleDegrees2=90)
    body = body.fuse(sphere(radius, start), sphere(radius, end))
    roots, tips = [], []
    for sign in (-1, 1):
        x = sign * spacing / 2
        y = curve_radius - math.sqrt(curve_radius**2 - x**2)
        root = cq.Vector(x, y, p['prong_root_height_mm'])
        direction = cq.Vector(sign * p['prong_outward_lean'],
                              p['prong_rearward_lean'], 1).normalized()
        length = p['prong_stem_length_mm']
        tip = root + direction * length
        post = cq.Solid.makeCylinder(p['prong_radius_mm'], length, root, direction)
        post = post.fuse(sphere(p['prong_radius_mm'], tip))
        body = body.fuse(post)
        roots.append(root.toTuple())
        tips.append(tip.toTuple())
    # Solid decorative hose spigot: nominal 2.5 mm ID flexible tube.
    # The barb and end taper are small enough to preserve the reference silhouette.
    outward = tangent * -1
    base = cq.Vector(-half, bow, p['hose_spigot_radius_mm'])
    length = p['hose_spigot_length_mm']
    r = p['hose_spigot_radius_mm']
    if length < 4:
        raise ValueError('hose_spigot_length_mm must be at least 4 mm.')
    connector = cq.Solid.makeCylinder(r, length - 1.0, base, outward)
    connector = connector.fuse(cq.Solid.makeCone(
        p['hose_barb_radius_mm'], r * 0.88, 1.5,
        base + outward * (length - 1.5), outward))
    body = body.fuse(connector).clean()
    # A flat bed contact on the curved bar and barb, with all tips left rounded.
    upper_halfspace = cq.Workplane('XY').box(200, 200, 100,
                                            centered=(True, True, False)).val()
    body = body.intersect(upper_halfspace).clean()
    return body, {'prong_root_centers_mm': roots, 'prong_tip_centers_mm': tips,
                  'prong_root_spacing_mm': spacing,
                  'prong_tip_spacing_mm': tips[1][0] - tips[0][0]}


def export_and_check(shape, stem, p, details):
    output = ROOT / 'output'
    output.mkdir(exist_ok=True)
    step_path, stl_path = output / f'{stem}.step', output / f'{stem}.stl'
    assert shape.isValid(), f'{stem}: invalid CAD geometry'
    assert len(shape.Solids()) == 1, f'{stem}: expected one connected solid'
    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(shape, str(stl_path),
                        tolerance=p['stl_linear_tolerance_mm'],
                        angularTolerance=p['stl_angular_tolerance_radians'])
    # Verify the delivered files, not just the in-memory model.
    restored = cq.importers.importStep(str(step_path)).val()
    assert restored.isValid() and len(restored.Solids()) == 1
    error = abs(restored.Volume() - shape.Volume()) / shape.Volume()
    assert error < 1e-6, 'STEP round-trip volume mismatch'
    mesh = trimesh.load_mesh(str(stl_path))
    # OCCT can emit zero-area triangles at spherical poles. Weld at 0.000001 mm
    # and discard those triangles; this does not change the analytic STEP solid.
    mesh.merge_vertices(digits_vertex=6)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    mesh.export(str(stl_path))
    mesh = trimesh.load_mesh(str(stl_path))
    assert mesh.is_watertight, f'{stem}: STL is not watertight'
    assert mesh.is_winding_consistent and mesh.volume > 0
    assert len(mesh.split()) == 1, f'{stem}: disconnected STL'
    b = shape.BoundingBox()
    result = {
        'name': stem, 'units': 'mm', **details,
        'bounds_xyz_mm': [b.xlen, b.ylen, b.zlen],
        'min_z_mm': b.zmin, 'volume_mm3': shape.Volume(),
        'cad_valid': True, 'cad_solids': 1,
        'step_round_trip_valid': True, 'step_relative_volume_error': error,
        'stl_watertight': bool(mesh.is_watertight),
        'stl_winding_consistent': bool(mesh.is_winding_consistent),
        'stl_connected_components': 1, 'stl_triangles': len(mesh.faces)
    }
    print(f'{stem}: valid STEP, watertight STL; '
          f'{b.xlen:.2f} x {b.ylen:.2f} x {b.zlen:.2f} mm')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spacing', type=float, help='Export one custom root spacing in mm')
    args = parser.parse_args()
    p = json.loads((ROOT / 'parameters.json').read_text())
    results = []
    spacings = ([args.spacing] if args.spacing is not None else
                [p['default_spacing_mm'], *p['fit_variant_spacing_mm']])
    for spacing in spacings:
        shape, details = build(p, spacing)
        if args.spacing is None and spacing == p['default_spacing_mm']:
            stem = 'dune_nose_piece'
        else:
            stem = f'dune_nose_piece_spacing_{spacing:g}mm'
        results.append(export_and_check(shape, stem, p, details))
    report = 'validation.json' if args.spacing is None else 'validation_custom.json'
    (ROOT / 'output' / report).write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
