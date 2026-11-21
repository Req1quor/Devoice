"""Modern minimalist MainWindow for Devoice."""

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
    QGridLayout,
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
from devoice.engine import ModelManager
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.worker import SeparationWorker

logger = logging.getLogger(__name__)

OUTPUT_FORMATS = [
    "WAV (16-bit)",
    "FLAC (24-bit)",
    "MP3 (320 kbps)",
]


class MainWindow(QMainWindow):
    """Clean, modern, and minimalist studio vocal separation desktop app."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Devoice — Séparation Vocale Haute Fidélité")
        self.setMinimumSize(700, 600)
        self.resize(760, 650)

        self.pending_files: List[Path] = []
        self.output_dir: Path | None = None
        self.worker: SeparationWorker | None = None
        self._last_processed_file: Path | None = None
        self._current_diagnostic: Optional[AudioDiagnostic] = None

        self._build_ui()
        self._update_device_label()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        # ── (a) Header ────────────────────────────────────────────────────
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title_label = QLabel("DEVOICE")
        self.title_label.setObjectName("TitleLabel")

        self.subtitle_label = QLabel("Séparation vocale & instrumentale de qualité studio")
        self.subtitle_label.setObjectName("SubtitleLabel")

        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)

        header.addLayout(title_col)
        header.addStretch()

        self.device_label = QLabel("Détection matériel...")
        self.device_label.setObjectName("DeviceBadge")
        header.addWidget(self.device_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        root.addLayout(header)

        # ── (b) Hero Drop Zone ───────────────────────────────────────────
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        root.addWidget(self.drop_zone)

        # ── (c) File Queue (Visible only if multiple files) ──────────────
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(65)
        self.file_list.setVisible(False)
        root.addWidget(self.file_list)

        # ── (d) Clean Settings Card ──────────────────────────────────────
        self.settings_card = QFrame()
        self.settings_card.setObjectName("SettingsCard")
        card_layout = QVBoxLayout(self.settings_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        # Row 1: Model & Format & Output
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        row1.addWidget(QLabel("Moteur :"))
        self.model_combo = QComboBox()
        for model in ModelManager.available_models():
            self.model_combo.addItem(model.display_name, model.name)
        self.model_combo.setCurrentIndex(0)
        row1.addWidget(self.model_combo, stretch=3)

        row1.addWidget(QLabel("Format :"))
        self.format_combo = QComboBox()
        for display_name in OUTPUT_FORMATS:
            self.format_combo.addItem(display_name)
        row1.addWidget(self.format_combo, stretch=1)

        self.output_dir_btn = QPushButton("Dossier d'export")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        row1.addWidget(self.output_dir_btn)

        card_layout.addLayout(row1)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #1e222f; background-color: #1e222f; max-height: 1px;")
        card_layout.addWidget(divider)

        # Row 2: Intelligent Auto Studio Enhancement Toggle
        auto_row = QHBoxLayout()
        auto_row.setSpacing(10)

        auto_info = QVBoxLayout()
        auto_info.setSpacing(2)

        self.chk_auto_dsp = QCheckBox("Amélioration studio automatique")
        self.chk_auto_dsp.setChecked(True)
        self.chk_auto_dsp.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        self.chk_auto_dsp.toggled.connect(self._on_auto_dsp_toggled)

        self.lbl_auto_sub = QLabel(
            "Analyse le morceau pour éliminer le souffle, équilibrer le volume et prévenir la saturation."
        )
        self.lbl_auto_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")

        auto_info.addWidget(self.chk_auto_dsp)
        auto_info.addWidget(self.lbl_auto_sub)
        auto_row.addLayout(auto_info, stretch=1)

        self.btn_toggle_advanced = QPushButton("Options avancées ▾")
        self.btn_toggle_advanced.setStyleSheet(
            "background-color: transparent; border: 1px solid #282f40; color: #94a3b8; font-size: 11px; padding: 5px 12px;"
        )
        self.btn_toggle_advanced.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_advanced.clicked.connect(self._toggle_advanced_drawer)
        auto_row.addWidget(self.btn_toggle_advanced, alignment=Qt.AlignmentFlag.AlignVCenter)

        card_layout.addLayout(auto_row)

        # Collapsible Advanced Drawer (Hidden by default)
        self.drawer_widget = QWidget()
        self.drawer_widget.setVisible(False)
        drawer_layout = QGridLayout(self.drawer_widget)
        drawer_layout.setContentsMargins(4, 8, 4, 4)
        drawer_layout.setSpacing(10)

        self.chk_leveler = QCheckBox("Stabilisateur de volume (Vocal Rider)")
        self.chk_silence = QCheckBox("Nettoyage du souffle dans les pauses")
        self.chk_subbass = QCheckBox("Filtre coupe-bas anti-rumble")
        self.chk_true_peak = QCheckBox("Plafond de sécurité anti-saturation")
        self.chk_deesser = QCheckBox("Atténuation des sifflements (De-Esser)")
        self.chk_dereverb = QCheckBox("Dé-réverbération (Assèchement)")
        self.chk_debleed = QCheckBox("Anti-fuite de batterie (De-bleed)")

        drawer_layout.addWidget(self.chk_leveler, 0, 0)
        drawer_layout.addWidget(self.chk_silence, 0, 1)
        drawer_layout.addWidget(self.chk_subbass, 1, 0)
        drawer_layout.addWidget(self.chk_true_peak, 1, 1)
        drawer_layout.addWidget(self.chk_deesser, 2, 0)
        drawer_layout.addWidget(self.chk_dereverb, 2, 1)
        drawer_layout.addWidget(self.chk_debleed, 3, 0)

        card_layout.addWidget(self.drawer_widget)

        root.addWidget(self.settings_card)

        # ── (e) Hero Action Button ───────────────────────────────────────
        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.start_btn = QPushButton("SÉPARER L'AUDIO")
        self.start_btn.setObjectName("HeroButton")
        self.start_btn.setEnabled(False)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._start_separation)
        actions.addWidget(self.start_btn, stretch=1)

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._cancel_separation)
        actions.addWidget(self.cancel_btn)

        root.addLayout(actions)

        # ── (f) Status & Progress ────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("Déposez un morceau pour démarrer")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        root.addWidget(self.status_label)

        # ── (g) Integrated Triple Audio Player ───────────────────────────
        self.audio_player = AudioPreviewPlayer()
        root.addWidget(self.audio_player)

        root.addStretch()

    # ── UI Drawer & Toggles ─────────────────────────────────────────────

    def _toggle_advanced_drawer(self) -> None:
        is_visible = self.drawer_widget.isVisible()
        self.drawer_widget.setVisible(not is_visible)
        self.btn_toggle_advanced.setText("Masquer les options ▴" if not is_visible else "Options avancées ▾")

    def _on_auto_dsp_toggled(self, checked: bool) -> None:
        self.drawer_widget.setEnabled(checked)
        if not checked:
            self.lbl_auto_sub.setText("Mode brut : acapella 100% pure du modèle de neurones, aucun traitement.")
        else:
            self.lbl_auto_sub.setText("Analyse le morceau pour éliminer le souffle, équilibrer le volume et prévenir la saturation.")
            if self._current_diagnostic:
                self._apply_diagnostic_to_checkboxes(self._current_diagnostic)

    def _apply_diagnostic_to_checkboxes(self, diag: AudioDiagnostic) -> None:
        self.chk_subbass.setChecked(diag.has_subbass_rumble)
        self.chk_leveler.setChecked(diag.has_dynamic_imbalance)
        self.chk_deesser.setChecked(diag.has_harsh_sibilance)
        self.chk_silence.setChecked(diag.has_noise_in_pauses)
        self.chk_dereverb.setChecked(diag.has_reverb)
        self.chk_true_peak.setChecked(diag.recommend_true_peak)
        self.chk_debleed.setChecked(diag.recommend_debleed)

    # ── Logic & Signal Slots ────────────────────────────────────────────

    def _on_files_dropped(self, paths: list[Path]) -> None:
        self.pending_files.extend(paths)
        primary_file = paths[0]

        self.drop_zone.set_loaded_file(primary_file)

        if len(self.pending_files) > 1:
            self.file_list.clear()
            for p in self.pending_files:
                self.file_list.addItem(p.name)
            self.file_list.setVisible(True)
        else:
            self.file_list.setVisible(False)

        self.start_btn.setEnabled(True)
        self.status_label.setText(f"{primary_file.name} est prêt pour la séparation")

        try:
            diag = analyze_audio_track(primary_file)
            self._current_diagnostic = diag
            if self.chk_auto_dsp.isChecked():
                self._apply_diagnostic_to_checkboxes(diag)
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
            self.output_dir_btn.setText(self.output_dir.name)
            self.status_label.setText(f"Dossier d'export : {self.output_dir.name}")

    def _start_separation(self) -> None:
        if not self.pending_files:
            return

        model_name: str = self.model_combo.currentData()
        output_format: str = self.format_combo.currentText()

        self._last_processed_file = self.pending_files[0]

        cutoff_hz = self._current_diagnostic.adaptive_cutoff_hz if self._current_diagnostic else 65.0
        sibilance_hz = self._current_diagnostic.sibilance_hz if self._current_diagnostic else 7200.0

        use_dsp = self.chk_auto_dsp.isChecked()

        self.worker = SeparationWorker(
            files=list(self.pending_files),
            model_name=model_name,
            output_format=output_format,
            output_dir=self.output_dir,
            subbass_filter=use_dsp and self.chk_subbass.isChecked(),
            subbass_cutoff=cutoff_hz,
            deesser=use_dsp and self.chk_deesser.isChecked(),
            deesser_freq=sibilance_hz,
            dereverb=use_dsp and self.chk_dereverb.isChecked(),
            silence_purifier=use_dsp and self.chk_silence.isChecked(),
            vocal_leveler=use_dsp and self.chk_leveler.isChecked(),
            true_peak=use_dsp and self.chk_true_peak.isChecked(),
            spectral_debleed=use_dsp and self.chk_debleed.isChecked(),
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
        self.status_label.setText("Séparation audio en cours...")

    def _cancel_separation(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.status_label.setText("Annulation en cours...")

    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_file_completed(self, filename: str, results: Dict[str, Any]) -> None:
        self.status_label.setText(f"{filename} séparé avec succès !")
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
                self.device_label.setText(gpu_name)
                self.device_label.setStyleSheet(
                    "background-color: #0d281e; color: #34d399; border: 1px solid #166534; font-weight: 600; padding: 4px 12px; border-radius: 12px;"
                )
            else:
                self.device_label.setText("CPU")
                self.device_label.setStyleSheet(
                    "background-color: #1e2433; color: #94a3b8; border: 1px solid #2d374d; font-weight: 600; padding: 4px 12px; border-radius: 12px;"
                )
        except Exception:
            self.device_label.setText("CPU")
