import shutil
import sys
import os
from pathlib import Path


def find_ww_executable() -> str | None:
    """
    البحث عن ملف ww التنفيذي في النظام

    ترتيب البحث:
    1. PATH المعتاد
    2. مجلد البرنامج الحالي
    3. مجلدات مخصصة لكل نظام

    Returns:
        مسار ww أو None إذا لم يُوجد
    """
    # ── 1. البحث في PATH ──
    ww_in_path = shutil.which("ww")
    if ww_in_path:
        return ww_in_path

    # ── 2. البحث بجانب البرنامج ──
    current_dir = Path(sys.executable).parent
    candidates = [
        current_dir / "ww",
        current_dir / "ww.exe",
    ]

    # ── 3. مجلدات مخصصة ──
    if sys.platform == "win32":
        candidates += [
            Path(os.environ.get("LOCALAPPDATA", "")) / "ww" / "ww.exe",
            Path("C:/Program Files/ww/ww.exe"),
        ]
    elif sys.platform == "darwin":
        candidates += [
            Path("/usr/local/bin/ww"),
            Path("/opt/homebrew/bin/ww"),
        ]
    else:  # Linux
        candidates += [
            Path("/usr/local/bin/ww"),
            Path(os.environ.get("HOME", "")) / "go" / "bin" / "ww",
        ]

    for path in candidates:
        if path.exists() and path.is_file():
            return str(path)

    return None


def get_default_downloads_dir() -> str:
    """
    الحصول على مجلد التنزيلات الافتراضي

    Windows: C:/Users/User/Downloads
    macOS:   ~/Downloads
    Linux:   ~/Downloads
    """
    home = Path.home()

    downloads = home / "Downloads"
    if downloads.exists():
        return str(downloads)

    return str(home)


def sanitize_input(text: str) -> str:
    """
    تنظيف المدخلات من الأحرف الخطيرة
    لمنع command injection

    الأحرف المحذوفة: ; | & $ ` ( ) < > \n \r
    """
    dangerous = [';', '|', '&', '$', '`', '(', ')', '<', '>', '\n', '\r']
    for char in dangerous:
        text = text.replace(char, '')
    return text.strip()


def format_file_size(size_bytes: int) -> str:
    """تحويل الحجم لصيغة مقروءة"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def get_installation_guide() -> str:
    """
    رسالة تثبيت ww حسب نظام التشغيل
    """
    if sys.platform == "win32":
        return (
            "لم يتم العثور على WebWormhole CLI (ww)\n\n"
            "لتثبيته على Windows:\n"
            "1. ثبّت Go من https://golang.org/dl/\n"
            "2. شغّل: go install webwormhole.io/cmd/ww@latest\n"
            "3. تأكد من إضافة %GOPATH%\\bin إلى PATH"
        )
    elif sys.platform == "darwin":
        return (
            "لم يتم العثور على WebWormhole CLI (ww)\n\n"
            "لتثبيته على macOS:\n"
            "الطريقة 1 (Homebrew):\n"
            "  brew install webwormhole\n\n"
            "الطريقة 2 (Go):\n"
            "  go install webwormhole.io/cmd/ww@latest"
        )
    else:
        return (
            "لم يتم العثور على WebWormhole CLI (ww)\n\n"
            "لتثبيته على Linux:\n"
            "  go install webwormhole.io/cmd/ww@latest\n\n"
            "أو من المستودع:\n"
            "  https://github.com/nanoq-io/ww"
        )