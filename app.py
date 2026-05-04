# svg2androidwebp menubar app

import rumps
import threading
import tkinter as tk
from tkinter import filedialog

from converter import convert


class ConversionWindow:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.title("SVG to Android WebP")
        self.win.resizable(True, True)
        self.win.minsize(500, 260)

        pad = {"padx": 10, "pady": 6}

        # SVG File row
        tk.Label(self.win, text="SVG File:").grid(row=0, column=0, sticky="e", **pad)
        self.svg_var = tk.StringVar()
        self.svg_entry = tk.Entry(self.win, textvariable=self.svg_var, state="readonly", width=45)
        self.svg_entry.grid(row=0, column=1, sticky="ew", **pad)
        tk.Button(self.win, text="Browse...", command=self._browse_svg).grid(row=0, column=2, **pad)

        # Icon Name row
        tk.Label(self.win, text="Icon Name:").grid(row=1, column=0, sticky="e", **pad)
        self.name_var = tk.StringVar()
        self.name_var.trace_add("write", self._on_field_change)
        tk.Entry(self.win, textvariable=self.name_var, width=45).grid(row=1, column=1, sticky="ew", **pad)

        # Module Path row
        tk.Label(self.win, text="Module Path:").grid(row=2, column=0, sticky="e", **pad)
        self.module_var = tk.StringVar()
        self.module_entry = tk.Entry(self.win, textvariable=self.module_var, state="readonly", width=45)
        self.module_entry.grid(row=2, column=1, sticky="ew", **pad)
        tk.Button(self.win, text="Browse...", command=self._browse_module).grid(row=2, column=2, **pad)

        # Convert button
        self.convert_btn = tk.Button(self.win, text="Convert", command=self._on_convert, state="disabled")
        self.convert_btn.grid(row=3, column=1, sticky="w", **pad)

        # Result label
        self.result_var = tk.StringVar()
        self.result_label = tk.Label(self.win, textvariable=self.result_var, wraplength=460, justify="left")
        self.result_label.grid(row=4, column=0, columnspan=3, sticky="w", **pad)

        # "Convert another" button (hidden initially)
        self.reset_btn = tk.Button(self.win, text="Convert another", command=self._reset)
        self.reset_btn.grid(row=5, column=1, sticky="w", **pad)
        self.reset_btn.grid_remove()

        self.win.columnconfigure(1, weight=1)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.lift()
        self.win.focus_force()

    def _browse_svg(self):
        path = filedialog.askopenfilename(
            title="Select SVG file",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
        )
        if path:
            self.svg_var.set(path)
            self._on_field_change()

    def _browse_module(self):
        path = filedialog.askdirectory(title="Select Android module directory")
        if path:
            self.module_var.set(path)
            self._on_field_change()

    def _on_field_change(self, *_):
        if self.svg_var.get() and self.name_var.get().strip() and self.module_var.get():
            self.convert_btn.config(state="normal")
        else:
            self.convert_btn.config(state="disabled")

    def _on_convert(self):
        self.convert_btn.config(state="disabled")
        self.reset_btn.grid_remove()
        self.result_var.set("Converting...")

        svg = self.svg_var.get()
        name = self.name_var.get().strip()
        module = self.module_var.get()

        def run():
            try:
                msg = convert(svg, name, module)
                if self.winfo_exists():
                    self.win.after(0, self._on_success, msg)
            except Exception as e:
                if self.winfo_exists():
                    self.win.after(0, self._on_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_success(self, msg):
        self.result_var.set(msg)
        self.reset_btn.grid()

    def _on_error(self, msg):
        self.result_var.set(msg)
        self.convert_btn.config(state="normal")

    def _reset(self):
        self.svg_var.set("")
        self.name_var.set("")
        self.module_var.set("")
        self.result_var.set("")
        self.reset_btn.grid_remove()
        self.convert_btn.config(state="disabled")

    def _on_close(self):
        self.win.destroy()
        self.root.quit()

    def winfo_exists(self):
        try:
            return self.win.winfo_exists()
        except Exception:
            return False

    def lift(self):
        self.win.lift()

    def focus_force(self):
        self.win.focus_force()


class SVG2AndroidWebPApp(rumps.App):
    def __init__(self):
        super().__init__("SVG→WebP", quit_button=None)
        self.menu = [
            rumps.MenuItem("Convert SVG...", callback=self.open_window),
            None,  # separator
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self._window = None
        self._window_lock = threading.Lock()
        self._launching = False

    def open_window(self, _):
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return
        with self._window_lock:
            if self._launching:
                return
            if self._window is not None and self._window.winfo_exists():
                self._window.lift()
                self._window.focus_force()
                return
            self._launching = True
            self._launch_window()

    def _launch_window(self):
        t = threading.Thread(target=self._run_window, daemon=True)
        t.start()

    def _run_window(self):
        # NOTE: tkinter runs off the main thread here because rumps owns the
        # main thread via NSRunLoop. This is a known macOS-Tk trade-off and
        # works reliably for this single-window use case.
        try:
            root = tk.Tk()
            root.withdraw()
            self._window = ConversionWindow(root)
            self._launching = False
            root.mainloop()
        finally:
            self._launching = False
            self._window = None


if __name__ == "__main__":
    SVG2AndroidWebPApp().run()
