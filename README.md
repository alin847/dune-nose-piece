# Dune costume nose piece and TPU ear strap

Original CAD modeled from the supplied reference photo. The design has a gently
curved bridge, two rounded parallel prongs, a flat print base, and a spigot
on the left when viewed from the front. A separate **printable TPU strap** joins
the spigot, curves along the cheek, and ends in an open hook over the ear.
All dimensions are in **millimeters**.

## Start here

- **Complete assembled CAD:** `output/dune_complete_assembly.step`
- **TPU strap CAD / print:** `output/dune_ear_strap_TPU.step` and `.stl`
- **Nose CAD / print:** `output/dune_nose_piece.step` and `.stl`
- **Complete preview:** `previews/complete_assembly.png`
- **Strap print drawing:** `previews/ear_strap_print_reference.pdf`
- **Nose fit drawing:** `previews/fit_reference.pdf`
- **Strap fits:** `dune_ear_strap_TPU_short` and `dune_ear_strap_TPU_long`, both formats.
- **Nose fits:** files ending in `spacing_14mm` and `spacing_18mm`, both formats.
- **Both parts on one bed:** `output/dune_complete_print_layout.stl` (two separate
  bodies; use this only if printing both parts in TPU, or assign materials separately).

The assembly contains two named solids, with the socket engaged on the nose
spigot. It shows the strap's **relaxed, flat manufacturing shape**, not a custom
simulation of the shape on your face. The strap bends around the cheek and the
hook bends over the ear when worn. Print the separate parts using their STLs.

The STEP files contain editable solid boundary geometry, not a triangulated mesh.
The parameterized designs are in `build_model.py`, `build_strap.py`,
`parameters.json`, and `strap_parameters.json`;
STEP import into a CAD editor will not recreate that Python feature history.

## Dimensions and fit

| Feature | Default |
| --- | --- |
| Overall envelope, including hose spigot | 36.00 × 5.30 × 8.53 mm |
| Prong spacing, center to center | 16 mm |
| Alternative prong spacings | 14 mm and 18 mm |
| Prong diameter | 3.2 mm |
| Bridge nominal diameter, before flattening | 3.8 mm |
| Bridge top above print bed | 3.3 mm |
| Rearward prong lean | About 6.8° |
| Hose spigot nominal diameter | 2.5 mm |
| Hose barb maximum diameter | 2.9 mm |

Scale was estimated because the image has no known physical measurement.
The variants change only prong spacing, keeping the bridge and tubing fit the
same. Check the fit before finishing the print. This is a solid decorative prop
intended to sit externally below the nostrils; do not insert rigid printed prongs
into your nose. There are no airflow passages.

## TPU cheek strap and ear hook

The cheek section and open ear hook are one continuous printed solid, with a
rounded free tip and a socket at the nose end. No separate cheek hose is needed.

| Feature | Standard strap |
| --- | --- |
| Flat print footprint | Approximately 121.8 × 72.4 mm |
| Strap width / height | 3.6 / 3.3 mm |
| Maximum height at socket | 5.2 mm |
| Ear-hook inner width | 16.4 mm |
| Hook straight return length | 15 mm |
| Socket bore diameter / depth | 2.65 / 6 mm |
| Spigot insertion in assembly | 3.7 mm |
| Cheek reach parameter (socket to start of hook, along X) | 100 mm |
| Short / long cheek reach | 90 / 110 mm |

Cheek reach is a flat-layout coordinate, not the measured arc length along a
face. The small and large fits change the cheek reach without resizing the
socket, cross-section, or ear hook. Hook width, rise, and return length can be
edited independently in `strap_parameters.json`.

Print the strap in **flexible TPU**. The 2.65 mm bore intentionally grips the
2.9 mm nose barb through TPU stretch; the STEP assembly has a small intentional
interference at the barb. Push the nose spigot into the socket approximately
3.7 mm. Printer tolerances and TPU stiffness affect the fit. If the joint is too
tight or loose, adjust `socket_bore_diameter_mm` and rebuild. The nose piece can
be printed separately in a rigid material or in TPU.

## Printing

1. Open each part's STL in your slicer and retain millimeters / 100% scale.
2. Put the existing flat underside on the bed, with the prongs pointing up.
   The exported model is already in this orientation, at Z = 0.
3. For a 0.4 mm nozzle, a starting profile is 0.16 mm layers, three walls,
   100% infill, and a 3 mm brim for the small footprint. Use your printer's TPU
   material profile for the strap. The strap lies flat, with its socket opening
   pointing sideways; do not stand the ear hook vertically on the bed.
4. Inspect the sliced layers, especially the nose barb and the small bridge at
   the socket bore. Support needs depend on your printer; avoid filling the
   blind socket with supports that cannot be removed.
5. Remove the brim and smooth the contact edges before checking the fit.

No physical print or personal fit test has been performed. Prefer a small fit
print before painting or final assembly.

## Editing and rebuilding

CAD tooling was downloaded into the project's isolated `.venv`; it does not
require a full CAD application. A Python 3.12 runtime was obtained through `uv`
in its normal managed runtime location. Exact package versions are recorded in
`requirements-lock.txt`.

From this directory:

```sh
.venv/bin/python build_model.py
.venv/bin/python build_strap.py
.venv/bin/python make_preview.py
.venv/bin/python preview_complete.py
```

Change nose dimensions in `parameters.json` or strap dimensions in
`strap_parameters.json` and rerun those commands. To export one
additional spacing without replacing the default models:

```sh
.venv/bin/python build_model.py --spacing 15
```

To recreate the environment on another machine with `uv` installed:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-lock.txt
```

Modeling/export reference: [CadQuery installation](https://cadquery.readthedocs.io/en/latest/installation.html)
and [STEP/STL export documentation](https://cadquery.readthedocs.io/en/latest/importexport.html).

## Validation

`output/validation.json` records checks on all three sizes:

- Valid CAD shape containing exactly one connected solid.
- STEP reimport succeeds, remains valid, and preserves volume within 0.0001%.
- Exported STL is watertight, consistently wound, and has one connected component.
- Small zero-area tessellation triangles at sphere poles are removed from the
  STL; the analytic STEP geometry is preserved unchanged.

`output/strap_validation.json` records equivalent checks for the three strap
sizes, the two-solid assembled STEP, and the intended interference at the socket.
The combined print-layout STL is checked to contain two watertight bodies.

The previews are rendered from the delivered STL. The supplied reference is
preserved in `reference/dune-nose-piece.png`.
