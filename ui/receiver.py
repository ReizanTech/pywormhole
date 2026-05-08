import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable

from controllers.receive_controller import ReceiveController
from utils.helpers import get_default_downloads_dir
from utils.parser import validate_session_code


class ReceiverScreen(ttk.Frame):
    """
    شاشة الاستقبال

    ┌────────────────────────────────┐
    │  📥 استقبال ملف               │
    ├────────────────────────────────┤
    │  أدخل كود الجلسة:            │
    │  ┌──────────────────────────┐  │
    │  │  east-pep-aloe           │  │
    │  └──────────────────────────┘  │
    │  ✅ تنسيق الكود صحيح         │
    ├────────────────────────────────┤
    │  مجلد الحفظ:                  │
    │  C:/Users/.../Downloads [...]  │
    ├────────────────────────────────┤
    │  التقدم:                      │
    │  ████████░░░ 75%              │
    │  Receiving file.zip...        │
    ├────────────────────────────────┤
    │  [إلغاء]      [⬇️ استقبال]   │
    └────────────────────────────────┘
    """

    def __init__(self, parent: tk.Widget, on_back: Callable):
        super().__init__(parent, padding=20)
        self.on_back = on_back
        self._controller = ReceiveController()
        self._transfer_done = False

        self._build_ui()

    # ─────────────────────────────────────────
    # بناء الواجهة
    # ─────────────────────────────────────────
    def _build_ui(self) -> None:
        # ── العنوان ──
        ttk.Label(
            self,
            text="📥 استقبال ملف",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=(0, 10))

        # ── إدخال الكود ──
        code_frame = ttk.LabelFrame(self, text="كود الجلسة", padding=8)
        code_frame.pack(fill="x", pady=5)

        ttk.Label(
            code_frame,
            text="أدخل الكود الذي شاركه المرسل:",
            font=("Helvetica", 10),
        ).pack(anchor="w")

        self.code_var = tk.StringVar()
        self.code_var.trace_add("write", self._validate_code_input)

        self.code_entry = ttk.Entry(
            code_frame,
            textvariable=self.code_var,
            font=("Courier", 15),
            width=28,
        )
        self.code_entry.pack(pady=5, ipady=6)
        self.code_entry.focus()

        # مؤشر صحة الكود
        self.code_valid_var = tk.StringVar(value="")
        self.code_valid_label = ttk.Label(
            code_frame,
            textvariable=self.code_valid_var,
            font=("Helvetica", 9),
        )
        self.code_valid_label.pack()

        # ── مجلد الحفظ ──
        dir_frame = ttk.LabelFrame(self, text="مجلد الحفظ", padding=8)
        dir_frame.pack(fill="x", pady=5)

        dir_row = ttk.Frame(dir_frame)
        dir_row.pack(fill="x")

        self.save_dir_var = tk.StringVar(
            value=get_default_downloads_dir()
        )
        ttk.Entry(
            dir_row,
            textvariable=self.save_dir_var,
            font=("Helvetica", 9),
            width=38,
            state="readonly",
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            dir_row,
            text="...",
            command=self._pick_directory,
            width=4,
        ).pack(side="left")

        # ── شريط التقدم ──
        progress_frame = ttk.LabelFrame(self, text="التقدم", padding=8)
        progress_frame.pack(fill="x", pady=5)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=420,
            mode="indeterminate",  # نبدأ بـ indeterminate حتى نعرف الحجم
        )
        self.progress_bar.pack(fill="x")

        self.status_var = tk.StringVar(value="في انتظار إدخال الكود...")
        ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            foreground="gray",
        ).pack(pady=(4, 0))

        # ── الأزرار ──
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        self.cancel_btn = ttk.Button(
            btn_frame,
            text="✕ إلغاء",
            command=self._cancel,
        )
        self.cancel_btn.pack(side="left", padx=5)

        self.receive_btn = ttk.Button(
            btn_frame,
            text="⬇️ استقبال",
            command=self._start_receive,
        )
        self.receive_btn.pack(side="left", padx=5)

    # ─────────────────────────────────────────
    # التحقق من الكود أثناء الكتابة
    # ─────────────────────────────────────────
    def _validate_code_input(self, *args) -> None:
        code = self.code_var.get().strip()

        if not code:
            self.code_valid_var.set("")
            return

        if validate_session_code(code):
            self.code_valid_var.set("✅ تنسيق الكود صحيح")
            self.code_valid_label.config(foreground="green")
        else:
            self.code_valid_var.set("❌ التنسيق: كلمة-كلمة-كلمة")
            self.code_valid_label.config(foreground="red")

    # ─────────────────────────────────────────
    # اختيار مجلد الحفظ
    # ─────────────────────────────────────────
    def _pick_directory(self) -> None:
        directory = filedialog.askdirectory(
            title="اختر مجلد الحفظ",
            initialdir=self.save_dir_var.get(),
        )
        if directory:
            self.save_dir_var.set(directory)

    # ─────────────────────────────────────────
    # بدء الاستقبال
    # ─────────────────────────────────────────
    def _start_receive(self) -> None:
        code = self.code_var.get().strip()
        save_dir = self.save_dir_var.get()

        if not validate_session_code(code):
            messagebox.showwarning(
                "كود غير صحيح",
                "يرجى إدخال كود صحيح بالتنسيق:\n"
                "كلمة-كلمة-كلمة\n\n"
                "مثال: tiger-moon-cloud"
            )
            return

        # ── تحديث الواجهة ──
        self.receive_btn.config(state="disabled")
        self.code_entry.config(state="disabled")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)
        self.status_var.set(f"⏳ جارٍ الاتصال للكود: {code}")

        # ── بدء الاستقبال ──
        self._controller.start_receive(
            code=code,
            save_dir=save_dir,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    # ─────────────────────────────────────────
    # Callbacks
    # ─────────────────────────────────────────
    def _on_progress(self, percent: float, status: str) -> None:
        self.after(0, lambda: self._update_progress(percent, status))

    def _update_progress(self, percent: float, status: str) -> None:
        # التبديل لـ determinate عند معرفة النسبة
        if self.progress_bar["mode"] == "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate")

        self.progress_var.set(min(percent, 100))
        if status:
            self.status_var.set(status)

    def _on_complete(self) -> None:
        self.after(0, self._show_complete)

    def _show_complete(self) -> None:
        self._transfer_done = True

        if self.progress_bar["mode"] == "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate")

        self.progress_var.set(100)
        save_dir = self.save_dir_var.get()
        self.status_var.set(f"✅ تم الحفظ في: {save_dir}")

        messagebox.showinfo(
            "تم الاستقبال! ✓",
            f"تم استلام الملف وحفظه في:\n{save_dir}"
        )
        self.on_back()

    def _on_error(self, message: str) -> None:
        self.after(0, lambda: self._show_error(message))

    def _show_error(self, message: str) -> None:
        if self.progress_bar["mode"] == "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate")

        self.status_var.set(f"❌ {message}")
        self.receive_btn.config(state="normal")
        self.code_entry.config(state="normal")
        messagebox.showerror("خطأ في الاستقبال", message)

    # ─────────────────────────────────────────
    def _cancel(self) -> None:
        if not self._transfer_done:
            self._controller.cancel()
        self.on_back()