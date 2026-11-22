"""Windows Desktop Window Manager (DWM) dark mode & modern titlebar integration."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


def apply_windows_dark_titlebar(
    hwnd: int,
    bg_color: tuple[int, int, int] = (9, 9, 11),       # #09090b
    text_color: tuple[int, int, int] = (244, 244, 245), # #f4f4f5
    border_color: tuple[int, int, int] = (39, 39, 42),  # #27272a
) -> bool:
    """Apply native Windows 11/10 dark mode title bar and custom color accents.

    Uses DwmSetWindowAttribute with DWMWA_USE_IMMERSIVE_DARK_MODE (20),
    DWMWA_CAPTION_COLOR (35), DWMWA_TEXT_COLOR (36), and DWMWA_BORDER_COLOR (34).
    """
    if sys.platform != "win32":
        return False

    try:
        dwmapi = ctypes.windll.dwmapi
        DwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute

        # 1. Immersive Dark Mode (attribute 20 on Win11/Win10 build 19041+, attribute 19 on older Win10)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
        use_dark_mode = ctypes.c_int(1)

        res = DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(use_dark_mode),
            ctypes.sizeof(use_dark_mode),
        )
        if res != 0:
            DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                wintypes.DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE_OLD),
                ctypes.byref(use_dark_mode),
                ctypes.sizeof(use_dark_mode),
            )

        # 2. Windows 11 Custom Titlebar Caption, Text & Border Colors (Win11 Build 22000+)
        # COLORREF format in Win32: 0x00BBGGRR
        r, g, b = bg_color
        caption_ref = ctypes.c_uint32(r | (g << 8) | (b << 16))
        DWMWA_CAPTION_COLOR = 35
        DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_CAPTION_COLOR),
            ctypes.byref(caption_ref),
            ctypes.sizeof(caption_ref),
        )

        tr, tg, tb = text_color
        text_ref = ctypes.c_uint32(tr | (tg << 8) | (tb << 16))
        DWMWA_TEXT_COLOR = 36
        DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_TEXT_COLOR),
            ctypes.byref(text_ref),
            ctypes.sizeof(text_ref),
        )

        br, bg_b, bb = border_color
        border_ref = ctypes.c_uint32(br | (bg_b << 8) | (bb << 16))
        DWMWA_BORDER_COLOR = 34
        DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_BORDER_COLOR),
            ctypes.byref(border_ref),
            ctypes.sizeof(border_ref),
        )

        return True
    except Exception:
        return False
