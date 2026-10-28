"""Preview the full assembly and flat TPU strap from the validated meshes."""
from pathlib import Path
import json
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT = Path(__file__).resolve().parent
info = json.loads((ROOT/'output/strap_validation.json').read_text())
s = json.loads((ROOT/'strap_parameters.json').read_text())
bg, ink, accent = '#f5f1e9', '#272b30', '#946a3c'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': ink, 'font.size': 11})
strap = trimesh.load_mesh(ROOT/'output/dune_ear_strap_TPU.stl')
nose = trimesh.load_mesh(ROOT/'output/dune_nose_piece.stl')
assembled = strap.copy()
transform = trimesh.transformations.rotation_matrix(
    np.radians(info['assembly']['strap_rotation_z_degrees']), [0, 0, 1])
transform[:3,3] = info['assembly']['strap_translation_xyz_mm']
assembled.apply_transform(transform)
kit = trimesh.util.concatenate([nose, assembled])


def render(ax, mesh, tilt=0):
    rotation = trimesh.transformations.rotation_matrix(np.radians(tilt), [1, 0, 0])
    m = mesh.copy(); m.apply_transform(rotation)
    order = np.argsort(m.triangles_center[:,2])
    light = np.array([-.4, .4, 1]); light /= np.linalg.norm(light)
    shade = .20 + .32 * np.clip(m.face_normals @ light, 0, 1)
    colors = np.column_stack([shade*.86, shade*.94, shade, np.ones(len(shade))])
    ax.add_collection(PolyCollection(m.triangles[order,:,:2], facecolors=colors[order],
                                     edgecolors='none', antialiased=False,
                                     rasterized=True))
    ax.set_aspect('equal'); ax.set_facecolor(bg); ax.set_axis_off()
    ax.set_xlim(m.bounds[0,0]-8, m.bounds[1,0]+8)
    ax.set_ylim(m.bounds[0,1]-8, m.bounds[1,1]+8)
    return m


fig = plt.figure(figsize=(12, 9), facecolor=bg)
fig.text(.055, .94, 'DUNE / COMPLETE NOSE & EAR PIECE', fontsize=22, weight='bold')
fig.text(.055, .897, 'Nose fitting + printable TPU cheek strap + open ear hook', color=accent)
ax = fig.add_axes([.04, .22, .92, .64])
render(ax, kit, tilt=-22)
fig.text(.36, .80, 'OPEN EAR HOOK', color=accent, fontsize=11, weight='bold')
fig.text(.36, .77, 'Rounded return tip\n16.4 mm inner width', fontsize=10,
         linespacing=1.6, va='top')
fig.text(.48, .60, 'FLEXIBLE TPU STRAP', color=accent, fontsize=11, weight='bold')
fig.text(.48, .565, 'Prints flat; bends around the cheek', fontsize=10)
fig.text(.70, .40, 'NOSE FITTING', color=accent, fontsize=11, weight='bold')
fig.text(.70, .365, 'Push-fit socket connection', fontsize=10)
fig.text(.055, .15, 'ASSEMBLED STEP  +  SEPARATE PRINTABLE PARTS', fontsize=14, weight='bold')
fig.text(.055, .12, 'Shown in the relaxed flat-strap configuration, not fitted to a face.\n'
         'Short / standard / long cheek reaches: 90 / 100 / 110 mm. Fit remains untested.',
         fontsize=11, linespacing=1.6, va='top')
fig.savefig(ROOT/'previews/complete_assembly.png', dpi=170, facecolor=bg)
plt.close(fig)

fig = plt.figure(figsize=(12, 8), facecolor=bg)
fig.text(.055, .94, 'DUNE / TPU EAR STRAP', fontsize=23, weight='bold')
fig.text(.055, .89, 'Flat print orientation  /  All dimensions in mm', color=accent)
# Mirror Y only for a readable top view with the hook above the attachment.
flat = strap.copy()
flat.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1,0,0]))
ax = fig.add_axes([.05, .23, .66, .61])
render(ax, flat)
ax.annotate('Open hook', xy=(120,43), xytext=(62,45), color=accent,
            arrowprops={'arrowstyle':'->', 'color':accent}, fontsize=10)
ax.annotate('Socket opening', xy=(0,0), xytext=(12,22), color=accent,
            arrowprops={'arrowstyle':'->', 'color':accent}, fontsize=10)
fig.text(.73, .73, 'STANDARD SIZE', color=accent, fontsize=12, weight='bold')
fig.text(.73, .68,
         'Footprint: 121.8 × 72.4\nSocket height: 5.2\nStrap height: 3.3\nStrap width: 3.6\n'
         'Hook inner width: 16.4\nSocket bore: Ø2.65\nSocket depth: 6.0\n'
         'Nose insertion: 3.7', va='top', fontsize=11, linespacing=1.9)
fig.text(.055, .15, 'PRINT FLAT IN TPU', fontsize=14, weight='bold')
fig.text(.055, .12, 'The flat underside is already at Z = 0. The socket is the thicker end.\n'
         'The curved arm and hook are one continuous solid. Use the separate nose STL for a rigid nose fitting.',
         fontsize=10, linespacing=1.6, va='top')
fig.savefig(ROOT/'previews/ear_strap_print_reference.png', dpi=170, facecolor=bg)
fig.savefig(ROOT/'previews/ear_strap_print_reference.pdf', facecolor=bg)
plt.close(fig)
print('Rendered full assembly and TPU strap print reference.')
