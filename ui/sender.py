import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Callable

from controllers.send_controller import SendController
from utils.qr import generate_qr_image
from utils.helpers import format_file_size


class SenderScreen(ttk.Frame):
    """
    شاشة الإرسال مع Layout ثابت للأزرار

    ┌─────────────────────────────┐
    │  📤 إرسال ملف              │
    ├─────────────────────────────┤
    │  ┌─ Scrollable Frame ─────┐ │
    │  │  معلومات الملف        │ │
    │  │  كود الجلسة           │ │
    │  │  QR Code              │ │
    │  │  URL                  │ │
    │  │  شريط التقدم          │ │
    │  └───────────────────────┘ │
    ├─────────────────────────────┤
    │  [✕ إلغاء]     [✓ تم]     │  ← ثابت دائماً
    └─────────────────────────────┘
    """

    def __init__(self, parent: tk.Widget, on_back: Callable):
        super().__init__(parent)
        self.on_back = on_back
        self._controller = SendController()
        self._qr_image = None
        self._transfer_done = False

        self._build_layout()
        self._pick_and_send()

    # ─────────────────────────────────────────────────────
    # المرحلة 1: بناء الهيكل الأساسي (Layout)
    # ─────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        """
        تقسيم الشاشة لثلاث مناطق:

        ┌──────────────┐  ← header_frame  (ثابت - أعلى)
        ├──────────────┤
        │              │  ← scroll_area   (متمدد - وسط)
        ├──────────────┤
        └──────────────┘  ← footer_frame  (ثابت - أسفل)
        """

        # ── Header: العنوان ──────────────────────────────
        header_frame = ttk.Frame(self, padding=(20, 15, 20, 5))
        header_frame.pack(side="top", fill="x")

        ttk.Label(
            header_frame,
            text="📤 إرسال ملف",
            font=("Helvetica", 16, "bold"),
        ).pack()

        ttk.Separator(self, orient="horizontal").pack(
            side="top", fill="x", padx=20
        )

        # ── Footer: الأزرار ──────────────────────────────
        # نبنيه قبل المحتوى عشان يكون في الأسفل دائماً
        footer_frame = ttk.Frame(self, padding=(20, 10, 20, 15))
        footer_frame.pack(side="bottom", fill="x")

        ttk.Separator(self, orient="horizontal").pack(
            side="bottom", fill="x", padx=20
        )

        self._build_footer(footer_frame)

        # ── Scrollable Content Area ───────────────────────
        self._build_scroll_area()

    def _build_footer(self, parent: ttk.Frame) -> None:
        """أزرار التحكم — ثابتة في أسفل الشاشة دائماً"""

        # معلومات إضافية في اليسار
        self.footer_status_var = tk.StringVar(value="")
        ttk.Label(
            parent,
            textvariable=self.footer_status_var,
            font=("Helvetica", 9),
            foreground="gray",
        ).pack(side="left")

        # الأزرار في اليمين
        btn_container = ttk.Frame(parent)
        btn_container.pack(side="right")

        self.cancel_btn = ttk.Button(
            btn_container,
            text="✕ إلغاء",
            command=self._cancel,
            width=12,
        )
        self.cancel_btn.pack(side="left", padx=(0, 8))

        self.done_btn = ttk.Button(
            btn_container,
            text="✓ تم",
            command=self._on_done,
            width=12,
            state="disabled",
        )
        self.done_btn.pack(side="left")

    def _build_scroll_area(self) -> None:
        """
        منطقة المحتوى القابلة للتمرير

        Canvas + Scrollbar → Frame داخلي للمحتوى
        """
        # ── الإطار الخارجي للـ Canvas ──
        outer = ttk.Frame(self)
        outer.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        # ── Scrollbar ──
        scrollbar = ttk.Scrollbar(outer, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # ── Canvas ──
        self._canvas = tk.Canvas(
            outer,
            yscrollcommand=scrollbar.set,
            highlightthickness=0,
            bg=self.winfo_toplevel().cget("bg"),
        )
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._canvas.yview)

        # ── Frame داخل الـ Canvas (هنا نحط المحتوى) ──
        self._content_frame = ttk.Frame(self._canvas, padding=(0, 5))
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._content_frame,
            anchor="nw",
        )

        # ── ربط أحداث التمدد ──
        self._content_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # ── Scroll بعجلة الماوس ──
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        # ── بناء المحتوى ──
        self._build_content(self._content_frame)

    # ─────────────────────────────────────────────────────
    # المرحلة 2: بناء المحتوى
    # ─────────────────────────────────────────────────────
    def _build_content(self, parent: ttk.Frame) -> None:
        """كل عناصر الشاشة داخل الـ Scrollable Frame"""

        # ── معلومات الملف ────────────────────────────────
        file_frame = ttk.LabelFrame(
            parent, text="الملف المختار", padding=8
        )
        file_frame.pack(fill="x", pady=(0, 8))

        self.file_info_var = tk.StringVar(value="⏳ جارٍ الاختيار...")
        ttk.Label(
            file_frame,
            textvariable=self.file_info_var,
            font=("Helvetica", 10),
            wraplength=420,
        ).pack()

        # ── كود الجلسة ───────────────────────────────────
        code_frame = ttk.LabelFrame(
            parent, text="كود الجلسة", padding=8
        )
        code_frame.pack(fill="x", pady=(0, 8))

        self.code_var = tk.StringVar(value="⏳ في انتظار ww...")
        ttk.Label(
            code_frame,
            textvariable=self.code_var,
            font=("Courier", 20, "bold"),
            foreground="#2563EB",
        ).pack(pady=(0, 6))

        self.copy_btn = ttk.Button(
            code_frame,
            text="📋 نسخ الكود",
            command=self._copy_code,
            state="disabled",
        )
        self.copy_btn.pack()

        # ── QR Code ──────────────────────────────────────
        qr_frame = ttk.LabelFrame(
            parent, text="QR Code", padding=8
        )
        qr_frame.pack(pady=(0, 8))

        self.qr_label = ttk.Label(
            qr_frame,
            text="⏳ سيظهر QR بعد الحصول على الكود...",
            foreground="gray",
            font=("Helvetica", 10),
        )
        self.qr_label.pack(padx=10, pady=5)

        # URL تحت الـ QR
        self.url_var = tk.StringVar(value="")
        self.url_label = ttk.Label(
            qr_frame,
            textvariable=self.url_var,
            font=("Courier", 8),
            foreground="#2563EB",
            wraplength=420,
            cursor="hand2",
        )
        self.url_label.pack(pady=(4, 0))
        self.url_label.bind("<Button-1>", self._copy_url)

        # ── شريط التقدم ──────────────────────────────────
        progress_frame = ttk.LabelFrame(
            parent, text="التقدم", padding=8
        )
        progress_frame.pack(fill="x", pady=(0, 5))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.pack(fill="x")

        self.status_var = tk.StringVar(value="في انتظار الاتصال...")
        ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            foreground="gray",
            wraplength=420,
        ).pack(pady=(5, 0))

    # ─────────────────────────────────────────────────────
    # أحداث الـ Canvas (للـ Scroll)
    # ─────────────────────────────────────────────────────
    def _on_frame_configure(self, event=None) -> None:
        """تحديث منطقة الـ scroll عند تغيير حجم المحتوى"""
        self._canvas.configure(
            scrollregion=self._canvas.bbox("all")
        )

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """تمديد الـ Frame الداخلي ليملأ عرض الـ Canvas"""
        self._canvas.itemconfig(
            self._canvas_window,
            width=event.width,
        )

    def _bind_mousewheel(self, event=None) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>",   self._on_mousewheel)
        self._canvas.bind_all("<Button-5>",   self._on_mousewheel)

    def _unbind_mousewheel(self, event=None) -> None:
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        """تمرير الـ scroll بعجلة الماوس"""
        if event.num == 4:       # Linux scroll up
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:     # Linux scroll down
            self._canvas.yview_scroll(1, "units")
        else:                    # Windows / macOS
            self._canvas.yview_scroll(
                int(-1 * (event.delta / 120)), "units"
            )

    # ─────────────────────────────────────────────────────
    # منطق الإرسال
    # ─────────────────────────────────────────────────────
    def _pick_and_send(self) -> None:
        """فتح نافذة اختيار الملف ثم بدء الإرسال"""
        filepath = filedialog.askopenfilename(
            title="اختر الملف للإرسال"
        )

        if not filepath:
            self.on_back()
            return

        path = Path(filepath)
        size = format_file_size(path.stat().st_size)
        self.file_info_var.set(f"📄 {path.name}   ({size})")

        self._controller.start_send(
            filepath=filepath,
            on_code_received=self._on_code_received,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    # ─────────────────────────────────────────────────────
    # Callbacks (تُستدعى من خيط الشبكة)
    # ─────────────────────────────────────────────────────
    def _on_code_received(self, code: str) -> None:
        self.after(0, lambda: self._show_code(code))

    def _show_code(self, code: str) -> None:
        """عرض الكود والـ QR بعد الحصول عليهما"""
        self.code_var.set(code)
        self.copy_btn.config(state="normal")
        self.status_var.set("✅ جاهز — شارك الكود أو الـ QR مع المستقبل")
        self.footer_status_var.set(f"الكود: {code}")

        # ── الـ URL الكامل (نفس ما يُنتجه ww) ──
        url = f"https://webwormhole.com#{code}"
        self.url_var.set(url)

        # ── توليد QR بالـ URL ──
        try:
            self._qr_image = generate_qr_image(url, box_size=5)
            self.qr_label.config(image=self._qr_image, text="")
        except Exception:
            self.qr_label.config(text="⚠️ تعذر توليد QR")

        # تمرير للأعلى لإظهار الكود
        self._canvas.yview_moveto(0)

    def _on_progress(self, percent: float, status: str) -> None:
        self.after(0, lambda: self._update_progress(percent, status))

    def _update_progress(self, percent: float, status: str) -> None:
        self.progress_var.set(min(percent, 100))
        if status:
            self.status_var.set(status)

    def _on_complete(self) -> None:
        self.after(0, self._show_complete)

    def _show_complete(self) -> None:
        """اكتمال الإرسال — تفعيل زر التم والعودة"""
        self._transfer_done = True
        self.progress_var.set(100)
        self.status_var.set("✅ تم الإرسال بنجاح!")
        self.footer_status_var.set("✅ اكتمل النقل")

        # ── تفعيل زر التم + تعطيل إلغاء ──
        self.done_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

        # تمرير للأسفل لإظهار شريط التقدم
        self._canvas.yview_moveto(1)

        messagebox.showinfo(
            "تم الإرسال ✓",
            "تم إرسال الملف بنجاح!\n\nاضغط 'تم' للعودة للشاشة الرئيسية."
        )

        # ── تفعيل زر التم تلقائياً بعد رسالة النجاح ──
        self.done_btn.config(state="normal")

    def _on_error(self, message: str) -> None:
        self.after(0, lambda: self._show_error(message))

    def _show_error(self, message: str) -> None:
        self.status_var.set(f"❌ {message}")
        self.footer_status_var.set("❌ فشل النقل")
        self.cancel_btn.config(text="← رجوع")
        messagebox.showerror("خطأ في الإرسال", message)

    # ─────────────────────────────────────────────────────
    # إجراءات المستخدم
    # ─────────────────────────────────────────────────────
    def _copy_code(self) -> None:
        code = self.code_var.get()
        if code and "انتظار" not in code:
            self.clipboard_clear()
            self.clipboard_append(code)
            messagebox.showinfo("تم النسخ ✓", f"تم نسخ الكود:\n{code}")

    def _copy_url(self, event=None) -> None:
        url = self.url_var.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            messagebox.showinfo("تم النسخ ✓", f"تم نسخ الرابط:\n{url}")

    def _on_done(self) -> None:
        """زر تم — العودة للشاشة الرئيسية"""
        self._controller.cancel()
        self.on_back()

    def _cancel(self) -> None:
        """زر إلغاء"""
        if self._transfer_done:
            self.on_back()
            return

        if messagebox.askyesno(
            "تأكيد الإلغاء",
            "هل تريد إلغاء عملية الإرسال والعودة للرئيسية؟"
        ):
            self._controller.cancel()
            self.on_back()