# svg2androidwebp — macOS wizard app

from AppKit import (
    NSApplication, NSOpenPanel, NSAlert, NSTextField, NSMakeRect,
    NSImage, NSImageView, NSImageScaleProportionallyUpOrDown,
    NSView, NSPopUpButton, NSButton,
)
import objc
from Foundation import NSObject

NSOnState = 1
NSOffState = 0

from converter import convert, BASELINES

PREVIEW_H = 160


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


def _make_label(text, x, y, w, h):
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    return label


class _ToggleHandler(NSObject):
    """Handles the 'Use SVG size' checkbox toggle to enable/disable dimension fields."""

    def initWithFields_(self, fields):
        self = objc.super(_ToggleHandler, self).init()
        self._fields = fields
        return self

    def toggle_(self, sender):
        enabled = sender.state() == NSOffState
        for f in self._fields:
            f.setEnabled_(enabled)


def _ask_icon_details(svg_path):
    """
    Single dialog: SVG preview, icon name, dimension toggle + fields, baseline.
    Returns (icon_name, width, height, baseline) or None if cancelled.
    width/height are None when 'Use SVG size' is checked.
    """
    from converter import detect_dimensions

    detected = None
    try:
        detected = detect_dimensions(svg_path)
    except Exception:
        pass

    W = 420
    GAP = 8
    FIELD_H = 24
    LABEL_H = 18

    # Layout: build from bottom (y=0) upward
    y = 0

    # Baseline row (bottom)
    baseline_y = y
    y += 26 + GAP

    # Dimension fields row
    dims_field_y = y
    y += FIELD_H + 4

    # "Use SVG size" checkbox row
    checkbox_y = y
    y += FIELD_H + GAP

    # Icon name row
    name_label_y = y
    y += LABEL_H + 4
    name_field_y = y
    y += FIELD_H + GAP

    # Preview (top)
    preview_y = y
    y += PREVIEW_H

    container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, W, y))

    # SVG preview
    img_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, preview_y, W, PREVIEW_H))
    image = NSImage.alloc().initWithContentsOfFile_(svg_path)
    if image:
        img_view.setImage_(image)
        img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
    container.addSubview_(img_view)

    # Icon name
    container.addSubview_(_make_label("Icon name:", 0, name_label_y, W, LABEL_H))
    name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, name_field_y, W, FIELD_H))
    name_field.setPlaceholderString_("e.g. ic_home_euro_coin")
    container.addSubview_(name_field)

    # "Use SVG size" checkbox (checked = use SVG, unchecked = manual)
    checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(0, checkbox_y, W, FIELD_H))
    checkbox.setButtonType_(3)  # NSSwitchButton
    svg_size_label = f"Use SVG size ({detected[0]}×{detected[1]} px)" if detected else "Use SVG size"
    checkbox.setTitle_(svg_size_label)
    checkbox.setState_(NSOnState)
    container.addSubview_(checkbox)

    # Dimension fields (disabled by default since checkbox is ON)
    w_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, dims_field_y, 90, FIELD_H))
    w_field.setPlaceholderString_("Width (px)")
    w_field.setEnabled_(False)
    container.addSubview_(w_field)
    container.addSubview_(_make_label("×", 96, dims_field_y + 3, 14, LABEL_H))
    h_field = NSTextField.alloc().initWithFrame_(NSMakeRect(114, dims_field_y, 90, FIELD_H))
    h_field.setPlaceholderString_("Height (px)")
    h_field.setEnabled_(False)
    container.addSubview_(h_field)
    if detected:
        container.addSubview_(_make_label(
            f"(SVG: {detected[0]}×{detected[1]} px)", 214, dims_field_y + 3, 200, LABEL_H,
        ))

    # Wire checkbox → toggle handler
    handler = _ToggleHandler.alloc().initWithFields_([w_field, h_field])
    checkbox.setTarget_(handler)
    checkbox.setAction_("toggle:")

    # Baseline density
    container.addSubview_(_make_label("Baseline density:", 0, baseline_y + 3, 130, LABEL_H))
    popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(135, baseline_y, 180, 26))
    for d in BASELINES:
        popup.addItemWithTitle_(d)
    popup.selectItemWithTitle_("mdpi")
    container.addSubview_(popup)

    alert = NSAlert.alloc().init()
    alert.setMessageText_("Icon Details")
    alert.setInformativeText_("Configure the Android resource name and conversion settings:")
    alert.addButtonWithTitle_("Next")    # 1000
    alert.addButtonWithTitle_("Back")    # 1001
    alert.addButtonWithTitle_("Cancel")  # 1002
    alert.setAccessoryView_(container)
    alert.window().setInitialFirstResponder_(name_field)

    while True:
        response = alert.runModal()
        if response == 1002:
            return None
        if response == 1001:
            return "BACK"

        icon_name = name_field.stringValue().strip()
        if not icon_name:
            _show_result("Error", "Icon name cannot be empty.")
            continue

        custom_w = custom_h = None
        if checkbox.state() == NSOffState:
            w_str = w_field.stringValue().strip()
            h_str = h_field.stringValue().strip()
            if not (w_str and h_str):
                _show_result("Error", "Please enter both width and height.")
                continue
            try:
                custom_w = int(float(w_str))
                custom_h = int(float(h_str))
                if custom_w <= 0 or custom_h <= 0:
                    raise ValueError
            except ValueError:
                _show_result("Error", "Invalid dimensions. Please enter positive integers.")
                continue

        baseline = popup.titleOfSelectedItem()
        return icon_name, custom_w, custom_h, baseline


def _ask_module_path():
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Android Module Root")
    alert.setInformativeText_(
        "Select the module root folder (the one that contains src/main/res/).\n"
        "Type or paste the path, or leave blank and click Browse to choose in Finder:"
    )
    alert.addButtonWithTitle_("Next")    # 1000
    alert.addButtonWithTitle_("Back")    # 1001
    alert.addButtonWithTitle_("Browse…") # 1002
    alert.addButtonWithTitle_("Cancel")  # 1003
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 380, 24))
    field.setPlaceholderString_("e.g. libraries/MyModule/impl  (not the res/ folder)")
    alert.setAccessoryView_(field)
    alert.window().setInitialFirstResponder_(field)
    response = alert.runModal()

    if response == 1003:
        return None
    if response == 1001:
        return "BACK"
    typed = field.stringValue().strip()
    if response == 1000 and typed:
        return typed
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

    step = 1
    icon_name = custom_w = custom_h = baseline = None

    while True:
        if step == 1:
            result = _ask_icon_details(svg_path)
            if result is None:
                return
            if result == "BACK":
                # Step 1 is the first step after SVG pick — go back to SVG picker
                svg_path = _pick_file(
                    "Select SVG file",
                    allowed_types=["svg"],
                    message="Choose the SVG file to convert to Android WebP density variants.",
                    prompt="Select SVG",
                )
                if not svg_path:
                    return
                continue
            icon_name, custom_w, custom_h, baseline = result
            step = 2

        if step == 2:
            module_path = _ask_module_path()
            if module_path is None:
                return
            if module_path == "BACK":
                step = 1
                continue

            try:
                msg = convert(svg_path, icon_name, module_path, width=custom_w, height=custom_h, baseline=baseline)
                _show_result("Done", msg)
                return
            except Exception as e:
                _show_result("Error", str(e))


if __name__ == "__main__":
    main()
