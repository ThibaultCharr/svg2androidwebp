# svg2androidwebp — macOS wizard app

from AppKit import (
    NSApplication, NSOpenPanel, NSAlert, NSTextField, NSMakeRect,
)

from converter import convert


def _pick_file(title, allowed_types=None, choose_dirs=False, message=None, prompt=None):
    panel = NSOpenPanel.openPanel()
    panel.setTitle_(title)
    if message:
        panel.setMessage_(message)
    if prompt:
        panel.setPrompt_(prompt)
    panel.setCanChooseFiles_(not choose_dirs)
    panel.setCanChooseDirectories_(choose_dirs)
    panel.setAllowsMultipleSelection_(False)
    if allowed_types:
        panel.setAllowedFileTypes_(allowed_types)
    return panel.URL().path() if panel.runModal() == 1 else None


def _ask_text(title, message, placeholder=""):
    alert = NSAlert.alloc().init()
    alert.setMessageText_(title)
    alert.setInformativeText_(message)
    alert.addButtonWithTitle_("Next")
    alert.addButtonWithTitle_("Cancel")
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 320, 24))
    if placeholder:
        field.setPlaceholderString_(placeholder)
    alert.setAccessoryView_(field)
    alert.window().setInitialFirstResponder_(field)
    # NSAlertFirstButtonReturn = 1000
    return field.stringValue().strip() if alert.runModal() == 1000 else None


def _ask_module_path():
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Android Module Path")
    alert.setInformativeText_(
        "Type or paste the module path, or leave blank and click Browse to choose in Finder:"
    )
    alert.addButtonWithTitle_("Next")    # 1000
    alert.addButtonWithTitle_("Browse…") # 1001
    alert.addButtonWithTitle_("Cancel")  # 1002
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 380, 24))
    field.setPlaceholderString_("e.g. libraries/MyModule/impl")
    alert.setAccessoryView_(field)
    alert.window().setInitialFirstResponder_(field)
    response = alert.runModal()

    if response == 1002:
        return None
    typed = field.stringValue().strip()
    if response == 1000 and typed:
        return typed
    # Browse (1001) or Next with empty field → open Finder
    return _pick_file(
        "Select Android module folder",
        choose_dirs=True,
        message="Choose the Android module folder (containing src/main/res/)",
        prompt="Select Module",
    )


def _show_result(title, message):
    alert = NSAlert.alloc().init()
    alert.setMessageText_(title)
    alert.setInformativeText_(message)
    alert.addButtonWithTitle_("OK")
    alert.runModal()


def main():
    app = NSApplication.sharedApplication()
    app.activateIgnoringOtherApps_(True)

    svg_path = _pick_file(
        "Select SVG file",
        allowed_types=["svg"],
        message="Choose the SVG file to convert to Android WebP density variants.",
        prompt="Select SVG",
    )
    if not svg_path:
        return

    icon_name = _ask_text(
        "Icon Name",
        "Enter the Android resource name:",
        placeholder="e.g. ic_home_euro_coin",
    )
    if not icon_name:
        return

    module_path = _ask_module_path()
    if not module_path:
        return

    try:
        msg = convert(svg_path, icon_name, module_path)
        _show_result("Done", msg)
    except Exception as e:
        _show_result("Error", str(e))


if __name__ == "__main__":
    main()
