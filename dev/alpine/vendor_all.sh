#!/usr/bin/env bash

pants run dev/alpine/vendor_alpine.py -- --package python3 --version '3.15-stable' --dst dev/alpine/main/python39/
pants run dev/alpine/vendor_alpine.py -- --package python3 --version '3.17-stable' --dst dev/alpine/main/python310/
pants run dev/alpine/vendor_alpine.py -- --package python3 --version '3.19-stable' --dst dev/alpine/main/python311/
pants run dev/alpine/vendor_alpine.py -- --package python3 --version '3.20-stable' --dst dev/alpine/main/python312/
