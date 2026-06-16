from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.excel_parser.parser import parse_excel
from src.pipeline import run_pipeline
from src.ui_app.preview_renderer import render_dxf_preview, render_step_preview
from src.validation_engine.validator import validate_part


class CADSyncMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CADSync AI - Intelligent Excel-to-CAD Engine")
        self.resize(1400, 860)

        self.current_excel: Path | None = None
        self.last_output_dir: Path | None = None
        self._preview_pixmaps: dict[str, QPixmap] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        root.setStyleSheet(
            """
            QWidget { background: #f4f6f8; color: #203040; }
            QTextEdit { background: white; border: 1px solid #d9e1e8; border-radius: 10px; padding: 8px; }
            QPushButton {
                background: #204b57; color: white; border: none; border-radius: 8px;
                padding: 10px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #2b6473; }
            QTabWidget::pane { border: 1px solid #d9e1e8; background: white; border-radius: 10px; }
            QTabBar::tab { background: #dde6eb; padding: 10px 14px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background: #204b57; color: white; }
            """
        )

        title = QLabel("CADSync AI Desktop Platform")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #17313a;")
        subtitle = QLabel("Excel validation, AI analysis, optimization, CAD generation, and in-app engineering previews")
        subtitle.setStyleSheet("color: #4e6470; font-size: 13px;")

        hero = QFrame()
        hero.setStyleSheet("background: white; border: 1px solid #d9e1e8; border-radius: 14px;")
        hero_layout = QVBoxLayout(hero)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Excel")
        self.validate_btn = QPushButton("Validate")
        self.generate_btn = QPushButton("Generate CAD")
        self.export_btn = QPushButton("Open Output Folder")
        self.report_btn = QPushButton("Open Report")

        for btn in [self.upload_btn, self.validate_btn, self.generate_btn, self.export_btn, self.report_btn]:
            toolbar.addWidget(btn)
        toolbar.addStretch(1)

        split = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.validation_panel = QTextEdit()
        self.validation_panel.setReadOnly(True)
        self.validation_panel.setPlaceholderText("Validation results panel")

        self.optimization_panel = QTextEdit()
        self.optimization_panel.setReadOnly(True)
        self.optimization_panel.setPlaceholderText("Optimization and AI results panel")

        left_layout.addWidget(self._panel_title("Validation"))
        left_layout.addWidget(self.validation_panel)
        left_layout.addWidget(self._panel_title("AI + Optimization"))
        left_layout.addWidget(self.optimization_panel)

        self.preview_panel = QTextEdit()
        self.preview_panel.setReadOnly(True)
        self.preview_panel.setPlaceholderText(
            "Artifact summary panel\n"
            "Generated STEP, DXF, STL, PDF, and graph paths appear here."
        )

        self.preview_tabs = QTabWidget()
        self.preview_tabs.addTab(self.preview_panel, "Artifacts")
        self.step_preview_label = self._create_preview_label(
            "3D preview will appear here after generation.\nRendered from the STEP model geometry."
        )
        self.dxf_preview_label = self._create_preview_label(
            "DXF preview will appear here after generation.\nRendered from the generated manufacturing drawing."
        )
        self.preview_tabs.addTab(self._wrap_preview(self.step_preview_label), "3D Model")
        self.preview_tabs.addTab(self._wrap_preview(self.dxf_preview_label), "DXF Drawing")

        split.addWidget(left_panel)
        split.addWidget(self.preview_tabs)
        split.setSizes([460, 900])

        layout.addWidget(hero)
        layout.addLayout(toolbar)
        layout.addWidget(split)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Load an Excel file to validate or generate artifacts.")

        self.upload_btn.clicked.connect(self._on_upload)
        self.validate_btn.clicked.connect(self._on_validate)
        self.generate_btn.clicked.connect(self._on_generate)
        self.export_btn.clicked.connect(self._on_open_output)
        self.report_btn.clicked.connect(self._on_open_report)

    def _on_upload(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Engineering Excel",
            str(Path.cwd()),
            "Excel Files (*.xlsx *.xls)",
        )
        if file_path:
            self.current_excel = Path(file_path)
            self.validation_panel.setPlainText(f"Loaded Excel file:\n{self.current_excel}")
            self.statusBar().showMessage(f"Loaded input: {self.current_excel.name}")

    def _on_validate(self) -> None:
        if not self.current_excel:
            QMessageBox.warning(self, "Missing Input", "Upload an Excel file first.")
            return
        try:
            part = parse_excel(self.current_excel)
            validation = validate_part(part)
            txt = [f"Part ID: {part.part_id}", f"Valid: {validation.valid}"]
            if validation.errors:
                txt.append("\nErrors:")
                txt.extend(f"- {e}" for e in validation.errors)
            if validation.warnings:
                txt.append("\nWarnings:")
                txt.extend(f"- {w}" for w in validation.warnings)
            self.validation_panel.setPlainText("\n".join(txt))
            self.statusBar().showMessage(f"Validation completed for {part.part_id}")
        except Exception as exc:
            self.validation_panel.setPlainText(f"Validation failed:\n{exc}")
            self.statusBar().showMessage("Validation failed")

    def _on_generate(self) -> None:
        if not self.current_excel:
            QMessageBox.warning(self, "Missing Input", "Upload an Excel file first.")
            return
        try:
            result = run_pipeline(self.current_excel)
            self.last_output_dir = result.report_path.parent

            self.optimization_panel.setPlainText(
                "\n".join(
                    [
                        f"Anomaly score: {result.ai_result.anomaly_score:.4f}",
                        f"Anomaly flag: {result.ai_result.anomaly_flag}",
                        f"Manufacturability risk: {result.ai_result.manufacturability_risk}",
                        f"Risk probability: {result.ai_result.manufacturability_probability:.2%}",
                        f"Estimated cost (USD): {result.ai_result.estimated_cost}",
                        "",
                        "Optimized Parameters:",
                    ]
                    + [f"- {k}: {v}" for k, v in result.optimization.optimized_params.items()]
                )
            )

            self.preview_panel.setPlainText(
                "\n".join(
                    [
                        "Generated CAD Artifacts:",
                        f"STEP: {result.artifacts.step_path}",
                        f"IGES: {result.artifacts.iges_path}",
                        f"STL: {result.artifacts.stl_path}",
                        f"DXF: {result.artifacts.dxf_path}",
                        f"Report: {result.report_path}",
                        f"Knowledge Graph: {result.graph_path}",
                    ]
                )
            )
            self._update_previews(result.artifacts.step_path, result.artifacts.dxf_path)
            self.statusBar().showMessage(f"Generated outputs for {result.part_spec.part_id}")
        except Exception as exc:
            QMessageBox.critical(self, "Generation Failed", str(exc))
            self.statusBar().showMessage("Generation failed")

    def _on_open_output(self) -> None:
        if self.last_output_dir and self.last_output_dir.exists():
            self._open_local_path(self.last_output_dir)
            return
        QMessageBox.information(self, "No Output", "Generate CAD first.")

    def _on_open_report(self) -> None:
        if not self.last_output_dir:
            QMessageBox.information(self, "No Report", "Generate CAD first.")
            return
        report = self.last_output_dir / "engineering_report.pdf"
        if report.exists():
            self._open_local_path(report)
            return
        QMessageBox.information(self, "No Report", "Report file not found.")

    def _open_local_path(self, path: Path) -> None:
        resolved = path.resolve()
        url = QUrl.fromLocalFile(str(resolved))
        if QDesktopServices.openUrl(url):
            return

        if os.name == "nt":
            os.startfile(str(resolved))
            return

        QMessageBox.warning(self, "Open Failed", f"Could not open path:\n{resolved}")

    def _panel_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 14px; font-weight: 700; color: #17313a; margin: 6px 0 2px 2px;")
        return label

    def _create_preview_label(self, placeholder: str) -> QLabel:
        label = QLabel(placeholder)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setMinimumSize(620, 520)
        label.setStyleSheet(
            "background: #fbfcfe; color: #526471; border: 1px dashed #b8c6d1; border-radius: 10px; font-size: 14px; padding: 16px;"
        )
        return label

    def _wrap_preview(self, label: QLabel) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(label)
        scroll.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(scroll)
        return container

    def _update_previews(self, step_path: Path, dxf_path: Path) -> None:
        try:
            step_preview = render_step_preview(step_path, step_path.with_name(f"{step_path.stem}_preview.png"), step_path.stem)
            self._set_preview_image(self.step_preview_label, step_preview, "step")
        except Exception as exc:
            self.step_preview_label.setText(f"3D preview unavailable.\n{exc}")

        try:
            dxf_preview = render_dxf_preview(dxf_path, dxf_path.with_name(f"{dxf_path.stem}_preview.png"), dxf_path.stem)
            self._set_preview_image(self.dxf_preview_label, dxf_preview, "dxf")
        except Exception as exc:
            self.dxf_preview_label.setText(f"DXF preview unavailable.\n{exc}")

    def _set_preview_image(self, label: QLabel, image_path: Path, cache_key: str) -> None:
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            label.setText(f"Preview image could not be loaded:\n{image_path}")
            return
        self._preview_pixmaps[cache_key] = pixmap
        scaled = pixmap.scaled(880, 640, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled)
        label.setMinimumSize(scaled.size())
