# svg2androidwebp — macOS wizard app

import json
import os

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

PREVIEW_H = 80

_PREFS_PATH = os.path.expanduser(
    "~/Library/Preferences/com.thibaultcharr.svg2androidwebp.json"
)


def _load_prefs():
    try:
        with open(_PREFS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_prefs(prefs):
    try:
        with open(_PREFS_PATH, "w") as f:
            json.dump(prefs, f)
    except Exception:
        pass


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


class _DarkSVGHandler(NSObject):
    """Opens an SVG file picker and updates the preview area with both images."""

    def initWithSources_(self, sources):
        self = objc.super(_DarkSVGHandler, self).init()
        self._light_img_view, self._dark_img_view, self._dark_label, self._remove_btn, self._dark_btn, self._preview_y, self._state = sources
        return self

    def pick_(self, sender):
        path = _pick_file(
            "Select dark mode SVG",
            allowed_types=["svg"],
            message="Choose the dark mode SVG file.",
            prompt="Select SVG",
        )
        if not path:
            return
        self._state["dark_svg_path"] = path
        image = NSImage.alloc().initWithContentsOfFile_(path)
        if image:
            W = 420
            HALF = (W - 4) // 2
            y = self._preview_y
            self._light_img_view.setFrame_(NSMakeRect(0, y, HALF, PREVIEW_H))
            self._dark_img_view.setFrame_(NSMakeRect(HALF + 4, y, HALF, PREVIEW_H))
            self._dark_img_view.setImage_(image)
            self._dark_img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
            self._dark_img_view.setHidden_(False)
            self._dark_label.setHidden_(False)
            self._remove_btn.setFrame_(NSMakeRect(HALF + 4 + HALF - 36, y + PREVIEW_H - 36, 36, 36))
            self._remove_btn.setHidden_(False)
            self._dark_btn.setTitle_("Edit dark mode")

    def remove_(self, sender):
        W = 420
        y = self._preview_y
        self._light_img_view.setFrame_(NSMakeRect(0, y, W, PREVIEW_H))
        self._dark_img_view.setHidden_(True)
        self._dark_label.setHidden_(True)
        self._remove_btn.setHidden_(True)
        self._dark_btn.setTitle_("+ Dark mode")
        self._state["dark_svg_path"] = None


class _PreviewHandler(NSObject):
    """Shows a summary of output sizes for each density."""

    def initWithSources_(self, sources):
        self = objc.super(_PreviewHandler, self).init()
        self._checkbox, self._w_field, self._h_field, self._popup, self._detected = sources
        return self

    def preview_(self, sender):
        from converter import DENSITY_SCALES
        baseline = self._popup.titleOfSelectedItem()

        if self._checkbox.state() == NSOnState and self._detected:
            w, h = self._detected
        else:
            try:
                w = int(float(self._w_field.stringValue().strip()))
                h = int(float(self._h_field.stringValue().strip()))
            except (ValueError, TypeError):
                _show_result("Preview", "Enter dimensions first.")
                return

        baseline_scale = DENSITY_SCALES[baseline]
        lines = []
        for density, scale in DENSITY_SCALES.items():
            dw = max(1, round(w * scale / baseline_scale))
            dh = max(1, round(h * scale / baseline_scale))
            lines.append(f"{density:<10} {dw} × {dh} px")

        _show_result("Output sizes", "\n".join(lines))


def _ask_icon_details(svg_path):
    """
    Single dialog: SVG preview, icon name, dark mode button, dimension toggle + fields, baseline.
    Returns (icon_name, dark_svg_path, width, height, baseline) or None/BACK.
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
    dark_state = {"dark_svg_path": None}

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

    # Preview (top) — used for light only or side-by-side
    preview_y = y
    y += PREVIEW_H

    container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, W, y))

    # Light SVG preview (full width by default, shrinks when dark is added)
    img_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, preview_y, W, PREVIEW_H))
    image = NSImage.alloc().initWithContentsOfFile_(svg_path)
    if image:
        img_view.setImage_(image)
        img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
    container.addSubview_(img_view)

    # Dark SVG preview (hidden until picked)
    dark_img_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, preview_y, 0, PREVIEW_H))
    dark_img_view.setHidden_(True)
    container.addSubview_(dark_img_view)

    # "Dark" label above dark preview (hidden until picked)
    dark_label = _make_label("Dark", W // 2 + 2, preview_y + PREVIEW_H - LABEL_H, W // 2, LABEL_H)
    dark_label.setHidden_(True)
    container.addSubview_(dark_label)

    # Remove button (×) in top-right corner of dark preview (hidden until picked)
    remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(W - 36, preview_y + PREVIEW_H - 36, 36, 36))
    remove_btn.setTitle_("✕")
    remove_btn.setBezelStyle_(1)
    remove_btn.setHidden_(True)
    container.addSubview_(remove_btn)

    # Icon name label above field, dark mode button to the right
    container.addSubview_(_make_label("Icon name:", 0, name_label_y, 100, LABEL_H))
    name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, name_field_y, 300, FIELD_H))
    name_field.setPlaceholderString_("e.g. ic_home_euro_coin")
    container.addSubview_(name_field)

    dark_btn = NSButton.alloc().initWithFrame_(NSMakeRect(308, name_field_y, 112, FIELD_H))
    dark_btn.setTitle_("+ Dark mode")
    dark_btn.setBezelStyle_(1)
    container.addSubview_(dark_btn)

    dark_handler = _DarkSVGHandler.alloc().initWithSources_(
        (img_view, dark_img_view, dark_label, remove_btn, dark_btn, preview_y, dark_state)
    )
    dark_btn.setTarget_(dark_handler)
    dark_btn.setAction_("pick:")
    remove_btn.setTarget_(dark_handler)
    remove_btn.setAction_("remove:")

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
    popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(135, baseline_y, 150, 26))
    for d in BASELINES:
        popup.addItemWithTitle_(d)
    popup.selectItemWithTitle_("mdpi")
    container.addSubview_(popup)

    preview_btn = NSButton.alloc().initWithFrame_(NSMakeRect(293, baseline_y, 127, 26))
    preview_btn.setTitle_("Preview sizes…")
    preview_btn.setBezelStyle_(1)
    container.addSubview_(preview_btn)

    preview_handler = _PreviewHandler.alloc().initWithSources_(
        (checkbox, w_field, h_field, popup, detected)
    )
    preview_btn.setTarget_(preview_handler)
    preview_btn.setAction_("preview:")

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
        return icon_name, dark_state["dark_svg_path"], custom_w, custom_h, baseline


class _BrowseHandler(NSObject):
    """Opens a folder picker and writes the chosen path into a text field."""

    def initWithField_(self, field):
        self = objc.super(_BrowseHandler, self).init()
        self._field = field
        return self

    def browse_(self, sender):
        path = _pick_file(
            "Select Android module folder",
            choose_dirs=True,
            message="Choose the module root folder — the one that contains src/main/res/",
            prompt="Select Module",
        )
        if path:
            self._field.setStringValue_(path)


def _ask_module_path():
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Android Module Root")
    alert.setInformativeText_(
        "Select the module root folder (the one that contains src/main/res/)."
    )
    alert.addButtonWithTitle_("Convert") # 1000
    alert.addButtonWithTitle_("Back")    # 1001
    alert.addButtonWithTitle_("Cancel")  # 1002

    # Accessory view: path field (2-line) + Browse button side by side
    FIELD_H = 42
    container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 380, FIELD_H))
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 290, FIELD_H))
    field.setPlaceholderString_("e.g. libraries/MyModule/impl")
    field.cell().setWraps_(True)
    field.cell().setScrollable_(False)
    last_path = _load_prefs().get("last_module_path", "")
    if last_path:
        field.setStringValue_(last_path)
    container.addSubview_(field)

    browse_btn = NSButton.alloc().initWithFrame_(NSMakeRect(298, (FIELD_H - 24) // 2, 82, 24))
    browse_btn.setTitle_("Browse…")
    browse_btn.setBezelStyle_(1)  # NSRoundedBezelStyle
    container.addSubview_(browse_btn)

    alert.setAccessoryView_(container)
    alert.window().setInitialFirstResponder_(field)

    # Wire Browse button to open folder picker via a handler
    browse_handler = _BrowseHandler.alloc().initWithField_(field)
    browse_btn.setTarget_(browse_handler)
    browse_btn.setAction_("browse:")

    response = alert.runModal()

    if response == 1002:
        return None
    if response == 1001:
        return "BACK"
    typed = field.stringValue().strip()
    return typed if typed else None


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
            icon_name, dark_svg_path, custom_w, custom_h, baseline = result
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
                if dark_svg_path:
                    convert(dark_svg_path, icon_name, module_path, width=custom_w, height=custom_h, baseline=baseline, night=True)
                prefs = _load_prefs()
                prefs["last_module_path"] = module_path
                _save_prefs(prefs)
                _show_result("Done", msg)
                return
            except Exception as e:
                _show_result("Error", str(e))


if __name__ == "__main__":
    main()
