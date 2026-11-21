"""Unit tests for YouTube audio extraction in Devoice."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import QMimeData

from devoice.ui.drop_zone import DropZone
from devoice.youtube import download_youtube_audio, extract_youtube_url, is_youtube_url


def test_is_youtube_url():
    valid = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ&si=123",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "http://youtu.be/dQw4w9WgXcQ",
        "youtu.be/dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    for url in valid:
        assert is_youtube_url(url), f"Failed for {url}"

    invalid = [
        "https://soundcloud.com/artist/track",
        "https://spotify.com/track/123",
        "https://google.com",
        "C:\\Users\\music\\song.mp3",
        "",
        "not a url",
    ]
    for url in invalid:
        assert not is_youtube_url(url), f"Should not match {url}"


def test_extract_youtube_url():
    assert extract_youtube_url("https://youtu.be/dQw4w9WgXcQ") == "https://youtu.be/dQw4w9WgXcQ"
    assert extract_youtube_url("youtu.be/dQw4w9WgXcQ") == "https://youtu.be/dQw4w9WgXcQ"
    assert extract_youtube_url("Check this: https://youtube.com/watch?v=dQw4w9WgXcQ") == "https://youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_youtube_url("invalid") is None


def test_download_youtube_audio_mock(tmp_path: Path):
    target_mp3 = tmp_path / "Rick Astley - Never Gonna Give You Up.mp3"
    target_mp3.write_bytes(b"dummy mp3 data")

    with patch("devoice.youtube.yt_dlp.YoutubeDL") as mock_ydl_cls, \
         patch("devoice.youtube.static_ffmpeg.add_paths"):

        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        mock_ydl.extract_info.return_value = {
            "title": "Rick Astley - Never Gonna Give You Up",
            "requested_downloads": [{"filepath": str(target_mp3)}],
        }

        progress_calls = []

        def callback(pct, msg):
            progress_calls.append((pct, msg))

        result = download_youtube_audio(
            "https://youtu.be/dQw4w9WgXcQ",
            output_dir=tmp_path,
            progress_callback=callback,
        )

        assert result == target_mp3
        assert len(progress_calls) >= 1
        assert progress_calls[0][0] == 5


def test_drop_zone_youtube_signal(qapp):
    drop_zone = DropZone()
    received_urls = []
    drop_zone.youtube_url_dropped.connect(received_urls.append)

    # Simulate drop event with YouTube text
    mime = QMimeData()
    mime.setText("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    event = MagicMock()
    event.mimeData.return_value = mime
    drop_zone.dropEvent(event)

    assert len(received_urls) == 1
    assert "dQw4w9WgXcQ" in received_urls[0]


def test_main_window_youtube_integration(qapp, tmp_path: Path):
    from devoice.ui.main_window import MainWindow

    window = MainWindow()
    test_mp3 = tmp_path / "song.mp3"
    test_mp3.write_bytes(b"dummy")

    with patch("devoice.ui.main_window.YouTubeDownloadWorker") as mock_worker_cls:
        mock_worker = MagicMock()
        mock_worker_cls.return_value = mock_worker

        window.yt_input.setText("https://youtu.be/dQw4w9WgXcQ")
        window._on_youtube_download_clicked()

        assert window.yt_btn.text() == "…"
        assert not window.yt_btn.isEnabled()
        mock_worker.start.assert_called_once()

        # Simulate finished download
        window._on_youtube_finished(test_mp3)

        assert window.yt_btn.isEnabled()
        assert window.yt_btn.text() == "Télécharger"
        assert window.yt_input.text() == ""
        assert test_mp3 in window.pending_files
        assert window.start_btn.isEnabled()

