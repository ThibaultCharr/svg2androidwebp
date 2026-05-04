"""SVG to Android WebP converter — pure conversion logic, no UI dependency."""
import re
import shutil
import xml.etree.ElementTree as ET


def check_dependencies():
    """Returns a list of missing tool names, empty if all present."""
    missing = []
    if not shutil.which("rsvg-convert"):
        missing.append("librsvg")
    if not shutil.which("cwebp"):
        missing.append("webp")
    return missing


def detect_dimensions(svg_path):
    """
    Returns (width, height) as ints from the SVG file.
    Reads width/height attributes first, falls back to viewBox.
    Raises ValueError if dimensions cannot be detected.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    width = root.get("width", "")
    height = root.get("height", "")

    # Strip non-numeric characters (e.g. "24px" -> "24")
    width = re.sub(r"[^0-9]", "", width)
    height = re.sub(r"[^0-9]", "", height)

    if width and height and width != "0" and height != "0":
        return int(width), int(height)

    # Fallback to viewBox="0 0 W H"
    viewbox = root.get("viewBox", "")
    parts = viewbox.strip().split()
    if len(parts) == 4:
        try:
            return int(float(parts[2])), int(float(parts[3]))
        except ValueError:
            pass

    raise ValueError("Could not detect SVG dimensions.")
