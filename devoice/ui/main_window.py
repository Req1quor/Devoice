"""Main application window for Devoice (Minimalist Monochrome Edition with Adaptive Audio Diagnostic)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from devoice.audio_utils import AudioDiagnostic, analyze_audio_track
from devoice.config import OUTPUT_FORMATS
from devoice.model_manager import ModelManager
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.worker import SeparationWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary window assembling the UI and adaptive acoustic diagnostic workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Devoice")
        self.setMinimumSize(700, 680)
        self.resize(760, 720)

        self.pending_files: List[Path] = []
        self.output_dir: Path | None = None
        self.worker: SeparationWorker | None = None
        self._last_processed_file: Path | None = None
        self._current_diagnostic: Optional[AudioDiagnostic] = None

        self._build_ui()
        self._update_device_label()
        self._reset_diagnostic_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(12)

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
        self.file_list.setMaximumHeight(80)
        self.file_list.setVisible(False)
        root.addWidget(self.file_list)

        # ── (d) Settings Row (Model / Format / Export Dir) ──────────────
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

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

        # ── (e) Diagnostic & Adaptive Pro Options Card ──────────────────
        self.diag_card = QFrame()
        self.diag_card.setObjectName("DiagnosticCard")
        diag_layout = QVBoxLayout(self.diag_card)
        diag_layout.setContentsMargins(14, 12, 14, 12)
        diag_layout.setSpacing(8)

        # Diagnostic Headline
        diag_top = QHBoxLayout()
        self.diag_title = QLabel("💡 DIAGNOSTIC INTELLIGENT")
        self.diag_title.setObjectName("DiagnosticTitle")
        diag_top.addWidget(self.diag_title)

        diag_top.addStretch()

        self.diag_summary = QLabel("")
        self.diag_summary.setObjectName("DiagnosticSummary")
        diag_top.addWidget(self.diag_summary)
        diag_layout.addLayout(diag_top)

        # 3 Adaptive Treatment Rows (Checkbox + Reason/Badge)
        # 1. True Peak
        row1 = QVBoxLayout()
        row1.setSpacing(1)
        self.cb_true_peak = QCheckBox("Normalisation True-Peak (-1.0 dBFS)")
        self.lbl_true_peak_reason = QLabel("⚪ En attente de fichier…")
        self.lbl_true_peak_reason.setObjectName("ReasonLabel")
        row1.addWidget(self.cb_true_peak)
        row1.addWidget(self.lbl_true_peak_reason)
        diag_layout.addLayout(row1)

        # 2. Sub-Bass
        row2 = QVBoxLayout()
        row2.setSpacing(1)
        self.cb_subbass = QCheckBox("Coupe-bas Sub-Bass (65 Hz)")
        self.lbl_subbass_reason = QLabel("⚪ En attente de fichier…")
        self.lbl_subbass_reason.setObjectName("ReasonLabel")
        row2.addWidget(self.cb_subbass)
        row2.addWidget(self.lbl_subbass_reason)
        diag_layout.addLayout(row2)

        # 3. Spectral De-bleed
        row3 = QVBoxLayout()
        row3.setSpacing(1)
        self.cb_debleed = QCheckBox("Dé-bleed spectral (Suppression des fuites d'aigus)")
        self.lbl_debleed_reason = QLabel("⚪ En attente de fichier…")
        self.lbl_debleed_reason.setObjectName("ReasonLabel")
        row3.addWidget(self.cb_debleed)
        row3.addWidget(self.lbl_debleed_reason)
        diag_layout.addLayout(row3)

        root.addWidget(self.diag_card)

        # ── (f) Progress Bar & Status ───────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("Glissez-déposez un morceau pour démarrer…")
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

    # ── Diagnostic & Dynamic Adaptations ────────────────────────────────

    def _reset_diagnostic_ui(self) -> None:
        """Reset the diagnostic card to waiting state."""
        self.diag_title.setText("💡 ANALYSE ACOUSTIQUE ADAPTATIVE")
        self.diag_summary.setText("Déposez un morceau pour analyser son spectre")
        self.cb_true_peak.setEnabled(False)
        self.cb_subbass.setEnabled(False)
        self.cb_debleed.setEnabled(False)
        self.lbl_true_peak_reason.setText("⚪ Déposez un fichier pour adapter l'option")
        self.lbl_subbass_reason.setText("⚪ Déposez un fichier pour adapter l'option")
        self.lbl_debleed_reason.setText("⚪ Déposez un fichier pour adapter l'option")

    def _update_diagnostic_ui(self, diag: AudioDiagnostic) -> None:
        """Dynamically populate checkboxes and explanatory tags based on track analysis."""
        self._current_diagnostic = diag
        self.diag_title.setText(f"● ANALYSE : {diag.filename}")
        self.diag_summary.setText(f"{diag.duration_display} · Pic: {diag.peak_dbfs:.1f} dBFS · Sub: {diag.sub_bass_ratio*100:.1f}%")

        # 1. True-Peak Normalization
        self.cb_true_peak.setEnabled(True)
        self.cb_true_peak.setChecked(diag.recommend_true_peak)
        tp_icon = "🟢 Recommandé :" if diag.recommend_true_peak else "⚪ Non nécessaire :"
        self.lbl_true_peak_reason.setText(f"{tp_icon} {diag.true_peak_reason}")
        self.lbl_true_peak_reason.setProperty("recommended", "true" if diag.recommend_true_peak else "false")

        # 2. Sub-Bass Filter
        self.cb_subbass.setEnabled(True)
        self.cb_subbass.setChecked(diag.recommend_subbass)
        sub_icon = "🟢 Recommandé :" if diag.recommend_subbass else "⚪ Inactif conseillé :"
        self.lbl_subbass_reason.setText(f"{sub_icon} {diag.subbass_reason}")
        self.lbl_subbass_reason.setProperty("recommended", "true" if diag.recommend_subbass else "false")

        # 3. Spectral De-bleed
        self.cb_debleed.setEnabled(True)
        self.cb_debleed.setChecked(diag.recommend_debleed)
        deb_icon = "🟢 Recommandé :" if diag.recommend_debleed else "⚪ Inactif conseillé :"
        self.lbl_debleed_reason.setText(f"{deb_icon} {diag.debleed_reason}")
        self.lbl_debleed_reason.setProperty("recommended", "true" if diag.recommend_debleed else "false")

        # Force stylesheet refresh on reasons
        for lbl in (self.lbl_true_peak_reason, self.lbl_subbass_reason, self.lbl_debleed_reason):
            lbl.setStyle(lbl.style())

    # ── Logic & Signal Slots ────────────────────────────────────────────

    def _on_files_dropped(self, paths: list[Path]) -> None:
        self.pending_files.extend(paths)
        self.file_list.clear()
        for p in self.pending_files:
            self.file_list.addItem(f"🎵  {p.name}")

        self.file_list.setVisible(True)
        self.start_btn.setEnabled(True)
        self.status_label.setText(f"{len(self.pending_files)} fichier(s) prêt(s)")

        # Run instant acoustic analysis on the first track to adapt the options
        primary_file = paths[0]
        try:
            diag = analyze_audio_track(primary_file)
            self._update_diagnostic_ui(diag)
        except Exception as exc:
            logger.warning("Could not run acoustic analysis on %s: %s", primary_file.name, exc)

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
