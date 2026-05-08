from typing import Callable
from controllers.ww_wrapper import WWWrapper
from utils.parser import ProgressUpdate, validate_session_code


class ReceiveController:
    """
    يدير منطق الاستقبال الكامل
    """

    def __init__(self):
        self._wrapper = WWWrapper()

    @property
    def is_ww_available(self) -> bool:
        return self._wrapper.is_available

    def start_receive(
        self,
        code: str,
        save_dir: str,
        on_progress: Callable[[float, str], None],
        on_complete: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        """
        بدء عملية الاستقبال

        Args:
            code      : كود الجلسة (word-word-word)
            save_dir  : مجلد الحفظ
            on_progress: callback (percent, status_text)
            on_complete: callback عند الانتهاء
            on_error  : callback عند الخطأ
        """
        # ── التحقق من الكود ──
        if not validate_session_code(code):
            on_error(
                f"تنسيق الكود غير صحيح: '{code}'\n"
                "التنسيق المتوقع: كلمة-كلمة-كلمة\n"
                "مثال: tiger-moon-cloud"
            )
            return

        def handle_update(update: ProgressUpdate) -> None:
            if update.progress_percent is not None:
                on_progress(
                    update.progress_percent,
                    update.status_text or ""
                )
            if update.error_message:
                on_error(update.error_message)

        self._wrapper.receive(
            code=code,
            save_dir=save_dir,
            on_update=handle_update,
            on_complete=on_complete,
            on_error=on_error,
        )

    def cancel(self) -> None:
        """إلغاء الاستقبال"""
        self._wrapper.cancel()