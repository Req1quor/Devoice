"""Main application window for Devoice (High-End Studio Edition)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
from devoice.config import OUTPUT_FORMATS
from devoice.model_manager import ModelManager
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.ui.module_card import StudioModuleCard
from devoice.worker import SeparationWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary window assembling the modern studio UI and adaptive separation workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Devoice — Studio Acapella & Instrumental Separation")
        self.setMinimumSize(780, 750)
        self.resize(820, 780)

        self.pending_files: List[Path] = []
        self.output_dir: Path | None = None
        self.worker: SeparationWorker | None = None
        self._last_processed_file: Path | None = None
        self._current_diagnostic: Optional[AudioDiagnostic] = None
        self._is_pure_mode: bool = False

        self._build_ui()
        self._update_device_label()
        self._reset_diagnostic_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(12)

        # ── (a) Top Studio Header ─────────────────────────────────────────
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self.title_label = QLabel("DEVOICE")
        self.title_label.setObjectName("TitleLabel")

        self.subtitle_label = QLabel("Séparation vocale haute fidélité · BS-RoFormer & MDX-Net")
        self.subtitle_label.setObjectName("SubtitleLabel")

        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)

        header.addLayout(title_col)
        header.addStretch()

        self.device_label = QLabel("● Détection matériel…")
        self.device_label.setObjectName("DeviceLabel")
        header.addWidget(self.device_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        root.addLayout(header)

        # ── (b) Hero Drop Zone ───────────────────────────────────────────
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        root.addWidget(self.drop_zone)

        # ── (c) File Queue (Visible only if multiple files) ──────────────
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(70)
        self.file_list.setVisible(False)
        root.addWidget(self.file_list)

        # ── (d) Studio Processing Rack / Mode Bay ────────────────────────
        self.diag_card = QFrame()
        self.diag_card.setObjectName("DiagnosticCard")
        diag_layout = QVBoxLayout(self.diag_card)
        diag_layout.setContentsMargins(14, 12, 14, 12)
        diag_layout.setSpacing(10)

        # Mode Selector & Status Header
        top_bar = QHBoxLayout()

        # Mode Switcher Tabs
        self.btn_preset_pure = QPushButton("💎 PURE ACAPELLA (BRUT SOTA)")
        self.btn_preset_pure.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preset_pure.clicked.connect(self._apply_pure_mode)

        self.btn_preset_studio = QPushButton("🎛️ STUDIO PRO (POST-TRAITEMENTS)")
        self.btn_preset_studio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preset_studio.clicked.connect(self._apply_studio_mode)

        top_bar.addWidget(self.btn_preset_pure)
        top_bar.addWidget(self.btn_preset_studio)
        top_bar.addStretch()

        self.diag_summary = QLabel("Déposez un morceau pour calibrer la chaîne")
        self.diag_summary.setObjectName("DiagnosticSummary")
        top_bar.addWidget(self.diag_summary)

        diag_layout.addLayout(top_bar)

        # 2-Column Grid of Tactile Studio Module Cards
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(8)

        # 1. Pitch-Tracked Sub-Bass
        self.card_subbass = StudioModuleCard(
            title="Coupe-bas fréquentiel",
            default_param="F0 vocal",
            default_reason="Coupe le rumble sans rogner le coffre de la voix",
        )
        self.grid_layout.addWidget(self.card_subbass, 0, 0)

        # 2. Vocal Rider / Dynamic Leveler
        self.card_leveler = StudioModuleCard(
            title="Vocal Rider Studio",
            default_param="±4.5 dB",
            default_reason="Compense les trous de volume sur les prods chargées",
        )
        self.grid_layout.addWidget(self.card_leveler, 0, 1)

        # 3. Dynamic De-Esser
        self.card_deesser = StudioModuleCard(
            title="De-Esser chirurgical",
            default_param="5 - 9 kHz",
            default_reason="Adoucit les sifflantes agressives sans ternir l'air",
        )
        self.grid_layout.addWidget(self.card_deesser, 1, 0)

        # 4. Silence Purifier
        self.card_silence = StudioModuleCard(
            title="Purificateur de silences",
            default_param="Clean Gate",
            default_reason="Supprime les résidus d'instru et souffle dans les pauses",
        )
        self.grid_layout.addWidget(self.card_silence, 1, 1)

        # 5. De-Reverb Studio
        self.card_dereverb = StudioModuleCard(
            title="De-Reverb Studio",
            default_param="Dry cabine",
            default_reason="Assèche la pièce / réverbe pour un son direct cabine",
        )
        self.grid_layout.addWidget(self.card_dereverb, 2, 0)

        # 6. True-Peak Normalization
        self.card_true_peak = StudioModuleCard(
            title="Plafond True-Peak",
            default_param="-1.0 dBFS",
            default_reason="Plafond de sécurité prévenant l'écrêtage inter-échantillon",
        )
        self.grid_layout.addWidget(self.card_true_peak, 2, 1)

        diag_layout.addLayout(self.grid_layout)

        # Compact footer: Spectral de-bleed
        bottom_strip = QHBoxLayout()
        self.card_debleed = StudioModuleCard(
            title="Dé-bleed spectral anti-fuite (cymbales / aigus)",
            default_param="Aigus",
            default_reason="Atténue les fuites résiduelles de batterie dans la voix",
        )
        self.card_debleed.setFixedHeight(48)
        bottom_strip.addWidget(self.card_debleed)
        diag_layout.addLayout(bottom_strip)

        root.addWidget(self.diag_card)

        # ── (e) Hardware Settings Bar (Model / Format / Export) ──────────
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

        settings_row.addWidget(QLabel("Moteur :"))
        self.model_combo = QComboBox()
        for model in ModelManager.available_models():
            self.model_combo.addItem(model.display_name, model.name)
        self.model_combo.setCurrentIndex(0)
        settings_row.addWidget(self.model_combo, stretch=2)

        settings_row.addWidget(QLabel("Format :"))
        self.format_combo = QComboBox()
        for display_name in OUTPUT_FORMATS:
            self.format_combo.addItem(display_name)
        settings_row.addWidget(self.format_combo, stretch=1)

        self.output_dir_btn = QPushButton("📁 Dossier export")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        settings_row.addWidget(self.output_dir_btn)

        root.addLayout(settings_row)

        # ── (f) Hero Action Section (Start button / Progress) ────────────
        actions = QHBoxLayout()
        actions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions.setSpacing(12)

        self.start_btn = QPushButton("⚡ DÉMARRER LA SÉPARATION")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_separation)
        actions.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_separation)
        actions.addWidget(self.cancel_btn)

        root.addLayout(actions)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("Glissez-déposez un morceau pour démarrer…")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        # ── (g) Synchronized Triple-Sync Audio Player (A/B/C) ────────────
        self.audio_player = AudioPreviewPlayer()
        root.addWidget(self.audio_player)

        root.addStretch()

        # Default to Studio Mode
        self._apply_studio_mode()

    # ── Mode Presets (Pure vs Studio) ───────────────────────────────────

    def _apply_pure_mode(self) -> None:
        """Switch to 100% Pure BS-RoFormer Neural separation (Zero DSP)."""
        self._is_pure_mode = True
        for card in (
            self.card_subbass,
            self.card_leveler,
            self.card_deesser,
            self.card_silence,
            self.card_dereverb,
            self.card_true_peak,
            self.card_debleed,
        ):
            card.setChecked(False)

        self.btn_preset_pure.setStyleSheet(
            "font-size: 11px; font-weight: 700; padding: 6px 14px; "
            "background-color: #ffffff; color: #000000; border-radius: 7px; border: none;"
        )
        self.btn_preset_studio.setStyleSheet(
            "font-size: 11px; font-weight: 600; padding: 6px 14px; "
            "background-color: #12131a; color: #8b8ea4; border-radius: 7px; border: 1px solid #1f2230;"
        )
        self.diag_summary.setText("💎 Mode Brut actif · Acapella 100% pure du réseau de neurones")

    def _apply_studio_mode(self) -> None:
        """Switch to Studio Adaptive Post-Processing mode."""
        self._is_pure_mode = False
        if self._current_diagnostic:
            self._update_diagnostic_ui(self._current_diagnostic)

        self.btn_preset_studio.setStyleSheet(
            "font-size: 11px; font-weight: 700; padding: 6px 14px; "
            "background-color: #ffffff; color: #000000; border-radius: 7px; border: none;"
        )
        self.btn_preset_pure.setStyleSheet(
            "font-size: 11px; font-weight: 600; padding: 6px 14px; "
            "background-color: #12131a; color: #8b8ea4; border-radius: 7px; border: 1px solid #1f2230;"
        )

    # ── Diagnostic & Dynamic Adaptations ────────────────────────────────

    def _reset_diagnostic_ui(self) -> None:
        """Reset the studio rack to idle state."""
        self.drop_zone.set_loaded_file(None)
        self.diag_summary.setText("Déposez un morceau pour calibrer la chaîne")
        for card in (
            self.card_subbass,
            self.card_leveler,
            self.card_deesser,
            self.card_silence,
            self.card_dereverb,
            self.card_true_peak,
            self.card_debleed,
        ):
            card.setEnabled(False)
            card.setChecked(False)

    def _update_diagnostic_ui(self, diag: AudioDiagnostic) -> None:
        """Dynamically configure studio module cards based on acoustic analysis."""
        self._current_diagnostic = diag
        f0_txt = f"F0 ~{int(diag.pitch_f0)} Hz" if diag.pitch_f0 > 0 else "F0 standard"
        self.diag_summary.setText(f"{diag.voice_type} · {f0_txt}")

        # 1. Pitch-Tracked Sub-Bass
        self.card_subbass.setEnabled(True)
        self.card_subbass.update_info(
            param_text=f"{int(diag.adaptive_cutoff_hz)} Hz",
            reason_text=diag.subbass_reason,
            recommended=diag.has_subbass_rumble,
        )
        self.card_subbass.setChecked(diag.has_subbass_rumble and not self._is_pure_mode)

        # 2. Vocal Rider / Dynamic Leveler
        self.card_leveler.setEnabled(True)
        self.card_leveler.update_info(
            param_text="±4.5 dB",
            reason_text=diag.leveler_reason,
            recommended=diag.has_dynamic_imbalance,
        )
        self.card_leveler.setChecked(diag.has_dynamic_imbalance and not self._is_pure_mode)

        # 3. Dynamic De-Esser
        self.card_deesser.setEnabled(True)
        self.card_deesser.update_info(
            param_text=f"{diag.sibilance_hz/1000:.1f} kHz",
            reason_text=diag.sibilance_reason,
            recommended=diag.has_harsh_sibilance,
        )
        self.card_deesser.setChecked(diag.has_harsh_sibilance and not self._is_pure_mode)

        # 4. Silence Purifier
        self.card_silence.setEnabled(True)
        self.card_silence.update_info(
            param_text="-46 dB",
            reason_text=diag.silence_reason,
            recommended=diag.has_noise_in_pauses,
        )
        self.card_silence.setChecked(diag.has_noise_in_pauses and not self._is_pure_mode)

        # 5. De-Reverb Studio
        self.card_dereverb.setEnabled(True)
        self.card_dereverb.update_info(
            param_text="Dry",
            reason_text=diag.reverb_reason,
            recommended=diag.has_reverb,
        )
        self.card_dereverb.setChecked(diag.has_reverb and not self._is_pure_mode)

        # 6. True-Peak Normalization Ceiling
        self.card_true_peak.setEnabled(True)
        self.card_true_peak.update_info(
            param_text="-1.0 dBFS",
            reason_text=diag.true_peak_reason,
            recommended=diag.recommend_true_peak,
        )
        self.card_true_peak.setChecked(diag.recommend_true_peak and not self._is_pure_mode)

        # 7. Spectral De-bleed
        self.card_debleed.setEnabled(True)
        self.card_debleed.update_info(
            param_text="Soft",
            reason_text=diag.debleed_reason,
            recommended=diag.recommend_debleed,
        )
        self.card_debleed.setChecked(diag.recommend_debleed and not self._is_pure_mode)

    # ── Logic & Signal Slots ────────────────────────────────────────────

    def _on_files_dropped(self, paths: list[Path]) -> None:
        self.pending_files.extend(paths)
        primary_file = paths[0]

        # Update hero card in drop zone
        self.drop_zone.set_loaded_file(primary_file)

        if len(self.pending_files) > 1:
            self.file_list.clear()
            for p in self.pending_files:
                self.file_list.addItem(f"🎵  {p.name}")
            self.file_list.setVisible(True)
        else:
            self.file_list.setVisible(False)

        self.start_btn.setEnabled(True)
        self.status_label.setText(f"● {primary_file.name} chargé et prêt")

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
            self.output_dir_btn.setText(f"📁 {self.output_dir.name}")
            self.status_label.setText(f"Dossier : {self.output_dir.name}")

    def _start_separation(self) -> None:
        if not self.pending_files:
            return

        model_name: str = self.model_combo.currentData()
        output_format: str = self.format_combo.currentText()

        self._last_processed_file = self.pending_files[0]

        cutoff_hz = self._current_diagnostic.adaptive_cutoff_hz if self._current_diagnostic else 65.0
        sibilance_hz = self._current_diagnostic.sibilance_hz if self._current_diagnostic else 7200.0

        self.worker = SeparationWorker(
            files=list(self.pending_files),
            model_name=model_name,
            output_format=output_format,
            output_dir=self.output_dir,
            subbass_filter=self.card_subbass.isChecked(),
            subbass_cutoff=cutoff_hz,
            deesser=self.card_deesser.isChecked(),
            deesser_freq=sibilance_hz,
            dereverb=self.card_dereverb.isChecked(),
            silence_purifier=self.card_silence.isChecked(),
            vocal_leveler=self.card_leveler.isChecked(),
            true_peak=self.card_true_peak.isChecked(),
            spectral_debleed=self.card_debleed.isChecked(),
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
        self.status_label.setText("Calcul spectral haute fidélité en cours…")

    def _cancel_separation(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.status_label.setText("Annulation en cours…")

    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_file_completed(self, filename: str, results: Dict[str, Any]) -> None:
        self.status_label.setText(f"✓ {filename} séparé avec succès")
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
