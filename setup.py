from setuptools import setup

APP = ["app.py"]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["converter"],
    "plist": {
        "CFBundleName": "svg2androidwebp",
        "CFBundleDisplayName": "svg2androidwebp",
        "CFBundleIdentifier": "com.thibaultcharr.svg2androidwebp",
        "CFBundleVersion": "1.0.0",
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
