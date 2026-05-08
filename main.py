import tkinter as tk
from tkinter import ttk

# ── الـ import يُشغّل detect() تلقائياً (السطر 11-12 في ww_wrapper.py) ──
from controllers.ww_wrapper import get_runtime

# ── الشاشات ──
from ui.home          import HomeScreen
from ui.sender        import SenderScreen
from ui.receiver      import ReceiverScreen
from ui.install_guide import InstallGuideWindow
from utils.runtime_manager import RuntimeMode


class PyWormholeApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("PyWormhole")
        self.geometry("520x620")
        self.resizable(False, False)
        self._apply_style()

        self._current: ttk.Frame | None = None

        # ── إذا لم يُعثر على ww، نفتح دليل التثبيت فوراً ──
        if get_runtime().mode == RuntimeMode.NOT_FOUND:
            self.show_home()
            self.after(200, self._show_install_on_startup)
        else:
            self.show_home()

    def _show_install_on_startup(self) -> None:
        InstallGuideWindow(self, on_recheck=self._on_install_recheck)

    def _on_install_recheck(self) -> None:
        """بعد التثبيت: تحديث الشاشة الرئيسية"""
        if isinstance(self._current, HomeScreen):
            self._current._refresh_status()

    def show_home(self) -> None:
        self._switch(
            HomeScreen(
                self,
                on_send=self.show_sender,
                on_receive=self.show_receiver,
            )
        )

    def show_sender(self) -> None:
        self._switch(SenderScreen(self, on_back=self.show_home))

    def show_receiver(self) -> None:
        self._switch(ReceiverScreen(self, on_back=self.show_home))

    def _switch(self, frame: ttk.Frame) -> None:
        if self._current:
            self._current.destroy()
        self._current = frame
        frame.pack(fill="both", expand=True)

    def _apply_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton",    padding=6, font=("Helvetica", 11))
        style.configure("TLabel",     font=("Helvetica", 11))
        style.configure("TLabelframe.Label", font=("Helvetica", 10, "bold"))


if __name__ == "__main__":
    app = PyWormholeApp()
    app.mainloop()