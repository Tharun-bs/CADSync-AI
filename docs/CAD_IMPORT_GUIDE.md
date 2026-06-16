# CAD Import & Manufacturing Drawing Guide

## Overview

CADSync AI generates three key CAD/engineering artifacts:

1. **STEP (.step)** – Neutral 3D parametric model for CATIA, Fusion 360, SolidWorks
2. **IGES (.iges)** – Legacy neutral format (fallback for legacy systems)
3. **DXF (.dxf)** – 2D manufacturing drawing with dimensioning and annotations

---

## Troubleshooting Empty/Missing Geometry in Fusion 360

### Root Causes & Solutions

#### Issue 1: Invalid STEP File Format

**Symptom:** File opens but shows no geometry

**Root Cause:** Previous versions used fallback stub STEP writers. CADSync AI v2.1+ now uses **CadQuery** to generate full parametric geometry with proper STEP/ISO-10303-21 format.

**Solution:**
1. Ensure **cadquery ≥ 2.3.0** is installed: `pip install cadquery`
2. Regenerate the STEP file: `python demo/run_demo.py`
3. Verify STEP file size >100 KB (should contain full parametric geometry)
4. Open in Fusion 360 with "File > Open" (not drag-and-drop initially)

#### Issue 2: Wrong Import Settings in Fusion 360

**Symptom:** File imports but geometry doesn't render

**Solution:**
1. In Fusion 360, go to **File > Open**
2. Select your **.step** file
3. In the import dialog:
   - Check **"Import as single part"** ✓
   - Uncheck **"Create new design"** (use current project)
   - Set **Unit System** to **Millimeters** (critical!)
   - Ensure **Geometry reference set** is NOT "None"
4. Click **Import**

#### Issue 3: Hole Pattern Not Visible

**Symptom:** Base plate appears but holes are missing

**Cause:** Holes may be positioned outside part bounds or overlapping.

**Solution:**
1. Check the **validation_log.json** in the outputs folder
2. Look for hole position warnings
3. Edit the Excel `HolePatterns` sheet to correct coordinates
4. Re-generate: `python demo/run_demo.py`

#### Issue 4: Fusion 360 Shows "Cannot Read File"

**Symptom:** File import fails with error

**Solution:**
1. Download **FreeCAD** (opensource) to validate STEP
2. Open the STEP file in FreeCAD to verify it's valid
3. If FreeCAD opens it, the file is valid → Fusion 360 needs update
4. If FreeCAD cannot open, regenerate from demo

---

## STEP File Format Details (CadQuery Generation)

### What You Should See When Imported

When imported into Fusion 360:

- **Rectangular plate** with correct overall dimensions (L × W × H)
- **Multiple circular holes** at specified pattern coordinates
- **Filleted edges** (chamfers on top surfaces for realism)
- **Proper part tree** showing base box → hole cuts → fillets applied

### Expected File Content

Valid STEP file starts with:
```
ISO-10303-21
HEADER
FILE_DESCRIPTION(...)
```

File size should be **>100 KB** for parametric geometry with holes.

---

## Manufacturing Drawing Standards (DXF Format)

### Complete Dimension Specification: 25-30+ Dimensions

#### 1. Overall Dimensions (3)
- **Length (X):** 220 mm
- **Width (Y):** 140 mm
- **Height/Thickness (Z):** 12 mm

#### 2. Hole Pattern Positioning Dimensions (2 per hole)
- **Each hole X-coordinate** from reference edge
- **Each hole Y-coordinate** from reference edge
- For 4 holes: 8 individual position dimensions

#### 3. Hole Feature Dimensions (3-5)
- **Hole diameter:** φ12.0 mm
- **Hole tolerance class:** H7 (standard machined)
- **Through/blind:** Through (full thickness)
- **Quantity:** 4 holes

#### 4. Tolerance & GD&T Callouts (6-8)
- **Linear tolerance:** ±0.08 mm on all dimensions
- **Geometric tolerances:**
  - Flatness: 0.05 mm max (all surfaces)
  - Perpendicularity: 0.10 mm relative to Datum A
  - Position: ±0.10 mm (hole pattern location)
  - Angularity: Material dependent

#### 5. Datum Planes (3)
- **Datum A:** Bottom face (primary locating surface)
- **Datum B:** Left edge (secondary reference)
- **Datum C:** Front edge (tertiary reference)

#### 6. Feature Callouts & Manufacturing Notes (6+)
- "Break all sharp edges with 0.5 mm fillet/chamfer"
- "Drilling sequence: Center → Pilot hole → Finish"
- "Remove all burrs and swarf after drilling"
- "Surface finish: Ra 1.6 µm on all machined surfaces"
- "Material: Aluminum 6061-T6"
- "100% hole location verification required"

#### 7. Title Block & Administrative (5)
- **Part Number:** PLATE_A100
- **Revision:** A
- **Date Created:** 2026-03-12
- **Scale:** 1:1
- **Material:** Aluminum 6061-T6

#### 8. View Labels & References (2-3)
- "TOP VIEW" (main)
- "FRONT VIEW" (auxiliary showing thickness)
- Projection standard (ISO/US alignment)

**TOTAL: ~30-35 distinct dimensions and specifications**

---

## Manufacturing Drawing Best Practices

### Layout & Organization

✓ Design for **single-page A3 or 11×17** printout
✓ **Top view (center):** Primary working drawing with hole pattern
✓ **Front view (side):** Shows thickness dimension
✓ **Title block (bottom-right):** Legal/approval area
✓ **10 mm margins** on all sides

### Dimension Placement Rules

✓ **Horizontal overall dimensions:** Below the view outline (2-3 levels down)
✓ **Vertical overall dimensions:** Left side of outline (2-3 levels left)
✓ **Hole callouts:** Leader lines pointing to each hole with label
✓ **Feature notes:** Placed with clear arrow/pointer
✗ Never place dimensions overlapping geometry
✗ Never have crossing dimension lines

### Tolerance Strategy for CNC

**For this design:**
- **Overall dimensions:** ±0.08 mm (reasonable for CNC turning/milling)
- **Hole locations:** ±0.1 mm position tolerance (H7 fit = ±0.009 mm bore, ±0.10 mm position)
- **Surface finish:** Ra 1.6 µm standard for aluminum (achievable with standard end mills)

**Tolerance stack-up example:**
```
Hole pattern tolerance budget:
  Reference surface flatness:     ±0.05 mm
  Hole position:                  ±0.10 mm
  Hole diameter H7:               ±0.009 mm
  ────────────────────────────
  Total hole location error:       ±0.159 mm (acceptable for 12 mm hole)
```

### Annotation Example

```
TITLE BLOCK
┌──────────────────────────────┐
│ PART: PLATE_A100             │
│ REV: A       DATE: 3/12/2026 │
│ MATERIAL: Aluminum 6061-T6   │
│ SCALE: 1:1                   │
│ All dimensions in mm unless  │
│ otherwise specified          │
└──────────────────────────────┘

✓ Hole location tolerance: ±0.1 mm from Datum A & B
✓ Surface finish: Ra 1.6 µm CNC standard
✓ Break edges: 0.5 mm chamfer or fillet
✓ Material spec clear at top
```

---

## Importing Generated DXF into CAM/Manufacturing Software

### Fusion 360 (CAM Workflow)

1. **File > Import** → Select **.dxf**
2. Set **Unit System: Millimeters**
3. Import as **Sketch** (not drawing document)
4. Create **CAM toolpath** from sketch geometry
5. Generate **G-code** for CNC machine

### Mastercam / SolidCAM

1. **File > Import (DXF)** 
2. Ensure scale is **1:1** (metric)
3. Map DXF layers:
   - **Geometry layer** → Machine cutting paths
   - **Dimensions layer** → Reference/documentation
4. Create 2D or 3D toolpaths as needed

### Carveco Makercam (Laser/Routes)

1. **Import DXF**
2. Scale: **1:1** (already in mm)
3. Layer visibility: Enable all
4. Calibrate workpiece reference to Datum A (bottom face)
5. Generate cutting sequence

---

## File Size & Validation

### Expected Output Sizes

| File | Typical Size | Contains |
|------|------|----------|
| STEP (.step) | 100-500 KB | Full parametric geometry with holes, fillets |
| IGES (.iges) | 50-100 KB | Legacy geometry format wrapper |
| STL (.stl) | 1-5 MB | Tessellated mesh (high-res) |
| DXF (.dxf) | 20-50 KB | 2D views, dimensions, annotations |
| PDF Report | 150-300 KB | Rendered tables, images, metadata |

**If STEP < 50 KB:** Likely not generated correctly (stub file)

---

## Diagnostic Checklist

- [ ] CadQuery installed: `pip show cadquery`
- [ ] STEP file exists and size > 100 KB
- [ ] File opens in FreeCAD without errors
- [ ] Fusion 360 units set to **Millimeters** during import
- [ ] Part is visible in Fusion 360 model tree
- [ ] Validation log shows no critical errors
- [ ] DXF opens in LibreCAD or similar viewer

---

## Next Steps

1. **Regenerate outputs** with improved pipeline: `python demo/run_demo.py`
2. **Import STEP** into Fusion 360 (ensure units = mm)
3. **Verify** all 4 holes are visible at correct coordinates
4. **Extract DXF** drawing for manufacturing/CAM use
5. **Use PDF report** for engineering documentation and tool selections
6. **Iterate:** Modify Excel input → Regenerate → Re-verify in CAD
