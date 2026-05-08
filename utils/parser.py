import re
from dataclasses import dataclass, field


@dataclass
class ProgressUpdate:
    progress_percent: float | None = None
    status_text: str | None = None
    session_code: str | None = None
    error_message: str | None = None
    is_complete: bool = False


class WWOutputParser:
    """
    محلل output الـ WebWormhole CLI

    Output الفعلي لـ ww send:
    ──────────────────────────
    grasp-jolt-crust                          ← السطر الأول
    [QR في الترمنال]
    https://webwormhole.com#grasp-jolt-crust  ← آخر سطر

    Output الفعلي لـ ww receive:
    ─────────────────────────────
    Receiving receiver.py
    100% |████████████| 1.2 kB/1.2 kB
    """

    def __init__(self):
        self._code_found = False
        self._line_count = 0
        self._last_url: str | None = None

    def parse_line(self, line: str) -> ProgressUpdate:
        line_stripped = line.strip()
        if not line_stripped:
            return ProgressUpdate()

        self._line_count += 1
        update = ProgressUpdate()

        # ────────────────────────────────────────────────
        # 1. السطر الأول دايماً هو الكود
        #    grasp-jolt-crust
        # ────────────────────────────────────────────────
        if self._line_count == 1:
            if re.match(r'^[a-z]+-[a-z]+-[a-z]+$', line_stripped):
                update.session_code = line_stripped
                self._code_found = True
                return update

        # ────────────────────────────────────────────────
        # 2. آخر سطر هو الـ URL
        #    https://webwormhole.com#grasp-jolt-crust
        #    نقرأ الكود منه كـ fallback لو السطر الأول فاتنا
        # ────────────────────────────────────────────────
        url_match = re.search(
            r'https?://\S+#([a-z]+-[a-z]+-[a-z]+)',
            line_stripped
        )
        if url_match:
            self._last_url = line_stripped
            if not self._code_found:
                update.session_code = url_match.group(1)
                self._code_found = True
            # الـ URL = نهاية جزء الإعداد
            update.status_text = "✅ جاهز — في انتظار المستقبل"
            return update

        # ────────────────────────────────────────────────
        # 3. تجاهل سطور الـ QR (تحتوي على █ أو ▄ أو ▀)
        # ────────────────────────────────────────────────
        if re.search(r'[█▄▀]', line_stripped):
            return ProgressUpdate()

        # ────────────────────────────────────────────────
        # 4. نسبة التقدم
        #    100% |████| 1.2 kB/1.2 kB
        # ────────────────────────────────────────────────
        progress_match = re.search(r'(\d+(?:\.\d+)?)\s*%', line_stripped)
        if progress_match:
            update.progress_percent = float(progress_match.group(1))
            update.status_text = line_stripped

        # ────────────────────────────────────────────────
        # 5. اكتمال النقل
        # ────────────────────────────────────────────────
        if re.search(
            r'\b(done|complete|saved|received|sent)\b',
            line_stripped,
            re.IGNORECASE
        ):
            update.is_complete = True
            update.progress_percent = 100.0

        # ────────────────────────────────────────────────
        # 6. الأخطاء
        # ────────────────────────────────────────────────
        error_match = re.search(
            r'\b(error|failed|refused|invalid|timeout)\b[:\s]*(.*)',
            line_stripped,
            re.IGNORECASE
        )
        if error_match:
            update.error_message = (
                error_match.group(2).strip() or line_stripped
            )

        if not update.progress_percent and not update.is_complete:
            update.status_text = line_stripped

        return update

    def reset(self) -> None:
        self._code_found = False
        self._line_count = 0
        self._last_url = None


def validate_session_code(code: str) -> bool:
    """
    التحقق من صحة تنسيق كود الجلسة
    التنسيق: word-word-word
    """
    return bool(re.match(r'^[a-z]+-[a-z]+-[a-z]+$', code.strip().lower()))