#!/usr/bin/env bash
LIB_NAME=pypelined
DOCS_DIR=docs

cd ${DOCS_DIR}
rm source/api/*
sphinx-apidoc -M -e -o source/api ../${LIB_NAME} --force && \
python3 $(which sphinx-build) -b html -d build/doctrees . build/html/ && \
open build/html/index.html
