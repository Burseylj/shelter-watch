#!/bin/bash
set -e

rm -rf build
mkdir build

cp lambda_function.py fetch.py render.py build/

pip install -r requirements.txt \
  --platform manylinux2014_x86_64 \
  --target build \
  --only-binary=:all: \
  --python-version 3.12

echo "Build complete: ./build"