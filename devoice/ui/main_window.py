"""Main application window for Devoice (Minimalist Monochrome Edition)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from devoice.config import OUTPUT_FORMATS
from devoice.model_manager import ModelManager
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.worker import SeparationWorker


class MainWindow(QMainWindow):
    """Primary window that assembles every UI element of Devoice."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Devoice")
        self.setMinimumSize(680, 640)
        self.resize(750, 700)

        self.pending_files: List[Path] = []
        self.output_dir: Path | None = None
        self.worker: SeparationWorker | None = None
        self._last_processed_file: Path | None = None

        self._build_ui()
        self._update_device_label()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        # ── (a) Header ──────────────────────────────────────────────────
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title_label = QLabel("DEVOICE")
        self.title_label.setObjectName("TitleLabel")

        self.subtitle_label = QLabel("Séparation vocale haute fidélité · BS-RoFormer")
        self.subtitle_label.setObjectName("SubtitleLabel")

        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)

        header.addLayout(title_col)
        header.addStretch()

        self.device_label = QLabel("● Détection matériel…")
        self.device_label.setObjectName("DeviceLabel")
        header.addWidget(self.device_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        root.addLayout(header)

        # ── (b) Drop Zone ───────────────────────────────────────────────
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        root.addWidget(self.drop_zone)

        # ── (c) File Queue List ─────────────────────────────────────────
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(90)
        self.file_list.setVisible(False)
        root.addWidget(self.file_list)

        # ── (d) Settings Row ────────────────────────────────────────────
        settings_row = QHBoxLayout()
        settings_row.setSpacing(12)

        settings_row.addWidget(QLabel("Mode :"))
        self.model_combo = QComboBox()
        for model in ModelManager.available_models():
            self.model_combo.addItem(model.display_name, model.name)
        self.model_combo.setCurrentIndex(0)  # BS-RoFormer by default
        settings_row.addWidget(self.model_combo, stretch=2)

        settings_row.addWidget(QLabel("Format :"))
        self.format_combo = QComboBox()
        for display_name in OUTPUT_FORMATS:
            self.format_combo.addItem(display_name)
        settings_row.addWidget(self.format_combo, stretch=1)

        self.output_dir_btn = QPushButton("📁 Dossier")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        settings_row.addWidget(self.output_dir_btn)

        root.addLayout(settings_row)

        # ── (e) Pro Audio Options ───────────────────────────────────────
        opts_layout = QHBoxLayout()
        opts_layout.setSpacing(16)

        opts_title = QLabel("Options Pro :")
        opts_title.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 600;")
        opts_layout.addWidget(opts_title)

        self.cb_true_peak = QCheckBox("Normalisation True-Peak (-1 dBFS)")
        self.cb_true_peak.setChecked(True)
        opts_layout.addWidget(self.cb_true_peak)

        self.cb_subbass = QCheckBox("Coupe-bas Sub-Bass (65 Hz)")
        self.cb_subbass.setChecked(True)
        opts_layout.addWidget(self.cb_subbass)

        self.cb_debleed = QCheckBox("Dé-bleed spectral")
        self.cb_debleed.setChecked(False)
        opts_layout.addWidget(self.cb_debleed)

        opts_layout.addStretch()
        root.addLayout(opts_layout)

        # ── (f) Progress Bar & Status ───────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("En attente d'un fichier audio…")
        self.status_label.setObjectName("StatusLabel")
        root.addWidget(self.status_label)

        # ── (g) Action Buttons ──────────────────────────────────────────
        actions = QHBoxLayout()
        actions.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("SÉPARER L'AUDIO")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_separation)
        actions.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_separation)
        actions.addWidget(self.cancel_btn)

        root.addLayout(actions)

        # ── (h) Synchronized A/B/C Audio Player ─────────────────────────
        self.audio_player = AudioPreviewPlayer()
        root.addWidget(self.audio_player)

        root.addStretch()

    # ── Logic & Signal Slots ────────────────────────────────────────────

    def _on_files_dropped(self, paths: list[Path]) -> None:
        self.pending_files.extend(paths)
        self.file_list.clear()
        for p in self.pending_files:
            self.file_list.addItem(f"🎵  {p.name}")

        self.file_list.setVisible(True)
        self.start_btn.setEnabled(True)
        self.status_label.setText(f"{len(self.pending_files)} fichier(s) prêt(s)")

    def _select_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier d'export",
            str(self.output_dir) if self.output_dir else "",
        )
        if directory:
            self.output_dir = Path(directory)
            self.status_label.setText(f"Dossier : {self.output_dir.name}")

    def _start_separation(self) -> None:
        if not self.pending_files:
            return

        model_name: str = self.model_combo.currentData()
        output_format: str = self.format_combo.currentText()

        self._last_processed_file = self.pending_files[0]

        self.worker = SeparationWorker(
            files=list(self.pending_files),
            model_name=model_name,
            output_format=output_format,
            output_dir=self.output_dir,
            subbass_filter=self.cb_subbass.isChecked(),
            true_peak=self.cb_true_peak.isChecked(),
            spectral_debleed=self.cb_debleed.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.file_completed.connect(self._on_file_completed)
        self.worker.file_error.connect(self._on_file_error)
        self.worker.all_completed.connect(self._on_all_completed)

        self.worker.start()

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.start_btn.setEnabled(False)
        self.status_label.setText("Initialisation du traitement…")

    def _cancel_separation(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.status_label.setText("Annulation en cours…")

    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_file_completed(self, filename: str, results: Dict[str, Any]) -> None:
        self.status_label.setText(f"● {filename} séparé avec succès")
        vocals_path = Path(results.get("vocals", ""))
        instru_path = Path(results.get("instru", "") or results.get("instrumental", ""))

        if vocals_path.exists() and instru_path.exists():
            # Pass original track to allow synchronized 3-way A/B/C comparison
            self.audio_player.set_results(
                vocals_path=vocals_path,
                instru_path=instru_path,
                original_path=self._last_processed_file,
            )

    def _on_file_error(self, filename: str, error: str) -> None:
        self.status_label.setText(f"Erreur sur {filename} : {error}")

    def _on_all_completed(self) -> None:
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.start_btn.setEnabled(True)
        self.pending_files.clear()
        self.file_list.clear()
        self.file_list.setVisible(False)

    def _update_device_label(self) -> None:
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                self.device_label.setText(f"● {gpu_name} (CUDA)")
                self.device_label.setStyleSheet("color: #4ade80; border: 1px solid #14532d; background-color: #052e16;")
            else:
                self.device_label.setText("● CPU")
                self.device_label.setStyleSheet("color: #a1a1aa; border: 1px solid #27272a; background-color: #121215;")
        except Exception:
            self.device_label.setText("● CPU")
