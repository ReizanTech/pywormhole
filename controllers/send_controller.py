from typing import Callable
from controllers.ww_wrapper import WWWrapper
from utils.parser import ProgressUpdate


class SendController:
    """
    يدير منطق الإرسال الكامل

    يربط بين:
    - UI (SenderScreen)
    - WWWrapper (subprocess)
    - Parser (output parsing)
    """

    def __init__(self):
        self._wrapper = WWWrapper()
        self._session_code: str | None = None

    @property
    def is_ww_available(self) -> bool:
        return self._wrapper.is_available

    @property
    def session_code(self) -> str | None:
        return self._session_code

    def start_send(
        self,
        filepath: str,
        on_code_received: Callable[[str], None],
        on_progress: Callable[[float, str], None],
        on_complete: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        """
        بدء عملية الإرسال

        Args:
            filepath        : مسار الملف
            on_code_received: callback عند ظهور الكود
            on_progress     : callback (percent, status_text)
            on_complete     : callback عند الانتهاء
            on_error        : callback عند الخطأ
        """
        self._session_code = None

        def handle_update(update: ProgressUpdate) -> None:
            # ── استخرج الكود ──
            if update.session_code and not self._session_code:
                self._session_code = update.session_code
                on_code_received(update.session_code)

            # ── التقدم ──
            if update.progress_percent is not None:
                on_progress(
                    update.progress_percent,
                    update.status_text or ""
                )

            # ── خطأ ──
            if update.error_message:
                on_error(update.error_message)

        self._wrapper.send(
            filepath=filepath,
            on_update=handle_update,
            on_complete=on_complete,
            on_error=on_error,
        )

    def cancel(self) -> None:
        """إلغاء الإرسال"""
        self._wrapper.cancel()