import tkinter as tk
from tkinter import ttk
import sys
import webbrowser


class InstallGuideWindow(tk.Toplevel):
    """
    نافذة دليل التثبيت الاحترافية

    ┌─────────────────────────────────────────┐
    │  🪱 تثبيت WebWormhole CLI              │
    ├─────────────────────────────────────────┤
    │  ❌ لم يتم العثور على ww               │
    │                                         │
    │  ┌─ الخطوة 1 ───────────────────────┐  │
    │  │  ثبّت Go                         │  │
    │  │  ┌───────────────────────────┐   │  │
    │  │  │ https://golang.org/dl/    │[نسخ]│ │
    │  │  └───────────────────────────┘   │  │
    │  │              [🌐 فتح في المتصفح] │  │
    │  └──────────────────────────────────┘  │
    │                                         │
    │  ┌─ الخطوة 2 ───────────────────────┐  │
    │  │  شغّل هذا الأمر:               │  │
    │  │  ┌───────────────────────────┐   │  │
    │  │  │ go install webwormhole... │[نسخ]│ │
    │  │  └───────────────────────────┘   │  │
    │  └──────────────────────────────────┘  │
    │                                         │
    │  ┌─ الخطوة 3 ───────────────────────┐  │
    │  │  أضف إلى PATH:                  │  │
    │  │  ┌───────────────────────────┐   │  │
    │  │  │ %GOPATH%\bin              │[نسخ]│ │
    │  │  └───────────────────────────┘   │  │
    │  └──────────────────────────────────┘  │
    ├─────────────────────────────────────────┤
    │  [🔄 إعادة التحقق]        [✕ إغلاق]  │
    └─────────────────────────────────────────┘
    """

    def __init__(self, parent: tk.Widget, on_recheck: callable = None):
        super().__init__(parent)
        self.on_recheck = on_recheck

        self.title("تثبيت WebWormhole CLI")
        self.resizable(False, False)
        self.grab_set()  # نافذة Modal
        self.focus_set()

        # توسيط النافذة
        self.geometry("520x600")
        self._center_window()

        self._build_ui()

    def _center_window(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - 260
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"520x600+{x}+{y}")

    # ─────────────────────────────────────────────────────
    # بناء الواجهة
    # ─────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # ── Header ──
        header = ttk.Frame(self, padding=(20, 15, 20, 10))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="🪱 تثبيت WebWormhole CLI",
            font=("Helvetica", 14, "bold"),
        ).pack()

        # رسالة الخطأ
        error_frame = ttk.Frame(self, padding=(20, 0))
        error_frame.pack(fill="x")

        error_bg = tk.Frame(error_frame, bg="#FEE2E2", padx=10, pady=8)
        error_bg.pack(fill="x")

        tk.Label(
            error_bg,
            text="❌  لم يتم العثور على (ww) في النظام",
            bg="#FEE2E2",
            fg="#991B1B",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w")

        tk.Label(
            error_bg,
            text="اتبع الخطوات التالية لتثبيته:",
            bg="#FEE2E2",
            fg="#7F1D1D",
            font=("Helvetica", 9),
        ).pack(anchor="w")

        ttk.Separator(self, orient="horizontal").pack(
            fill="x", padx=20, pady=10
        )

        # ── Scrollable Steps ──
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=20)

        scrollbar = ttk.Scrollbar(outer, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(
            outer,
            yscrollcommand=scrollbar.set,
            highlightthickness=0,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        content = ttk.Frame(canvas)
        win = canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width)
        )

        # بناء خطوات التثبيت
        self._build_steps(content)

        # ── Footer ──
        ttk.Separator(self, orient="horizontal").pack(
            fill="x", padx=20, pady=(10, 0)
        )

        footer = ttk.Frame(self, padding=(20, 10, 20, 15))
        footer.pack(fill="x")

        self._build_footer(footer)

    def _build_steps(self, parent: ttk.Frame) -> None:
        """بناء خطوات التثبيت حسب نظام التشغيل"""
        steps = self._get_steps()

        for i, step in enumerate(steps, 1):
            self._build_step_card(parent, i, step)

    def _build_step_card(
        self,
        parent: ttk.Frame,
        number: int,
        step: dict,
    ) -> None:
        """
        بناء كارد خطوة واحدة

        step = {
            "title": "ثبّت Go",
            "description": "...",
            "items": [
                {"label": "الرابط:", "value": "https://...", "type": "url"},
                {"label": "الأمر:", "value": "go install ...", "type": "cmd"},
            ]
        }
        """
        # ── إطار الخطوة ──
        card = ttk.LabelFrame(
            parent,
            text=f"  الخطوة {number}: {step['title']}  ",
            padding=10,
        )
        card.pack(fill="x", pady=(0, 10))

        # الوصف
        if step.get("description"):
            ttk.Label(
                card,
                text=step["description"],
                font=("Helvetica", 9),
                foreground="#555",
                wraplength=420,
            ).pack(anchor="w", pady=(0, 8))

        # العناصر القابلة للنسخ
        for item in step.get("items", []):
            self._build_copyable_item(card, item)

    def _build_copyable_item(
        self,
        parent: ttk.Frame,
        item: dict,
    ) -> None:
        """
        عنصر قابل للنسخ مع زر

        ┌─ label ───────────────────────────────┐
        │ ┌─────────────────────────┐  [📋 نسخ] │
        │ │  value                  │  [🌐 فتح] │
        │ └─────────────────────────┘           │
        └────────────────────────────────────────┘
        """
        # Label
        if item.get("label"):
            ttk.Label(
                parent,
                text=item["label"],
                font=("Helvetica", 9, "bold"),
                foreground="#374151",
            ).pack(anchor="w")

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(2, 8))

        # حقل النص (readonly + قابل للتحديد)
        entry_var = tk.StringVar(value=item["value"])

        style = "Cmd.TEntry" if item.get("type") == "cmd" else "TEntry"

        entry = tk.Entry(
            row,
            textvariable=entry_var,
            font=(
                "Courier" if item.get("type") in ("cmd", "path") else "Helvetica",
                10
            ),
            fg="#1E40AF" if item.get("type") == "url" else "#1F2937",
            bg="#F8FAFC" if item.get("type") == "cmd" else "#FFFFFF",
            relief="solid",
            bd=1,
            state="readonly",
            readonlybackground=(
                "#F1F5F9" if item.get("type") == "cmd" else "#F8FAFC"
            ),
        )
        entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))

        # أزرار
        btn_frame = ttk.Frame(row)
        btn_frame.pack(side="left")

        # زر النسخ
        def copy_value(v=item["value"]):
            self.clipboard_clear()
            self.clipboard_append(v)
            self._show_toast(f"✅ تم النسخ!")

        ttk.Button(
            btn_frame,
            text="📋",
            command=copy_value,
            width=3,
        ).pack(side="left", padx=(0, 3))

        # زر الفتح (للروابط فقط)
        if item.get("type") == "url":
            def open_url(v=item["value"]):
                webbrowser.open(v)

            ttk.Button(
                btn_frame,
                text="🌐",
                command=open_url,
                width=3,
            ).pack(side="left")

    def _build_footer(self, parent: ttk.Frame) -> None:
        """أزرار أسفل النافذة"""

        ttk.Button(
            parent,
            text="✕  إغلاق",
            command=self.destroy,
            width=14,
        ).pack(side="right", padx=(8, 0))

        if self.on_recheck:
            ttk.Button(
                parent,
                text="🔄  إعادة التحقق",
                command=self._recheck,
                width=16,
            ).pack(side="right")

        # رابط المستودع
        link = ttk.Label(
            parent,
            text="🔗 webwormhole.io",
            foreground="#2563EB",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        link.pack(side="left")
        link.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://webwormhole.io")
        )

    # ─────────────────────────────────────────────────────
    # Toast إشعار مؤقت
    # ─────────────────────────────────────────────────────
    def _show_toast(self, message: str, duration: int = 1500) -> None:
        """إشعار مؤقت يظهر ويختفي"""
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)  # بدون إطار

        # توسيط فوق النافذة
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width()  // 2 - 80
        y = self.winfo_y() + self.winfo_height() - 60
        toast.geometry(f"180x35+{x}+{y}")

        tk.Label(
            toast,
            text=message,
            bg="#1F2937",
            fg="white",
            font=("Helvetica", 10),
            padx=15,
            pady=8,
        ).pack(fill="both", expand=True)

        # اختفاء تلقائي
        toast.after(duration, toast.destroy)

    # ─────────────────────────────────────────────────────
    # إعادة التحقق
    # ─────────────────────────────────────────────────────
    def _recheck(self) -> None:
        from utils.helpers import find_ww_executable

        ww = find_ww_executable()
        if ww:
            self._show_toast("✅ تم العثور على ww!")
            self.after(1000, self.destroy)
            if self.on_recheck:
                self.after(1100, self.on_recheck)
        else:
            self._show_toast("❌ لم يتم العثور على ww بعد")

    # ─────────────────────────────────────────────────────
    # بيانات الخطوات حسب النظام
    # ─────────────────────────────────────────────────────
    def _get_steps(self) -> list[dict]:
        if sys.platform == "win32":
            return self._steps_windows()
        elif sys.platform == "darwin":
            return self._steps_macos()
        else:
            return self._steps_linux()

    def _steps_windows(self) -> list[dict]:
        return [
            {
                "title": "ثبّت Go",
                "description": "WebWormhole مبني بلغة Go — يجب تثبيتها أولاً.",
                "items": [
                    {
                        "label": "رابط التثبيت:",
                        "value": "https://golang.org/dl/",
                        "type": "url",
                    },
                ],
            },
            {
                "title": "ثبّت ww عبر Go",
                "description": "افتح Command Prompt أو PowerShell وشغّل:",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "go install webwormhole.io/cmd/ww@latest",
                        "type": "cmd",
                    },
                ],
            },
            {
                "title": "أضف Go إلى PATH",
                "description": (
                    "تأكد من إضافة مجلد Go bin إلى متغير البيئة PATH\n"
                    "عادةً يكون المسار:"
                ),
                "items": [
                    {
                        "label": "المسار:",
                        "value": r"%GOPATH%\bin",
                        "type": "path",
                    },
                    {
                        "label": "أو المسار الافتراضي:",
                        "value": r"C:\Users\<اسمك>\go\bin",
                        "type": "path",
                    },
                ],
            },
            {
                "title": "تحقق من التثبيت",
                "description": "شغّل هذا الأمر للتأكد:",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "ww --version",
                        "type": "cmd",
                    },
                ],
            },
        ]

    def _steps_macos(self) -> list[dict]:
        return [
            {
                "title": "ثبّت Go (طريقة Homebrew)",
                "description": "الطريقة الأسهل على macOS:",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "brew install go",
                        "type": "cmd",
                    },
                ],
            },
            {
                "title": "ثبّت ww",
                "description": "بعد تثبيت Go:",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "go install webwormhole.io/cmd/ww@latest",
                        "type": "cmd",
                    },
                ],
            },
            {
                "title": "أضف Go إلى PATH",
                "description": "أضف هذا السطر لـ ~/.zshrc أو ~/.bashrc:",
                "items": [
                    {
                        "label": "السطر:",
                        "value": 'export PATH="$HOME/go/bin:$PATH"',
                        "type": "cmd",
                    },
                    {
                        "label": "ثم شغّل:",
                        "value": "source ~/.zshrc",
                        "type": "cmd",
                    },
                ],
            },
            {
                "title": "تحقق من التثبيت",
                "description": "",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "ww --version",
                        "type": "cmd",
                    },
                ],
            },
        ]

    def _steps_linux(self) -> list[dict]:
        return [
            {
                "title": "ثبّت Go",
                "description": "حسب التوزيعة:",
                "items": [
                    {
                        "label": "Ubuntu / Debian:",
                        "value": "sudo apt install golang-go",
                        "type": "cmd",
                    },
                    {
                        "label": "Fedora:",
                        "value": "sudo dnf install golang",
                        "type": "cmd",
                    },
                    {
                        "label": "أو من الموقع الرسمي:",
                        "value": "https://golang.org/dl/",
                        "type": "url",
                    },
                ],
            },
            {
                "title": "ثبّت ww",
                "description": "",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "go install webwormhole.io/cmd/ww@latest",
                        "type": "cmd",
                    },
                ],
            },
            {
                "title": "أضف Go إلى PATH",
                "description": "أضف لـ ~/.bashrc أو ~/.profile:",
                "items": [
                    {
                        "label": "السطر:",
                        "value": 'export PATH="$HOME/go/bin:$PATH"',
                        "type": "cmd",
                    },
                    {
                        "label": "ثم شغّل:",
                        "value": "source ~/.bashrc",
                        "type": "cmd",
                    },
                ],
            },
            {
                "title": "تحقق من التثبيت",
                "description": "",
                "items": [
                    {
                        "label": "الأمر:",
                        "value": "ww --version",
                        "type": "cmd",
                    },
                ],
            },
        ]