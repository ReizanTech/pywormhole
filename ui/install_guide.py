import tkinter as tk
from tkinter import ttk
import sys
import webbrowser
from typing import Callable


class InstallGuideWindow(tk.Toplevel):
    """
    نافذة إعداد WebWormhole — تدعم وضعين:

    ┌─────────────────────────────────────────────┐
    │  🪱 إعداد WebWormhole                       │
    ├─────────────────────────────────────────────┤
    │  ❌ لم يتم العثور على ww                    │
    │                                             │
    │  ┌─ ⭐ Embedded Mode (موصى به) ───────────┐ │
    │  │  ✅ لا يحتاج Go                        │ │
    │  │  ✅ تحميل تلقائي                       │ │
    │  │  [ ⬇️ تحميل ww.exe تلقائياً ]         │ │
    │  │  ████████░░ 75%  (شريط التحميل)        │ │
    │  └────────────────────────────────────────┘ │
    │                                             │
    │  ┌─ 🛠️ CLI Mode (للمطورين) ──────────────┐ │
    │  │  ① https://go.dev/dl/    [📋] [🌐]    │ │
    │  │  ② go install ww@latest  [📋]          │ │
    │  │  ③ ww --version          [📋]          │ │
    │  └────────────────────────────────────────┘ │
    ├─────────────────────────────────────────────┤
    │  🔗 webwormhole.io  [🔄 تحقق] [✕ إغلاق]  │
    └─────────────────────────────────────────────┘
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_recheck: Callable | None = None,
    ):
        super().__init__(parent)
        self.on_recheck = on_recheck

        self.title("إعداد WebWormhole")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.transient(parent)

        self._center(560, 600)
        self._build_ui()

    # ─────────────────────────────────────────────────────
    # توسيط النافذة
    # ─────────────────────────────────────────────────────
    def _center(self, w: int, h: int) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw // 2) - (w // 2)
        y  = (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ─────────────────────────────────────────────────────
    # بناء الواجهة الكاملة
    # ─────────────────────────────────────────────────────
    def _build_ui(self) -> None:

        # ── العنوان ──────────────────────────────────────
        ttk.Label(
            self,
            text="🪱  إعداد WebWormhole",
            font=("Helvetica", 14, "bold"),
            padding=(20, 15, 20, 5),
        ).pack()

        # ── رسالة الخطأ ──────────────────────────────────
        err_frame = tk.Frame(self, bg="#FEE2E2", padx=15, pady=10)
        err_frame.pack(fill="x", padx=20, pady=(0, 5))

        tk.Label(
            err_frame,
            text="❌  لم يتم العثور على ww في النظام",
            bg="#FEE2E2",
            fg="#991B1B",
            font=("Helvetica", 10, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            err_frame,
            text="اختر إحدى الطريقتين أدناه للتثبيت:",
            bg="#FEE2E2",
            fg="#7F1D1D",
            font=("Helvetica", 9),
            anchor="w",
        ).pack(fill="x")

        ttk.Separator(self, orient="horizontal").pack(
            fill="x", padx=20, pady=8
        )

        # ── Scrollable Area ───────────────────────────────
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=20)

        scrollbar = ttk.Scrollbar(outer, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self._canvas = tk.Canvas(
            outer,
            yscrollcommand=scrollbar.set,
            highlightthickness=0,
        )
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._canvas.yview)

        content = ttk.Frame(self._canvas)
        win_id  = self._canvas.create_window(
            (0, 0), window=content, anchor="nw"
        )

        content.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            ),
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(win_id, width=e.width),
        )

        # ── بناء الخيارين ──
        self._build_embedded_section(content)
        ttk.Separator(content, orient="horizontal").pack(
            fill="x", pady=10
        )
        self._build_cli_section(content)

        # ── Footer ────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(
            fill="x", padx=20, pady=(8, 0)
        )
        self._build_footer()

    # ─────────────────────────────────────────────────────
    # القسم 1: Embedded Mode
    # ─────────────────────────────────────────────────────
    def _build_embedded_section(self, parent: ttk.Frame) -> None:

        frame = ttk.LabelFrame(
            parent,
            text="  ⭐  Embedded Mode  —  موصى به للمستخدم العادي  ",
            padding=12,
        )
        frame.pack(fill="x", pady=(0, 5))

        # وصف المميزات
        features = [
            ("✅", "لا يحتاج تثبيت Go"),
            ("✅", "يعمل فوراً بعد التحميل"),
            ("✅", "أسهل وأسرع إعداد"),
            ("⚠️", "حجم إضافي صغير (~10 MB)"),
        ]
        for icon, text in features:
            row = tk.Frame(frame)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=icon, font=("Helvetica", 9),
                     width=3).pack(side="left")
            tk.Label(row, text=text, font=("Helvetica", 9),
                     fg="#374151", anchor="w").pack(side="left")

        # شريط التقدم
        self._dl_progress = tk.DoubleVar(value=0)
        self._dl_status   = tk.StringVar(value="")

        self._dl_bar = ttk.Progressbar(
            frame,
            variable=self._dl_progress,
            maximum=100,
            mode="indeterminate",
        )
        self._dl_bar.pack(fill="x", pady=(10, 2))

        ttk.Label(
            frame,
            textvariable=self._dl_status,
            font=("Helvetica", 8),
            foreground="gray",
        ).pack()

        # زر التحميل
        self._dl_btn = ttk.Button(
            frame,
            text="⬇️  تحميل ww.exe تلقائياً",
            command=self._start_download,
            width=32,
        )
        self._dl_btn.pack(pady=(10, 0), ipady=6)

    # ─────────────────────────────────────────────────────
    # القسم 2: CLI Mode
    # ─────────────────────────────────────────────────────
    def _build_cli_section(self, parent: ttk.Frame) -> None:

        frame = ttk.LabelFrame(
            parent,
            text="  🛠️  CLI Mode  —  للمطورين  ",
            padding=12,
        )
        frame.pack(fill="x", pady=(0, 5))

        # وصف
        features = [
            ("✅", "أحدث نسخة دائماً من المصدر"),
            ("✅", "مناسب للمطورين"),
            ("❌", "يحتاج تثبيت Go أولاً"),
            ("❌", "يحتاج إعداد PATH"),
        ]
        for icon, text in features:
            row = tk.Frame(frame)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=icon, font=("Helvetica", 9),
                     width=3).pack(side="left")
            tk.Label(row, text=text, font=("Helvetica", 9),
                     fg="#374151", anchor="w").pack(side="left")

        ttk.Separator(frame, orient="horizontal").pack(
            fill="x", pady=8
        )

        # الخطوات
        steps = [
            {
                "label": "① ثبّت Go:",
                "value": "https://go.dev/dl/",
                "type":  "url",
            },
            {
                "label": "② ثبّت ww:",
                "value": "go install webwormhole.io/cmd/ww@latest",
                "type":  "cmd",
            },
            {
                "label": "③ تحقق من التثبيت:",
                "value": "ww --version",
                "type":  "cmd",
            },
        ]
        for step in steps:
            self._build_copyable_row(frame, step)

    # ─────────────────────────────────────────────────────
    # صف قابل للنسخ
    # ─────────────────────────────────────────────────────
    def _build_copyable_row(self, parent, item: dict) -> None:
        """
        ┌─ label ──────────────────────────────────┐
        │  ┌─────────────────────┐  [📋]  [🌐]    │
        │  │  value              │                 │
        │  └─────────────────────┘                 │
        └──────────────────────────────────────────┘
        """
        ttk.Label(
            parent,
            text=item["label"],
            font=("Helvetica", 9, "bold"),
            foreground="#374151",
        ).pack(anchor="w", pady=(6, 1))

        row = ttk.Frame(parent)
        row.pack(fill="x")

        # حقل النص
        var = tk.StringVar(value=item["value"])
        entry = tk.Entry(
            row,
            textvariable=var,
            font=("Courier", 9),
            fg="#1E40AF" if item["type"] == "url" else "#1F2937",
            readonlybackground=(
                "#EFF6FF" if item["type"] == "url" else "#F8FAFC"
            ),
            relief="solid",
            bd=1,
            state="readonly",
        )
        entry.pack(
            side="left", fill="x", expand=True,
            ipady=5, padx=(0, 5)
        )

        # زر النسخ
        ttk.Button(
            row,
            text="📋",
            width=3,
            command=lambda v=item["value"]: self._copy(v),
        ).pack(side="left", padx=(0, 3))

        # زر الفتح في المتصفح (للروابط فقط)
        if item["type"] == "url":
            ttk.Button(
                row,
                text="🌐",
                width=3,
                command=lambda v=item["value"]: webbrowser.open(v),
            ).pack(side="left")

    # ─────────────────────────────────────────────────────
    # Footer
    # ─────────────────────────────────────────────────────
    def _build_footer(self) -> None:
        footer = ttk.Frame(self, padding=(20, 10, 20, 15))
        footer.pack(fill="x")

        # رابط الموقع
        link = ttk.Label(
            footer,
            text="🔗 webwormhole.io",
            foreground="#2563EB",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        link.pack(side="left")
        link.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://webwormhole.io"),
        )

        # زر الإغلاق
        ttk.Button(
            footer,
            text="✕  إغلاق",
            command=self.destroy,
            width=12,
        ).pack(side="right", padx=(8, 0))

        # زر إعادة التحقق
        ttk.Button(
            footer,
            text="🔄  إعادة التحقق",
            command=self._recheck,
            width=16,
        ).pack(side="right")

    # ─────────────────────────────────────────────────────
    # منطق التحميل
    # ─────────────────────────────────────────────────────
    def _start_download(self) -> None:
        """بدء تحميل ww.exe في الخلفية"""
        self._dl_btn.config(
            state="disabled",
            text="⏳  جارٍ التحميل...",
        )
        self._dl_bar.config(mode="indeterminate")
        self._dl_bar.start(10)
        self._dl_status.set("جارٍ الاتصال...")

        try:
            # ← نستخدم الـ instance المشترك وليس instance جديد
            from controllers.ww_wrapper import get_runtime
            get_runtime().download_embedded(
                on_progress=self._on_dl_progress,
                on_complete=self._on_dl_complete,
                on_error=self._on_dl_error,
            )
        except Exception as e:
            self._on_dl_error(str(e))

    def _on_dl_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            percent  = downloaded / total * 100
            dl_mb    = downloaded / 1024 / 1024
            total_mb = total      / 1024 / 1024
        else:
            percent  = 0
            dl_mb    = downloaded / 1024 / 1024
            total_mb = 0

        def _update():
            self._dl_bar.stop()
            self._dl_bar.config(mode="determinate")
            self._dl_progress.set(percent)
            if total_mb > 0:
                self._dl_status.set(
                    f"{dl_mb:.1f} MB / {total_mb:.1f} MB"
                    f"  ({percent:.0f}%)"
                )
            else:
                self._dl_status.set(f"{dl_mb:.1f} MB مُحمَّل")

        self.after(0, _update)

    def _on_dl_complete(self, ww_path: str) -> None:
        self.after(0, lambda: self._show_dl_success(ww_path))

    def _show_dl_success(self, ww_path: str) -> None:
        """بعد اكتمال التحميل — عرض خيار التسجيل في PATH"""
        self._dl_bar.stop()
        self._dl_progress.set(100)
        self._dl_status.set(f"✅ تم الحفظ في: {ww_path}")
        self._dl_btn.config(
            text="✅  تم التحميل بنجاح!",
            state="disabled",
        )

        # ── زر تسجيل في PATH ──────────────────────────────
        self._register_btn = ttk.Button(
            self._dl_btn.master,
            text="🌐  تسجيل في PATH (اختياري)",
            command=self._register_path,
            width=32,
        )
        self._register_btn.pack(pady=(5, 0), ipady=4)

        ttk.Label(
            self._dl_btn.master,
            text="يتيح لك استخدام ww من أي Terminal",
            font=("Helvetica", 8),
            foreground="gray",
        ).pack()

        self._show_toast("✅ تم تحميل ww.exe بنجاح!")

        # ── زر "تم — ابدأ الاستخدام" ─────────────────────
        ttk.Button(
            self._dl_btn.master,
            text="🚀  تم — ابدأ الاستخدام",
            command=self._recheck,
            width=32,
        ).pack(pady=(10, 0), ipady=6)

    def _on_dl_error(self, message: str) -> None:
        self.after(0, lambda: self._show_dl_error(message))

    def _show_dl_error(self, message: str) -> None:
        self._dl_bar.stop()
        self._dl_progress.set(0)
        self._dl_status.set(f"❌ {message}")
        self._dl_btn.config(
            state="normal",
            text="🔁  إعادة المحاولة",
        )

    def _register_path(self) -> None:
        """تسجيل runtime/ في PATH النظام"""
        try:
            from controllers.ww_wrapper import get_runtime
            rt = get_runtime()   # ← الـ instance المشترك

            success, message = rt.register_global_path()

            if success:
                self._show_toast("✅ تم التسجيل في PATH!")
                self._register_btn.config(
                    state="disabled",
                    text="✅  مسجّل في PATH",
                )
                # إظهار رسالة تفصيلية تشرح الخطوة التالية
                import tkinter.messagebox as mb
                mb.showinfo(
                    "تم التسجيل ✓",
                    f"{message}\n\nيمكنك الآن استخدام:\n  ww --version\nمن أي PowerShell جديد."
                )
            else:
                self._show_toast(f"❌ {message}")

        except Exception as e:
            self._show_toast(f"❌ {e}")

    # ─────────────────────────────────────────────────────
    # إعادة التحقق
    # ─────────────────────────────────────────────────────
    def _recheck(self) -> None:
        """إعادة البحث عن ww — يستخدم الـ instance المشترك دائماً"""
        try:
            from controllers.ww_wrapper import get_runtime
            from utils.runtime_manager import RuntimeMode

            rt   = get_runtime()
            mode = rt.recheck()   # ← يحدّث نفس الـ instance المشترك

            if mode != RuntimeMode.NOT_FOUND:
                self._show_toast(
                    f"✅ تم العثور على ww! ({rt.mode_label})"
                )

                def _close_and_update():
                    if self.on_recheck:
                        self.on_recheck()
                    self.destroy()

                self.after(2000, _close_and_update)
            else:
                self._show_toast("❌ لم يتم العثور على ww بعد")

        except Exception as e:
            self._show_toast(f"❌ خطأ: {e}")

    # ─────────────────────────────────────────────────────
    # أدوات مساعدة
    # ─────────────────────────────────────────────────────
    def _copy(self, text: str) -> None:
        """نسخ نص إلى الحافظة"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self._show_toast("📋  تم النسخ!")

    def _show_toast(self, message: str, ms: int = 2000) -> None:
        """
        إشعار مؤقت يظهر أسفل النافذة ويختفي تلقائياً
        """
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        self.update_idletasks()
        tw = 240
        th = 38
        x  = self.winfo_x() + (self.winfo_width()  // 2) - (tw // 2)
        y  = self.winfo_y() +  self.winfo_height()  - 55
        toast.geometry(f"{tw}x{th}+{x}+{y}")

        tk.Label(
            toast,
            text=message,
            bg="#1F2937",
            fg="white",
            font=("Helvetica", 10),
            padx=15,
            pady=8,
        ).pack(fill="both", expand=True)

        toast.after(ms, toast.destroy)