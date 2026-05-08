import tkinter as tk
from tkinter import ttk
from typing import Callable

from utils.helpers import find_ww_executable


class HomeScreen(ttk.Frame):
    """
    الشاشة الرئيسية

    ┌─────────────────────────────┐
    │  🪱 PyWormhole              │
    │  نقل ملفات آمن P2P         │
    │                             │
    │  ✅ ww: متصل                │
    │                             │
    │  [ 📤 إرسال ملف ]          │
    │  [ 📥 استقبال ملف ]        │
    │                             │
    │  v1.0 | webwormhole.io     │
    └─────────────────────────────┘
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_send: Callable,
        on_receive: Callable,
    ):
        super().__init__(parent, padding=30)
        self.on_send = on_send
        self.on_receive = on_receive
        self._build_ui()
        self._check_ww()

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

        # ── حالة ww ──
        self.ww_status_var = tk.StringVar(value="⏳ جارٍ التحقق...")
        self.ww_status_label = ttk.Label(
            self,
            textvariable=self.ww_status_var,
            font=("Helvetica", 10),
        )
        self.ww_status_label.pack(pady=(0, 20))

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        # ── الأزرار ──
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

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=15)

        # ── رابط التثبيت ──
        install_label = ttk.Label(
            self,
            text="كيفية تثبيت ww CLI ؟",
            foreground="#2563EB",
            cursor="hand2",
            font=("Helvetica", 9, "underline"),
        )
        install_label.pack()
        install_label.bind("<Button-1>", self._show_install_guide)

        ttk.Label(
            self,
            text="v1.0 — Powered by WebWormhole",
            font=("Helvetica", 8),
            foreground="gray",
        ).pack(pady=(10, 0))

    def _check_ww(self) -> None:
        """التحقق من وجود ww وتحديث الحالة"""
        ww_path = find_ww_executable()

        if ww_path:
            self.ww_status_var.set(f"✅ ww: جاهز  ({ww_path})")
            self.ww_status_label.config(foreground="green")
            self.btn_send.config(state="normal")
            self.btn_receive.config(state="normal")
        else:
            self.ww_status_var.set("❌ ww: غير مثبت — انقر للمساعدة")
            self.ww_status_label.config(foreground="red")
            self.btn_send.config(state="disabled")
            self.btn_receive.config(state="disabled")
            self.ww_status_label.bind(
                "<Button-1>", self._show_install_guide
            )

    def _show_install_guide(self, event=None) -> None:
        """فتح نافذة دليل التثبيت"""
        from ui.install_guide import InstallGuideWindow

        InstallGuideWindow(
            self,
            on_recheck=self._recheck_ww,
        )

    def _recheck_ww(self) -> None:
        """إعادة التحقق من ww بعد التثبيت"""
        ww_path = find_ww_executable()
        if ww_path:
            self.ww_status_var.set(f"✅ ww: جاهز  ({ww_path})")
            self.ww_status_label.config(foreground="green")
            self.btn_send.config(state="normal")
            self.btn_receive.config(state="normal")
        else:
            self.ww_status_var.set("❌ ww: غير مثبت — انقر للمساعدة")
            self.ww_status_label.config(foreground="red")