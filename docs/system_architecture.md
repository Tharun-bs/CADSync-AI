# CADSync AI System Architecture

## Pipeline Overview

1. Excel input ingestion (`Geometry`, `HolePatterns`, `Features`, `Configurations`, `Metadata`)
2. Schema and rule-based validation
3. AI risk analysis (anomaly + manufacturability)
4. Parametric design optimization
5. 3D CAD generation and neutral exports (STEP/IGES/STL)
6. 2D drawing generation (DXF)
7. Knowledge graph update and visualization
8. Automated engineering report generation
9. Desktop preview and export control via PyQt6

## Modules

- `src/excel_parser`: strict Excel schema parsing and typed extraction
- `src/validation_engine`: geometry, tolerance, conflict and naming checks
- `src/ai_engine`: ML-based anomaly and manufacturability prediction
- `src/optimization_engine`: GA + SciPy design optimization
- `src/cad_generator`: FreeCAD parametric model generation and exports
- `src/drawing_generator`: technical DXF top-view export
- `src/knowledge_graph`: part-feature-constraint relationship graph
- `src/report_generator`: ReportLab PDF engineering report
- `src/ui_app`: desktop platform for engineer workflow

## Interoperability Strategy

- Primary neutral CAD outputs: STEP and IGES
- Auxiliary output: STL preview and DXF technical drawing
- Target systems: CATIA, Fusion 360, SolidWorks
- FreeCAD runtime branch for production geometry export
- Fallback mode for CI/demo environments without FreeCAD installation
