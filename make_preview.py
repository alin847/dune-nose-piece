"""Render the exported STL, so the previews show the actual delivered geometry."""
from pathlib import Path
import json
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parent
mesh = trimesh.load_mesh(ROOT / 'output/dune_nose_piece.stl')
report = json.loads((ROOT / 'output/validation.json').read_text())[0]
p = json.loads((ROOT / 'parameters.json').read_text())
bg = '#f5f1e9'
ink = '#272b30'
accent = '#946a3c'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': ink,
                     'axes.labelcolor': ink, 'font.size': 11})
normals = mesh.face_normals
light = np.array([-0.3, -0.6, 1.0]); light /= np.linalg.norm(light)
brightness = 0.33 + 0.67 * np.clip(normals @ light, 0, 1)
colors = np.column_stack([0.20 + brightness * 0.29,
                          0.23 + brightness * 0.29,
                          0.26 + brightness * 0.29,
                          np.ones(len(brightness))])
bounds = mesh.bounds
center = bounds.mean(axis=0)
extent = np.maximum(mesh.extents, [0, 8, 10])


def view(ax, elev, azim, title):
    ax.add_collection3d(Poly3DCollection(mesh.triangles, facecolors=colors,
                                        edgecolors='none', linewidths=0,
                                        antialiased=False))
    for i, setter in enumerate([ax.set_xlim, ax.set_ylim, ax.set_zlim]):
        setter(center[i] - extent[i] * .55, center[i] + extent[i] * .55)
    ax.set_box_aspect(extent.copy())
    ax.set_proj_type('ortho')
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor(bg)
    ax.set_title(title, loc='left', fontsize=12, color=accent, pad=-10)


fig = plt.figure(figsize=(12, 7), facecolor=bg)
fig.text(.055, .935, 'DUNE / NOSE PIECE', fontsize=23, weight='bold')
fig.text(.055, .889, 'Costume prop  /  Reference-inspired CAD  /  Dimensions in mm',
         fontsize=11, color=accent)
ax = fig.add_axes([.02, .14, .96, .73], projection='3d')
view(ax, 23, -66, '')
x, y, z = report['bounds_xyz_mm']
fig.text(.055, .12, f'{x:.1f} W  ×  {y:.1f} D  ×  {z:.1f} H',
         fontsize=16, weight='bold')
fig.text(.055, .073, f'Prong spacing {p["default_spacing_mm"]:g}   •   '
         f'Prong diameter {2*p["prong_radius_mm"]:g}   •   Flat print base at Z = 0',
         fontsize=11)
fig.savefig(ROOT / 'previews/model_preview.png', dpi=180, facecolor=bg)
plt.close(fig)

fig = plt.figure(figsize=(12, 9), facecolor=bg)
fig.text(.06, .94, 'DUNE / FIT & PRINT REFERENCE', fontsize=21, weight='bold')
fig.text(.06, .90, 'All dimensions in mm. Views are not printed to scale.', color=accent)
def orthographic(ax, coords, depth_axis, sign, title):
    order = np.argsort(sign * mesh.triangles_center[:, depth_axis])
    polygons = mesh.triangles[order][:, :, list(coords)]
    ax.add_collection(PolyCollection(polygons, facecolors=colors[order],
                                     edgecolors='none', antialiased=False,
                                     rasterized=True))
    ax.set_xlim(bounds[0, coords[0]] - 3, bounds[1, coords[0]] + 3)
    ax.set_ylim(bounds[0, coords[1]] - 3.5, bounds[1, coords[1]] + 4)
    ax.set_aspect('equal')
    ax.set_axis_off()
    ax.set_title(title, loc='left', color=accent, fontsize=12)

def dimension(ax, a, b, label, offset=(0, .5)):
    ax.annotate('', xy=b, xytext=a,
                arrowprops={'arrowstyle': '|-|', 'color': accent, 'lw': .9})
    ax.text((a[0]+b[0])/2+offset[0], (a[1]+b[1])/2+offset[1], label,
            color=accent, ha='center', va='bottom', fontsize=10)

front = fig.add_axes([.06, .51, .58, .34])
orthographic(front, (0, 2), 1, -1, 'FRONT')
dimension(front, (bounds[0,0], -2), (bounds[1,0], -2), f'{x:.2f}')
s = p['default_spacing_mm'] / 2
dimension(front, (-s, 10.5), (s, 10.5), f'{2*s:g} centers')
top = fig.add_axes([.06, .25, .58, .20])
orthographic(top, (0, 1), 2, 1, 'TOP / FACE IS TOWARD +Y')
side = fig.add_axes([.71, .55, .23, .28])
orthographic(side, (1, 2), 0, 1, 'SIDE')
notes = [
    f'Overall width: {x:.2f}', f'Overall depth: {y:.2f}', f'Overall height: {z:.2f}',
    f'Prong center spacing: {p["default_spacing_mm"]:g}',
    f'Prong diameter: {2*p["prong_radius_mm"]:.1f}',
    f'Bridge diameter: {2*p["bar_radius_mm"]:.1f}',
    f'Hose spigot: Ø{2*p["hose_spigot_radius_mm"]:.1f}',
    f'Barb maximum: Ø{2*p["hose_barb_radius_mm"]:.1f}',
    'Fit variants: 14 / 16 / 18 spacing',
]
fig.text(.70, .48, '\n'.join(notes), va='top', fontsize=11, linespacing=1.75)
fig.text(.06, .14, 'PRINT: flat underside on the bed; prongs point upward. Slice at 100% scale.',
         fontsize=11, weight='bold')
fig.text(.06, .095, 'Use the included TPU cheek strap and ear hook. This sheet shows only the nose fitting.\n'
         'Fit is estimated from a single photo; check before finishing. Wear externally below the nostrils.',
         fontsize=10, linespacing=1.6)
fig.savefig(ROOT / 'previews/fit_reference.png', dpi=160, facecolor=bg)
fig.savefig(ROOT / 'previews/fit_reference.pdf', facecolor=bg)
plt.close(fig)
print('Rendered model_preview.png and fit_reference.png/pdf from exported STL.')
