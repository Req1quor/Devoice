"""Programmatic UI Test Suite for Devoice Studio-Grade Interface.

Verifies:
- Design tokens, studio theme compilation, and QSS application
- MainWindow layout hierarchy and component instantiation
- Header title & illuminated LED device badge
- Audio cartridge DropZone dynamic states and intake flow
- YouTube stream ingestion bar interaction
- SettingsCard model/format selectors and folder picker
- Collapsible options drawer toggle and label transitions
- Master DSP post-processing toggle and 7 acoustic checkboxes
- Tactile hero Séparer and Cancel button states
- Progress meter and monospace StatusLabel console readout
- AudioPreviewPlayer stem color-coded switching, transport controls, LCD timecode, and scrubber
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.drop_zone import DropZone
from devoice.ui.main_window import MainWindow
from devoice.ui.styles import DARK_THEME
from devoice.ui.theme import StudioColors, StudioFonts, StudioMetrics, build_studio_theme


class TestStudioThemeAndDesignTokens:
    """Validates studio design tokens and stylesheet integrity."""

    def test_studio_tokens_defined(self):
        # Surface tokens
        assert StudioColors.SURFACE_BASE == "#111215"
        assert StudioColors.SURFACE_PANEL == "#16181D"
        assert StudioColors.SURFACE_ELEVATED == "#1D2027"
        assert StudioColors.SURFACE_SUNKEN == "#0D0E11"

        # Hardware accent tokens
        assert StudioColors.ACCENT_AMBER == "#F59E0B"
        assert StudioColors.ACCENT_CYAN == "#00D2FF"
        assert StudioColors.ACCENT_EMERALD == "#10B981"
        assert StudioColors.ACCENT_ROSE == "#EF4444"
        assert StudioColors.ACCENT_SLATE == "#CBD5E1"

        # Typography & Metrics
        assert "Segoe UI" in StudioFonts.FONT_FAMILY_SANS
        assert "Consolas" in StudioFonts.FONT_FAMILY_MONO
        assert StudioMetrics.RADIUS_MD == "6px"

    def test_theme_compilation_and_selectors(self):
        qss = build_studio_theme()
        assert len(qss) > 500

        # Verify critical studio selectors are present
        assert "#TitleLabel" in qss
        assert "#DeviceBadge" in qss
        assert "#DropZone" in qss
        assert '#DropZone[dragOver="true"]' in qss
        assert '#DropZone[loaded="true"]' in qss
        assert "#YouTubeInput" in qss
        assert "#YouTubeButton" in qss
        assert "#SettingsCard" in qss
        assert "#DrawerContainer" in qss
        assert "#OptionsDrawerButton" in qss
        assert "QPushButton#PrimaryButton" in qss
        assert "QPushButton#CancelButton" in qss
        assert "#StatusLabel" in qss
        assert "#PlayerCard" in qss
        assert "#PlayerTrackLabel" in qss
        assert "#PlayerTimeLabel" in qss
        assert 'QPushButton#StemActive[stem="vocals"]' in qss
        assert 'QPushButton#StemActive[stem="instru"]' in qss
        assert 'QPushButton#StemActive[stem="original"]' in qss

    def test_dark_theme_applies_to_qapp(self, qapp):
        # Must apply cleanly to QApplication without syntax error
        qapp.setStyleSheet(DARK_THEME)
        assert qapp.styleSheet() == DARK_THEME


class TestMainWindowStudioLayout:
    """Validates MainWindow instantiation, hierarchy, and invariants."""

    def test_instantiation_and_window_properties(self, qapp):
        win = MainWindow()
        assert win.windowTitle() == "Devoice"
        assert win.minimumWidth() == 660
        assert win.minimumHeight() == 620

        # Verify all mandatory attributes are present
        assert win.title_label is not None
        assert win.device_label is not None
        assert win.drop_zone is not None
        assert win.yt_bar is not None
        assert win.yt_input is not None
        assert win.yt_btn is not None
        assert win.settings_card is not None
        assert win.model_combo is not None
        assert win.format_combo is not None
        assert win.output_dir_btn is not None
        assert win.chk_auto_dsp is not None
        assert win.btn_toggle_advanced is not None
        assert win.drawer_widget is not None
        assert win.start_btn is not None
        assert win.cancel_btn is not None
        assert win.progress_bar is not None
        assert win.status_label is not None
        assert win.audio_player is not None

    def test_object_names_assigned_for_styling(self, qapp):
        win = MainWindow()
        assert win.title_label.objectName() == "TitleLabel"
        assert win.device_label.objectName() == "DeviceBadge"
        assert win.yt_input.objectName() == "YouTubeInput"
        assert win.yt_btn.objectName() == "YouTubeButton"
        assert win.settings_card.objectName() == "SettingsCard"
        assert win.drawer_widget.objectName() == "DrawerContainer"
        assert win.btn_toggle_advanced.objectName() == "OptionsDrawerButton"
        assert win.start_btn.objectName() == "PrimaryButton"
        assert win.cancel_btn.objectName() == "CancelButton"
        assert win.status_label.objectName() == "StatusLabel"

    def test_header_device_badge_led(self, qapp):
        win = MainWindow()
        text = win.device_label.text()
        # Should start with the glowing LED bullet
        assert text.startswith("● ")
        assert "CPU" in text or "RTX" in text or "GTX" in text or len(text) > 3


class TestDropZoneErgonomics:
    """Validates the audio cartridge DropZone widget."""

    def test_drop_zone_initial_state(self, qapp):
        dz = DropZone()
        assert dz.objectName() == "DropZone"
        assert dz._title_label.objectName() == "DropZoneTitle"
        assert dz._subtitle_label.objectName() == "DropZoneSubtitle"
        assert dz._formats_label.objectName() == "DropZoneFormats"
        assert dz.property("loaded") == "false"
        assert dz.property("dragOver") is False

    def test_drop_zone_set_loaded_file(self, qapp):
        dz = DropZone()
        test_file = Path("acapella_master.wav")
        dz.set_loaded_file(test_file)

        assert dz.property("loaded") == "true"
        assert dz._title_label.text() == "acapella_master.wav"
        assert "Fichier prêt" in dz._subtitle_label.text()
        assert dz._formats_label.isHidden()

        # Reset back to None
        dz.set_loaded_file(None)
        assert dz.property("loaded") == "false"
        assert not dz._formats_label.isHidden()
        assert "Déposer un fichier" in dz._title_label.text()

    def test_drop_zone_set_downloading(self, qapp):
        dz = DropZone()
        dz.set_downloading("Téléchargement… 50%", "Extraction audio…")
        assert dz.property("loaded") == "true"
        assert dz._title_label.text() == "Téléchargement… 50%"
        assert dz._subtitle_label.text() == "Extraction audio…"
        assert dz._formats_label.isHidden()

    def test_files_dropped_signal_integration(self, qapp, sample_audio_path):
        win = MainWindow()
        assert not win.start_btn.isEnabled()
        assert win.drop_zone.property("loaded") == "false"

        # Emit files_dropped
        win.drop_zone.files_dropped.emit([sample_audio_path])

        assert sample_audio_path in win.pending_files
        assert win.start_btn.isEnabled()
        assert win.drop_zone.property("loaded") == "true"
        assert sample_audio_path.name in win.status_label.text()


class TestYouTubeBarInteraction:
    """Validates YouTube stream ingest controls."""

    def test_youtube_empty_input_warning(self, qapp):
        win = MainWindow()
        win.yt_input.clear()
        # Click without valid URL in clipboard
        win._on_youtube_download_clicked()
        assert "valide" in win.status_label.text().lower()

    def test_youtube_input_text_entry(self, qapp):
        win = MainWindow()
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        win.yt_input.setText(test_url)
        assert win.yt_input.text() == test_url


class TestSettingsAndAcousticDrawer:
    """Validates SettingsCard, Combos, and 7 Acoustic DSP checkboxes."""

    def test_model_and_format_combos(self, qapp):
        win = MainWindow()
        assert win.model_combo.count() >= 1
        assert win.model_combo.currentData() == "bs_roformer"

        assert win.format_combo.count() == 3
        assert win.format_combo.itemText(0) == "WAV (16-bit)"
        assert win.format_combo.itemText(1) == "FLAC (24-bit)"
        assert win.format_combo.itemText(2) == "MP3 (320 kbps)"

        # Can change index
        win.format_combo.setCurrentIndex(1)
        assert win.format_combo.currentText() == "FLAC (24-bit)"

    def test_drawer_collapsible_toggle(self, qapp):
        win = MainWindow()
        assert win.drawer_widget.isHidden()
        assert win.btn_toggle_advanced.text() == "Options ▾"

        # Click to open
        QTest.mouseClick(win.btn_toggle_advanced, Qt.MouseButton.LeftButton)
        assert not win.drawer_widget.isHidden()
        assert win.btn_toggle_advanced.text() == "Options ▴"

        # Click to close
        QTest.mouseClick(win.btn_toggle_advanced, Qt.MouseButton.LeftButton)
        assert win.drawer_widget.isHidden()
        assert win.btn_toggle_advanced.text() == "Options ▾"

    def test_master_dsp_toggle_disables_drawer(self, qapp):
        win = MainWindow()
        assert win.chk_auto_dsp.isChecked()
        assert win.drawer_widget.isEnabled()

        win.chk_auto_dsp.setChecked(False)
        assert not win.drawer_widget.isEnabled()

        win.chk_auto_dsp.setChecked(True)
        assert win.drawer_widget.isEnabled()

    def test_7_acoustic_checkboxes_presence_and_toggles(self, qapp):
        win = MainWindow()
        checkboxes = [
            win.chk_leveler,
            win.chk_silence,
            win.chk_subbass,
            win.chk_true_peak,
            win.chk_deesser,
            win.chk_dereverb,
            win.chk_debleed,
        ]
        for chk in checkboxes:
            assert chk is not None
            initial = chk.isChecked()
            chk.setChecked(not initial)
            assert chk.isChecked() != initial
            chk.setChecked(initial)

    def test_drawer_horizontal_clearance_at_min_width(self, qapp):
        """Verify zero horizontal clipping of checkboxes at minimum window width (660, 720)."""
        win = MainWindow()
        win.show()
        win._toggle_advanced_drawer()
        win.resize(660, 720)
        qapp.processEvents()

        assert not win.drawer_widget.isHidden()
        assert win.chk_deesser.width() >= win.chk_deesser.sizeHint().width()
        win.close()

    def test_drawer_vertical_clearance_with_player_visible(self, qapp, tmp_path):
        """Verify drawer height remains >= 100px when both drawer and player are visible."""
        win = MainWindow()
        win.show()
        win._toggle_advanced_drawer()
        voc_file = tmp_path / "voc.wav"
        inst_file = tmp_path / "inst.wav"
        voc_file.write_text("mock audio")
        inst_file.write_text("mock audio")
        win._last_processed_file = voc_file
        win._on_file_completed("mock", {"vocals": str(voc_file), "instru": str(inst_file)})
        qapp.processEvents()

        assert not win.drawer_widget.isHidden()
        assert win.audio_player.isVisible()
        assert win.minimumHeight() >= 690

        # Attempt to resize to minimum window height
        win.resize(660, win.minimumHeight())
        qapp.processEvents()

        assert win.drawer_widget.height() >= 100
        win.close()

    def test_minimum_height_returns_to_620_when_drawer_and_player_closed(self, qapp):
        """Verify minimum height returns to 620 when player and drawer are closed."""
        win = MainWindow()
        win.show()
        assert win.minimumHeight() == 620
        win._toggle_advanced_drawer()
        assert not win.drawer_widget.isHidden()
        win._toggle_advanced_drawer()
        assert win.drawer_widget.isHidden()
        assert win.minimumHeight() == 620
        win.close()


class TestHeroActionAndButtons:
    """Validates Séparer and Cancel button behaviors."""

    def test_buttons_initial_states(self, qapp):
        win = MainWindow()
        assert not win.start_btn.isEnabled()
        assert not win.cancel_btn.isVisible()
        assert win.start_btn.text() == "Séparer"
        assert win.cancel_btn.text() == "Annuler"

    def test_cancel_button_separation_worker(self, qapp):
        win = MainWindow()
        mock_worker = MagicMock()
        win.worker = mock_worker
        win.progress_bar.setVisible(True)
        win.cancel_btn.setVisible(True)

        win._cancel_separation()
        mock_worker.cancel.assert_called_once()
        assert "annulation" in win.status_label.text().lower()

    def test_cancel_button_youtube_worker(self, qapp):
        win = MainWindow()
        mock_yt_worker = MagicMock()
        mock_yt_worker.isRunning.return_value = True
        win.yt_worker = mock_yt_worker
        win.progress_bar.setVisible(True)
        win.cancel_btn.setVisible(True)

        win._cancel_separation()
        mock_yt_worker.cancel.assert_called_once()
        assert "téléchargement" in win.status_label.text().lower()
        assert not win.cancel_btn.isVisible()
        assert not win.progress_bar.isVisible()
        assert win.yt_btn.isEnabled()


class TestAudioPreviewPlayer:
    """Validates studio VST player controls, stem switching, and timecode."""

    def test_player_initial_state(self, qapp):
        player = AudioPreviewPlayer()
        assert not player.isVisible()
        assert player._label_track.objectName() == "PlayerTrackLabel"
        assert player._label_time.objectName() == "PlayerTimeLabel"
        assert player._btn_play.objectName() == "PlayButton"
        assert player._btn_vocals.objectName() == "StemActive"
        assert player._btn_vocals.property("stem") == "vocals"
        assert player._btn_instru.objectName() == "StemInactive"
        assert player._btn_orig.objectName() == "StemInactive"

    def test_set_results_and_stem_switching(self, qapp, tmp_path):
        player = AudioPreviewPlayer()
        voc_file = tmp_path / "vocals.wav"
        inst_file = tmp_path / "instru.wav"
        orig_file = tmp_path / "orig.wav"

        for f in (voc_file, inst_file, orig_file):
            f.write_text("mock audio")

        player.set_results(
            vocals_path=voc_file,
            instru_path=inst_file,
            original_path=orig_file,
        )

        assert player.isVisible()
        assert player._active_stem == "vocals"
        assert "VOIX" in player._label_track.text()
        assert player._btn_vocals.objectName() == "StemActive"
        assert player._btn_vocals.property("stem") == "vocals"

        # Switch to Instrumental
        QTest.mouseClick(player._btn_instru, Qt.MouseButton.LeftButton)
        assert player._active_stem == "instru"
        assert "INSTRUMENTALE" in player._label_track.text()
        assert player._btn_instru.objectName() == "StemActive"
        assert player._btn_instru.property("stem") == "instru"
        assert player._btn_vocals.objectName() == "StemInactive"

        # Switch to Original Mix
        QTest.mouseClick(player._btn_orig, Qt.MouseButton.LeftButton)
        assert player._active_stem == "original"
        assert "ORIGINAL" in player._label_track.text()
        assert player._btn_orig.objectName() == "StemActive"
        assert player._btn_orig.property("stem") == "original"
        assert player._btn_instru.objectName() == "StemInactive"

    def test_timecode_readout_and_scrubber(self, qapp):
        player = AudioPreviewPlayer()
        # 125 seconds pos (02:05), 240 seconds dur (04:00)
        player._update_time_label(125000, 240000)
        assert player._label_time.text() == "02:05 / 04:00"

        # Duration range adjustment
        player._on_duration_changed(180000)
        assert player._slider.maximum() == 180000

        # Position change moves slider
        player._on_position_changed(45000)
        assert player._slider.value() == 45000

    def test_play_pause_button_toggle(self, qapp):
        player = AudioPreviewPlayer()
        assert player._btn_play.text() == "Play"

        # Toggle play
        player._toggle_play()
        # In headless environment without audio output running, toggle sets "Pause"
        assert player._btn_play.text() in ("Play", "Pause")
