import subprocess
import threading
import sys
from typing import Callable
from pathlib import Path

from utils.helpers import find_ww_executable, sanitize_input
from utils.parser import WWOutputParser, ProgressUpdate


class WWWrapper:
    """
    غلاف subprocess للـ WebWormhole CLI

    المسؤوليات:
    ───────────
    1. تنفيذ أوامر ww
    2. قراءة output بشكل streaming
    3. تمرير التحديثات للـ callbacks
    4. إدارة إلغاء العملية

    مثال الاستخدام:
    ───────────────
    wrapper = WWWrapper()
    wrapper.send(
        filepath="/path/to/file.zip",
        on_update=lambda u: print(u.progress_percent),
        on_complete=lambda: print("Done!"),
        on_error=lambda e: print(f"Error: {e}"),
    )
    """

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._ww_path: str | None = find_ww_executable()

    # ─────────────────────────────────────────
    # التحقق من وجود ww
    # ─────────────────────────────────────────
    @property
    def is_available(self) -> bool:
        """هل ww مثبت ومتاح؟"""
        return self._ww_path is not None

    # ─────────────────────────────────────────
    # إرسال ملف
    # ─────────────────────────────────────────
    def send(
        self,
        filepath: str,
        on_update: Callable[[ProgressUpdate], None] | None = None,
        on_complete: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """
        تنفيذ: ww send <filepath>

        يعمل في خيط منفصل لعدم تجميد الـ UI
        """
        if not self.is_available:
            if on_error:
                on_error("ww غير مثبت")
            return

        # تنظيف المدخلات
        safe_path = sanitize_input(filepath)

        self._thread = threading.Thread(
            target=self._run_command,
            args=(
                [self._ww_path, "send", safe_path],
                on_update,
                on_complete,
                on_error,
            ),
            daemon=True,
        )
        self._thread.start()

    # ─────────────────────────────────────────
    # استقبال ملف
    # ─────────────────────────────────────────
    def receive(
        self,
        code: str,
        save_dir: str | None = None,
        on_update: Callable[[ProgressUpdate], None] | None = None,
        on_complete: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """
        تنفيذ: ww receive <code>

        يعمل في خيط منفصل لعدم تجميد الـ UI
        """
        if not self.is_available:
            if on_error:
                on_error("ww غير مثبت")
            return

        safe_code = sanitize_input(code)
        cmd = [self._ww_path, "receive", safe_code]

        # تغيير مجلد العمل لتحديد مكان الحفظ
        cwd = save_dir if save_dir else None

        self._thread = threading.Thread(
            target=self._run_command,
            args=(cmd, on_update, on_complete, on_error),
            kwargs={"cwd": cwd},
            daemon=True,
        )
        self._thread.start()

    # ─────────────────────────────────────────
    # إلغاء العملية
    # ─────────────────────────────────────────
    def cancel(self) -> None:
        """إيقاف عملية ww الجارية"""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()

    # ─────────────────────────────────────────
    # تنفيذ الأمر (داخلي)
    # ─────────────────────────────────────────
    def _run_command(
        self,
        cmd: list[str],
        on_update: Callable[[ProgressUpdate], None] | None,
        on_complete: Callable[[], None] | None,
        on_error: Callable[[str], None] | None,
        cwd: str | None = None,
    ) -> None:
        """
        تنفيذ الأمر وقراءة output بشكل streaming

        التدفق:
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  Popen   │───►│  قراءة  │───►│ callback │
        │  (cmd)   │    │  stdout │    │  update  │
        └──────────┘    └──────────┘    └──────────┘
        """
        parser = WWOutputParser()

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # دمج stderr مع stdout
                text=True,
                bufsize=1,                 # line buffered
                cwd=cwd,
                # منع ظهور نافذة cmd على Windows
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32" else 0
                ),
            )

            # ── قراءة output سطراً بسطر ──
            for line in self._process.stdout:
                update = parser.parse_line(line)

                if on_update:
                    on_update(update)

                # اكتملت العملية؟
                if update.is_complete:
                    break

            # انتظار انتهاء العملية
            self._process.wait()

            # ── تحديد النتيجة ──
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
                on_error(f"الأمر غير موجود: {cmd[0]}")
        except Exception as e:
            if on_error:
                on_error(str(e))
        finally:
            self._process = None