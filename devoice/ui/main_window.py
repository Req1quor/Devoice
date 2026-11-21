"""Studio-grade, high-contrast, ergonomic MainWindow for Devoice."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from devoice.audio_utils import AudioDiagnostic, DSPRackConfig, analyze_audio_track
from devoice.engine import ModelManager, SeparationEngine
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.worker import ReprocessWorker, SeparationWorker, YouTubeDownloadWorker
from devoice.youtube import extract_youtube_url, is_youtube_url

logger = logging.getLogger(__name__)

OUTPUT_FORMATS = [
    "WAV (16-bit)",
    "FLAC (24-bit)",
    "MP3 (320 kbps)",
]


class MainWindow(QMainWindow):
    """Studio-grade audio separation and post-processing desktop workstation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Devoice")
        self.setMinimumSize(660, 620)
        self.resize(680, 640)

        self.pending_files: list[Path] = []
        self.output_dir: Path | None = None
        self.worker: SeparationWorker | None = None
        self.yt_worker: YouTubeDownloadWorker | None = None
        self._last_processed_file: Path | None = None
        self._current_diagnostic: AudioDiagnostic | None = None

        # Post-Separation DSP Reprocessing state
        self._current_raw_vocals_path: Path | None = None
        self._current_raw_instru_path: Path | None = None
        self._current_processed_vocals_path: Path | None = None
        self._reprocess_worker: ReprocessWorker | None = None
        self._ping_pong_flag: bool = False

        self._reprocess_timer = QTimer(self)
        self._reprocess_timer.setSingleShot(True)
        self._reprocess_timer.timeout.connect(self._trigger_reprocess)

        self._build_ui()
        self._update_device_label()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        # ── (a) Header ────────────────────────────────────────────────────
        header = QHBoxLayout()

        self.title_label = QLabel("DEVOICE")
        self.title_label.setObjectName("TitleLabel")
        header.addWidget(self.title_label)

        header.addStretch()

        self.device_label = QLabel("...")
        self.device_label.setObjectName("DeviceBadge")
        header.addWidget(self.device_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        root.addLayout(header)

        # ── (b) Drop Zone ─────────────────────────────────────────────────
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        self.drop_zone.youtube_url_dropped.connect(self._start_youtube_download)
        root.addWidget(self.drop_zone)

        # ── YouTube Ingest Bar ────────────────────────────────────────────
        self.yt_bar = QWidget()
        yt_layout = QHBoxLayout(self.yt_bar)
        yt_layout.setContentsMargins(0, 0, 0, 0)
        yt_layout.setSpacing(8)

        self.yt_input = QLineEdit()
        self.yt_input.setObjectName("YouTubeInput")
        self.yt_input.setPlaceholderText("Coller un lien YouTube (ex: https://youtu.be/...)")
        self.yt_input.returnPressed.connect(self._on_youtube_download_clicked)
        yt_layout.addWidget(self.yt_input, stretch=1)

        self.yt_btn = QPushButton("Télécharger")
        self.yt_btn.setObjectName("YouTubeButton")
        self.yt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.yt_btn.clicked.connect(self._on_youtube_download_clicked)
        yt_layout.addWidget(self.yt_btn)

        root.addWidget(self.yt_bar)

        # ── (c) File Queue (if multiple) ──────────────────────────────────
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(60)
        self.file_list.setVisible(False)
        root.addWidget(self.file_list)

        # ── (d) Settings Card ─────────────────────────────────────────────
        self.settings_card = QFrame()
        self.settings_card.setObjectName("SettingsCard")
        card_layout = QVBoxLayout(self.settings_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        # Row 1: Model & Format & Output
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl_model = QLabel("Modèle :")
        row1.addWidget(lbl_model, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.model_combo = QComboBox()
        self.model_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for model in ModelManager.available_models():
            self.model_combo.addItem(model.display_name, model.name)
        self.model_combo.setCurrentIndex(0)
        row1.addWidget(self.model_combo, stretch=2)

        lbl_format = QLabel("Format :")
        row1.addWidget(lbl_format, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.format_combo = QComboBox()
        self.format_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for display_name in OUTPUT_FORMATS:
            self.format_combo.addItem(display_name)
        row1.addWidget(self.format_combo, stretch=1)

        self.output_dir_btn = QPushButton("Dossier…")
        self.output_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        row1.addWidget(self.output_dir_btn)

        card_layout.addLayout(row1)

        # Row 2: Post-processing toggle
        auto_row = QHBoxLayout()
        auto_row.setSpacing(10)

        self.chk_auto_dsp = QCheckBox("Post-traitement audio (égalisation et réduction du souffle)")
        self.chk_auto_dsp.setChecked(True)
        self.chk_auto_dsp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_auto_dsp.toggled.connect(self._on_auto_dsp_toggled)
        self.chk_auto_dsp.toggled.connect(self._on_dsp_parameter_changed)
        auto_row.addWidget(self.chk_auto_dsp, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.btn_toggle_advanced = QPushButton("Options ▾")
        self.btn_toggle_advanced.setObjectName("OptionsDrawerButton")
        self.btn_toggle_advanced.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_advanced.clicked.connect(self._toggle_advanced_drawer)
        auto_row.addWidget(self.btn_toggle_advanced, alignment=Qt.AlignmentFlag.AlignVCenter)

        card_layout.addLayout(auto_row)

        # Collapsible Drawer
        self.drawer_widget = QWidget()
        self.drawer_widget.setObjectName("DrawerContainer")
        self.drawer_widget.setVisible(False)
        drawer_layout = QGridLayout(self.drawer_widget)
        drawer_layout.setContentsMargins(2, 8, 2, 4)
        drawer_layout.setHorizontalSpacing(10)
        drawer_layout.setVerticalSpacing(10)

        self.chk_leveler = QCheckBox("Égalisation de volume")
        self.chk_silence = QCheckBox("Réduction du souffle")
        self.chk_subbass = QCheckBox("Filtre coupe-bas")
        self.chk_true_peak = QCheckBox("Limiteur anti-crête")
        self.chk_deesser = QCheckBox("De-Esser (sifflements)")
        self.chk_dereverb = QCheckBox("Dé-réverbération")
        self.chk_debleed = QCheckBox("Atténuation des fuites résiduelles")

        drawer_layout.addWidget(self.chk_leveler, 0, 0)
        drawer_layout.addWidget(self.chk_silence, 0, 1)
        drawer_layout.addWidget(self.chk_subbass, 1, 0)
        drawer_layout.addWidget(self.chk_true_peak, 1, 1)
        drawer_layout.addWidget(self.chk_deesser, 2, 0)
        drawer_layout.addWidget(self.chk_dereverb, 2, 1)
        drawer_layout.addWidget(self.chk_debleed, 3, 0, 1, 2)

        for chk in (
            self.chk_subbass,
            self.chk_deesser,
            self.chk_dereverb,
            self.chk_silence,
            self.chk_leveler,
            self.chk_true_peak,
            self.chk_debleed,
        ):
            chk.setCursor(Qt.CursorShape.PointingHandCursor)
            chk.toggled.connect(self._on_dsp_parameter_changed)

        card_layout.addWidget(self.drawer_widget)

        root.addWidget(self.settings_card)

        # ── (e) Action Button ─────────────────────────────────────────────
        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.start_btn = QPushButton("Séparer")
        self.start_btn.setObjectName("PrimaryButton")
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

        # ── (f) Status & Progress ─────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("Prêt")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        # ── (g) Audio Player ──────────────────────────────────────────────
        self.audio_player = AudioPreviewPlayer()
        root.addWidget(self.audio_player)

        root.addStretch()

    # ── UI Drawer & Toggles ─────────────────────────────────────────────

    def _toggle_advanced_drawer(self) -> None:
        is_visible = not self.drawer_widget.isHidden()
        self.drawer_widget.setVisible(not is_visible)
        self.btn_toggle_advanced.setText("Options ▴" if not is_visible else "Options ▾")
        if not is_visible:
            target_h = 790 if self.file_list.isVisible() else 720
            self.resize(self.width(), max(self.height(), target_h))
            if self.audio_player.isVisible():
                self.setMinimumHeight(690)
        else:
            if not self.audio_player.isVisible() and not self.file_list.isVisible():
                self.setMinimumHeight(620)

    def _on_auto_dsp_toggled(self, checked: bool) -> None:
        self.drawer_widget.setEnabled(checked)
        if checked and self._current_diagnostic:
            self._apply_diagnostic_to_checkboxes(self._current_diagnostic)

    def _apply_diagnostic_to_checkboxes(self, diag: AudioDiagnostic) -> None:
        self.chk_subbass.setChecked(diag.has_subbass_rumble)
        self.chk_leveler.setChecked(diag.has_dynamic_imbalance)
        self.chk_deesser.setChecked(diag.has_harsh_sibilance)
        self.chk_silence.setChecked(diag.has_noise_in_pauses)
        self.chk_dereverb.setChecked(diag.has_reverb)
        self.chk_true_peak.setChecked(diag.recommend_true_peak)
        self.chk_debleed.setChecked(diag.recommend_debleed)

    def _on_dsp_parameter_changed(self) -> None:
        """Slot invoked when any DSP checkbox parameter is toggled."""
        if self._current_raw_vocals_path and self._current_raw_vocals_path.exists():
            self.status_label.setText("Actualisation DSP…")
            self._reprocess_timer.start(120)

    def _trigger_reprocess(self) -> None:
        """Debounced trigger launching ReprocessWorker on the retained raw vocal stem."""
        if not (self._current_raw_vocals_path and self._current_raw_vocals_path.exists()):
            return

        if self._reprocess_worker is not None and self._reprocess_worker.isRunning():
            self._reprocess_worker.cancel()
            self._reprocess_worker.wait(300)

        use_dsp = self.chk_auto_dsp.isChecked()
        cutoff_hz = self._current_diagnostic.adaptive_cutoff_hz if self._current_diagnostic else 65.0
        sibilance_hz = self._current_diagnostic.sibilance_hz if self._current_diagnostic else 7200.0

        config = DSPRackConfig(
            enabled=use_dsp,
            silence_purifier=use_dsp and self.chk_silence.isChecked(),
            subbass_filter=use_dsp and self.chk_subbass.isChecked(),
            subbass_cutoff=cutoff_hz,
            dereverb=use_dsp and self.chk_dereverb.isChecked(),
            deesser=use_dsp and self.chk_deesser.isChecked(),
            deesser_freq=sibilance_hz,
            vocal_leveler=use_dsp and self.chk_leveler.isChecked(),
            true_peak=use_dsp and self.chk_true_peak.isChecked(),
            spectral_debleed=use_dsp and self.chk_debleed.isChecked(),
        )

        # Alternating ping-pong output file paths to prevent Windows QMediaPlayer [WinError 32]
        self._ping_pong_flag = not self._ping_pong_flag
        tag = "_vocals_v2.wav" if self._ping_pong_flag else "_vocals_v1.wav"

        raw_stem_name = self._current_raw_vocals_path.stem
        if raw_stem_name.endswith("_raw"):
            clean_base = raw_stem_name[:-4]
        else:
            clean_base = raw_stem_name

        output_path = self._current_raw_vocals_path.parent / f"{clean_base}{tag}"

        engine = SeparationEngine(
            model_name=self.model_combo.currentData() or "bs_roformer",
            output_dir=self._current_raw_vocals_path.parent,
            output_format="WAV",
        )

        self._reprocess_worker = ReprocessWorker(
            engine=engine,
            raw_vocals_path=self._current_raw_vocals_path,
            output_path=output_path,
            config=config,
            instru_path=self._current_raw_instru_path,
            parent=self,
        )
        self._reprocess_worker.reprocess_finished.connect(self._on_reprocess_finished)
        self._reprocess_worker.reprocess_error.connect(self._on_reprocess_error)
        self._reprocess_worker.start()

    def _on_reprocess_finished(self, new_vocals_path: Path) -> None:
        """Handle background reprocess completion: update player and status."""
        self._current_processed_vocals_path = new_vocals_path
        self.audio_player.update_vocals(new_vocals_path)
        self.status_label.setText("Traitement DSP mis à jour")

    def _on_reprocess_error(self, error_message: str) -> None:
        """Handle background reprocess failure."""
        logger.warning("Reprocessing failed: %s", error_message)
        self.status_label.setText(f"Erreur DSP : {error_message}")

    # ── Logic & Signal Slots ────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Paste):
            cb_text = QApplication.clipboard().text().strip()
            if is_youtube_url(cb_text):
                self.yt_input.setText(cb_text)
                self._start_youtube_download(cb_text)
                return
        super().keyPressEvent(event)

    def _on_youtube_download_clicked(self) -> None:
        url_text = self.yt_input.text().strip()
        if not url_text:
            # Check clipboard as a fast shortcut
            cb = QApplication.clipboard().text().strip()
            if is_youtube_url(cb):
                url_text = cb
                self.yt_input.setText(url_text)
            else:
                self.status_label.setText("Collez un lien YouTube valide")
                self.yt_input.setFocus()
                return

        self._start_youtube_download(url_text)

    def _start_youtube_download(self, url: str) -> None:
        norm_url = extract_youtube_url(url)
        if not norm_url:
            self.status_label.setText("Lien YouTube non reconnu")
            return

        self.yt_input.setEnabled(False)
        self.yt_btn.setEnabled(False)
        self.yt_btn.setText("…")
        self.drop_zone.set_downloading("Téléchargement YouTube…", "Connexion à YouTube…")
        self.progress_bar.setValue(5)
        self.progress_bar.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.status_label.setText("Téléchargement YouTube en cours…")

        self.yt_worker = YouTubeDownloadWorker(norm_url, output_dir=self.output_dir)
        self.yt_worker.progress.connect(self._on_youtube_progress)
        self.yt_worker.finished.connect(self._on_youtube_finished)
        self.yt_worker.error.connect(self._on_youtube_error)
        self.yt_worker.start()

    def _on_youtube_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)
        self.drop_zone.set_downloading(f"Téléchargement YouTube… {pct}%", msg)

    def _on_youtube_finished(self, file_path: Path) -> None:
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.yt_input.setEnabled(True)
        self.yt_btn.setEnabled(True)
        self.yt_btn.setText("Télécharger")
        self.yt_input.clear()
        # Automatically load and select the downloaded file for separation!
        self._on_files_dropped([file_path])
        self.status_label.setText(f"{file_path.name} téléchargé et prêt")

    def _on_youtube_error(self, err_msg: str) -> None:
        import re

        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.yt_input.setEnabled(True)
        self.yt_btn.setEnabled(True)
        self.yt_btn.setText("Télécharger")
        self.drop_zone.set_loaded_file(None)
        clean_err = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", err_msg)
        clean_err = clean_err.replace("ERROR:", "").strip()
        short_err = clean_err.split("\n")[-1].strip()
        self.status_label.setText(f"Erreur téléchargement : {short_err}")

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
        self.status_label.setText(f"{primary_file.name} prêt")

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
            "Dossier de sortie",
            str(self.output_dir) if self.output_dir else "",
        )
        if directory:
            self.output_dir = Path(directory)
            self.output_dir_btn.setText(self.output_dir.name)
            self.status_label.setText(f"Dossier : {self.output_dir.name}")

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
        self.status_label.setText("Séparation en cours…")

    def _cancel_separation(self) -> None:
        if self.yt_worker is not None and self.yt_worker.isRunning():
            self.yt_worker.cancel()
            self.status_label.setText("Annulation du téléchargement…")
            self.drop_zone.set_loaded_file(None)
            self.yt_input.setEnabled(True)
            self.yt_btn.setEnabled(True)
            self.yt_btn.setText("Télécharger")
            self.progress_bar.setVisible(False)
            self.cancel_btn.setVisible(False)
        elif self.worker is not None:
            self.worker.cancel()
            self.status_label.setText("Annulation…")
        if not self.audio_player.isVisible() and self.drawer_widget.isHidden():
            self.setMinimumHeight(620)

    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_file_completed(self, filename: str, results: dict[str, Any]) -> None:
        self.status_label.setText(f"{filename} terminé")
        vocals_path = Path(results.get("vocals", ""))
        instru_path = Path(results.get("instru", "") or results.get("instrumental", ""))

        raw_v = results.get("raw_vocals")
        if raw_v:
            self._current_raw_vocals_path = Path(raw_v)
        elif vocals_path.exists():
            self._current_raw_vocals_path = vocals_path

        raw_i = results.get("raw_instrumental") or results.get("raw_instru")
        if raw_i:
            self._current_raw_instru_path = Path(raw_i)
        elif instru_path.exists():
            self._current_raw_instru_path = instru_path

        if vocals_path.exists():
            self._current_processed_vocals_path = vocals_path

        if vocals_path.exists() and instru_path.exists():
            self.audio_player.set_results(
                vocals_path=vocals_path,
                instru_path=instru_path,
                original_path=self._last_processed_file,
            )
            if not self.drawer_widget.isHidden():
                self.setMinimumHeight(690)
                self.resize(self.width(), max(self.height(), 760))
            else:
                self.resize(self.width(), max(self.height(), 700))
        elif not self.audio_player.isVisible() and self.drawer_widget.isHidden():
            self.setMinimumHeight(620)

    def _on_file_error(self, filename: str, error: str) -> None:
        self.status_label.setText(f"Erreur : {error}")

    def _on_all_completed(self) -> None:
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.start_btn.setEnabled(True)
        self.pending_files.clear()
        self.file_list.clear()
        self.file_list.setVisible(False)
        if not self.audio_player.isVisible() and self.drawer_widget.isHidden():
            self.setMinimumHeight(620)

    def _update_device_label(self) -> None:
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                short_gpu = gpu_name.replace("NVIDIA GeForce ", "").replace("NVIDIA ", "")
                self.device_label.setText(f"● {short_gpu}")
            else:
                self.device_label.setText("● CPU")
        except Exception:
            self.device_label.setText("● CPU")
