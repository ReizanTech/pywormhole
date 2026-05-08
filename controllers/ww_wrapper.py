import subprocess
import threading
import sys
from typing import Callable

from utils.runtime_manager import RuntimeManager, RuntimeMode
from utils.helpers import sanitize_input
from utils.parser import WWOutputParser, ProgressUpdate

# instance مشترك في كل البرنامج
_runtime = RuntimeManager()
_runtime.detect()


def get_runtime() -> RuntimeManager:
    """الحصول على الـ RuntimeManager المشترك"""
    return _runtime


class WWWrapper:
    """
    غلاف subprocess للـ WebWormhole CLI
    يدعم CLI Mode و Embedded Mode تلقائياً
    """

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._cancelled: bool = False   # ← flag لتمييز الإلغاء عن الخطأ

    @property
    def is_available(self) -> bool:
        return _runtime.is_available

    @property
    def runtime_mode(self) -> RuntimeMode:
        return _runtime.mode

    # ─────────────────────────────────────────
    def send(
        self,
        filepath: str,
        on_update: Callable[[ProgressUpdate], None] | None = None,
        on_complete: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if not self.is_available:
            if on_error:
                on_error("ww غير متاح")
            return

        safe_path = sanitize_input(filepath)
        self._run_async(
            [_runtime.ww_path, "send", safe_path],
            on_update, on_complete, on_error,
        )

    def receive(
        self,
        code: str,
        save_dir: str | None = None,
        on_update: Callable[[ProgressUpdate], None] | None = None,
        on_complete: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if not self.is_available:
            if on_error:
                on_error("ww غير متاح")
            return

        safe_code = sanitize_input(code)
        self._run_async(
            [_runtime.ww_path, "receive", safe_code],
            on_update, on_complete, on_error,
            cwd=save_dir,
        )

    def cancel(self) -> None:
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()

    # ─────────────────────────────────────────
    def _run_async(
        self,
        cmd: list[str],
        on_update, on_complete, on_error,
        cwd: str | None = None,
    ) -> None:
        self._cancelled = False   # ← reset عند كل عملية جديدة
        self._thread = threading.Thread(
            target=self._run_command,
            args=(cmd, on_update, on_complete, on_error),
            kwargs={"cwd": cwd},
            daemon=True,
        )
        self._thread.start()

    def _run_command(
        self,
        cmd, on_update, on_complete, on_error,
        cwd=None,
    ) -> None:
        parser = WWOutputParser()
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cwd,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32" else 0
                ),
            )
            for line in self._process.stdout:
                update = parser.parse_line(line)
                if on_update and (
                    update.session_code
                    or update.progress_percent is not None
                    or update.is_complete
                    or update.error_message
                ):
                    on_update(update)
                if update.is_complete:
                    break

            self._process.wait()

            if self._cancelled:
                return   # ← المستخدم ألغى — لا نُطلق on_error

            if self._process.returncode == 0:
                if on_complete:
                    on_complete()
            else:
                if on_error:
                    on_error(
                        f"فشل ww برمز الخروج: {self._process.returncode}"
                    )
        except FileNotFoundError:
            if on_error:
                on_error(f"الملف غير موجود: {cmd[0]}")
        except Exception as e:
            if not self._cancelled and on_error:
                on_error(str(e))
        finally:
            self._process = None