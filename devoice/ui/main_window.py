"""Main application window for Devoice."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
from devoice.model_manager import MODELS
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.worker import SeparationWorker


class MainWindow(QMainWindow):
    """Primary window that assembles every UI element of the Devoice app.

    Manages the full separation workflow: file selection → settings →
    processing → preview of results.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Devoice")
        self.setMinimumSize(700, 600)
        self.resize(800, 650)

        self.pending_files: List[Path] = []
        self.output_dir: Path | None = None
        self.worker: SeparationWorker | None = None

        self._build_ui()
        self._update_device_label()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble every widget inside a central vertical layout."""
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        # ---- (a) Header ----
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        self.title_label = QLabel("Devoice")
        self.title_label.setObjectName("TitleLabel")
        title_col.addWidget(self.title_label)

        self.subtitle_label = QLabel("Séparation vocale haute qualité")
        self.subtitle_label.setObjectName("SubtitleLabel")
        title_col.addWidget(self.subtitle_label)

        header.addLayout(title_col)
        header.addStretch()

        self.device_label = QLabel("")
        self.device_label.setObjectName("DeviceLabel")
        header.addWidget(self.device_label, alignment=Qt.AlignmentFlag.AlignRight)

        root.addLayout(header)

        # ---- (b) Drop Zone ----
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        root.addWidget(self.drop_zone)

        # ---- (c) File queue list ----
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(120)
        self.file_list.setVisible(False)
        root.addWidget(self.file_list)

        # ---- (d) Settings row ----
        settings_row = QHBoxLayout()

        settings_row.addWidget(QLabel("Mode :"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("💎 Studio (BS-RoFormer - Qualité Max)", "bs_roformer")
        self.model_combo.addItem("🎯 Équilibré (MDX-Net - Rapide & Clean)", "mdx_net")
        self.model_combo.setCurrentIndex(0)
        settings_row.addWidget(self.model_combo)

        settings_row.addSpacing(16)

        settings_row.addWidget(QLabel("Format :"))
        self.format_combo = QComboBox()
        for display_name in OUTPUT_FORMATS:
            self.format_combo.addItem(display_name)
        settings_row.addWidget(self.format_combo)

        settings_row.addStretch()

        self.output_dir_btn = QPushButton("📁 Dossier de sortie")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        settings_row.addWidget(self.output_dir_btn)

        root.addLayout(settings_row)

        # ---- (e) Progress bar ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        # ---- (f) Status label ----
        self.status_label = QLabel("En attente de fichiers…")
        self.status_label.setObjectName("StatusLabel")
        root.addWidget(self.status_label)

        # ---- (g) Action buttons ----
        actions = QHBoxLayout()
        actions.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("🎤  Séparer")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_separation)
        actions.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_separation)
        actions.addWidget(self.cancel_btn)

        root.addLayout(actions)

        # ---- (h) Audio preview player ----
        self.audio_player = AudioPreviewPlayer()
        root.addWidget(self.audio_player)

        # ---- (i) Bottom stretch ----
        root.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_files_dropped(self, files: List[Path]) -> None:
        """Add *files* to the pending queue and update the file list widget.

        Args:
            files: Paths emitted by :class:`DropZone`.
        """
        for f in files:
            if f not in self.pending_files:
                self.pending_files.append(f)
                self.file_list.addItem(f.name)
        self.file_list.setVisible(True)
        self.start_btn.setEnabled(True)
        self.status_label.setText(f"{len(self.pending_files)} fichier(s) en attente")

    def _select_output_dir(self) -> None:
        """Open a directory picker and store the chosen output folder."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de sortie",
            str(self.output_dir) if self.output_dir else "",
        )
        if directory:
            self.output_dir = Path(directory)
            self.status_label.setText(f"Dossier de sortie : {self.output_dir}")

    def _start_separation(self) -> None:
        """Launch the separation worker with current settings."""
        if not self.pending_files:
            return

        model_name: str = self.model_combo.currentData()
        output_format: str = self.format_combo.currentText()

        self.worker = SeparationWorker(
            files=list(self.pending_files),
            model_name=model_name,
            output_format=output_format,
            output_dir=self.output_dir,
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
        """Request cancellation of the running worker."""
        if self.worker is not None:
            self.worker.cancel()
            self.status_label.setText("Annulation en cours…")

    def _on_progress(self, pct: int, msg: str) -> None:
        """Update progress bar value and status text.

        Args:
            pct: Progress percentage (0-100).
            msg: Human-readable status message.
        """
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_file_completed(self, filename: str, results: Dict[str, Any]) -> None:
        """Handle a single file's successful completion.

        Args:
            filename: Base name of the processed file.
            results: Dict with ``"vocals"`` and ``"instru"`` path strings.
        """
        self.status_label.setText(f"✅ {filename} terminé")
        vocals_path = Path(results.get("vocals", ""))
        instru_path = Path(results.get("instru", "") or results.get("instrumental", ""))
        if vocals_path.exists() and instru_path.exists():
            self.audio_player.set_results(vocals_path, instru_path)

    def _on_file_error(self, filename: str, error: str) -> None:
        """Display an error message for a failed file.

        Args:
            filename: Base name of the file that failed.
            error: Error description.
        """
        self.status_label.setText(f"❌ Erreur sur {filename} : {error}")

    def _on_all_completed(self) -> None:
        """Reset UI state after all files have been processed."""
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.start_btn.setEnabled(True)
        self.status_label.setText("Terminé !")
        self.pending_files.clear()
        self.file_list.clear()
        self.file_list.setVisible(False)

    def _update_device_label(self) -> None:
        """Detect CUDA availability and display the device name."""
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                self.device_label.setText(f"⚡ GPU : {gpu_name}")
                self.device_label.setStyleSheet("color: #4ade80; font-weight: bold;")
            else:
                self.device_label.setText("💻 CPU (Pas de CG active)")
                self.device_label.setStyleSheet("color: #facc15; font-weight: bold;")
        except ImportError:
            self.device_label.setText("💻 CPU")
