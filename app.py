import rumps
import threading
import tkinter as tk

class SVG2AndroidWebPApp(rumps.App):
    def __init__(self):
        super().__init__("SVG→WebP", quit_button=None)
        self.menu = [
            rumps.MenuItem("Convert SVG...", callback=self.open_window),
            None,  # separator
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self._window = None

    def open_window(self, _):
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return
        self._launch_window()

    def _launch_window(self):
        t = threading.Thread(target=self._run_window, daemon=True)
        t.start()

    def _run_window(self):
        root = tk.Tk()
        root.withdraw()  # hide root window
        self._window = ConversionWindow(root)
        root.mainloop()


if __name__ == "__main__":
    SVG2AndroidWebPApp().run()
