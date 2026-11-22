"""Studio-Grade Runtime Setup Dialog for Devoice.

Displays detected hardware, lets the user select their preferred runtime flavor
(NVIDIA CUDA GPU or Standard CPU), and performs seamless dynamic downloading
with a live progress bar and status readout in pure Noir & Blanc style.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtCore import QSettings, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from devoice.runtime_manager import (
    detect_system_hardware,
    download_file_with_progress,
    extract_zip_archive,
    get_runtime_dir,
    setup_runtime_environment,
)
from devoice.ui.window_effects import apply_windows_dark_titlebar


class RuntimeDownloadWorker(QThread):
    """Background worker for downloading and unpacking the AI runtime."""

    progress_updated = pyqtSignal(int, str)
    finished_success = pyqtSignal()
    finished_error = pyqtSignal(str)

    def __init__(self, flavor: str, target_dir: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.flavor = flavor
        self.target_dir = target_dir or get_runtime_dir()
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(self) -> None:
        try:
            runtime_dir = self.target_dir
            runtime_dir.mkdir(parents=True, exist_ok=True)

            # Official PyTorch Windows wheels (standard zip archives)
            # Extracted directly into the user chosen runtime directory
            if self.flavor == "cuda":
                # PyTorch 2.5.1 + CUDA 12.1 for Windows
                url = "https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp39-cp39-win_amd64.whl"
                whl_name = "torch_cuda.whl"
            else:
                # PyTorch 2.5.1 CPU for Windows
                url = "https://download.pytorch.org/whl/cpu/torch-2.5.1%2Bcpu-cp39-cp39-win_amd64.whl"
                whl_name = "torch_cpu.whl"

            dest_whl = runtime_dir / whl_name
            self.progress_updated.emit(5, "Connexion au serveur de téléchargement…")

            download_file_with_progress(
                url=url,
                dest_path=dest_whl,
                progress_callback=lambda pct, msg: self.progress_updated.emit(int(pct * 0.85), msg),
                cancel_flag=lambda: self._is_cancelled,
            )

            if self._is_cancelled:
                return

            self.progress_updated.emit(88, "Décompression et enregistrement du moteur IA…")
            extract_zip_archive(
                zip_path=dest_whl,
                target_dir=runtime_dir,
                progress_callback=lambda pct, msg: self.progress_updated.emit(88 + int(pct * 0.11), msg),
            )

            # Clean up wheel archive to save disk space
            try:
                if dest_whl.exists():
                    dest_whl.unlink()
            except Exception:
                pass

            # Activate newly deployed runtime
            setup_runtime_environment(runtime_dir)
            self.progress_updated.emit(100, "Moteur audio prêt.")
            self.finished_success.emit()

        except Exception as e:
            self.finished_error.emit(str(e))


class RuntimeSetupDialog(QDialog):
    """Studio-grade onboarding dialog to download the AI runtime on first launch."""

    runtime_ready = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Devoice — Configuration Initiale")
        self.setFixedSize(560, 470)
        self.setStyleSheet("background-color: #09090B; color: #F4F4F5; font-family: 'Segoe UI', sans-serif;")

        self._worker: RuntimeDownloadWorker | None = None
        self._build_ui()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        apply_windows_dark_titlebar(
            int(self.winId()),
            bg_color=(9, 9, 11),
            text_color=(244, 244, 245),
            border_color=(39, 39, 42),
        )

    def _get_disk_space_text(self, path_str: str) -> str:
        try:
            p = Path(path_str)
            anchor = p.anchor if p.anchor else "C:\\"
            _, _, free = shutil.disk_usage(anchor)
            free_gb = free / (1024**3)
            drive_letter = p.drive or "C:"
            return f"Emplacement : {drive_letter} ({free_gb:.1f} Go d'espace libre disponible)"
        except Exception:
            return ""

    def _on_browse_location(self) -> None:
        current = self.path_edit.text()
        chosen = QFileDialog.getExistingDirectory(self, "Choisir le dossier de stockage Devoice", current)
        if chosen:
            chosen_path = Path(chosen)
            if chosen_path.name.lower() != "runtime":
                chosen_path = chosen_path / "runtime"
            self.path_edit.setText(str(chosen_path))
            self.disk_info_label.setText(self._get_disk_space_text(str(chosen_path)))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header Title
        title_label = QLabel("DEVOICE")
        title_label.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 1.5px; color: #FFFFFF;")
        layout.addWidget(title_label)

        sub_label = QLabel("Configuration initiale du moteur de séparation neuronale")
        sub_label.setStyleSheet("font-size: 13px; color: #A1A1AA; font-weight: 500;")
        layout.addWidget(sub_label)

        # Hardware detection badge card
        hw = detect_system_hardware()
        badge_card = QFrame()
        badge_card.setStyleSheet("background-color: #111114; border: 1px solid #27272A; border-radius: 8px; padding: 12px;")
        badge_layout = QVBoxLayout(badge_card)
        badge_layout.setSpacing(6)

        gpu_name = hw["gpu_name"]
        badge_text = QLabel(f"● Matériel détecté : {gpu_name}")
        badge_text.setStyleSheet("font-size: 12.5px; font-weight: 700; color: #FFFFFF;")
        badge_layout.addWidget(badge_text)

        desc_text = QLabel(
            "L'installateur Devoice a été optimisé à ~130 Mo. "
            "Pour démarrer la séparation audio, choisissez le pack d'exécution adapté à votre PC :"
        )
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11.5px; color: #A1A1AA;")
        badge_layout.addWidget(desc_text)
        layout.addWidget(badge_card)

        # Radio options
        self.radio_cuda = QRadioButton("Pack GPU NVIDIA (CUDA 12.1) — Recommandé (Séparation en 10-15s)")
        self.radio_cuda.setStyleSheet("font-size: 12px; font-weight: 600; color: #FFFFFF; spacing: 8px;")

        self.radio_cpu = QRadioButton("Pack Standard Processeur (CPU) — Pour tout ordinateur sans carte NVIDIA")
        self.radio_cpu.setStyleSheet("font-size: 12px; font-weight: 500; color: #A1A1AA; spacing: 8px;")

        if hw["has_nvidia"]:
            self.radio_cuda.setChecked(True)
        else:
            self.radio_cpu.setChecked(True)

        layout.addWidget(self.radio_cuda)
        layout.addWidget(self.radio_cpu)

        # Location selection card (ensures user drive choice is respected)
        loc_frame = QFrame()
        loc_frame.setStyleSheet("background-color: #111114; border: 1px solid #27272A; border-radius: 8px; padding: 10px 12px;")
        loc_layout = QVBoxLayout(loc_frame)
        loc_layout.setSpacing(6)

        loc_label = QLabel("Emplacement de stockage du moteur et des modèles IA :")
        loc_label.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #FFFFFF;")
        loc_layout.addWidget(loc_label)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(str(get_runtime_dir()))
        self.path_edit.setStyleSheet("background-color: #18181B; border: 1px solid #3F3F46; border-radius: 4px; padding: 6px 10px; color: #F4F4F5; font-size: 11px;")
        self.path_edit.setReadOnly(True)

        self.btn_browse = QPushButton("Parcourir…")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet(
            "QPushButton { background-color: #27272A; color: #FFFFFF; border: 1px solid #3F3F46; border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; }"
            "QPushButton:hover { background-color: #3F3F46; }"
        )
        self.btn_browse.clicked.connect(self._on_browse_location)
        path_row.addWidget(self.path_edit)
        path_row.addWidget(self.btn_browse)
        loc_layout.addLayout(path_row)

        self.disk_info_label = QLabel(self._get_disk_space_text(self.path_edit.text()))
        self.disk_info_label.setStyleSheet("font-size: 10.5px; color: #71717A;")
        loc_layout.addWidget(self.disk_info_label)
        layout.addWidget(loc_frame)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #18181B; border: 1px solid #27272A; border-radius: 4px; color: transparent; }"
            "QProgressBar::chunk { background-color: #FFFFFF; border-radius: 3px; }"
        )
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status text
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 11.5px; color: #A1A1AA; font-weight: 500;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Action button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_download = QPushButton("Télécharger et activer le moteur")
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #000000; border: 1px solid #FFFFFF; "
            "border-radius: 6px; font-size: 13px; font-weight: 700; padding: 10px 22px; }"
            "QPushButton:hover { background-color: #E4E4E7; border-color: #E4E4E7; }"
            "QPushButton:pressed { background-color: #D4D4D8; }"
            "QPushButton:disabled { background-color: #18181B; color: #52525B; border-color: #27272A; }"
        )
        self.btn_download.clicked.connect(self._on_start_download)
        btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)

    def _on_start_download(self) -> None:
        self.btn_download.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.radio_cuda.setEnabled(False)
        self.radio_cpu.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.status_label.setText("Démarrage du téléchargement…")

        target_dir = Path(self.path_edit.text())
        # Save choice to persistent registry
        settings = QSettings("Devoice", "Devoice")
        settings.setValue("runtime_dir", str(target_dir))
        settings.setValue("models_dir", str(target_dir.parent / "models"))

        flavor = "cuda" if self.radio_cuda.isChecked() else "cpu"
        self._worker = RuntimeDownloadWorker(flavor=flavor, target_dir=target_dir, parent=self)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.finished_success.connect(self._on_success)
        self._worker.finished_error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_success(self) -> None:
        self.status_label.setText("Moteur configuré avec succès ! Démarrage de Devoice…")
        self.runtime_ready.emit()
        self.accept()

    def _on_error(self, err_msg: str) -> None:
        self.btn_download.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.radio_cuda.setEnabled(True)
        self.radio_cpu.setEnabled(True)
        self.status_label.setText(f"Erreur : {err_msg}")
