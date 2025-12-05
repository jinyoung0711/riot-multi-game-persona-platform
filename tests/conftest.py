# tests/conftest.py

import os
import sys

# 프로젝트 루트 디렉토리 경로 (tests의 상위 폴더)
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

# sys.path에 루트 디렉토리가 없으면 추가
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
