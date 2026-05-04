# svg2androidwebp menubar app

import rumps
import threading

from AppKit import NSApp, NSOpenPanel

from converter import convert


class SVG2AndroidWebPApp(rumps.App):
    def __init__(self):
        super().__init__("SVG→WebP", quit_button=None)
        self.menu = [
            rumps.MenuItem("Convert SVG...", callback=self.start_conversion),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self._result = None
        self._result_lock = threading.Lock()

    def start_conversion(self, _):
        # Step 1: Pick SVG file
        NSApp.activateIgnoringOtherApps_(True)
        panel = NSOpenPanel.openPanel()
        panel.setTitle_("Select SVG file")
        panel.setAllowedFileTypes_(["svg"])
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        if panel.runModal() != 1:
            return
        svg_path = panel.URL().path()

        # Step 2: Get icon name
        NSApp.activateIgnoringOtherApps_(True)
        response = rumps.Window(
            title="SVG to Android WebP",
            message="Icon name (lowercase letters, digits, underscores):",
            ok="Next",
            cancel="Cancel",
            dimensions=(320, 24),
        ).run()
        if not response.clicked:
            return
        icon_name = response.text.strip()
        if not icon_name:
            rumps.alert("Error", "Icon name cannot be empty.")
            return

        # Step 3: Pick Android module directory
        NSApp.activateIgnoringOtherApps_(True)
        panel2 = NSOpenPanel.openPanel()
        panel2.setTitle_("Select Android module folder")
        panel2.setCanChooseFiles_(False)
        panel2.setCanChooseDirectories_(True)
        panel2.setAllowsMultipleSelection_(False)
        if panel2.runModal() != 1:
            return
        module_path = panel2.URL().path()

        # Disable menu item during conversion
        self.menu["Convert SVG..."].set_callback(None)
        with self._result_lock:
            self._result = None

        def run():
            try:
                msg = convert(svg_path, icon_name, module_path)
                with self._result_lock:
                    self._result = ("ok", msg)
            except Exception as e:
                with self._result_lock:
                    self._result = ("err", str(e))

        threading.Thread(target=run, daemon=True).start()

        # Poll for result on the main thread via timer
        def check(timer):
            with self._result_lock:
                result = self._result
            if result is None:
                return
            timer.stop()
            self.menu["Convert SVG..."].set_callback(self.start_conversion)
            if result[0] == "ok":
                rumps.alert("Done", result[1])
            else:
                rumps.alert("Error", result[1])

        rumps.Timer(check, 0.2).start()


if __name__ == "__main__":
    SVG2AndroidWebPApp().run()
