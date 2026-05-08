import os
import sys
import shutil
import subprocess
import threading
import urllib.request
from pathlib import Path
from enum import Enum, auto
from typing import Callable


class RuntimeMode(Enum):
    CLI_GLOBAL = auto()   # ww مثبت عالمياً في PATH
    EMBEDDED   = auto()   # ww.exe داخل runtime/
    NOT_FOUND  = auto()   # لم يتم العثور عليه


class RuntimeManager:
    """
    مدير وضع التشغيل

    أولوية البحث:
    ─────────────────────────────────────────
    1. runtime/ww.exe  (بجانب البرنامج)
    2. PATH العالمي    (go install)
    3. المسارات الافتراضية لـ Go
    4. NOT_FOUND
    """

    DOWNLOAD_URL = (
        "https://github.com/ReizanTech/pywormhole"
        "/raw/main/assets/bin/ww.exe"
    )

    def __init__(self):
        self._mode: RuntimeMode | None = None
        self._ww_path: str | None = None
        self._runtime_dir = self._get_runtime_dir()

    # ─────────────────────────────────────────────────────
    # تحديد مجلد runtime/
    # ─────────────────────────────────────────────────────
    @staticmethod
    def _get_runtime_dir() -> Path:
        """
        تحديد مجلد runtime/ بالنسبة للبرنامج

        PyInstaller → مجلد الـ exe
        Development → مجلد المشروع (pywormhole/)
        """
        if getattr(sys, "frozen", False):
            # تشغيل من PyInstaller
            base = Path(sys.executable).parent
        else:
            # تشغيل من الكود مباشرة
            base = Path(__file__).resolve().parent.parent

        return base / "runtime"

    # ─────────────────────────────────────────────────────
    # الاكتشاف الرئيسي
    # ─────────────────────────────────────────────────────
    def detect(self) -> "RuntimeMode":
        """
        البحث عن ww بالترتيب:

        ┌─────────────────────────────────────────┐
        │  1. runtime/ww.exe  (Embedded)          │ ← أولوية قصوى
        │  2. PATH العالمي    (CLI Global)         │
        │  3. مسارات Go الافتراضية               │
        │  4. NOT_FOUND                           │
        └─────────────────────────────────────────┘
        """

        # ── 1. البحث في runtime/ أولاً ──────────────────
        embedded = self._find_embedded()
        if embedded:
            self._mode    = RuntimeMode.EMBEDDED
            self._ww_path = embedded
            return self._mode

        # ── 2. البحث في PATH العالمي ─────────────────────
        global_ww = shutil.which("ww")
        if global_ww:
            self._mode    = RuntimeMode.CLI_GLOBAL
            self._ww_path = global_ww
            return self._mode

        # ── 3. مسارات Go الافتراضية ──────────────────────
        go_default = self._find_go_default()
        if go_default:
            self._mode    = RuntimeMode.CLI_GLOBAL
            self._ww_path = go_default
            return self._mode

        # ── 4. لم يتم العثور ─────────────────────────────
        self._mode = RuntimeMode.NOT_FOUND
        return self._mode

    # ─────────────────────────────────────────────────────
    # البحث في runtime/
    # ─────────────────────────────────────────────────────
    def _find_embedded(self) -> str | None:
        """
        البحث عن ww.exe في مجلد runtime/

        يبحث في:
        - runtime/ww.exe   (Windows)
        - runtime/ww       (Linux/macOS)
        """
        candidates = [
            self._runtime_dir / "ww.exe",
            self._runtime_dir / "ww",
        ]

        for path in candidates:
            if path.exists() and path.is_file():
                # التحقق أنه قابل للتنفيذ
                if self._is_executable(path):
                    return str(path)

        return None

    # ─────────────────────────────────────────────────────
    # البحث في مسارات Go الافتراضية
    # ─────────────────────────────────────────────────────
    def _find_go_default(self) -> str | None:
        """
        البحث في المسارات التي يضعها Go تلقائياً

        Windows:
          C:\\Users\\<user>\\go\\bin\\ww.exe
          %GOPATH%\\bin\\ww.exe

        macOS / Linux:
          ~/go/bin/ww
          $GOPATH/bin/ww
        """
        home    = Path.home()
        gopath  = os.environ.get("GOPATH", "")

        candidates: list[Path] = []

        if sys.platform == "win32":
            candidates += [
                home / "go" / "bin" / "ww.exe",
                Path(gopath) / "bin" / "ww.exe" if gopath else None,
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "go" / "bin" / "ww.exe",
            ]
        else:
            candidates += [
                home / "go" / "bin" / "ww",
                Path(gopath) / "bin" / "ww" if gopath else None,
                Path("/usr/local/bin/ww"),
                Path("/usr/bin/ww"),
            ]

        for path in candidates:
            if path and path.exists() and path.is_file():
                if self._is_executable(path):
                    return str(path)

        return None

    # ─────────────────────────────────────────────────────
    # التحقق من قابلية التنفيذ
    # ─────────────────────────────────────────────────────
    @staticmethod
    def _is_executable(path: Path) -> bool:
        """التحقق أن الملف قابل للتنفيذ"""
        if sys.platform == "win32":
            return True  # Windows يعتمد على الامتداد .exe
        return os.access(path, os.X_OK)

    # ─────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────
    @property
    def mode(self) -> RuntimeMode | None:
        return self._mode

    @property
    def ww_path(self) -> str | None:
        return self._ww_path

    @property
    def runtime_dir(self) -> Path:
        return self._runtime_dir

    @property
    def is_available(self) -> bool:
        return self._mode in (
            RuntimeMode.CLI_GLOBAL,
            RuntimeMode.EMBEDDED,
        )

    @property
    def mode_label(self) -> str:
        labels = {
            RuntimeMode.CLI_GLOBAL: "CLI Global",
            RuntimeMode.EMBEDDED:   "Embedded Runtime",
            RuntimeMode.NOT_FOUND:  "غير موجود",
        }
        return labels.get(self._mode, "غير معروف")

    # ─────────────────────────────────────────────────────
    # إعادة الاكتشاف
    # ─────────────────────────────────────────────────────
    def recheck(self) -> "RuntimeMode":
        """إعادة البحث من الصفر"""
        self._mode    = None
        self._ww_path = None
        return self.detect()

    # ─────────────────────────────────────────────────────
    # تحميل ww.exe
    # ─────────────────────────────────────────────────────
    def download_embedded(
        self,
        on_progress: Callable[[int, int], None] | None = None,
        on_complete: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """تحميل ww.exe في خيط منفصل"""
        thread = threading.Thread(
            target=self._download_thread,
            args=(on_progress, on_complete, on_error),
            daemon=True,
        )
        thread.start()

    def _download_thread(
        self,
        on_progress: Callable | None,
        on_complete: Callable | None,
        on_error: Callable | None,
    ) -> None:
        try:
            # ── إنشاء مجلد runtime/ ──
            self._runtime_dir.mkdir(parents=True, exist_ok=True)

            # ── اسم الملف حسب النظام ──
            filename = "ww.exe" if sys.platform == "win32" else "ww"
            save_path = self._runtime_dir / filename

            # ── تحميل مع تتبع التقدم ──
            def reporthook(block_num: int, block_size: int, total_size: int):
                if on_progress:
                    downloaded = min(block_num * block_size, total_size)
                    on_progress(downloaded, total_size)

            urllib.request.urlretrieve(
                self.DOWNLOAD_URL,
                str(save_path),
                reporthook,
            )

            # ── صلاحيات التنفيذ (Linux/macOS) ──
            if sys.platform != "win32":
                save_path.chmod(0o755)

            # ── تحديث الـ mode ──
            self._mode    = RuntimeMode.EMBEDDED
            self._ww_path = str(save_path)

            if on_complete:
                on_complete(str(save_path))

        except Exception as e:
            if on_error:
                on_error(str(e))

    # ─────────────────────────────────────────────────────
    # تسجيل runtime/ في PATH (اختياري)
    # ─────────────────────────────────────────────────────
    def register_global_path(self) -> tuple[bool, str]:
        """
        إضافة runtime/ إلى PATH النظام
        حتى يعمل ww من أي Terminal

        Returns:
            (success, message)
        """
        runtime_str = str(self._runtime_dir)

        try:
            if sys.platform == "win32":
                return self._register_windows(runtime_str)
            else:
                return self._register_unix(runtime_str)
        except Exception as e:
            return False, str(e)

    def _register_windows(self, path: str) -> tuple[bool, str]:
        """
        إضافة المسار إلى User PATH في الـ registry مباشرة.

        لماذا لا نستخدم setx PATH <full_path>؟
        - os.environ["PATH"] يدمج User PATH + System PATH
        - setx له حد أقصى 1024 حرف
        - تمريره بالكامل يُفسد الـ PATH أو يقطعه

        الحل الصحيح: قراءة User PATH من الـ registry وإضافة المسار إليه فقط.
        """
        try:
            import winreg

            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE,
            )

            # قراءة User PATH الحالي (بدون System PATH)
            try:
                user_path, _ = winreg.QueryValueEx(reg_key, "PATH")
            except FileNotFoundError:
                user_path = ""

            # التحقق إذا كان المسار موجوداً بالفعل
            existing = [p.strip() for p in user_path.split(";") if p.strip()]
            if path.lower() in [p.lower() for p in existing]:
                winreg.CloseKey(reg_key)
                return True, "المسار موجود بالفعل في PATH"

            # إضافة المسار الجديد
            new_path = f"{user_path};{path}" if user_path else path
            winreg.SetValueEx(reg_key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(reg_key)

            # تحديث الـ session الحالي أيضاً
            os.environ["PATH"] = os.environ.get("PATH", "") + f";{path}"

            # إخطار Windows بتغيير بيئة النظام
            try:
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                    0x0002, 5000, None
                )
            except Exception:
                pass  # ليست حرجة

            return True, (
                f"تم إضافة المسار إلى User PATH:\n{path}\n\n"
                "⚠️ افتح نافذة PowerShell جديدة لتفعيل التغيير."
            )

        except ImportError:
            # winreg غير متاح (لا ينبغي أن يحدث على Windows)
            return False, "winreg غير متاح"
        except PermissionError:
            return False, "لا توجد صلاحيات كافية لتعديل الـ registry"
        except Exception as e:
            return False, str(e)

    def _register_unix(self, path: str) -> tuple[bool, str]:
        shell_rc = Path.home() / (
            ".zshrc"
            if (Path.home() / ".zshrc").exists()
            else ".bashrc"
        )

        export_line = f'\nexport PATH="$PATH:{path}"\n'

        with open(shell_rc, "a") as f:
            f.write(export_line)

        os.environ["PATH"] = f"{os.environ.get('PATH', '')}:{path}"
        return True, f"تم إضافة السطر إلى {shell_rc}"

    # ─────────────────────────────────────────────────────
    # تشخيص (للـ debugging)
    # ─────────────────────────────────────────────────────
    def get_debug_info(self) -> dict:
        """معلومات تشخيصية كاملة"""
        return {
            "mode":         self.mode_label,
            "ww_path":      self._ww_path,
            "runtime_dir":  str(self._runtime_dir),
            "runtime_exists": self._runtime_dir.exists(),
            "embedded_exe": str(self._runtime_dir / "ww.exe"),
            "embedded_exists": (self._runtime_dir / "ww.exe").exists(),
            "global_ww":    shutil.which("ww"),
            "go_default":   self._find_go_default(),
            "platform":     sys.platform,
            "frozen":       getattr(sys, "frozen", False),
        }