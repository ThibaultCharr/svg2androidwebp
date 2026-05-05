from setuptools import setup

APP = ["app.py"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "icon.icns",
    "packages": ["converter", "cairosvg", "PIL", "cssselect2", "tinycss2", "defusedxml"],
    "includes": ["pyexpat"],
    "plist": {
        "CFBundleName": "SVG2AndroidWebP",
        "CFBundleDisplayName": "SVG2AndroidWebP",
        "CFBundleIdentifier": "com.thibaultcharr.svg2androidwebp",
        "CFBundleVersion": "1.0.0",
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="SVG2AndroidWebP",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
