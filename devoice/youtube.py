"""YouTube audio extraction utility for Devoice using yt-dlp."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable, Optional

import static_ffmpeg
import yt_dlp

logger = logging.getLogger(__name__)

# Matches standard YouTube URLs, short URLs, YouTube Music, and Shorts
YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.|m\.|music\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[a-zA-Z0-9_-]+",
    re.IGNORECASE,
)


def is_youtube_url(text: str) -> bool:
    """Return True if text is or contains a valid YouTube video URL."""
    if not text:
        return False
    clean = text.strip()
    return bool(YOUTUBE_REGEX.search(clean))


def extract_youtube_url(text: str) -> Optional[str]:
    """Extract and normalize a YouTube URL from an input string."""
    if not text:
        return None
    clean = text.strip()
    match = YOUTUBE_REGEX.search(clean)
    if not match:
        return None
    url = match.group(0)
    # If schema is missing, prepend https://
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def download_youtube_audio(
    url: str,
    output_dir: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Path:
    """Download highest quality audio from a YouTube video and convert to MP3.

    Parameters
    ----------
    url : str
        YouTube video URL.
    output_dir : Path
        Directory where the downloaded MP3 file will be saved.
    progress_callback : callable, optional
        Callback receiving (percentage: int, status_message: str).

    Returns
    -------
    Path
        Path to the downloaded and converted MP3 file.
    """
    # Ensure static ffmpeg binaries are in PATH
    static_ffmpeg.add_paths()

    output_dir.mkdir(parents=True, exist_ok=True)
    norm_url = extract_youtube_url(url)
    if not norm_url:
        raise ValueError(f"URL YouTube invalide : {url}")

    def _progress_hook(d: dict) -> None:
        if not progress_callback:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            pct = int(downloaded / total * 100) if total > 0 else 10
            pct = max(5, min(90, pct))
            progress_callback(pct, f"Téléchargement… {pct}%")
        elif status == "finished":
            progress_callback(95, "Extraction audio MP3...")

    # yt-dlp configuration
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "windowsfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_progress_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
    }

    if progress_callback:
        progress_callback(5, "Connexion à YouTube…")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(norm_url, download=True)
        if info_dict is None:
            raise RuntimeError("Impossible de récupérer les informations de la vidéo.")

        # Check requested_downloads first
        req_dl = info_dict.get("requested_downloads")
        if req_dl and isinstance(req_dl, list) and len(req_dl) > 0:
            final_filepath = req_dl[-1].get("filepath")
            if final_filepath and Path(final_filepath).exists():
                return Path(final_filepath)

        # Fallback to prepared filename with .mp3 extension
        prepared = Path(ydl.prepare_filename(info_dict)).with_suffix(".mp3")
        if prepared.exists():
            return prepared

        # Last resort: find newest mp3 in output_dir
        mp3_candidates = list(output_dir.glob("*.mp3"))
        if mp3_candidates:
            mp3_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return mp3_candidates[0]

        raise FileNotFoundError("Le fichier audio MP3 n'a pas pu être localisé après l'extraction.")
