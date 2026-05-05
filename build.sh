#!/bin/bash
set -e
rm -rf build dist
.venv312/bin/python setup.py py2app
echo "Build complete."
