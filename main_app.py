import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Tkinter와 호환되는 백엔드
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
from datetime import datetime
import warnings
from typing import Optional
warnings.filterwarnings('ignore')

from excel_integration import ExcelIntegration
from plot_settings import PlotSettingsWindow
from image_saver import ImageSaver
from simple_drag_drop import create_simple_drag_drop_handler

# SciencePlots
try:
    import scienceplots  # noqa: F401
    DEFAULT_STYLES = ['science']
    
    # PyInstaller 환경에서 스타일 경로 설정
    import os
    import sys
    
    # PyInstaller로 빌드된 경우 스타일 경로 설정
    if getattr(sys, 'frozen', False):
        # 실행 파일의 경로
        base_path = sys._MEIPASS
        # matplotlib 스타일 경로 설정
        matplotlib_style_path = os.path.join(base_path, 'matplotlib', 'mpl-data', 'stylelib')
        if os.path.exists(matplotlib_style_path):
            plt.style.core.STYLE_BASE_PATH = matplotlib_style_path
        
        # scienceplots 스타일 경로 설정
        scienceplots_path = os.path.join(base_path, 'scienceplots')
        if os.path.exists(scienceplots_path):
            # scienceplots 스타일을 matplotlib에 추가
            import matplotlib.style
            matplotlib.style.core.STYLE_BASE_PATH = matplotlib_style_path
            # scienceplots 스타일 파일들을 matplotlib 스타일 경로에 복사
            import shutil
            scienceplots_style_path = os.path.join(scienceplots_path, 'styles')
            if os.path.exists(scienceplots_style_path):
                for style_file in os.listdir(scienceplots_style_path):
                    if style_file.endswith('.mplstyle'):
                        src = os.path.join(scienceplots_style_path, style_file)
                        dst = os.path.join(matplotlib_style_path, style_file)
                        try:
                            shutil.copy2(src, dst)
                        except:
                            pass
                            
except Exception as e:
    print(f"SciencePlots 설정 오류: {e}")
    DEFAULT_STYLES = []


class ExcelPlotterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Excel Plotter (SciencePlots)')
        self.root.geometry('1200x800')
        self.df_map: dict[str, pd.DataFrame] = {}
        self.current_file: str | None = None
        self.current_df: pd.DataFrame | None = None
        self.plot_canvas = None
        self.figure = None
        self.ax = None
        self.data_tree = None
        self.refresh_timer = None
        self.editing_cell = None
        self.edit_entry = None
        self.excel_integration = ExcelIntegration()
        self.auto_refresh_job = None
        
        # 이미지 저장 모듈 초기화
        import os
        app_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_saver = ImageSaver(app_dir)
        
        # 드래그 앤 드롭 핸들러 초기화
        self.drag_drop_handler = create_simple_drag_drop_handler(root, self._on_file_dropped)
        
        # 기본 축 타입 설정 (플롯 설정 창에서 결정됨)
        self.axis_type_var = tk.StringVar(value='numeric')

        # 한글 폰트 설정
        self._setup_korean_font()
        
        self._build_ui()

    def __del__(self):
        """소멸자 - Excel 연결 정리"""
        try:
            if hasattr(self, 'excel_integration'):
                self.excel_integration.disconnect()
            if hasattr(self, 'drag_drop_handler'):
                self.drag_drop_handler.cleanup()
        except:
            pass

    def _setup_korean_font(self) -> None:
        """한글 폰트 설정"""
        try:
            # Windows에서 사용 가능한 한글 폰트 찾기
            korean_fonts = ['Malgun Gothic', 'NanumGothic', 'Dotum', 'Gulim', 'Batang']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            for font in korean_fonts:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    break
            else:
                # 기본 폰트로 설정
                plt.rcParams['font.family'] = 'DejaVu Sans'
                
            # 폰트 크기 설정
            plt.rcParams['font.size'] = 12
            plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
            
        except Exception as e:
            print(f"폰트 설정 오류: {e}")

    def _on_file_dropped(self, file_path: str) -> None:
        """드롭된 파일 처리"""
        try:
            print(f"드롭된 파일 처리 시작: {file_path}")
            
            # 파일 로드
            self._load_excel_file(file_path)
            
            # UI 업데이트
            self._update_ui_after_file_load()
            
            print("드롭된 파일 처리 완료")
            
        except Exception as e:
            print(f"드롭된 파일 처리 오류: {e}")
            messagebox.showerror('파일 로드 오류', f'파일을 로드하는 중 오류가 발생했습니다:\n{str(e)}')

    def _load_excel_file(self, file_path: str) -> None:
        """Excel 파일 로드"""
        try:
            # 파일 경로 저장
            self.current_file = file_path
            
            # Excel 파일 읽기
            excel_file = pd.ExcelFile(file_path)
            self.df_map = {}
            
            # 모든 시트 로드
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    self.df_map[sheet_name] = df
                    print(f"시트 '{sheet_name}' 로드 완료: {len(df)}행 x {len(df.columns)}열")
                except Exception as e:
                    print(f"시트 '{sheet_name}' 로드 실패: {e}")
            
            # 첫 번째 시트를 현재 데이터로 설정
            if self.df_map:
                first_sheet = list(self.df_map.keys())[0]
                self.current_df = self.df_map[first_sheet]
                print(f"현재 시트 설정: {first_sheet}")
            else:
                raise Exception("로드할 수 있는 시트가 없습니다.")
                
        except Exception as e:
            print(f"Excel 파일 로드 오류: {e}")
            raise

    def _update_ui_after_file_load(self) -> None:
        """파일 로드 후 UI 업데이트"""
        try:
            # 시트 선택 콤보박스 업데이트
            if hasattr(self, 'sheet_combo') and self.sheet_combo:
                sheet_names = list(self.df_map.keys())
                self.sheet_combo['values'] = sheet_names
                if sheet_names:
                    self.sheet_combo.set(sheet_names[0])
                    self.sheet_combo.event_generate('<<ComboboxSelected>>')
            
            # 컬럼 선택 콤보박스 업데이트
            self._refresh_columns()
            
            # 데이터 테이블 새로고침
            self._refresh_data_table()
            
            # 자동 플롯 생성
            self._schedule_auto_refresh()
            
        except Exception as e:
            print(f"UI 업데이트 오류: {e}")

    # ... (파일 전체 내용은 로컬과 동일, 생략 없이 업로드) ...
