# Devoice V1: Production Release Audit & Strategic Engineering Roadmap

**Document Version**: 1.0.0  
**Status**: Authoritative Technical Audit & Release Specification  
**Target Release**: Devoice V1.0 Desktop Production Suite  
**Supported Platforms**: Windows 10/11 (x86_64), macOS 12+ (Apple Silicon & Intel), Linux (x86_64)  
**Author**: Devoice Core Architecture & Quality Assurance Working Group  
**Date**: November 2026  

---

## Executive Summary & V1 Release Readiness Scorecard

Devoice is an advanced desktop audio workstation delivering state-of-the-art vocal isolation and real-time studio-grade acoustic post-processing. Powered by deep neural separation architectures (BS-RoFormer and MDX-Net) and coupled with a dedicated studio DSP rack (sub-bass filtering, dynamic de-essing, vocal leveling, silence purification, and de-reverberation), the software bridges consumer usability with professional studio fidelity.

While the core algorithmic capabilities and separation quality achieve industry-leading SDR (Signal-to-Distortion Ratio) benchmarks, an exhaustive engineering audit reveals that the current application codebase operates at a **Beta / Release Candidate 0 (RC-0)** maturity level. Crucial architectural gaps across binary distribution, automatic hardware failure recovery, asynchronous model ingestion, diagnostic infrastructure, audio codec compatibility, and legal licensing prevent Devoice from meeting enterprise-grade release standards.

This document serves as the formal audit report and binding engineering roadmap required to elevate Devoice from an experimental prototype to a resilient, standalone, production-grade V1 desktop release.

### V1 Release Readiness Scorecard

| Subsystem / Area | Current Status | Severity | Primary Risk / Technical Blocker | Target Milestone |
| :--- | :---: | :---: | :--- | :---: |
| **Packaging & Distribution** | Deficient | **CRITICAL** | Omission of dynamic dependencies (`audio-separator`, ONNX Runtime GPU DLLs, `yt-dlp`, static FFmpeg) in PyInstaller spec causing launch failures on clean client machines. | Phase 3 (RC) |
| **Licensing Compliance** | Non-Compliant | **CRITICAL** | Direct linking of `PyQt6` (GPLv3) within an MIT-licensed repository violates GNU copyleft terms upon binary distribution. | Phase 1 (Alpha) |
| **Hardware Fallback & Memory** | Fragile | **HIGH** | Out-of-memory (`CUDA OOM`) exceptions trigger a naive re-try on the same exhausted GPU without VRAM cache flush, aborting batch jobs without CPU fallback. | Phase 2 (Beta) |
| **Model Download UX** | Inadequate | **HIGH** | Large model weights (~600 MB) trigger synchronous CLI `tqdm` downloads redirected to `NUL` in GUI mode, causing UI lockups with no SHA-256 validation. | Phase 3 (RC) |
| **Audio File Integrity & Codec** | Partially Broken | **HIGH** | Hardcoded `subtype="FLOAT"` in audio writing triggers silent `ValueError` failures on FLAC (24-bit) and MP3 formats, bypassing DSP filters entirely. | Phase 1 (Alpha) |
| **Diagnostics & Error Handling** | Rudimentary | **MEDIUM** | Absence of persistent rotating file logging, lack of `sys.excepthook` crash dialog, and error messages clipped in the status bar without copyable tracebacks. | Phase 2 (Beta) |
| **Audio DSP Quality & True-Peak** | Good | **LOW** | Peak detection relies on simple sample extrema rather than 4x polyphase sinc true-peak detection (ITU-R BS.1770-4); causal IIR filters induce slight phase shifts. | Phase 1 (Alpha) |

---

## Section 1: Standalone Binary Packaging & Multi-Platform Distribution

### 1.1 PyInstaller Specification Audit & Hidden Imports Gap
The original PyInstaller specification (`packaging/devoice.spec`) collected static assets and binaries exclusively for `torch`, `demucs`, and `PyQt6`. When compiling a standalone directory (`--onedir`), execution on an operating system without an active Python development environment fails immediately upon invoking core workflows:
- **`audio_separator`**: Contains dynamic model architectures, runtime YAML configuration assets (`mdx_c_configs`), and custom loader stubs omitted by standard PyInstaller AST walkers.
- **`onnxruntime` / `onnxruntime-gpu`**: Requires native runtime libraries (`onnxruntime.dll`, `onnxruntime_providers_cuda.dll`, `onnxruntime_providers_shared.dll`, `onnxruntime_providers_tensorrt.dll`). PyInstaller hooks fail to identify these dynamically loaded C++ provider plugins without explicit binary collection.
- **`scipy` (`scipy.signal`, `scipy.ndimage`, `scipy.special`)**: Heavy reliance on compiled C-extensions and Cython wrappers for SOS filtering, Butterworth designs, and FFT calculations.
- **`librosa`, `soundfile`, `pydub`**: Rely on bundled external C-libraries (such as `libsndfile.dll`) and dynamic backend dispatching.
- **`yt_dlp`**: Employs lazy runtime module discovery for hundreds of media extractors and signature deciphering routines.

**Production Packaging Solution**:
The updated `packaging/devoice.spec` implements comprehensive programmatic collection via `PyInstaller.utils.hooks.collect_all` for all runtime dependencies:
```python
packages_to_collect = [
    "torch", "torchaudio", "demucs", "PyQt6",
    "audio_separator", "onnxruntime", "scipy",
    "librosa", "soundfile", "pydub", "yt_dlp", "static_ffmpeg",
]
for pkg in packages_to_collect:
    pkg_data = collect_all(pkg)
    binaries.extend(pkg_data.get("binaries", []))
    datas.extend(pkg_data.get("datas", []))
    collected_hiddenimports.extend(pkg_data.get("hiddenimports", []))
```

### 1.2 Static FFmpeg Binary Resolution & Bundling
Devoice requires `ffmpeg` and `ffprobe` for format transcoding, sample rate conversions, and fallback audio pre-conditioning. Previous builds assumed FFmpeg was pre-installed on the host system PATH or manually dropped into the working directory.

The updated packaging architecture integrates dynamic resolution via `static_ffmpeg`:
```python
try:
    import static_ffmpeg._add_paths as sff
    ffmpeg_exe, ffprobe_exe = sff.get_or_fetch_platform_executables_else_raise()
    if ffmpeg_exe and Path(ffmpeg_exe).exists():
        binaries.append((str(ffmpeg_exe), "."))
    if ffprobe_exe and Path(ffprobe_exe).exists():
        binaries.append((str(ffprobe_exe), "."))
except Exception as exc:
    pass
```
At runtime, `main.py` prepends the bundled executable folder (`sys._MEIPASS` or the root executable directory) to `os.environ["PATH"]`, ensuring deterministic, hermetic FFmpeg availability across all host configurations without external user setup.

### 1.3 Multi-Platform Packaging Architecture
Devoice V1 will support three primary operating systems using native distribution paradigms:

| Operating System | Package Format | Distribution Architecture | Target Hardware Engines | Code Signing / Notarization |
| :--- | :--- | :--- | :--- | :--- |
| **Windows 10 / 11** | Inno Setup `.exe` / `.zip` | Onedir folder with bundled Python 3.10 runtime | NVIDIA CUDA 12.1 or DirectML / CPU | Microsoft Authenticode Certificate |
| **macOS 12+** | Drag-and-Drop `.dmg` | Standard `.app` Bundle (Universal2 / arm64) | Apple Silicon MPS or CPU | Apple Developer ID + `notarytool` |
| **Linux (glibc 2.31+)**| Self-Contained `.AppImage` | Single executable AppImage container | NVIDIA CUDA / ROCm / OpenVINO / CPU | GPG Detached Signatures |

- **Windows Dual-Edition Strategy**:
  - **Devoice GPU Edition (CUDA 12.1)**: Bundles PyTorch CUDA runtime and ONNX Runtime GPU (~2.0 GB compressed). Target: Users with NVIDIA GeForce RTX / GTX GPUs.
  - **Devoice Standard Edition (CPU / DirectML)**: Bundles PyTorch CPU and ONNX Runtime DirectML (~280 MB compressed). Target: Users with Intel Core, AMD Ryzen, or Intel Arc / AMD Radeon GPUs.

### 1.4 Modern Windows Installer Design (Inno Setup / NSIS)
A production desktop application requires an automated, non-technical setup experience. An Inno Setup 6 configuration (`packaging/installer.iss`) provides:
- **Per-User Non-Elevated Installation**: Installs to `%LOCALAPPDATA%\Programs\Devoice`, avoiding UAC elevation prompts for non-admin enterprise users.
- **System Integration**: Optional Start Menu shortcut, Desktop icon, and file type associations for `.wav`, `.mp3`, and `.flac`.
- **Clean Uninstallation**: Uninstaller cleanly purges application binaries while offering the user an explicit prompt to preserve or delete model checkpoints in `%LOCALAPPDATA%\Devoice\models`.

```pascal
; Inno Setup 6 Script Architecture (packaging/installer.iss)
[Setup]
AppName=Devoice
AppVersion=1.0.0
DefaultDirName={localappdata}\Programs\Devoice
DefaultGroupName=Devoice
OutputDir=..\dist\Installer
OutputBaseFilename=Devoice-1.0.0-Setup
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\Devoice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Devoice"; Filename: "{app}\Devoice.exe"
Name: "{autodesktop}\Devoice"; Filename: "{app}\Devoice.exe"; Tasks: desktopicon

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Devoice\cache"
Type: filesandordirs; Name: "{localappdata}\Devoice\logs"
```

### 1.5 Auto-Update Architecture
Devoice V1 incorporates an asynchronous, lightweight update manager:
- **Endpoint**: Queries the GitHub Releases API (`/repos/cash/devoice/releases/latest`) on application launch.
- **Background Worker**: Evaluates the semantic version (`semver`) against the current running version string.
- **Notification & Download**: Displays an unobtrusive update badge in the title bar. Upon user consent, the installer is streamed to a temporary directory, cryptographically verified against the release SHA-256 manifest, and spawned while Devoice gracefully shuts down.

```python
class UpdateChecker(QThread):
    update_available = Signal(str, str, str)  # version, changelog, download_url

    def run(self):
        try:
            resp = requests.get("https://api.github.com/repos/cash/devoice/releases/latest", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                if is_newer_version(CURRENT_VERSION, latest_tag):
                    for asset in data.get("assets", []):
                        if asset["name"].endswith("-Setup.exe"):
                            self.update_available.emit(latest_tag, data.get("body", ""), asset["browser_download_url"])
                            break
        except Exception as exc:
            logger.debug("Silent update check skipped: %s", exc)
```

---

## Section 2: Hardware Acceleration & Automatic CUDA-to-CPU Fallback

### 2.1 Post-Mortem of Current Fallback Failure & VRAM Leak
In Devoice, separation inference failure triggers an audio fallback routine in `devoice/engine.py:173-199`:
```python
try:
    output_files = self._separator.separate(str(audio_path))
except Exception as exc:
    logger.warning("Séparation directe échouée (%s), conversion de secours", exc)
    clean_input = self.output_dir / f"_clean_{audio_path.stem}.wav"
    # Transcode to WAV...
    output_files = self._separator.separate(str(clean_input))
```
**Defect Analysis**:
When a user with modest VRAM (e.g. 4GB - 6GB VRAM on GTX 1650 or RTX 3050 Laptop) attempts to process a high-resolution or lengthy audio file with BS-RoFormer, PyTorch raises `torch.cuda.OutOfMemoryError`. Devoice incorrectly misdiagnoses this memory exhaustion as an audio container defect, converts the file to a clean WAV via FFmpeg, and re-invokes `separate()` on the **identical CUDA device** without clearing cached tensors. The uncollected VRAM memory buffers guarantee a secondary fatal crash, aborting the process entirely.

### 2.2 Resilient Multi-Stage Fallback Architecture
The V1 engine implements a deterministic two-stage recovery protocol:

```
[Audio Ingest] -> [Run GPU Separation (CUDA)]
                         |
                 (OutOfMemoryError)
                         v
       +------------------------------------+
       | Stage 1: VRAM Cache Flush & Retry  |
       |  - torch.cuda.empty_cache()        |
       |  - gc.collect()                    |
       |  - Reduce chunk size / batch = 1   |
       +------------------------------------+
                         |
                 (Secondary OOM)
                         v
       +------------------------------------+
       | Stage 2: Graceful CPU Evacuation   |
       |  - Re-instantiate separator:       |
       |    device="cpu", CPUProvider       |
       |  - Emit UI Warning Banner:         |
       |    "VRAM saturated; running on CPU"|
       |  - Resume processing seamlessly    |
       +------------------------------------+
```

**Implementation Pattern**:
```python
def execute_separation_resilient(self, audio_path: Path) -> dict[str, Path]:
    try:
        return self._separator.separate(str(audio_path))
    except (torch.cuda.OutOfMemoryError, RuntimeError) as exc:
        if "out of memory" not in str(exc).lower() and not isinstance(exc, torch.cuda.OutOfMemoryError):
            raise
        logger.warning("CUDA VRAM saturation detected. Initiating Stage 1 recovery.")
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Stage 1: Attempt separation with batch_size=1
        try:
            self._separator.arch_specific_config["batch_size"] = 1
            return self._separator.separate(str(audio_path))
        except Exception as oom2:
            logger.warning("Stage 1 throttle failed. Evacuating to Stage 2 CPU fallback: %s", oom2)
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Stage 2: Re-instantiate separator on CPU
            self._separator = self._create_separator(device="cpu")
            self.device_fallback_triggered.emit("VRAM saturée. Basculement transparent sur CPU.")
            return self._separator.separate(str(audio_path))
```

### 2.3 Multi-Backend Acceleration Roadmap
To support diverse client hardware ecosystems without requiring proprietary NVIDIA CUDA stacks:
- **NVIDIA Hardware**: Direct CUDA 12.x execution with TensorRT optimization for production builds.
- **Apple Silicon (macOS)**: Native PyTorch Metal Performance Shaders (`torch.device("mps")`) acceleration, offering up to 8x speedup over CPU on M1/M2/M3/M4 chips.
- **AMD & Intel Hardware (Windows)**: Implementation of `onnxruntime-directml` for MDX-Net ONNX models. DirectML enables hardware acceleration across any DirectX 12 compatible GPU (AMD Radeon RX 5000/6000/7000 series, Intel Arc, and Intel Iris Xe integrated graphics).
- **Universal CPU Execution**: Accelerated via Intel OneDNN and AVX-512 vectorization, ensuring reliable baseline performance across all x86_64 machines.

---

## Section 3: Model Prefetching & Download Progress UX

### 3.1 Failure Mode of Current CLI Download Routine
Separation models (`model_bs_roformer_ep_317_sdr_12.9755.ckpt` ~600 MB and `UVR-MDX-NET-Inst_HQ_3.onnx` ~65 MB) are fetched on first use via `audio_separator/separator.py:download_file_if_not_exists`.
- **The Issue**: Downloads execute via synchronous `requests.get()` inside the main processing thread or worker, rendering `tqdm` progress bars to stdout.
- **GUI Blindness**: In production desktop builds (`console=False`), standard output is discarded. The application appears completely frozen in "Chargement du modèle...", prompting users to forcefully terminate the process.
- **Corrupted Cache Deadlock**: If network connectivity drops or the user terminates the process during transfer, an incomplete, corrupted file remains on disk. On subsequent launches, `os.path.isfile(output_path)` returns `True`, causing unrecoverable deserialization crashes.

### 3.2 Thread-Safe GUI Model Manager Architecture
Devoice V1 introduces an independent `ModelDownloadWorker(QThread)`:
- **Non-Blocking Operation**: Runs outside the UI thread, emitting Qt signals:
  - `download_started(model_id: str, total_bytes: int)`
  - `download_progress(model_id: str, bytes_downloaded: int, percent: float, speed_mbps: float, eta_seconds: int)`
  - `download_completed(model_id: str, file_path: Path)`
  - `download_failed(model_id: str, error_message: str)`
- **Resilient Transport**: Implements HTTP `Range` request headers allowing automatic resumption of interrupted downloads.
- **User Control**: Dedicated Model Settings drawer providing download, cancellation, pause, and storage consumption metrics.

```python
class ModelDownloadWorker(QThread):
    progress_changed = Signal(int, int, float, float, int)  # done, total, pct, mbps, eta
    download_finished = Signal(Path)
    download_error = Signal(str)

    def __init__(self, url: str, target_path: Path, expected_sha256: str):
        super().__init__()
        self.url = url
        self.target_path = target_path
        self.part_path = target_path.with_suffix(target_path.suffix + ".part")
        self.expected_sha256 = expected_sha256
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            downloaded = self.part_path.stat().st_size if self.part_path.exists() else 0
            headers = {"Range": f"bytes={downloaded}-"} if downloaded > 0 else {}
            resp = requests.get(self.url, headers=headers, stream=True, timeout=15)
            
            total_size = downloaded + int(resp.headers.get("content-length", 0))
            hasher = hashlib.sha256()
            mode = "ab" if downloaded > 0 else "wb"
            start_time = time.time()

            with open(self.part_path, mode) as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if self._is_cancelled:
                        return
                    if chunk:
                        f.write(chunk)
                        hasher.update(chunk)
                        downloaded += len(chunk)
                        elapsed = max(time.time() - start_time, 0.001)
                        mbps = (downloaded / (1024 * 1024)) / elapsed
                        eta = int((total_size - downloaded) / (downloaded / elapsed)) if downloaded > 0 else 0
                        pct = (downloaded / total_size) * 100 if total_size > 0 else 0.0
                        self.progress_changed.emit(downloaded, total_size, pct, mbps, eta)

            # Atomic Commit upon SHA-256 verification
            if self._verify_hash(self.part_path, self.expected_sha256):
                self.part_path.replace(self.target_path)
                self.download_finished.emit(self.target_path)
            else:
                self.part_path.unlink(missing_ok=True)
                self.download_error.emit("Échec de vérification cryptographique (SHA-256 incorrect).")
        except Exception as exc:
            self.download_error.emit(str(exc))
```

### 3.3 Cryptographic Integrity Verification & Atomic Swapping
To prevent cache poisoning and partial write corruptions:
1. **Target Hashes Registry**: A hardcoded cryptographic manifest records the official SHA-256 hash for every registered model checkpoint:
   - `model_bs_roformer_ep_317_sdr_12.9755.ckpt`: `8a4f3b...`
   - `UVR-MDX-NET-Inst_HQ_3.onnx`: `1c9d2e...`
2. **Staged Downloading**: Downloads stream to temporary staging files (`.model_name.ckpt.part`).
3. **Atomic Verification**: Upon stream completion, the worker computes the SHA-256 digest in chunks of 64KB. If the digest matches, the staging file is atomically moved to its destination path using `os.replace()`. If the digest fails, the staging file is immediately unlinked and an integrity warning is returned.

### 3.4 Centralized Model Cache Directory Management
The cache location is standardized across operating systems using standard specifications:
- **Windows**: `%LOCALAPPDATA%\Devoice\models`
- **macOS**: `~/Library/Caches/Devoice/models`
- **Linux**: `~/.cache/devoice/models`

Users can view total disk allocation in application preferences, relocate the model cache to external storage drives (crucial for users with small SSD system drives), or purge downloaded checkpoints with a single click.

---

## Section 4: Resilient Error Handling & Diagnostics

### 4.1 Global Exception Hooks & Crash Dialog
To prevent silent process crashes from unhandled thread errors:
- **Hook Registration**: Configure `sys.excepthook` for main thread failures and `threading.excepthook` for worker threads in `main.py`.
- **UI Crash Dialog (`CrashReportDialog`)**: Intercepts uncaught exceptions and displays a modal dialog:
  - Human-readable failure explanation (e.g., "GPU driver lost contact during separation").
  - System diagnostics matrix (Devoice version, OS, PyTorch version, GPU model, VRAM available).
  - Sanitized technical traceback.
  - One-click "Copy Error Report" and "Submit Issue to GitHub" actions.

```python
def setup_crash_reporter(app: QApplication):
    def global_excepthook(exc_type, exc_value, exc_traceback):
        logger.critical("Uncaught fatal exception", exc_info=(exc_type, exc_value, exc_traceback))
        from devoice.ui.crash_dialog import CrashReportDialog
        dialog = CrashReportDialog(exc_type, exc_value, exc_traceback)
        dialog.exec()
        sys.exit(1)
    sys.excepthook = global_excepthook
```

### 4.2 Audio File Integrity Pre-Validation
Before enqueueing audio into the separation pipeline, the input undergoes fast header validation:
- **Zero-Byte Detection**: Rejects empty files immediately.
- **Header Parsing**: Evaluates file validity via `soundfile.info()`, verifying readable audio streams, valid channel counts (1 or 2 channels), non-zero sample rates, and non-infinite durations.
- **Transcode Pre-flight**: If container parsing fails, invokes `ffprobe` to verify format support. Unreadable or DRM-protected streams are rejected upfront with actionable advice rather than triggering engine crashes.

```python
def validate_audio_file(file_path: Path) -> tuple[bool, str]:
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False, "Le fichier audio est vide ou introuvable (0 octet)."
    try:
        info = sf.info(str(file_path))
        if info.frames <= 0 or info.samplerate <= 0:
            return False, "En-tête audio corrompu ou durée invalide."
        if info.channels not in (1, 2):
            return False, f"Format audio multicanal non supporté ({info.channels} canaux). Seul le mono/stéréo est accepté."
        return True, "Fichier valide"
    except Exception as exc:
        # Fallback inspection via ffprobe
        return probe_audio_container_ffprobe(file_path)
```

### 4.3 Structured Diagnostic Logging Subsystem
- **Rotating File Handler**: Configures `logging.handlers.RotatingFileHandler` initialized at `%LOCALAPPDATA%\Devoice\logs\devoice.log` (5 MB maximum size, 3 rolling backup files).
- **Privacy & Token Scrubbing**: Implements a custom log formatter that redacts user home folder paths, system usernames, and query tokens from logged YouTube URLs.
- **In-App Diagnostic Viewer**: "Help -> View Diagnostic Logs" menu item allowing users to view logs in real-time and export them for bug reports.

```python
class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Scrub user home paths (e.g. C:\Users\Username)
        user_home = str(Path.home())
        if user_home in msg:
            msg = msg.replace(user_home, "~")
        # Scrub sensitive query parameters in URLs
        msg = re.sub(r'([?&](?:key|token|auth)=)[^&\s]+', r'\1[REDACTED]', msg)
        return msg
```

---

## Section 5: Audio Fidelity & DSP Quality Standards

### 5.1 End-to-End 32-Bit Floating Point Pipeline
Digital audio processing pipelines risk accumulating re-quantization distortion if audio undergoes repeated conversions between fixed-point integer PCM and floating-point representations:
- **Zero Re-Quantization Invariant**: Audio extracted from the neural separation engine is retained strictly as IEEE 754 32-bit floating point NumPy arrays (`float32`, range $[-1.0, 1.0]$) in memory throughout the DSP rack.
- **Target Format Conversion**: Audio is only quantized to fixed-point integer (`PCM_16` or `PCM_24`) during final file export.
- **Dithering**: When exporting from 32-bit float to 16-bit PCM, Triangular Probability Density Function (TPDF) dither is applied to eliminate low-level harmonic truncation distortion.

```python
def apply_tpdf_dither(audio_float: np.ndarray, bit_depth: int = 16) -> np.ndarray:
    """Applies triangular probability density function dither prior to quantization."""
    scale = (2 ** (bit_depth - 1)) - 1
    # Two uniform random variables subtracted produce a triangular distribution [-1, 1] LSB
    dither = (np.random.rand(*audio_float.shape) - np.random.rand(*audio_float.shape)) / scale
    dithered = audio_float + dither
    return np.clip(dithered, -1.0, 1.0)
```

### 5.2 True-Peak Limiting Compliance (ITU-R BS.1770-4 / EBU R128)
- **The Issue in Legacy Code**: `apply_true_peak_normalization` currently checks `np.max(np.abs(data))`. This simple peak check only evaluates sampled discrete points. When digital audio is reconstructed through a Digital-to-Analog Converter (DAC) in audio monitors or consumer headphones, inter-sample peaks can overshoot the discrete points by up to +3.0 dBFS, inducing analog clipping distortion.
- **V1 Specification**: The output limiter incorporates 4x polyphase sinc oversampling conforming to ITU-R BS.1770-4. Peak estimation operates on the oversampled signal with a default ceiling of **-1.0 dBFS**, guaranteeing zero clipping distortion across modern streaming encoders (AAC, Opus, MP3).

$$\text{TruePeak}(x) = \max_{t} |x_{4\times}(t)| \le -1.0 \text{ dBFS}$$

```python
def compute_true_peak(audio: np.ndarray, sr: int) -> float:
    """Computes ITU-R BS.1770-4 compliant true peak with 4x polyphase oversampling."""
    # 4x oversampling using band-limited Kaiser polyphase filter
    oversampled = scipy.signal.resample_poly(audio, up=4, down=1, axis=0)
    max_val = np.max(np.abs(oversampled))
    return float(20.0 * np.log10(max(max_val, 1e-9)))
```

### 5.3 Sample Rate Consistency & High-Fidelity Resampling
- **Preserving Native Sample Rates**: Neural separation models (BS-RoFormer) process audio natively at 44.1 kHz. When users import high-resolution audio (e.g. 48.0 kHz or 96.0 kHz broadcast/studio masters), downsampling to 44.1 kHz without proper reconstruction permanently degrades high-frequency content.
- **Polyphase Resampling Engine**: Devoice V1 preserves the input sample rate ($F_{in}$). If $F_{in} \neq 44.1\text{ kHz}$, audio is upsampled back to $F_{in}$ upon exiting the separation model using band-limited Kaiser-windowed polyphase sinc interpolation (`scipy.signal.resample_poly` or `libsoxr`), maintaining spectral transparency up to 96 kHz.

### 5.4 Phase-Coherent Zero-Phase Filtering
The sub-bass high-pass filter and dynamic de-esser historically used causal single-pass IIR filters (`scipy.signal.sosfilt`), introducing non-linear phase shifts across the frequency spectrum. When the filtered vocal stem is layered back over the instrumental backing track, phase misalignment causes audible comb filtering in the lower midrange (100 Hz - 300 Hz).
- **V1 Fix**: All DSP rack filters are transitioned to forward-backward zero-phase filtering (`scipy.signal.sosfiltfilt`). This achieves zero net phase alteration across all frequencies, preserving vocal transient punch and acoustic phase alignment with the backing instrumentation.

$$H_{\text{zero}}(z) = H(z) \cdot H(z^{-1}) = |H(z)|^2, \quad \angle H_{\text{zero}}(z) = 0$$

---

## Section 6: Licensing & Dependency Compliance

### 6.1 The PyQt6 GPLv3 Legal Incompatibility & PySide6 Migration
Devoice is released as open-source software under the **MIT License**. However, the current implementation imports `PyQt6`:
- **GPLv3 Violation**: Riverbank Computing's `PyQt6` is licensed strictly under GNU GPLv3 (or an expensive commercial proprietary license). It is **not** licensed under LGPL. Under Section 5 and 6 of the GNU General Public License v3, distributing a compiled binary application that links against a GPL library legally obligates the entire application to be licensed under GPLv3. Distributing Devoice as an MIT-licensed binary using PyQt6 is a direct copyright infringement of PyQt6.
- **Resolution Strategy**: Complete migration to **PySide6** (The Qt Company's official Python binding):
  - PySide6 is distributed under the **LGPLv3** license.
  - Under LGPLv3, proprietary or permissive open-source applications (such as MIT) may legally link dynamically against LGPL Qt shared libraries without viral copyleft contamination of the application's source code.
- **Migration Effort**: PySide6 maintains near 1:1 API compatibility with PyQt6. The migration requires updating imports from `PyQt6` to `PySide6`, mapping `pyqtSignal` to `Signal`, `pyqtSlot` to `Slot`, and testing multimedia backends.

```python
# PyQt6 to PySide6 Import Translation Standard
# From:
# from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
# from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
# To:
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
```

### 6.2 Complete Third-Party Dependency License Matrix

| Dependency | Runtime Version | Declared License | License Category | Commercial Distribution Compatibility |
| :--- | :---: | :---: | :---: | :---: |
| **Python** | 3.9.13 / 3.10+ | PSF License | Permissive | Compatible |
| **PySide6** (Target) | 6.8.x | LGPLv3 | Weak Copyleft | Compatible (via dynamic linking) |
| **PyQt6** (Legacy) | 6.10.2 | GPLv3 | Strong Copyleft | **INCOMPATIBLE with MIT** (Must Replace) |
| **PyQt6-Qt6** | 6.10.2 | LGPLv3 / GPLv3 | Weak Copyleft | Compatible if dynamically linked |
| **PyQt6_sip** | 13.10.2 | BSD-2-Clause | Permissive | Compatible |
| **PyTorch** (`torch`) | 2.5.1+cu121 | BSD-3-Clause | Permissive | Compatible |
| **torchaudio** | 2.5.1+cu121 | BSD-2-Clause | Permissive | Compatible |
| **torchvision** | 0.23.0 | BSD-3-Clause | Permissive | Compatible |
| **audio-separator** | 0.18.0 | MIT | Permissive | Compatible |
| **demucs** | 4.0.1 | MIT | Permissive | Compatible |
| **onnxruntime-gpu** | 1.19.2 | MIT | Permissive | Compatible |
| **onnx** | 1.19.1 | Apache 2.0 | Permissive | Compatible |
| **scipy** | 1.13.1 | BSD-3-Clause | Permissive | Compatible |
| **numpy** | 2.0.2 | BSD-3-Clause | Permissive | Compatible |
| **librosa** | 0.11.0 | ISC License | Permissive | Compatible |
| **soundfile** | 0.13.1 | BSD-3-Clause | Permissive | Compatible (Bundles libsndfile LGPL) |
| **pydub** | 0.25.1 | MIT | Permissive | Compatible |
| **yt-dlp** | 2025.10.14 | Unlicense | Public Domain | Compatible |
| **static_ffmpeg** | 3.0 | MIT | Permissive | Bundles FFmpeg binaries (LGPL/GPL) |
| **FFmpeg Binaries** | 6.1+ | LGPL 2.1+ / GPL 2.0+ | Copyleft | Compatible under LGPL builds |
| **requests** | 2.32.5 | Apache 2.0 | Permissive | Compatible |
| **tqdm** | 4.70.1 | MPL 2.0 / MIT | Permissive / Weak | Compatible |
| **soxr** | 1.1.0 | LGPL 2.1+ | Weak Copyleft | Compatible |
| **samplerate** | 0.1.0 | BSD-2-Clause | Permissive | Compatible |
| **diffq** | 0.2.4 | MIT | Permissive | Compatible |
| **einops** | 0.8.2 | MIT | Permissive | Compatible |
| **rotary-embedding-torch**| 0.6.5 | MIT | Permissive | Compatible |

### 6.3 Pretrained Neural Network Weights License Audit
The machine learning models leveraged by Devoice have distinct legal and commercial licensing boundaries:
1. **BS-RoFormer (`model_bs_roformer_ep_317_sdr_12.9755.ckpt`)**:
   - Trained and published by UVR community researchers (ViperX / TRvlvr).
   - Distributed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0)**.
   - *Implication*: End-users may freely utilize this model for personal, educational, and research workflows. Commercial monetization, sale of model weights, or integration into paid commercial software packages is strictly prohibited without explicit licensing from the authors.
2. **MDX-Net (`UVR-MDX-NET-Inst_HQ_3.onnx`)**:
   - Developed by Kuielab / UVR Community under UVR Non-Commercial Terms.
   - *Implication*: Non-commercial use only.
3. **Distribution Policy for Devoice V1**:
   - Devoice repository, binary executable, and DSP rack remain 100% permissively licensed (MIT / LGPLv3).
   - Model weights are **never bundled directly** inside the installer binary.
   - Instead, the application acts as an open client frontend, downloading model weights on-demand from public community repositories directly to the user's local machine upon user request. This insulates Devoice distribution from direct model weight licensing encumbrances.

---

## Section 7: Phased V1 Release Roadmap & Milestone Timeline

```
+-----------------------------------------------------------------------------+
|                               PHASE TIMELINE                                |
+-----------------------------------------------------------------------------+
|  Phase 1: Alpha 0.9      Phase 2: Beta 1.0       Phase 3: RC 1.0     GA 1.0 |
|  Core & Audio Fixes     Hardware Resilience       Packaging & UX     Launch |
|     (Weeks 1-3)             (Weeks 4-6)            (Weeks 7-9)      (Wk 10) |
+-----------------------------------------------------------------------------+
```

### 7.1 Phase 1: Alpha 0.9 — Core Pipeline Hardening & Audio Fidelity (Weeks 1-3)
*Focus: Resolving audio corruption defects, zero-phase filtering, and licensing compliance.*
- **Deliverables**:
  - Implement pure in-memory DSP rack (`process_dsp_rack`) preventing intermediate disk round-trips.
  - Fix `soundfile` format and subtype handling for FLAC (16/24-bit) and MP3 formats.
  - Implement forward-backward zero-phase filtering (`sosfiltfilt`) for sub-bass and de-esser stages.
  - Complete legal migration from `PyQt6` to `PySide6` (LGPLv3 compliance).
- **Exit Gate / Acceptance Criteria**:
  - 100% pass on unit and integration test suite across WAV, FLAC, and MP3 formats.
  - License audit scanner confirms zero GPLv3 packages linked to the binary.

### 7.2 Phase 2: Beta 1.0 — Hardware Agility & Resilient Diagnostics (Weeks 4-6)
*Focus: Out-of-memory survival, robust error reporting, and audio ingest validation.*
- **Deliverables**:
  - Implement two-stage automatic hardware fallback: catch `torch.cuda.OutOfMemoryError`, empty VRAM cache, reduce batch size, and fall back to CPU seamlessly.
  - Integrate global exception handler (`sys.excepthook`) and user-facing `CrashReportDialog`.
  - Implement audio ingest pre-validator rejecting corrupt, zero-byte, or unreadable audio files before separation pipeline entry.
  - Configure persistent rotating file logging (`%LOCALAPPDATA%\Devoice\logs\devoice.log`).
- **Exit Gate / Acceptance Criteria**:
  - Inducing simulated CUDA OOM recovers gracefully to CPU without application crash or data loss.
  - All unexpected errors generate structured diagnostic logs and user crash dialogs.

### 7.3 Phase 3: Release Candidate 1.0 (RC-1) — Packaging & Model Management UX (Weeks 7-9)
*Focus: Desktop installer, multi-backend support, and transparent asset downloads.*
- **Deliverables**:
  - Harden `packaging/devoice.spec` with all runtime hidden imports and static FFmpeg bundling.
  - Create Inno Setup 6 installer script with desktop shortcuts, file associations, and uninstaller.
  - Build GUI Model Manager with background QThread downloader, byte progress reporting, download cancellation, and SHA-256 verification.
  - Multi-platform packaging pipeline for Windows `.exe` and macOS `.dmg`.
- **Exit Gate / Acceptance Criteria**:
  - Standalone executable executes flawlessly on clean Windows 10/11 VMs without Python pre-installed.
  - Interrupted model downloads resume properly and verify SHA-256 checksums before loading.

### 7.4 Phase 4: General Availability 1.0 (GA) — Public Release (Week 10)
*Focus: Distribution, continuous integration, and community launch.*
- **Deliverables**:
  - Publish GitHub Actions automated release matrix building both Windows GPU Edition and CPU/DirectML Edition.
  - macOS notarization and Gatekeeper signing.
  - Comprehensive user documentation, quickstart guide, and troubleshooting handbook.
  - Official V1.0.0 release publication on GitHub Releases.
- **Exit Gate / Acceptance Criteria**:
  - Full end-to-end regression pass on Windows, macOS, and Linux.
  - Formal security and dependency vulnerability audit sign-off.
