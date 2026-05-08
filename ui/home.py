import tkinter as tk
from tkinter import ttk
from typing import Callable


class HomeScreen(ttk.Frame):
    """
    الشاشة الرئيسية

    ┌─────────────────────────────┐
    │  🪱 PyWormhole              │
    │  نقل ملفات آمن P2P         │
    │                             │
    │  ✅ ww: جاهز — CLI Mode    │
    │                             │
    │  [ 📤 إرسال ملف ]          │
    │  [ 📥 استقبال ملف ]        │
    │                             │
    │  ⚙️ إعداد WebWormhole CLI  │
    └─────────────────────────────┘
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_send: Callable,
        on_receive: Callable,
    ):
        super().__init__(parent, padding=30)
        self.on_send    = on_send
        self.on_receive = on_receive
        self._build_ui()
        self._refresh_status()

    # ─────────────────────────────────────────────────────
    # بناء الواجهة
    # ─────────────────────────────────────────────────────
    def _build_ui(self) -> None:

        # ── الشعار ──
        ttk.Label(
            self,
            text="🪱",
            font=("Helvetica", 48),
        ).pack(pady=(0, 5))

        ttk.Label(
            self,
            text="PyWormhole",
            font=("Helvetica", 22, "bold"),
        ).pack()

        ttk.Label(
            self,
            text="نقل ملفات آمن ومباشر بين الأجهزة",
            font=("Helvetica", 11),
            foreground="gray",
        ).pack(pady=(3, 20))

        # ── كارد حالة ww ──
        status_card = tk.Frame(
            self,
            bg="#F1F5F9",
            padx=12,
            pady=10,
            relief="flat",
        )
        status_card.pack(fill="x", pady=(0, 15))

        # أيقونة الحالة
        self._status_icon_var = tk.StringVar(value="⏳")
        tk.Label(
            status_card,
            textvariable=self._status_icon_var,
            bg="#F1F5F9",
            font=("Helvetica", 14),
        ).pack(side="left", padx=(0, 8))

        # نص الحالة
        info = tk.Frame(status_card, bg="#F1F5F9")
        info.pack(side="left", fill="x", expand=True)

        self._status_main_var = tk.StringVar(value="جارٍ التحقق...")
        self._status_main_lbl = tk.Label(
            info,
            textvariable=self._status_main_var,
            bg="#F1F5F9",
            font=("Helvetica", 10, "bold"),
            anchor="w",
        )
        self._status_main_lbl.pack(fill="x")

        self._status_sub_var = tk.StringVar(value="")
        tk.Label(
            info,
            textvariable=self._status_sub_var,
            bg="#F1F5F9",
            font=("Helvetica", 8),
            fg="gray",
            anchor="w",
        ).pack(fill="x")

        ttk.Separator(self, orient="horizontal").pack(
            fill="x", pady=5
        )

        # ── أزرار الإرسال والاستقبال ──
        self.btn_send = ttk.Button(
            self,
            text="📤  إرسال ملف",
            command=self.on_send,
            width=22,
        )
        self.btn_send.pack(pady=8, ipady=12)

        self.btn_receive = ttk.Button(
            self,
            text="📥  استقبال ملف",
            command=self.on_receive,
            width=22,
        )
        self.btn_receive.pack(pady=8, ipady=12)

        ttk.Separator(self, orient="horizontal").pack(
            fill="x", pady=15
        )

        # ── رابط الإعداد ──
        setup_lbl = ttk.Label(
            self,
            text="⚙️  إعداد WebWormhole CLI",
            foreground="#2563EB",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        setup_lbl.pack()
        setup_lbl.bind("<Button-1>", self._show_install_guide)

        ttk.Label(
            self,
            text="v1.0 — Powered by WebWormhole",
            font=("Helvetica", 8),
            foreground="gray",
        ).pack(pady=(10, 0))

    # ─────────────────────────────────────────────────────
    # تحديث حالة ww
    # ─────────────────────────────────────────────────────
    def _refresh_status(self) -> None:
        """
        قراءة وضع التشغيل وتحديث الواجهة

        RuntimeMode.CLI_GLOBAL → ✅ أخضر
        RuntimeMode.EMBEDDED   → ✅ أخضر
        RuntimeMode.NOT_FOUND  → ❌ أحمر
        """
        try:
            from controllers.ww_wrapper import get_runtime
            from utils.runtime_manager import RuntimeMode

            rt   = get_runtime()
            mode = rt.mode

        except Exception:
            # لو فيه خطأ في الاستيراد
            self._status_icon_var.set("⚠️")
            self._status_main_var.set("خطأ في تحميل RuntimeManager")
            self._status_main_lbl.config(fg="#92400E")
            return

        if mode == RuntimeMode.CLI_GLOBAL:
            self._status_icon_var.set("✅")
            self._status_main_var.set("ww جاهز")
            self._status_sub_var.set(f"CLI Mode — {rt.ww_path}")
            self._status_main_lbl.config(fg="#166534")
            self._set_buttons("normal")

        elif mode == RuntimeMode.EMBEDDED:
            self._status_icon_var.set("✅")
            self._status_main_var.set("ww جاهز")
            self._status_sub_var.set(f"Embedded Mode — {rt.ww_path}")
            self._status_main_lbl.config(fg="#166534")
            self._set_buttons("normal")

        else:  # NOT_FOUND
            self._status_icon_var.set("❌")
            self._status_main_var.set("ww غير موجود — انقر للإعداد")
            self._status_sub_var.set("اضغط على الرابط أدناه للتثبيت")
            self._status_main_lbl.config(fg="#991B1B")
            self._set_buttons("disabled")

    def _set_buttons(self, state: str) -> None:
        """تفعيل أو تعطيل أزرار الإرسال والاستقبال"""
        self.btn_send.config(state=state)
        self.btn_receive.config(state=state)

    # ─────────────────────────────────────────────────────
    # نافذة الإعداد
    # ─────────────────────────────────────────────────────
    def _show_install_guide(self, event=None) -> None:
        """فتح نافذة دليل التثبيت"""
        from ui.install_guide import InstallGuideWindow

        InstallGuideWindow(
            self,
            on_recheck=self._refresh_status,
        )