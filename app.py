# svg2androidwebp — macOS wizard app

from AppKit import (
    NSApplication, NSOpenPanel, NSAlert, NSTextField, NSMakeRect,
    NSImage, NSImageView, NSImageScaleProportionallyUpOrDown,
    NSView, NSPopUpButton,
)

from converter import convert, BASELINES

PREVIEW_SIZE = 160


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


def _ask_text(title, message, placeholder="", preview_path=None):
    alert = NSAlert.alloc().init()
    alert.setMessageText_(title)
    alert.setInformativeText_(message)
    alert.addButtonWithTitle_("Next")
    alert.addButtonWithTitle_("Cancel")

    width = 380
    field_h = 24
    gap = 8

    if preview_path:
        # Container view: image preview on top, text field below
        total_h = PREVIEW_SIZE + gap + field_h
        container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, total_h))

        img_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect(0, field_h + gap, width, PREVIEW_SIZE)
        )
        image = NSImage.alloc().initWithContentsOfFile_(preview_path)
        if image:
            img_view.setImage_(image)
            img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        container.addSubview_(img_view)

        field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, width, field_h))
        container.addSubview_(field)
        alert.setAccessoryView_(container)
    else:
        field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, width, field_h))
        alert.setAccessoryView_(field)

    if placeholder:
        field.setPlaceholderString_(placeholder)
    alert.window().setInitialFirstResponder_(field)
    # NSAlertFirstButtonReturn = 1000
    return field.stringValue().strip() if alert.runModal() == 1000 else None


def _make_label(text, x, y, w, h):
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    return label


def _ask_dimensions(svg_path):
    """
    Returns (width, height) or (None, None) to use SVG size.
    Returns False if cancelled.
    """
    from converter import detect_dimensions
    detected = None
    try:
        detected = detect_dimensions(svg_path)
    except Exception:
        pass

    alert = NSAlert.alloc().init()
    alert.setMessageText_("Source Dimensions (hdpi baseline)")
    info = "The SVG dimensions are used as the hdpi (1.5x) baseline for all density outputs."
    if detected:
        info += f"\n\nDetected size: {detected[0]}×{detected[1]} px."
    alert.setInformativeText_(info)
    alert.addButtonWithTitle_("Use SVG Size")   # 1000
    alert.addButtonWithTitle_("Enter Manually") # 1001
    alert.addButtonWithTitle_("Cancel")         # 1002

    response = alert.runModal()
    if response == 1002:
        return False
    if response == 1000:
        return None, None  # use SVG size

    # Manual entry — show a second dialog with two fields
    alert2 = NSAlert.alloc().init()
    alert2.setMessageText_("Enter Source Dimensions")
    alert2.setInformativeText_("Enter the width and height in pixels for the hdpi (1.5x) baseline:")
    alert2.addButtonWithTitle_("Next")   # 1000
    alert2.addButtonWithTitle_("Cancel") # 1001

    container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 260, 56))

    container.addSubview_(_make_label("Width (px):", 0, 32, 90, 20))
    w_field = NSTextField.alloc().initWithFrame_(NSMakeRect(95, 32, 80, 24))
    if detected:
        w_field.setStringValue_(str(detected[0]))
    container.addSubview_(w_field)

    container.addSubview_(_make_label("Height (px):", 0, 4, 90, 20))
    h_field = NSTextField.alloc().initWithFrame_(NSMakeRect(95, 4, 80, 24))
    if detected:
        h_field.setStringValue_(str(detected[1]))
    container.addSubview_(h_field)

    alert2.setAccessoryView_(container)
    alert2.window().setInitialFirstResponder_(w_field)

    if alert2.runModal() != 1000:
        return False
    try:
        w = int(float(w_field.stringValue().strip()))
        h = int(float(h_field.stringValue().strip()))
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except (ValueError, Exception):
        _show_result("Error", "Invalid dimensions. Please enter positive integers.")
        return False


def _ask_baseline():
    """Returns the chosen baseline density string, or None if cancelled."""
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Baseline Density")
    alert.setInformativeText_(
        "Which density do your source dimensions represent?\n\n"
        "hdpi (1.5×) is the most common choice for hand-drawn SVGs."
    )
    alert.addButtonWithTitle_("Next")   # 1000
    alert.addButtonWithTitle_("Cancel") # 1001

    popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 200, 26))
    for density in BASELINES:
        popup.addItemWithTitle_(density)
    popup.selectItemWithTitle_("hdpi")
    alert.setAccessoryView_(popup)

    if alert.runModal() != 1000:
        return None
    return popup.titleOfSelectedItem()


def _ask_module_path():
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Android Module Root")
    alert.setInformativeText_(
        "Select the module root folder (the one that contains src/main/res/).\n"
        "Type or paste the path, or leave blank and click Browse to choose in Finder:"
    )
    alert.addButtonWithTitle_("Next")    # 1000
    alert.addButtonWithTitle_("Browse…") # 1001
    alert.addButtonWithTitle_("Cancel")  # 1002
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 380, 24))
    field.setPlaceholderString_("e.g. libraries/MyModule/impl  (not the res/ folder)")
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
        message="Choose the module root folder — the one that contains src/main/res/ (do NOT select the res/ folder itself)",
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
    app.setActivationPolicy_(0)  # NSApplicationActivationPolicyRegular — shows in Dock
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
        preview_path=svg_path,
    )
    if not icon_name:
        return

    dims = _ask_dimensions(svg_path)
    if dims is False:
        return
    custom_w, custom_h = dims if dims != (None, None) else (None, None)

    baseline = _ask_baseline()
    if baseline is None:
        return

    module_path = _ask_module_path()
    if not module_path:
        return

    try:
        msg = convert(svg_path, icon_name, module_path, width=custom_w, height=custom_h, baseline=baseline)
        _show_result("Done", msg)
    except Exception as e:
        _show_result("Error", str(e))


if __name__ == "__main__":
    main()
