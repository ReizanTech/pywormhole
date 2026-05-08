import tkinter as tk
from tkinter import ttk

from ui.home     import HomeScreen
from ui.sender   import SenderScreen
from ui.receiver import ReceiverScreen


class PyWormholeApp(tk.Tk):
    """
    تطبيق PyWormhole — GUI Wrapper لـ WebWormhole CLI

    التنقل بين الشاشات:
    ┌──────────┐   send    ┌──────────┐
    │          │──────────►│  Sender  │
    │   Home   │◄──────────│          │
    │          │  receive  └──────────┘
    │          │──────────►┌──────────┐
    │          │◄──────────│ Receiver │
    └──────────┘           └──────────┘
    """

    def __init__(self):
        super().__init__()

        self.title("PyWormhole")
        self.geometry("520x680")
        self.resizable(False, False)

        self._apply_style()
        self._current: ttk.Frame | None = None

        self.show_home()

    # ─────────────────────────────────────────
    def show_home(self) -> None:
        self._switch(HomeScreen(
            self,
            on_send=self.show_sender,
            on_receive=self.show_receiver,
        ))

    def show_sender(self) -> None:
        self._switch(SenderScreen(self, on_back=self.show_home))

    def show_receiver(self) -> None:
        self._switch(ReceiverScreen(self, on_back=self.show_home))

    def _switch(self, frame: ttk.Frame) -> None:
        if self._current:
            self._current.destroy()
        self._current = frame
        frame.pack(fill="both", expand=True)

    # ─────────────────────────────────────────
    def _apply_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton",   padding=6, font=("Helvetica", 11))
        style.configure("TLabel",    font=("Helvetica", 11))
        style.configure("TLabelframe.Label", font=("Helvetica", 10, "bold"))


if __name__ == "__main__":
    app = PyWormholeApp()
    app.mainloop()