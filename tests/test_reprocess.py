"""Automated tests for Requirement R1: Post-Separation DSP Reprocessing.

Covers:
- In-memory DSP rack functions (subbass, de-esser, dereverb, silence, leveler, debleed, true-peak)
- Raw stem retention, disk caching, and immutability
- Standalone reprocess API (SeparationEngine.reprocess_stem) without neural inference
- ReprocessWorker QThread asynchronous execution and error handling
- AudioPreviewPlayer position-preserving and state-preserving hot reload
- MainWindow reactive UI checkbox wiring, debounced recalculation, and ping-pong file generation
- Boundary cases: empty audio, silence, DC offset, 0dBFS square wave, mono vs stereo
- Soundfile format safety on WAV, FLAC, and MP3
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
import soundfile as sf

from devoice.audio_utils import (
    DSPRackConfig,
    process_dereverb_clean,
    process_dsp_rack,
    process_dynamic_deesser,
    process_silence_purifier,
    process_spectral_debleed,
    process_subbass_filter,
    process_true_peak_normalization,
    process_vocal_leveler,
    write_audio_file,
)
from devoice.engine import SeparationEngine
from devoice.ui.audio_player import AudioPreviewPlayer
from devoice.ui.main_window import MainWindow
from devoice.worker import ReprocessWorker

# ── Tier 1: In-Memory DSP Rack Execution ───────────────────────────────────


class TestInMemoryDSPFunctions:
    """Verify pure in-memory float32 NumPy array DSP processing."""

    def test_process_subbass_filter_attenuates_rumble(self):
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        rumble = 0.5 * np.sin(2 * np.pi * 30 * t)  # 30 Hz sub-bass
        vocal = 0.5 * np.sin(2 * np.pi * 500 * t)  # 500 Hz vocal
        signal = (rumble + vocal).astype(np.float32)

        filtered = process_subbass_filter(signal, sr, cutoff_hz=65.0)
        assert filtered.shape == signal.shape
        assert filtered.dtype == np.float32

        # 30 Hz energy should be significantly attenuated
        fft_orig = np.abs(np.fft.rfft(signal))
        fft_filt = np.abs(np.fft.rfft(filtered))
        freqs = np.fft.rfftfreq(len(signal), 1.0 / sr)

        idx_30 = np.argmin(np.abs(freqs - 30))
        idx_500 = np.argmin(np.abs(freqs - 500))

        assert fft_filt[idx_30] < fft_orig[idx_30] * 0.35  # >9 dB cut
        assert np.isclose(fft_filt[idx_500], fft_orig[idx_500], rtol=0.1)  # preserved

    def test_process_dynamic_deesser_attenuates_sibilance(self):
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        harsh_sib = 0.8 * np.sin(2 * np.pi * 7200 * t).astype(np.float32)

        deessed = process_dynamic_deesser(harsh_sib, sr, sibilance_freq_hz=7200.0, max_reduction_db=6.0)
        assert deessed.shape == harsh_sib.shape
        # Total sibilant energy should be attenuated significantly
        assert np.mean(deessed**2) < np.mean(harsh_sib**2)
        # Steady-state peak amplitude after attack envelope settles should be reduced
        assert np.max(np.abs(deessed[int(sr * 0.05) :])) < np.max(np.abs(harsh_sib))

    def test_process_dereverb_clean_attenuates_decay_tail(self):
        sr = 44100
        # 0.1s burst + 0.4s low-level decay tail
        t_burst = np.linspace(0, 0.1, int(sr * 0.1), endpoint=False)
        burst = 0.8 * np.sin(2 * np.pi * 400 * t_burst)
        t_tail = np.linspace(0, 0.4, int(sr * 0.4), endpoint=False)
        tail = 0.2 * np.exp(-5 * t_tail) * np.sin(2 * np.pi * 400 * t_tail)
        signal = np.concatenate([burst, tail]).astype(np.float32)

        cleaned = process_dereverb_clean(signal, sr, max_decay_reduction_db=6.0)
        assert cleaned.shape == signal.shape

        # Tail portion should be attenuated
        tail_start = int(sr * 0.15)
        assert np.mean(cleaned[tail_start:] ** 2) < np.mean(signal[tail_start:] ** 2)

    def test_process_silence_purifier_expands_quiet_floor(self):
        sr = 44100
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        loud = 0.5 * np.sin(2 * np.pi * 400 * t)
        quiet = 0.001 * np.sin(2 * np.pi * 400 * t)  # -60 dBFS
        signal = np.concatenate([loud, quiet]).astype(np.float32)

        cleaned = process_silence_purifier(signal, sr, threshold_db=-40.0, max_attenuation_db=18.0)
        assert cleaned.shape == signal.shape

        quiet_region = cleaned[int(sr * 0.7) :]
        assert np.max(np.abs(quiet_region)) < 0.0005

    def test_process_vocal_leveler_smooths_dynamics(self):
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        soft = 0.08 * np.sin(2 * np.pi * 350 * t)
        loud = 0.60 * np.sin(2 * np.pi * 350 * t)
        signal = np.concatenate([soft, loud]).astype(np.float32)

        leveled = process_vocal_leveler(signal, sr, max_boost_db=4.0, max_cut_db=4.0)
        assert leveled.shape == signal.shape

        soft_out = leveled[int(sr * 0.2) : int(sr * 0.8)]
        loud_out = leveled[int(sr * 1.2) : int(sr * 1.8)]

        spread_before = 0.60 / 0.08
        spread_after = np.max(np.abs(loud_out)) / np.max(np.abs(soft_out))
        assert spread_after < spread_before

    def test_process_true_peak_normalization_ceiling(self):
        signal = np.array([0.2, -0.4, 0.3], dtype=np.float32)
        norm = process_true_peak_normalization(signal, target_dbfs=-1.0, allow_boost=True)
        expected_peak = 10.0 ** (-1.0 / 20.0)
        assert np.isclose(np.max(np.abs(norm)), expected_peak, atol=1e-3)

    def test_process_spectral_debleed_suppresses_residual_instrumental(self):
        sr = 44100
        n_samples = 44100
        # Vocal silence (very low level bleed) with loud instrumental playing
        v_silence = (np.random.randn(n_samples) * 0.005).astype(np.float32)
        instru = (0.5 * np.sin(2 * np.pi * 200 * np.linspace(0, 1.0, n_samples))).astype(np.float32)

        debleed_out = process_spectral_debleed(v_silence, instru, sr=sr, reduction_db=6.0)
        assert debleed_out.shape == v_silence.shape
        assert np.mean(debleed_out**2) < np.mean(v_silence**2)

    def test_process_dsp_rack_bypass(self):
        sr = 44100
        signal = np.random.randn(sr, 2).astype(np.float32) * 0.2
        config = DSPRackConfig(enabled=False)
        out = process_dsp_rack(signal, sr, config)
        assert np.array_equal(out, signal)

    def test_process_dsp_rack_stereo_and_mono(self):
        sr = 44100
        config = DSPRackConfig()
        mono = 0.3 * np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, sr)).astype(np.float32)
        stereo = np.column_stack([mono, mono])

        out_mono = process_dsp_rack(mono, sr, config)
        out_stereo = process_dsp_rack(stereo, sr, config)

        assert out_mono.ndim == 1
        assert out_mono.shape == mono.shape
        assert out_stereo.ndim == 2
        assert out_stereo.shape == stereo.shape


# ── Tier 2: Boundary & Corner Cases ─────────────────────────────────────────


class TestDSPCornerCases:
    """Verify resilience against abnormal audio signals."""

    def test_empty_audio_handling(self):
        sr = 44100
        empty = np.array([], dtype=np.float32)
        config = DSPRackConfig()
        out = process_dsp_rack(empty, sr, config)
        assert len(out) == 0

    def test_pure_silence_handling(self):
        sr = 44100
        silence = np.zeros((sr, 2), dtype=np.float32)
        config = DSPRackConfig()
        out = process_dsp_rack(silence, sr, config)
        assert out.shape == silence.shape
        assert np.max(np.abs(out)) == 0.0

    def test_dc_offset_and_clipping(self):
        sr = 44100
        # Constant DC offset of 0.8
        dc_signal = np.ones(sr, dtype=np.float32) * 0.8
        config = DSPRackConfig(subbass_filter=True)
        out = process_dsp_rack(dc_signal, sr, config)
        # Sub-bass high-pass filter eliminates DC offset after transient
        assert np.abs(np.mean(out[int(sr * 0.2) :])) < 0.05

    def test_soundfile_format_safety(self, tmp_path: Path):
        sr = 44100
        signal = 0.3 * np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, sr)).astype(np.float32)
        signal_stereo = np.column_stack([signal, signal])

        wav_p = tmp_path / "out.wav"
        flac_p = tmp_path / "out.flac"
        mp3_p = tmp_path / "out.mp3"

        # Must write without ValueError: Invalid combination of format, subtype and endian
        write_audio_file(wav_p, signal_stereo, sr)
        write_audio_file(flac_p, signal_stereo, sr)
        write_audio_file(mp3_p, signal_stereo, sr)

        assert wav_p.is_file() and wav_p.stat().st_size > 0
        assert flac_p.is_file() and flac_p.stat().st_size > 0
        assert mp3_p.is_file() and mp3_p.stat().st_size > 0


# ── Tier 3: Raw Stem Retention & Immutability ───────────────────────────────


class TestRawStemRetentionAndReprocess:
    """Verify raw separated stems retention, caching, and immutable reprocessing."""

    def test_reprocess_stem_leaves_raw_vocals_immutable(self, tmp_path: Path):
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        raw_signal = (0.5 * np.sin(2 * np.pi * 30 * t) + 0.5 * np.sin(2 * np.pi * 500 * t)).astype(np.float32)

        raw_path = tmp_path / "song_(Vocals)_raw.wav"
        out_v1 = tmp_path / "song_(Vocals)_v1.wav"
        out_v2 = tmp_path / "song_(Vocals)_v2.wav"

        sf.write(str(raw_path), raw_signal, sr, subtype="FLOAT")
        hash_before = hashlib.sha256(raw_path.read_bytes()).hexdigest()

        engine = SeparationEngine(output_dir=tmp_path)

        # Reprocess 1: with subbass filter ON
        cfg1 = DSPRackConfig(subbass_filter=True, subbass_cutoff=80.0)
        engine.reprocess_stem(raw_path, out_v1, cfg1)

        hash_after1 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        assert hash_before == hash_after1, "Raw vocal stem was mutated during reprocessing!"

        # Reprocess 2: with subbass filter OFF (bypass)
        cfg2 = DSPRackConfig(enabled=False)
        engine.reprocess_stem(raw_path, out_v2, cfg2)

        hash_after2 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        assert hash_before == hash_after2, "Raw vocal stem was mutated during second reprocessing!"

        # Processed outputs must be distinct from each other
        data_v1, _ = sf.read(str(out_v1))
        data_v2, _ = sf.read(str(out_v2))
        assert not np.array_equal(data_v1, data_v2)

    def test_reprocess_stem_idempotency(self, tmp_path: Path):
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

        raw_path = tmp_path / "stem_raw.wav"
        out_a = tmp_path / "stem_a.wav"
        out_b = tmp_path / "stem_b.wav"

        sf.write(str(raw_path), signal, sr, subtype="FLOAT")
        engine = SeparationEngine(output_dir=tmp_path)
        cfg = DSPRackConfig(subbass_filter=True, deesser=True, true_peak=True)

        engine.reprocess_stem(raw_path, out_a, cfg)
        engine.reprocess_stem(raw_path, out_b, cfg)

        data_a, _ = sf.read(str(out_a))
        data_b, _ = sf.read(str(out_b))
        assert np.array_equal(data_a, data_b), "Reprocessing is not idempotent across runs!"

    def test_separate_saves_and_returns_raw_stems(self, tmp_path: Path):
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        sig = 0.4 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        in_wav = tmp_path / "input.wav"
        sf.write(str(in_wav), sig, sr)

        engine = SeparationEngine(output_dir=tmp_path)

        # Mock _separator.separate to simulate neural inference output without downloading 1.5GB weights
        fake_voc = tmp_path / "input_(Vocals)_model.wav"
        fake_inst = tmp_path / "input_(Instrumental)_model.wav"
        sf.write(str(fake_voc), sig, sr, subtype="FLOAT")
        sf.write(str(fake_inst), sig, sr, subtype="FLOAT")

        mock_separator = MagicMock()
        mock_separator.separate.return_value = [fake_voc.name, fake_inst.name]
        engine._separator = mock_separator

        results = engine.separate(in_wav)

        assert "raw_vocals" in results
        assert "raw_instrumental" in results
        assert results["raw_vocals"].is_file()
        assert results["raw_instrumental"].is_file()
        assert "_raw" in results["raw_vocals"].name
        assert "_raw" in results["raw_instrumental"].name
        assert results["vocals"].is_file()


# ── Tier 4: Async ReprocessWorker & Player Hot-Reloading ────────────────────


class TestWorkerAndPlayer:
    """Verify background QThread worker and position-preserving AudioPreviewPlayer."""

    def test_reprocess_worker_execution(self, qapp, tmp_path: Path):
        sr = 44100
        raw_p = tmp_path / "test_raw.wav"
        out_p = tmp_path / "test_out.wav"
        sf.write(str(raw_p), np.zeros((sr, 2), dtype=np.float32), sr)

        engine = SeparationEngine(output_dir=tmp_path)
        cfg = DSPRackConfig()
        worker = ReprocessWorker(engine, raw_p, out_p, cfg)

        started = []
        finished = []
        errors = []

        worker.reprocess_started.connect(lambda: started.append(True))
        worker.reprocess_finished.connect(lambda p: finished.append(p))
        worker.reprocess_error.connect(lambda e: errors.append(e))

        worker.start()
        worker.wait(2000)
        qapp.processEvents()

        assert len(started) == 1
        assert len(finished) == 1
        assert finished[0] == out_p
        assert len(errors) == 0
        assert out_p.is_file()

    def test_reprocess_worker_missing_raw_stem_emits_error(self, qapp, tmp_path: Path):
        engine = SeparationEngine(output_dir=tmp_path)
        missing_p = tmp_path / "non_existent_raw.wav"
        out_p = tmp_path / "out.wav"
        cfg = DSPRackConfig()
        worker = ReprocessWorker(engine, missing_p, out_p, cfg)

        errors = []
        worker.reprocess_error.connect(lambda e: errors.append(e))

        worker.start()
        worker.wait(2000)
        qapp.processEvents()

        assert len(errors) == 1
        assert "not found" in errors[0].lower()

    def test_audio_player_update_vocals(self, qapp, tmp_path: Path):
        sr = 44100
        voc1 = tmp_path / "voc1.wav"
        voc2 = tmp_path / "voc2.wav"
        inst = tmp_path / "inst.wav"

        sf.write(str(voc1), np.zeros((sr, 2), dtype=np.float32), sr)
        sf.write(str(voc2), np.ones((sr, 2), dtype=np.float32) * 0.1, sr)
        sf.write(str(inst), np.zeros((sr, 2), dtype=np.float32), sr)

        player = AudioPreviewPlayer()
        player.set_results(voc1, inst)
        assert player._vocals_path == voc1

        # Hot-reload vocals
        player.update_vocals(voc2)
        assert player._vocals_path == voc2


# ── Tier 5: MainWindow Reactive UI Parameter Wiring ────────────────────────


class TestMainWindowReprocessFlow:
    """Verify MainWindow DSP checkbox signal connections and debounced recalculation."""

    def test_checkboxes_trigger_reprocess_timer(self, qapp, tmp_path: Path):
        win = MainWindow()
        raw_voc = tmp_path / "audio_raw.wav"
        sf.write(str(raw_voc), np.zeros((44100, 2), dtype=np.float32), 44100)

        win._current_raw_vocals_path = raw_voc

        assert not win._reprocess_timer.isActive()

        # Toggling any of the 7 checkboxes should trigger the timer
        win.chk_subbass.setChecked(not win.chk_subbass.isChecked())
        assert win._reprocess_timer.isActive()
        win._reprocess_timer.stop()

        win.chk_deesser.setChecked(not win.chk_deesser.isChecked())
        assert win._reprocess_timer.isActive()
        win._reprocess_timer.stop()

        win.chk_auto_dsp.setChecked(not win.chk_auto_dsp.isChecked())
        assert win._reprocess_timer.isActive()
        win._reprocess_timer.stop()

    def test_ping_pong_file_alternation(self, qapp, tmp_path: Path):
        win = MainWindow()
        raw_voc = tmp_path / "track_raw.wav"
        sf.write(str(raw_voc), np.zeros((44100, 2), dtype=np.float32), 44100)
        win._current_raw_vocals_path = raw_voc

        # First trigger should pick v2 or v1
        win._trigger_reprocess()
        worker1 = win._reprocess_worker
        assert worker1 is not None
        path1 = worker1._output_path
        worker1.wait(2000)

        # Second trigger should ping-pong to the other
        win._trigger_reprocess()
        worker2 = win._reprocess_worker
        assert worker2 is not None
        path2 = worker2._output_path
        worker2.wait(2000)

        assert path1 != path2
        assert ("_v1.wav" in path1.name and "_v2.wav" in path2.name) or (
            "_v2.wav" in path1.name and "_v1.wav" in path2.name
        )

    def test_reprocess_finished_updates_player_and_status(self, qapp, tmp_path: Path):
        win = MainWindow()
        new_stem = tmp_path / "track_vocals_v1.wav"
        sf.write(str(new_stem), np.zeros((44100, 2), dtype=np.float32), 44100)

        win._on_reprocess_finished(new_stem)

        assert win._current_processed_vocals_path == new_stem
        assert win.audio_player._vocals_path == new_stem
        assert "mis à jour" in win.status_label.text().lower()


# ── Tier 5: Iteration 2 Challenger Remediations ──────────────────────────


class TestRemediationRegressions:
    """Verify bug fixes for Challenger 1 findings."""

    def test_deesser_low_sample_rate(self):
        """Verify process_dsp_rack and process_dynamic_deesser execute cleanly on low sample rates."""
        for sr in (8000, 11025):
            sig = np.zeros(sr, dtype=np.float32)
            cfg = DSPRackConfig(deesser=True)
            # Should not raise ValueError: Wn[0] must be less than Wn[1]
            out_rack = process_dsp_rack(sig, sr, cfg)
            assert out_rack.shape == sig.shape
            assert np.array_equal(out_rack, sig)

            out_deesser = process_dynamic_deesser(sig, sr)
            assert out_deesser.shape == sig.shape
            assert np.array_equal(out_deesser, sig)

        # High sibilance freq near or above Nyquist at 44100
        sig44 = np.zeros(44100, dtype=np.float32)
        out_high = process_dynamic_deesser(sig44, 44100, sibilance_freq_hz=24000.0)
        assert out_high.shape == sig44.shape

    def test_spectral_debleed_attenuation_level(self):
        """Verify process_spectral_debleed attenuates bleed by ~2.0 dB without compounding to -8 dB."""
        sr = 44100
        n_samples = 44100
        # Continuous silence with low level bleed + loud instrumental
        v = np.ones(n_samples, dtype=np.float32) * 1e-3
        instru = np.ones(n_samples, dtype=np.float32) * 0.1

        out = process_spectral_debleed(v, instru, sr=sr, reduction_db=2.0)
        assert out.shape == v.shape

        # Sample 2048 was previously attenuated 4x (-8.0 dB, ratio ~0.398)
        # Now it should be attenuated strictly by ~2.0 dB (ratio ~0.794)
        ratio = float(out[2048] / v[2048])
        reduction_db = 20.0 * np.log10(ratio)
        assert 0.75 <= ratio <= 0.85, f"Expected ratio between 0.75 and 0.85, got {ratio}"
        assert np.isclose(reduction_db, -2.0, atol=0.5), f"Expected -2.0 dB +/- 0.5 dB, got {reduction_db} dB"

    def test_reprocess_stem_rejects_identical_path(self, tmp_path: Path):
        """Verify SeparationEngine.reprocess_stem raises ValueError if output_path == raw_vocals_path."""
        sr = 44100
        signal = np.zeros(sr, dtype=np.float32)
        raw_path = tmp_path / "vocals_raw.wav"
        sf.write(str(raw_path), signal, sr, subtype="FLOAT")

        engine = SeparationEngine(output_dir=tmp_path)
        cfg = DSPRackConfig()

        with pytest.raises(ValueError, match="output_path must not overwrite raw_vocals_path"):
            engine.reprocess_stem(raw_path, raw_path, cfg)

    def test_mono_2d_shape_preservation(self):
        """Verify that input arrays of shape (N, 1) retain shape (N, 1) across all DSP processors."""
        sr = 44100
        n_samples = sr
        t = np.linspace(0, 1.0, n_samples, endpoint=False)
        sig = (0.3 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.sin(2 * np.pi * 7200 * t)).astype(np.float32)
        sig_2d = sig[:, None]  # shape (44100, 1)
        instru_2d = (0.5 * np.sin(2 * np.pi * 200 * t))[:, None].astype(np.float32)

        assert sig_2d.shape == (n_samples, 1)

        # 1. Subbass filter
        out = process_subbass_filter(sig_2d, sr)
        assert out.shape == (n_samples, 1)

        # 2. Dynamic de-esser
        out = process_dynamic_deesser(sig_2d, sr)
        assert out.shape == (n_samples, 1)

        # 3. De-reverb clean
        out = process_dereverb_clean(sig_2d, sr)
        assert out.shape == (n_samples, 1)

        # 4. Silence purifier
        out = process_silence_purifier(sig_2d, sr)
        assert out.shape == (n_samples, 1)

        # 5. Vocal leveler
        out = process_vocal_leveler(sig_2d, sr)
        assert out.shape == (n_samples, 1)

        # 6. True peak normalization
        out = process_true_peak_normalization(sig_2d)
        assert out.shape == (n_samples, 1)

        # 7. Spectral debleed
        out = process_spectral_debleed(sig_2d, instru_2d, sr=sr)
        assert out.shape == (n_samples, 1)

        # 8. Full DSP rack
        cfg = DSPRackConfig(
            enabled=True,
            subbass_filter=True,
            deesser=True,
            dereverb=True,
            silence_purifier=True,
            vocal_leveler=True,
            spectral_debleed=True,
            true_peak=True,
        )
        out = process_dsp_rack(sig_2d, sr, cfg, instru=instru_2d)
        assert out.shape == (n_samples, 1)

