import shutil


def check_dependencies():
    """Returns a list of missing tool names, empty if all present."""
    missing = []
    if not shutil.which("rsvg-convert"):
        missing.append("librsvg")
    if not shutil.which("cwebp"):
        missing.append("webp")
    return missing
