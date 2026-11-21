<div align="center">

# Devoice

**Studio-grade neural audio source separation and acoustic DSP workstation**

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-18181b?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B%20CUDA%2012.1-18181b?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-18181b?style=flat-square)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/Code%20Style-Ruff-18181b?style=flat-square&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Tests: 43 passed](https://img.shields.io/badge/Tests-43%20Passed-18181b?style=flat-square)](tests/)

</div>

---

## Overview

**Devoice** is an offline desktop workstation designed for mix engineers, beatmakers, and vocalists who require pristine vocal isolation and stem separation. 

Unlike conventional tools that produce dry acapellas with residual phase artifacts, background bleed, and dynamic fluctuations, Devoice pairs deep neural separation architectures (**BS-RoFormer** and **MDX-Net**) with an automated, in-memory **Studio DSP Rack**.

Once separated, stems can be **reprocessed in real time** (~100 ms) directly from the cached dry signal, allowing users to fine-tune vocal riding, de-essing, de-reverberation, and noise gating without re-running heavy neural inference.

---

## Key Capabilities

- **State-of-the-Art Separation** : Built on BS-RoFormer (ViperX SDR 12.98) and MDX-Net, offering exceptional vocal and instrumental isolation even on dense, heavily compressed productions.
- **Real-Time DSP Reprocessing** : Adjust filters, vocal leveler, or de-esser on isolated stems with sub-second feedback. Dry stems remain immutable in memory while the output updates live in the playback preview.
- **Integrated YouTube Ingestion** : Paste any video or track URL (or drag-and-drop from your browser) to extract high-bitrate audio and prepare it for separation in one click.
- **Lossless 32-bit Float Processing** : Internal audio pipelines operate in continuous IEEE 32-bit float NumPy arrays, avoiding quantization distortion and inter-sample clipping before final export.
- **Zero Cloud Dependency** : All model inference, DSP calculations, and file rendering run 100% locally on your GPU (NVIDIA CUDA) or CPU. Your audio never leaves your machine.
- **Monochrome Interface** : A distraction-free, high-contrast desktop GUI built with PyQt6.

---

## Signal Flow Architecture

```
[ Input Audio File / YouTube Stream ]
                  │
                  ▼
   [ Neural Separation Engine ] ──► (BS-RoFormer / MDX-Net)
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 [ Raw Instrumental ]  [ Raw Vocals (Cached Dry) ]
        │                   │
        │        ┌──────────┴──────────────────────────┐
        │        ▼                                     ▼
        │   [ Sub-Bass Highpass ]              (Real-Time DSP Tuning)
        │   [ Dynamic Lookahead Leveler ]              │
        │   [ Dynamic De-Esser (5-9 kHz) ]             │
        │   [ Downward Silence Purifier ]              │
        │   [ Energy Envelope De-Reverb ]              │
        │   [ Inter-Stem Spectral De-Bleed ]           │
        │   [ ITU-R BS.1770 True-Peak Limiter ]        │
        │        └──────────┬──────────────────────────┘
        │                   ▼
        └─────────────► [ Master Stems ] ──► [ Studio Preview Player & Export ]
```

---

## Performance Benchmark

Signal-to-Distortion Ratio (SDR) on standard vocal isolation benchmarks (higher is better):

| Architecture | Model | Vocal SDR (dB) | Artifact Suppression |
| :--- | :--- | :---: | :---: |
| **BS-RoFormer** | **ViperX SDR 12.98 (Default)** | **12.98 dB** | **Industry Lead** |
| MDX-Net | MDX23C-8KFFT | 10.87 dB | High |
| Demucs v4 | HTDemucs-FT | 9.20 dB | Moderate |
| Spleeter | 2-Stems | 6.30 dB | Low (Audible Phase Bleed) |

---

## Studio DSP Modules

| Module | Algorithm | Function |
| :--- | :--- | :--- |
| **Vocal Rider** | Dynamic lookahead RMS leveling | Stabilizes vocal dynamics and levels out drops in volume caused by loud instrumentals. |
| **Dynamic De-Esser** | Spectral band splitting (5–9 kHz) | Attenuates harsh sibilants without dulling vocal brightness or high-end air. |
| **Silence Purifier** | Soft-knee downward expander | Silences instrument bleed, headphone spill, and background noise during vocal pauses. |
| **De-Reverb** | Decay envelope suppression | Tames room reflections and wet tails to yield a dry, direct cabin vocal. |
| **Sub-Bass Filter** | 2nd-order Butterworth highpass | Filters sub-audible rumble calibrated to the fundamental vocal frequency (F0). |
| **Spectral De-Bleed** | Cross-stem phase attenuation | Attenuates residual cymbal and high-frequency spill between vocal and instrumental tracks. |
| **True-Peak Limiter** | Oversampled peak ceiling (-1.0 dBFS) | Prevents digital inter-sample clipping during lossy MP3/AAC compression or DAC playback. |

---

## Installation

### Binary Release (Recommended for End Users)

1. Download the latest `Devoice-Setup.exe` from the [Releases](https://github.com/USERNAME/devoice/releases) page.
2. Run the installer and launch **Devoice** from your desktop or start menu.

### Building from Source

**Prerequisites:** Python 3.10+, Git, and an NVIDIA GPU with CUDA drivers (optional, CPU fallback supported).

```bash
# Clone the repository
git clone https://github.com/USERNAME/devoice.git
cd devoice

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install dependencies with CUDA acceleration
pip install --upgrade pip
pip install -r requirements.txt

# Launch application
python main.py
```

---

## Development & Verification

Devoice adheres to strict quality assurance standards. The test suite includes full integration coverage, extreme boundary DSP checks, and concurrency verification.

```bash
# Run the test suite (43 automated tests)
pytest tests/ -v

# Run linting and code quality checks
ruff check devoice/ tests/
```

---

## Project Structure

```
devoice/
├── audio_utils.py       # Acoustic diagnostics, NumPy DSP rack, and format writers
├── config.py            # Global constants and supported format definitions
├── engine.py            # Neural separation engine, model registry, and stem cache
├── worker.py            # Background QThread workers (Separation, YouTube, Reprocess)
├── youtube.py           # yt-dlp stream extraction and static-ffmpeg audio pipeline
└── ui/
    ├── audio_player.py  # Studio preview player with dynamic stem hot-swapping
    ├── drop_zone.py     # Minimalist drag & drop and URL ingestion widget
    ├── main_window.py   # Primary application window, controls, and event wiring
    └── styles.py        # Cohesive dark monochrome design system (Noir & Blanc)
```

---

## License & Credits

- Distributed under the [GNU General Public License v3.0 (GPLv3)](LICENSE).
- Core neural models courtesy of the **BS-RoFormer** and **MDX-Net** research communities.
- Audio extraction powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [static-ffmpeg](https://github.com/zackees/static-ffmpeg).
