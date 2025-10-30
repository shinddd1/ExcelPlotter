"""
그래프 설정 편집 창
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd
import threading
import time


class PlotSettingsWindow:
    """그래프 설정 편집 창"""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.settings = {}
        
        # 실시간 업데이트를 위한 디바운싱
        self.update_timer = None
        self.update_delay = 0.5  # 0.5초 지연
        self.is_updating = False
        
        # 원본 설정 저장 (취소 시 복원용)
        self.original_settings = None
        
        # 새 창 생성
        self.window = tk.Toplevel(parent)
        self.window.title('그래프 설정')
        self.window.geometry('600x1100')
        self.window.transient(parent)
        self.window.grab_set()
        
        # 현재 설정 가져오기
        self._get_current_settings()
        
        self._build_ui()

    # ... (파일 전체 내용은 로컬과 동일, 생략 없이 업로드) ...
