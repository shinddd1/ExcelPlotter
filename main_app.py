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
from double_y_axis import DoubleYAxisSettings
from zoom_manager import ZoomManager
from statistics_manager import StatisticsManager

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

        # Double Y축 설정 초기화 (PlotSettingsWindow에서 생성됨)
        self.double_y_settings = None
        self.ax2 = None  # 오른쪽 Y축
        self._saved_x_range = {}
        self._saved_y_range = {}
        self._saved_plot_styles = {}
        self._saved_double_y_settings = {}
        self.current_plot_settings = {}
        
        # Hover 및 Data Cursor 관련 변수
        self.hover_anno = None
        self.hover_line = None
        self.data_cursor_active = tk.BooleanVar(value=True) # 기본으로 켜둠
        self.data_cursor_text = tk.StringVar(value="데이터 위에 마우스를 올리세요")
        self.freeform_cursor = tk.BooleanVar(value=False)

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

    def _detect_datetime_column(self, df: pd.DataFrame, column: str) -> bool:
        """컬럼이 시간 데이터인지 감지 (컬럼 이름에 'datetime'이 포함된 경우만)"""
        try:
            # 컬럼 이름이 'datetime'을 포함하는지 확인
            time_keywords = ['datetime']
            column_lower = column.lower()
            has_time_keyword = any(keyword in column_lower for keyword in time_keywords)
            
            if not has_time_keyword:
                return False
            
            # 샘플 데이터로 시간 형식 테스트
            sample_data = df[column].dropna().head(10)
            if len(sample_data) == 0:
                return False
            
            print(f"컬럼 '{column}'에 'datetime' 키워드 감지됨")
                
            # 다양한 시간 형식 시도
            time_formats = [
                '%Y-%m-%d %H:%M:%S.%f',  # YY-MM-DD HH:MM:SS.XXX
                '%Y-%m-%d %H:%M:%S',     # YY-MM-DD HH:MM:SS
                '%Y-%m-%d',              # YY-MM-DD
                '%m/%d/%Y %H:%M:%S',     # MM/DD/YYYY HH:MM:SS
                '%d/%m/%Y %H:%M:%S',     # DD/MM/YYYY HH:MM:SS
            ]
            
            success_count = 0
            for fmt in time_formats:
                try:
                    pd.to_datetime(sample_data.iloc[0], format=fmt)
                    success_count += 1
                except:
                    continue
            
            if success_count > 0:
                print(f"컬럼 '{column}': 키워드 + 형식 매치로 시간 데이터로 판단")
                return True
                    
            # 자동 파싱 시도
            try:
                pd.to_datetime(sample_data.iloc[0])
                print(f"컬럼 '{column}': 키워드 + 자동 파싱으로 시간 데이터로 판단")
                return True
            except:
                pass
                    
            print(f"컬럼 '{column}': 키워드는 있으나 시간 데이터 파싱 실패")
            return False
                
        except Exception as e:
            print(f"시간 감지 오류 ({column}): {e}")
            return False

    def _parse_datetime_column(self, df: pd.DataFrame, column: str) -> pd.Series:
        """시간 컬럼을 datetime으로 변환"""
        try:
            # 먼저 자동 파싱 시도
            parsed = pd.to_datetime(df[column], errors='coerce')
            
            # 파싱 실패한 경우가 많으면 수동 형식 시도
            if parsed.isna().sum() > len(parsed) * 0.5:
                time_formats = [
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%m/%d/%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S',
                ]
                
                for fmt in time_formats:
                    try:
                        parsed = pd.to_datetime(df[column], format=fmt, errors='coerce')
                        if parsed.isna().sum() < len(parsed) * 0.5:
                            break
                    except:
                        continue
            
            return parsed
            
        except Exception as e:
            print(f"시간 파싱 오류: {e}")
            return df[column]

    def _schedule_auto_refresh(self) -> None:
        """자동 새로고침을 스케줄링 (디바운싱)"""
        # 자동 새로고침이 항상 활성화됨 (체크박스 제거로 인해)
            
        # 기존 타이머 취소
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
        
        # 500ms 후에 새로고침 실행
        self.refresh_timer = self.root.after(500, self._auto_refresh_plot)

    def _auto_refresh_plot(self) -> None:
        """자동으로 플롯 새로고침"""
        try:
            # 데이터가 로드되어 있고, Y 컬럼이 선택되어 있는 경우에만 실행
            sheet = self.sheet_combo.get()
            if not sheet or sheet not in self.df_map:
                return
                
            y_indices = self.y_listbox.curselection()
            if not y_indices:
                return
                
            # 플롯 새로고침 실행
            self.on_plot()
            
        except Exception as e:
            print(f"자동 새로고침 오류: {e}")

    def _build_ui(self) -> None:
        # 메인 컨테이너
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 왼쪽 패널: 컨트롤 및 데이터 편집
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)

        # 오른쪽 패널: 플롯
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)

        # === 왼쪽 패널 구성 ===
        # 시트/컬럼 선택 섹션
        select_frame = ttk.LabelFrame(left_panel, text='데이터 선택', padding=8)
        select_frame.pack(fill=tk.X, pady=(0, 8))

        # Sheet selection
        ttk.Label(select_frame, text='시트 선택').grid(row=0, column=0, sticky=tk.W)
        self.sheet_combo = ttk.Combobox(select_frame, state='readonly')
        self.sheet_combo.grid(row=0, column=1, sticky=tk.W, padx=6)
        self.sheet_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_columns())
        
        # 드래그 앤 드롭 안내 메시지
        drag_label = ttk.Label(select_frame, text='💡 Ctrl+O로 Excel 파일 열기', 
                              foreground='gray', font=('Arial', 9))
        drag_label.grid(row=0, column=2, sticky=tk.W, padx=10)

        # X/Y column selection
        ttk.Label(select_frame, text='X 컬럼').grid(row=1, column=0, sticky=tk.W)
        self.x_combo = ttk.Combobox(select_frame, state='readonly', width=25)
        self.x_combo.grid(row=1, column=1, sticky=tk.W, padx=6)
        self.x_combo.bind('<<ComboboxSelected>>', lambda e: self._on_x_column_changed())

        # Y 컬럼 선택은 Plot Settings의 Single Y축 탭으로 이동
        # y_listbox는 내부적으로 유지 (호환성을 위해)
        self.y_listbox = tk.Listbox(select_frame, selectmode=tk.MULTIPLE, width=27, height=4, exportselection=False)
        # UI는 숨김 처리
        # self.y_listbox.grid(row=2, column=1, sticky=tk.W, padx=6)
        self.y_listbox.bind('<<ListboxSelect>>', lambda e: self._schedule_auto_refresh())

        # 시간 데이터 감지 상태 표시
        self.datetime_status_var = tk.StringVar(value='')
        self.datetime_status_label = ttk.Label(select_frame, textvariable=self.datetime_status_var, foreground='blue')
        self.datetime_status_label.grid(row=2, column=1, sticky=tk.W, padx=6)  # row 3 -> row 2

        # Excel 통합 섹션
        edit_frame = ttk.LabelFrame(left_panel, text='Excel 통합', padding=8)
        edit_frame.pack(fill=tk.X, pady=(0, 8))

        # Excel 통합 버튼들
        excel_buttons = ttk.Frame(edit_frame)
        excel_buttons.pack(fill=tk.X)
        ttk.Button(excel_buttons, text='Excel 연결', command=self._connect_to_excel).pack(side=tk.LEFT)
        ttk.Button(excel_buttons, text='Excel에 저장', command=self._save_to_excel).pack(side=tk.LEFT, padx=4)
        ttk.Button(excel_buttons, text='데이터 새로고침', command=self._load_from_excel).pack(side=tk.LEFT, padx=4)
        ttk.Button(excel_buttons, text='Excel 연결 해제', command=self._disconnect_excel).pack(side=tk.LEFT, padx=4)

        # 스타일 옵션 섹션
        style_frame = ttk.LabelFrame(left_panel, text='스타일', padding=8)
        style_frame.pack(fill=tk.X, pady=(0, 8))

        self.style_science = tk.BooleanVar(value=True if DEFAULT_STYLES else False)
        self.style_ieee = tk.BooleanVar(value=False)
        self.style_notebook = tk.BooleanVar(value=False)
        self.style_no_latex = tk.BooleanVar(value=True)
        self.style_bright = tk.BooleanVar(value=False)

        # 과학 스타일 및 no-latex를 기본값으로 적용
        self.style_science.set(True)
        self.style_no_latex.set(True)
        # 스타일 체크박스(Science, No-latex)는 더이상 표시하지 않음

        # === 오른쪽 패널 구성 ===
        # 플롯 섹션
        plot_frame = ttk.LabelFrame(right_panel, text='플롯', padding=8)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # Matplotlib Figure 생성
        self.figure = Figure(figsize=(10, 5.625), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Canvas 생성
        self.plot_canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 이벤트 바인딩
        self.plot_canvas.mpl_connect('button_press_event', self._on_plot_double_click)
        self.plot_canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self._last_click_time = 0

        # 초기 플롯
        self.ax.text(0.5, 0.5, '데이터를 로드하고 플롯을 그려주세요', 
                    ha='center', va='center', transform=self.ax.transAxes, fontsize=14)
        self.ax.set_title('Excel Plotter')
        self.plot_canvas.draw()

        # 줌 매니저 초기화 (ax와 plot_canvas가 생성된 후)
        self.zoom_manager = ZoomManager(self)
        
        # 줌 컨트롤 섹션
        zoom_frame = ttk.LabelFrame(left_panel, text='줌 컨트롤', padding=8)
        zoom_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 줌 컨트롤 UI 생성
        self.zoom_manager.create_zoom_controls(zoom_frame)

        # 데이터 커서 섹션
        cursor_frame = ttk.LabelFrame(left_panel, text='데이터 커서(Data Cursor)', padding=8)
        cursor_frame.pack(fill=tk.X, pady=(0, 8))
        
        cursor_top = ttk.Frame(cursor_frame)
        cursor_top.pack(fill=tk.X)
        
        ttk.Checkbutton(cursor_top, text='데이터 커서 활성화', variable=self.data_cursor_active).pack(side=tk.LEFT)
        ttk.Checkbutton(cursor_top, text='자유형 커서(Freeform)', variable=self.freeform_cursor).pack(side=tk.LEFT, padx=(10, 0))
        
        # 데이터 표시 레이블
        self.cursor_label = ttk.Label(cursor_frame, textvariable=self.data_cursor_text, 
                                     justify=tk.LEFT, background='#f0f0f0', padding=5,
                                     font=('Consolas', 10))
        self.cursor_label.pack(fill=tk.X, pady=(5, 0))

        # 통계 컨트롤 섹션
        stats_frame_container = ttk.Frame(left_panel)
        stats_frame_container.pack(fill=tk.X, pady=(0, 8))
        
        # 통계 매니저 초기화 및 UI 생성
        self.stats_manager = StatisticsManager(self)
        self.stats_manager.create_ui(stats_frame_container)

        # 플롯 컨트롤 섹션
        plot_controls = ttk.Frame(left_panel)
        plot_controls.pack(fill=tk.X)

        ttk.Button(plot_controls, text='이미지 저장', command=self.on_save).pack(side=tk.LEFT)

    def _evaluate_formulas_in_dataframes(self):
        """DataFrame의 수식들을 평가 (비활성화)"""
        # 수식 처리 기능 비활성화
        pass

    def _refresh_sheets(self) -> None:
        sheets = list(self.df_map.keys())
        print(f"시트 새로고침 - 사용 가능한 시트: {sheets}")
        self.sheet_combo['values'] = sheets
        if sheets:
            self.sheet_combo.set(sheets[0])
            print(f"시트 선택: {sheets[0]}")
            self._refresh_columns()
            self._refresh_data_table()
        else:
            print("사용 가능한 시트가 없음")

    def _refresh_columns(self) -> None:
        sheet = self.sheet_combo.get()
        print(f"컬럼 새로고침 - 시트: {sheet}")
        print(f"df_map 키들: {list(self.df_map.keys())}")
        if not sheet:
            print("시트가 선택되지 않음")
            return
        df = self.df_map.get(sheet)
        if df is None:
            print(f"시트 '{sheet}'의 DataFrame이 없음")
            return
        print(f"DataFrame 타입: {type(df)}")
        print(f"DataFrame 크기: {df.shape if hasattr(df, 'shape') else 'shape 속성 없음'}")
        print(f"DataFrame 컬럼 타입: {type(df.columns)}")
        print(f"DataFrame 컬럼: {df.columns}")
        cols = list(df.columns.astype(str))
        print(f"컬럼 목록 (문자열 변환 후): {cols}")
        print(f"x_combo 위젯: {self.x_combo}")
        print(f"y_listbox 위젯: {self.y_listbox}")
        
        # 기존 선택 보존
        prev_x: str = self.x_combo.get() if hasattr(self, 'x_combo') else ''
        prev_y_selected_names: list[str] = []
        try:
            prev_y_indices = self.y_listbox.curselection()
            prev_y_selected_names = [self.y_listbox.get(i) for i in prev_y_indices]
        except Exception:
            prev_y_selected_names = []

        # 콤보/리스트 갱신
        self.x_combo['values'] = cols
        self.y_listbox.delete(0, tk.END)
        for c in cols:
            self.y_listbox.insert(tk.END, c)

        # X 선택 복원 (없으면 첫 컬럼)
        if cols:
            if prev_x in cols:
                self.x_combo.set(prev_x)
                print(f"X 컬럼 유지: {prev_x}")
            else:
                self.x_combo.set(cols[0])
                print(f"X 컬럼 기본 설정: {cols[0]}")
            # X 컬럼 설정 후 자동으로 축 타입 결정
            self._on_x_column_changed()

        # Y 선택 복원
        if prev_y_selected_names:
            names_set = set(prev_y_selected_names)
            for idx, name in enumerate(cols):
                if name in names_set:
                    try:
                        self.y_listbox.select_set(idx)
                    except Exception:
                        pass
        
        # 데이터 편집기 창이 열려있으면 새로고침 (사용하지 않음)
        pass

    def _refresh_data_from_editor(self) -> None:
        """편집기에서 데이터 새로고침 (사용하지 않음)"""
        pass

    def _open_data_editor(self) -> None:
        """데이터 편집기 창 열기 (사용하지 않음)"""
        pass

    def _load_data_from_excel(self) -> Optional[pd.DataFrame]:
        """Excel에서 데이터 로드"""
        return self.excel_integration.load_data_from_excel()

    def _connect_to_excel(self) -> None:
        """Excel에 연결"""
        try:
            # 파일 선택 대화상자
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ('Excel files', '*.xlsx *.xls'),
                    ('All files', '*.*'),
                ],
                title="Excel 파일 선택 (새 파일을 만들려면 취소)"
            )
            
            if self.excel_integration.connect_to_excel(file_path if file_path else None):
                messagebox.showinfo('성공', 'Excel에 연결되었습니다.')
                # 연결 상태 표시
                status = self.excel_integration.get_status()
                print(f"Excel 연결 상태: {status}")
                
                # 자동으로 데이터 로드
                self._load_from_excel_auto()
            else:
                messagebox.showerror('오류', 'Excel 연결에 실패했습니다.')
                
        except Exception as e:
            messagebox.showerror('오류', f'Excel 연결 중 오류가 발생했습니다: {e}')

    def _load_from_excel_auto(self) -> None:
        """Excel에서 데이터 자동 로드 (메시지 박스 없음)"""
        if not self.excel_integration.is_connected:
            print("Excel이 연결되지 않음")
            return
            
        try:
            df = self.excel_integration.load_data_from_excel()
            print(f"Excel에서 로드된 DataFrame: {df is not None and not df.empty}")
            if df is not None and not df.empty:
                # 현재 시트 이름 가져오기
                sheet_name = self.excel_integration.worksheet.name if self.excel_integration.worksheet else 'Excel'
                print(f"시트 이름: {sheet_name}")
                print(f"DataFrame 크기: {len(df)}행 x {len(df.columns)}열")
                print(f"컬럼 이름: {list(df.columns)}")
                
                # DataFrame 저장
                self.df_map[sheet_name] = df
                self.current_file = f"Excel: {sheet_name}"
                
                # UI 새로고침
                print("UI 새로고침 시작")
                self._refresh_sheets()
                
                # 자동 새로고침 시작 (5초마다)
                self._start_auto_refresh()
                
                print(f"Excel에서 데이터를 자동 로드했습니다. 행: {len(df)}, 열: {len(df.columns)}")
            else:
                print("Excel에서 로드할 데이터가 없습니다.")
                
        except Exception as e:
            print(f"Excel 데이터 자동 로드 중 오류: {e}")

    def _load_from_excel(self) -> None:
        """Excel에서 데이터 로드"""
        if not self.excel_integration.is_connected:
            messagebox.showwarning('경고', '먼저 Excel에 연결하세요.')
            return
            
        try:
            df = self.excel_integration.load_data_from_excel()
            if df is not None and not df.empty:
                # 현재 시트 이름 가져오기
                sheet_name = self.excel_integration.worksheet.name if self.excel_integration.worksheet else 'Excel'
                
                # DataFrame 저장
                self.df_map[sheet_name] = df
                self.current_file = f"Excel: {sheet_name}"
                
                # UI 새로고침
                self._refresh_sheets()
                
                messagebox.showinfo('성공', f'Excel에서 데이터를 로드했습니다.\n행: {len(df)}, 열: {len(df.columns)}')
            else:
                messagebox.showwarning('경고', 'Excel에서 로드할 데이터가 없습니다.')
                
        except Exception as e:
            messagebox.showerror('오류', f'Excel 데이터 로드 중 오류가 발생했습니다: {e}')

    def _save_to_excel(self) -> None:
        """Excel에 데이터 저장"""
        if not self.excel_integration.is_connected:
            messagebox.showwarning('경고', '먼저 Excel에 연결하세요.')
            return
            
        sheet = self.sheet_combo.get()
        if not sheet or sheet not in self.df_map:
            messagebox.showwarning('경고', '저장할 데이터가 없습니다.')
            return
            
        try:
            df = self.df_map[sheet]
            
            if self.excel_integration.save_data_to_excel(df):
                messagebox.showinfo('성공', f'Excel에 데이터를 저장했습니다.\n행: {len(df)}, 열: {len(df.columns)}')
            else:
                messagebox.showerror('오류', 'Excel 데이터 저장에 실패했습니다.')
                
        except Exception as e:
            messagebox.showerror('오류', f'Excel 데이터 저장 중 오류가 발생했습니다: {e}')

    def _disconnect_excel(self) -> None:
        """Excel 연결 해제"""
        try:
            # 자동 새로고침 중지
            self._stop_auto_refresh()
            # Excel 연결 해제
            self.excel_integration.disconnect()
            messagebox.showinfo('성공', 'Excel 연결이 해제되었습니다.')
        except Exception as e:
            messagebox.showerror('오류', f'Excel 연결 해제 중 오류가 발생했습니다: {e}')

    def _start_auto_refresh(self) -> None:
        """자동 새로고침 시작 (5초마다)"""
        self._stop_auto_refresh()  # 기존 타이머가 있으면 중지
        self.auto_refresh_job = self.root.after(5000, self._auto_refresh_excel_data)
    
    def _stop_auto_refresh(self) -> None:
        """자동 새로고침 중지"""
        if self.auto_refresh_job:
            self.root.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
    
    def _auto_refresh_excel_data(self) -> None:
        """자동으로 Excel 데이터 새로고침"""
        if not self.excel_integration.is_connected:
            return
            
        try:
            df = self.excel_integration.load_data_from_excel()
            if df is not None and not df.empty:
                sheet_name = self.excel_integration.worksheet.name if self.excel_integration.worksheet else 'Excel'
                
                # 기존 데이터와 비교
                old_df = self.df_map.get(sheet_name)
                if old_df is None or not old_df.equals(df):
                    # 데이터가 변경되었으면 업데이트
                    self.df_map[sheet_name] = df
                    
                    # 현재 시트가 변경된 시트라면 UI 새로고침
                    if self.sheet_combo.get() == sheet_name:
                        self._refresh_columns()
                        self._refresh_data_table()
                        print(f"자동 새로고침: Excel 데이터 변경 감지 - {len(df)}행 x {len(df.columns)}열")
            
            # 다음 자동 새로고침 예약
            self.auto_refresh_job = self.root.after(5000, self._auto_refresh_excel_data)
            
        except Exception as e:
            print(f"자동 새로고침 오류: {e}")
            # 오류가 발생해도 다음 새로고침은 계속 시도
            self.auto_refresh_job = self.root.after(5000, self._auto_refresh_excel_data)

    def _on_excel_data_changed(self, df: pd.DataFrame) -> None:
        """Excel 데이터 변경 시 콜백 (비활성화)"""
        # 실시간 모니터링 비활성화 - 수동 새로고침 사용
        pass
    
    def _on_plot_double_click(self, event):
        """그래프 더블클릭 이벤트 핸들러"""
        # 줌 모드가 활성화되어 있으면 더블클릭 무시
        if self.zoom_manager.zoom_mode.get():
            return
            
        import time
        current_time = time.time()
        
        # 더블클릭 감지 (0.5초 이내)
        if current_time - self._last_click_time < 0.5:
            # 그래프 설정 창 열기
            try:
                PlotSettingsWindow(self.root, self)
            except Exception as e:
                messagebox.showerror('오류', f'그래프 설정 창을 열 수 없습니다: {e}')
        
        self._last_click_time = current_time
    
    
    def apply_plot_settings(self, settings: dict) -> None:
        """그래프 설정 적용"""
        try:
            # 기본 데이터 검증
            sheet = self.sheet_combo.get()
            if not sheet:
                messagebox.showwarning('경고', '시트를 선택하세요.')
                return
            df = self.df_map.get(sheet)
            if df is None or df.empty:
                messagebox.showwarning('경고', '데이터가 없습니다.')
                return
            x_col = self.x_combo.get()

            # Error Bar 모드 확인
            if settings.get('plot_mode') == 'errorbar':
                self._apply_error_bar_plot(df, x_col, settings)
                return

            # Double Y축 활성화 여부 확인 (설정 딕셔너리 기준)
            double_y_active = settings.get('use_double_y', False)

            # Y 컬럼 결정
            if double_y_active:
                left_cols = settings.get('left_y_columns', [])
                right_cols = settings.get('right_y_columns', [])
                y_cols = list(set(left_cols + right_cols))
            else:
                y_indices = self.y_listbox.curselection()
                if not y_indices:
                    messagebox.showwarning('경고', 'Y 컬럼을 하나 이상 선택하세요.')
                    return
                y_cols = [self.y_listbox.get(i) for i in y_indices]

            if not y_cols:
                messagebox.showwarning('경고', '선택된 Y 컬럼이 없습니다.')
                return

            # 데이터 변환 적용
            x, ymap = self._apply_transforms(df, x_col, y_cols)
            
            # 스타일 적용
            styles = self._collect_styles()
            try:
                if styles:
                    plt.style.use(styles)
            except Exception as e:
                print(f"스타일 적용 오류 (기본 스타일 사용): {e}")
                plt.style.use('default')

            # 색상 사이클 설정
            if self.style_bright.get():
                plt.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=['#4477AA', '#EE6677', '#228833', '#CCBB44', '#66CCEE', '#AA3377', '#BBBBBB'])

            # 기존 플롯 클리어
            self.ax.clear()
            self.hover_anno = None
            self.hover_line = None
            
            # Double Y축/Single Y축 분기 처리
            if double_y_active:
                # ax2 생성 또는 클리어
                if self.ax2 is None:
                    self.ax2 = self.ax.twinx()
                else:
                    self.ax2.clear()
                # 축 스케일 적용 (Linear/Log)
                self.ax.set_xscale(settings.get('x_scale', 'linear'))
                self.ax.set_yscale(settings.get('left_y_scale', 'linear'))
                if hasattr(self, 'ax2') and self.ax2:
                    self.ax2.set_yscale(settings.get('right_y_scale', 'linear'))
                
                # 데이터 플롯
                # 왼쪽 Y축 플롯
                for name in left_cols:
                    if name in ymap:
                        self._plot_series_on_axis(self.ax, x, ymap[name], name, settings)
                
                # 오른쪽 Y축 플롯
                for name in right_cols:
                    if name in ymap:
                        self._plot_series_on_axis(self.ax2, x, ymap[name], name, settings)
                
                # Z-Order logic
                y_zorders = settings.get('y_zorders', {})
                left_z = [y_zorders.get(c, 2) for c in left_cols if c in y_zorders]
                right_z = [y_zorders.get(c, 2) for c in right_cols if c in y_zorders]
                
                # Default to 2 if no columns/zorders found
                max_left = max(left_z) if left_z else 2
                max_right = max(right_z) if right_z else 2
                
                # 시리즈의 Z-order 최대값에 따라 축 자체의 Z-order를 결정
                # 이렇게 해야 서로 다른 축에 있는 데이터들 간의 우선순위가 지켜짐
                if max_left > max_right:
                    self.ax.set_zorder(2)
                    self.ax2.set_zorder(1)
                else:
                    self.ax.set_zorder(1)
                    self.ax2.set_zorder(2)
                
                # 두 축 모두 배경 투명하게 설정
                self.ax.patch.set_visible(False)
                self.ax2.patch.set_visible(False)

                # 한쪽 축이 다른 쪽 축의 색상 라인을 가리지 않도록 redundant spine은 숨김
                self.ax.spines['right'].set_visible(False)
                self.ax2.spines['left'].set_visible(False)

                # Grid 설정 (왼쪽 축 기준)
                if settings.get('grid', True):
                    self.ax.grid(True)
                else:
                    self.ax.grid(False)
                    self.ax2.grid(False)

                # 라벨 및 색상 설정
                left_color = settings.get('left_axis_color', '#000000')
                right_color = settings.get('right_axis_color', '#000000')

                # 왼쪽 Y축 스타일 적용
                if settings.get('left_ylabel'):
                    self.ax.set_ylabel(settings['left_ylabel'], fontsize=settings.get('label_fontsize', 16), color=left_color)
                
                self.ax.tick_params(axis='y', colors=left_color, labelsize=settings.get('tick_fontsize', 12))
                self.ax.spines['left'].set_color(left_color)
                
                # 왼쪽 축 위치 강제 설정
                self.ax.yaxis.set_label_position("left")
                self.ax.yaxis.set_ticks_position("left")
                
                # 오른쪽 Y축 스타일 적용
                if settings.get('right_ylabel'):
                    self.ax2.set_ylabel(settings['right_ylabel'], fontsize=settings.get('label_fontsize', 16), color=right_color)
                
                self.ax2.tick_params(axis='y', colors=right_color, labelsize=settings.get('tick_fontsize', 12))
                self.ax2.spines['right'].set_color(right_color)
                self.ax2.spines['right'].set_visible(True)
                self.ax2.spines['left'].set_visible(False)
                
                # 오른쪽 축 위치 강제 설정
                self.ax2.yaxis.set_label_position("right")
                self.ax2.yaxis.set_ticks_position("right")
                
                # Y축 범위 설정
                try:
                    self.ax.set_ylim(float(settings.get('left_ylim_min', 0)), float(settings.get('left_ylim_max', 10)))
                    self.ax2.set_ylim(float(settings.get('right_ylim_min', 0)), float(settings.get('right_ylim_max', 10)))
                except Exception as e:
                    print(f"Y축 범위 설정 오류: {e}")

                # Y축 틱 설정
                self._set_axis_ticks(self.ax, settings.get('left_ylim_min', 0), settings.get('left_ylim_max', 10), settings.get('left_y_ticks', 1))
                self._set_axis_ticks(self.ax2, settings.get('right_ylim_min', 0), settings.get('right_ylim_max', 10), settings.get('right_y_ticks', 1))

            else:
                # Single Y Mode
                # ax2 제거
                if self.ax2 is not None:
                    try:
                        self.ax2.clear()
                        self.ax2.remove()
                    except: pass
                    self.ax2 = None

                while len(self.figure.axes) > 1:
                    try: self.figure.axes[-1].remove()
                    except: break

                # Single Y축 모드: 오른쪽 spine 완전히 닫기
                self.ax.spines['right'].set_visible(True)
                self.ax.spines['right'].set_color('black')
                self.ax.spines['top'].set_visible(True)
                self.ax.spines['top'].set_color('black')
                self.ax.spines['left'].set_visible(True)
                self.ax.spines['left'].set_color('black')
                self.ax.spines['bottom'].set_visible(True)
                self.ax.spines['bottom'].set_color('black')

                # 배경 불투명하게 설정
                self.ax.patch.set_visible(True)
                self.ax.patch.set_facecolor('white')

                # z-order 기본값으로 설정
                self.ax.set_zorder(1)

                # 축 스케일 적용 (Linear/Log)
                self.ax.set_xscale(settings.get('x_scale', 'linear'))
                self.ax.set_yscale(settings.get('y_scale', 'linear'))

                # 일반 플롯 그리기
                for name, series in ymap.items():
                    self._plot_series_on_axis(self.ax, x, series, name, settings)

                # 라벨/타이틀 설정
                if settings.get('ylabel'):
                    self.ax.set_ylabel(settings['ylabel'], fontsize=settings.get('ylabel_fontsize', 16))
                else:
                    if len(y_cols) == 1:
                        self.ax.set_ylabel(y_cols[0], fontsize=settings.get('ylabel_fontsize', 16))
                    else:
                        self.ax.set_ylabel('Values', fontsize=settings.get('ylabel_fontsize', 16))

                # Y축 범위 및 틱
                try:
                     self.ax.set_ylim(float(settings.get('ylim_min', 0)), float(settings.get('ylim_max', 10)))
                except: pass
                self._set_axis_ticks(self.ax, settings.get('ylim_min', 0), settings.get('ylim_max', 10), settings.get('y_ticks', 1))

                self.ax.tick_params(axis='y', labelsize=settings.get('y_tick_fontsize', 12))
                self.ax.grid(False)

            # 공통 X축 설정
            title = settings.get('title', '')
            if title:
                self.ax.set_title(title, fontsize=settings.get('title_fontsize', 14) if not double_y_active else settings.get('title_fontsize', 14))
            else:
                self.ax.set_title('Excel Plotter')

            # X축 라벨
            xlabel = settings.get('xlabel', '')
            if xlabel:
                self.ax.set_xlabel(xlabel, fontsize=settings.get('xlabel_fontsize', 16) if not double_y_active else settings.get('label_fontsize', 16))
            else:
                 if not double_y_active:
                     self.ax.set_xlabel(x_col, fontsize=settings.get('xlabel_fontsize', 16))
                 else:
                     self.ax.set_xlabel(x_col, fontsize=settings.get('label_fontsize', 16))

            # X축 틱 및 범위 처리
            axis_type = self.axis_type_var.get()
            if axis_type == 'datetime':
                try:
                    import matplotlib.dates as mdates
                    time_format = settings.get('time_format', '%H:%M:%S.%f') if not double_y_active else settings.get('time_format', '%Y-%m-%d %H:%M')
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter(time_format))
                    
                    if not double_y_active:
                         interval_unit = settings.get('time_interval_unit', 'minutes')
                         interval_value = settings.get('time_interval_value', 1)
                         if interval_unit == 'seconds': locator = mdates.SecondLocator(interval=interval_value)
                         elif interval_unit == 'minutes': locator = mdates.MinuteLocator(interval=interval_value)
                         elif interval_unit == 'hours': locator = mdates.HourLocator(interval=interval_value)
                         elif interval_unit == 'days': locator = mdates.DayLocator(interval=interval_value)
                         else: locator = mdates.MinuteLocator(interval=interval_value)
                         self.ax.xaxis.set_major_locator(locator)
                    
                    # 범위 설정
                    if 'xlim_min' in settings and 'xlim_max' in settings:
                         xlim_min = pd.to_datetime(settings['xlim_min'])
                         xlim_max = pd.to_datetime(settings['xlim_max'])
                         self.ax.set_xlim(mdates.date2num(xlim_min), mdates.date2num(xlim_max))
                    
                    plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                except Exception as e:
                    print(f"Time axis error: {e}")
            else:
                # Numeric X
                try:
                    if 'xlim_min' in settings and 'xlim_max' in settings:
                        self.ax.set_xlim(float(settings['xlim_min']), float(settings['xlim_max']))
                    self._set_axis_ticks(self.ax, settings.get('xlim_min', 0), settings.get('xlim_max', 10), settings.get('x_ticks', 1), is_x=True)
                except Exception as e:
                    print(f"Numeric axis error: {e}")

            self.ax.tick_params(axis='x', labelsize=settings.get('x_tick_fontsize', 12) if not double_y_active else settings.get('tick_fontsize', 12))

            # 범례
            if double_y_active:
                # 합친 범례
                lines, labels = self.ax.get_legend_handles_labels()
                lines2, labels2 = self.ax2.get_legend_handles_labels()
                if lines + lines2:
                    self.ax.legend(lines + lines2, labels + labels2, loc=settings.get('legend_loc', 'upper right'))
            else:
                 # Single Y축 범례 - 항상 loc 적용
                 if len(ymap) >= 1:
                      self.ax.legend(loc=settings.get('legend_loc', 'upper right'))
                 else:
                      # 핸들/라벨이 없을 수 있으므로 안전하게 제거 또는 빈 범례
                      if self.ax.get_legend():
                          self.ax.get_legend().remove()

            # 현재 설정 저장
            self.current_plot_settings = settings.copy()
            
            # 레이아웃 조정 (라벨 겹침 방지)
            self.figure.tight_layout()
            
            self.plot_canvas.draw()
            
        except Exception as e:
            messagebox.showerror('오류', f'그래프 설정 적용 중 오류가 발생했습니다: {e}')
            print(f"상세 오류: {e}")
            import traceback
            traceback.print_exc()

    def _plot_series_on_axis(self, target_ax, x, series, name, settings):
        """특정 축에 시리즈 플롯"""
        # 안전한 값 가져오기 (기본값 제공)
        color = settings.get('y_colors', {}).get(name, settings.get('color', '#000000'))
        line_width = settings.get('y_line_widths', {}).get(name, settings.get('line_width', 1.5))
        line_style = settings.get('y_line_styles', {}).get(name, settings.get('line_style', '-'))
        marker = settings.get('y_markers', {}).get(name, settings.get('marker', 'o'))
        marker_size = settings.get('y_marker_sizes', {}).get(name, settings.get('marker_size', 6))
        plot_type = settings.get('y_plot_types', {}).get(name, settings.get('plot_type', 'line'))
        alpha = float(settings.get('y_alphas', {}).get(name, 1.0))
        zorder = int(settings.get('y_zorders', {}).get(name, 2))

        if plot_type == 'line':
            target_ax.plot(x, series, label=name, linestyle=line_style, color=color, linewidth=line_width, alpha=alpha, zorder=zorder)
        elif plot_type == 'scatter':
            target_ax.scatter(x, series, label=name, marker=marker, color=color, s=marker_size**2, alpha=alpha, zorder=zorder)
        else:
            target_ax.plot(x, series, label=name, linestyle=line_style, color=color, linewidth=line_width, marker=marker, markersize=marker_size, alpha=alpha, zorder=zorder)

    def _set_axis_ticks(self, target_ax, min_val, max_val, tick_val, is_x=False):
        """축 틱 설정"""
        try:
            start = float(min_val)
            end = float(max_val)
            step = max(1e-12, float(tick_val))
            ticks = np.arange(start, end + step/100, step) # include end roughly

            # 너무 많은 틱 방지
            if len(ticks) > 100:
                return

            if is_x:
                target_ax.set_xticks(ticks)
            else:
                target_ax.set_yticks(ticks)
        except:
            pass

    def _apply_error_bar_plot(self, df: pd.DataFrame, x_col: str, settings: dict) -> None:
        """Error Bar 플롯 적용"""
        try:
            # SciencePlots 스타일 적용
            try:
                import scienceplots
                plt.style.use(['science', 'no-latex'])
                print("SciencePlots 스타일 적용됨")
            except ImportError:
                print("scienceplots 라이브러리가 설치되지 않았습니다. 기본 스타일 사용.")
            except Exception as e:
                print(f"SciencePlots 스타일 적용 오류: {e}")

            # 기존 플롯 클리어
            self.ax.clear()
            self.hover_anno = None
            self.hover_line = None

            # ax2가 있으면 제거
            if self.ax2 is not None:
                try:
                    self.ax2.clear()
                    self.ax2.remove()
                except: pass
                self.ax2 = None

            while len(self.figure.axes) > 1:
                try: self.figure.axes[-1].remove()
                except: break

            # X 데이터 가져오기
            x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()

            # 데이터 모드에 따른 처리
            data_mode = settings.get('data_mode', 'repeated')

            if data_mode == 'repeated':
                # 반복 측정 모드: 여러 Y 컬럼의 평균/표준편차 계산
                y_columns = settings.get('y_columns', [])
                if not y_columns:
                    messagebox.showwarning('경고', 'Y 컬럼을 선택하세요.')
                    return

                # 각 행에서 선택된 컬럼들의 평균과 표준편차 계산
                y_data = df[y_columns].apply(pd.to_numeric, errors='coerce')
                y_mean = y_data.mean(axis=1)
                y_std = y_data.std(axis=1)

                # NaN 제거 (x, y_mean, y_std 모두 유효한 행만)
                valid_mask = ~(x_data.isna() | y_mean.isna() | y_std.isna())
                # 인덱스 정렬
                common_index = x_data.index.intersection(y_mean.index).intersection(y_std.index)
                valid_mask = valid_mask.reindex(common_index, fill_value=False)

                x_plot = x_data.reindex(common_index)[valid_mask].values
                y_mean_plot = y_mean.reindex(common_index)[valid_mask].values
                y_std_plot = y_std.reindex(common_index)[valid_mask].values

                label = f'Mean of {len(y_columns)} columns'

            else:
                # 미리 계산된 모드: Y 평균과 Y 에러 컬럼 사용
                y_mean_col = settings.get('y_mean_column', '')
                y_error_col = settings.get('y_error_column', '')

                if not y_mean_col:
                    messagebox.showwarning('경고', 'Y 평균 컬럼을 선택하세요.')
                    return

                y_mean = pd.to_numeric(df[y_mean_col], errors='coerce')

                if y_error_col and y_error_col in df.columns:
                    y_std = pd.to_numeric(df[y_error_col], errors='coerce')
                else:
                    y_std = pd.Series([0] * len(y_mean), index=y_mean.index)

                # NaN 제거
                valid_mask = ~(x_data.isna() | y_mean.isna())
                common_index = x_data.index.intersection(y_mean.index)
                valid_mask = valid_mask.reindex(common_index, fill_value=False)

                x_plot = x_data.reindex(common_index)[valid_mask].values
                y_mean_plot = y_mean.reindex(common_index)[valid_mask].values
                y_std_plot = y_std.reindex(common_index)[valid_mask].fillna(0).values

                label = y_mean_col

            # 스타일 설정 가져오기
            color = settings.get('color', '#2E86AB')
            ecolor = settings.get('ecolor', '#2E86AB')
            capsize = settings.get('capsize', 5.0)
            capthick = settings.get('capthick', 2.0)
            line_width = settings.get('line_width', 2.0)
            marker = settings.get('marker', 'o')
            marker_size = settings.get('marker_size', 8.0)

            # 마커가 'None'이면 실제로 None으로 변환
            if marker == 'None':
                marker = None

            # Error Bar 플롯
            fmt = f'{marker}-' if marker else '-'
            self.ax.errorbar(
                x_plot, y_mean_plot, yerr=y_std_plot,
                fmt=fmt, capsize=capsize, capthick=capthick,
                markersize=marker_size, color=color, ecolor=ecolor,
                linewidth=line_width, label=label
            )

            # SciencePlots 스타일 수동 적용 - 그리드 없음 (기본값)
            self.ax.grid(False)

            # Spine 설정 - SciencePlots 스타일 (모든 4면 표시)
            for spine in ['right', 'top', 'left', 'bottom']:
                self.ax.spines[spine].set_visible(True)
                self.ax.spines[spine].set_color('black')
                self.ax.spines[spine].set_linewidth(0.5)

            self.ax.patch.set_visible(True)
            self.ax.patch.set_facecolor('white')

            # SciencePlots 스타일 - 틱 설정 (안쪽 방향, 모든 4면)
            self.ax.tick_params(
                axis='both',
                which='both',
                direction='in',
                top=True,
                right=True,
                bottom=True,
                left=True
            )

            # 제목 - SciencePlots 스타일 폰트
            title = settings.get('title', '')
            if title:
                self.ax.set_title(title, fontsize=settings.get('title_fontsize', 14), fontweight='bold')
            else:
                self.ax.set_title('Error Bar Plot', fontweight='bold')

            # X축 라벨 - SciencePlots 스타일 폰트
            xlabel = settings.get('xlabel', '')
            if xlabel:
                self.ax.set_xlabel(xlabel, fontsize=settings.get('xlabel_fontsize', 12), fontweight='bold')
            else:
                self.ax.set_xlabel(x_col, fontsize=settings.get('xlabel_fontsize', 12), fontweight='bold')

            # Y축 라벨 - SciencePlots 스타일 폰트
            ylabel = settings.get('ylabel', '')
            if ylabel:
                self.ax.set_ylabel(ylabel, fontsize=settings.get('ylabel_fontsize', 12), fontweight='bold')
            else:
                self.ax.set_ylabel('Value', fontsize=settings.get('ylabel_fontsize', 12), fontweight='bold')

            # 축 범위 설정
            try:
                self.ax.set_xlim(float(settings.get('xlim_min', x_plot.min())),
                                float(settings.get('xlim_max', x_plot.max())))
                self.ax.set_ylim(float(settings.get('ylim_min', (y_mean_plot - y_std_plot).min())),
                                float(settings.get('ylim_max', (y_mean_plot + y_std_plot).max())))
            except Exception as e:
                print(f"축 범위 설정 오류: {e}")

            # 축 틱 설정
            self._set_axis_ticks(self.ax, settings.get('xlim_min', 0), settings.get('xlim_max', 10),
                               settings.get('x_ticks', 1), is_x=True)
            self._set_axis_ticks(self.ax, settings.get('ylim_min', 0), settings.get('ylim_max', 10),
                               settings.get('y_ticks', 1), is_x=False)

            # 틱 폰트 크기 - SciencePlots 스타일 유지 (direction='in')
            self.ax.tick_params(axis='x', labelsize=settings.get('x_tick_fontsize', 12), direction='in')
            self.ax.tick_params(axis='y', labelsize=settings.get('y_tick_fontsize', 12), direction='in')

            # 범례 - SciencePlots 스타일 (테두리, 그림자)
            self.ax.legend(loc=settings.get('legend_loc', 'best'), frameon=True, fancybox=True, shadow=True)

            # 현재 설정 저장
            self.current_plot_settings = settings.copy()

            # 레이아웃 조정
            self.figure.tight_layout()
            self.plot_canvas.draw()

        except Exception as e:
            messagebox.showerror('오류', f'Error Bar 플롯 중 오류가 발생했습니다: {e}')
            print(f"Error Bar 플롯 오류: {e}")
            import traceback
            traceback.print_exc()

    def _update_ui_from_excel(self, df: pd.DataFrame) -> None:
        """Excel에서 받은 데이터로 UI 업데이트 (비활성화)"""
        # 실시간 모니터링 비활성화 - 수동 새로고침 사용
        pass

    def _check_datetime_column(self) -> None:
        """선택된 X 컬럼이 시간 데이터인지 확인하고 상태 표시"""
        sheet = self.sheet_combo.get()
        x_col = self.x_combo.get()
        
        if not sheet or not x_col or sheet not in self.df_map:
            self.datetime_status_var.set('')
            return
            
        df = self.df_map[sheet]
        if self._detect_datetime_column(df, x_col):
            self.datetime_status_var.set('✓ 시간 데이터 감지됨')
            self.datetime_status_label.configure(foreground='green')
        else:
            self.datetime_status_var.set('')
            self.datetime_status_label.configure(foreground='blue')

    def _on_x_column_changed(self) -> None:
        """X 컬럼 변경 시 호출되는 함수"""
        x_col = self.x_combo.get()
        sheet = self.sheet_combo.get()
        
        if not x_col or not sheet or sheet not in self.df_map:
            return
            
        df = self.df_map[sheet]
        
        # X 컬럼 이름에 따라 축 타입 자동 결정
        if self._is_timestamp_column_name(x_col):
            # Timestamp 관련 컬럼명이면 시간축으로 설정
            self.axis_type_var.set('datetime')
            self.datetime_status_var.set('✓ 시간축 모드 (Timestamp 컬럼 감지)')
            self.datetime_status_label.configure(foreground='green')
            print(f"X 컬럼 '{x_col}': 시간축 모드로 자동 설정")
        else:
            # 그 외에는 숫자축으로 설정
            self.axis_type_var.set('numeric')
            self.datetime_status_var.set('✓ 숫자축 모드')
            self.datetime_status_label.configure(foreground='blue')
            print(f"X 컬럼 '{x_col}': 숫자축 모드로 자동 설정")
        
        # 자동 새로고침 실행
        self._schedule_auto_refresh()
    
    def _is_timestamp_column_name(self, column_name: str) -> bool:
        """컬럼 이름이 시간 관련인지 확인 ('datetime' 포함 여부만)"""
        time_keywords = ['datetime']
        column_lower = column_name.lower()
        return any(keyword in column_lower for keyword in time_keywords)

    def _check_datetime_column_and_refresh(self) -> None:
        """시간 데이터 감지 후 자동 새로고침"""
        self._check_datetime_column()
        self._schedule_auto_refresh()
    


    def _collect_styles(self) -> list[str]:
        styles: list[str] = []
        if self.style_science.get():
            styles.append('science')
        if self.style_ieee.get():
            styles.append('ieee')
        if self.style_notebook.get():
            styles.append('notebook')
        if self.style_no_latex.get():
            styles.append('no-latex')
        
        # LaTeX 오류 방지를 위해 no-latex가 없으면 추가
        if styles and 'no-latex' not in styles:
            styles.append('no-latex')
        elif not styles:
            styles = ['no-latex']  # 기본 스타일
            
        return styles

    def _refresh_data_table(self) -> None:
        """데이터 테이블을 현재 선택된 시트의 데이터로 새로고침 (더 이상 사용하지 않음)"""
        pass

    def _save_data_changes(self) -> None:
        """데이터 변경사항을 저장"""
        try:
            sheet = self.sheet_combo.get()
            if sheet and sheet in self.df_map:
                # 현재 편집 중인 셀이 있으면 저장
                if self.editing_cell:
                    self._finish_cell_edit()
                
                # DataFrame 업데이트
                self.df_map[sheet] = self.current_df.copy()
                messagebox.showinfo('알림', '데이터 변경사항이 저장되었습니다.')
                self._schedule_auto_refresh()
        except Exception as e:
            messagebox.showerror('저장 오류', f'데이터 저장 중 오류가 발생했습니다: {e}')

    def _apply_transforms(self, df: pd.DataFrame, x_col: str, y_cols: list[str]) -> tuple[pd.Series, dict[str, pd.Series]]:
        work = df.copy()
        axis_type = self.axis_type_var.get()

        # 사용자가 선택한 축 타입에 따라 X 컬럼 처리
        if axis_type == 'datetime':
            # 시간축 모드: 시간 데이터로 변환
            print(f"시간축 모드로 처리: {x_col}")
            work[x_col] = self._parse_datetime_column(work, x_col)
        else:
            # 숫자축 모드: 숫자로 변환
            print(f"숫자축 모드로 처리: {x_col}")
            if x_col not in work.columns:
                raise ValueError(f'컬럼 없음: {x_col}')
            work[x_col] = pd.to_numeric(work[x_col], errors='coerce')

        # Y 컬럼들을 숫자로 변환
        for c in y_cols:
            if c not in work.columns:
                raise ValueError(f'컬럼 없음: {c}')
            work[c] = pd.to_numeric(work[c], errors='coerce')

        # X축에 유효한 값이 있는 행만 필터링 (X축 기준)
        x = work[x_col].dropna()
        
        # Y 컬럼들은 X축의 인덱스에 맞춰서 정렬 (매칭 안되는 부분은 NaN)
        ymap: dict[str, pd.Series] = {}
        for c in y_cols:
            # X축 인덱스에 맞춰서 Y 데이터 재정렬 (없는 인덱스는 NaN)
            ymap[c] = work[c].reindex(x.index)
        
        return x, ymap

    def on_plot(self) -> None:
        try:
            sheet = self.sheet_combo.get()
            if not sheet:
                messagebox.showwarning('경고', '시트를 선택하세요.')
                return
            df = self.df_map.get(sheet)
            if df is None or df.empty:
                messagebox.showwarning('경고', '데이터가 없습니다.')
                return
            x_col = self.x_combo.get()
            y_indices = self.y_listbox.curselection()
            if not y_indices:
                messagebox.showwarning('경고', 'Y 컬럼을 하나 이상 선택하세요.')
                return
            y_cols = [self.y_listbox.get(i) for i in y_indices]

            x, ymap = self._apply_transforms(df, x_col, y_cols)

            # 줌 상태 초기화 (새로운 플롯이므로)
            self.zoom_stack = []

            styles = self._collect_styles()
            try:
                if styles:
                    plt.style.use(styles)
            except Exception as e:
                print(f"스타일 적용 오류 (기본 스타일 사용): {e}")
                plt.style.use('default')

            # color cycle
            if self.style_bright.get():
                plt.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=['#4477AA', '#EE6677', '#228833', '#CCBB44', '#66CCEE', '#AA3377', '#BBBBBB'])

            # 기존 플롯 완전히 클리어
            self.ax.clear()
            self.hover_anno = None
            self.hover_line = None
            
            # 기존 오른쪽 Y축(ax2) 완전히 제거
            if hasattr(self, 'ax2') and self.ax2 is not None:
                try:
                    self.ax2.clear()
                    self.ax2.remove()
                except Exception as e:
                    print(f"ax2 제거 중 오류: {e}")
                self.ax2 = None
            
            # Figure의 모든 추가 axes 제거
            while len(self.figure.axes) > 1:
                try:
                    self.figure.axes[-1].remove()
                    print(f"추가 axes 제거됨, 남은 axes 수: {len(self.figure.axes)}")
                except Exception as e:
                    print(f"추가 axes 제거 중 오류: {e}")
                    break
            
            # 플롯 그리기
            for name, series in ymap.items():
                self.ax.plot(x, series, label=name, linewidth=2)
            
            # 선택된 축 타입에 따른 X축 처리
            axis_type = self.axis_type_var.get()
            if axis_type == 'datetime':
                self.ax.set_xlabel(f'{x_col}', fontsize=16)
                # 시간 축 포맷팅
                import matplotlib.dates as mdates
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(x)//10)))
                # X축 레이블 회전
                plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            else:
                self.ax.set_xlabel(x_col, fontsize=16)
            
            self.ax.set_ylabel(', '.join(y_cols), fontsize=16)
            self.ax.set_title(f'{sheet} - {x_col} vs {", ".join(y_cols)}', fontsize=14)
            self.ax.legend()
            self.ax.grid(False)

            # 레이아웃 조정
            self.figure.tight_layout()
            
            # Canvas 업데이트
            self.plot_canvas.draw()
            
        except Exception as exc:
            messagebox.showerror('플롯 오류', str(exc))

    def _on_mouse_move(self, event):
        """마우스 이동 시 데이터 표시 (Hover)"""
        if event.inaxes is None or not hasattr(self, 'ax') or self.ax is None:
            if self.hover_anno:
                self.hover_anno.set_visible(False)
            if self.hover_line:
                self.hover_line.set_visible(False)
            self.plot_canvas.draw_idle()
            return

        x_mouse = event.xdata
        
        # 1. 자유형 커서 (Freeform) 처리
        if self.freeform_cursor.get():
            target_x = x_mouse
            text_parts = ["[자유형 커서(Freeform)]"]
            
            # X값 포맷팅 (datetime 처리)
            if self.axis_type_var.get() == 'datetime':
                try:
                    import matplotlib.dates as mdates
                    dt_x = mdates.num2date(target_x)
                    text_parts.append(f"X: {dt_x.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    text_parts.append(f"X: {target_x:.4f}")
            else:
                text_parts.append(f"X: {target_x:.4f}")

            # Y값 (Left Axis) - 픽셀 좌표를 ax 데이터 좌표로 변환
            try:
                _, y_left = self.ax.transData.inverted().transform((event.x, event.y))
                text_parts.append(f"Left Y: {y_left:.4f}")
            except:
                # fallback: event.ydata 사용 (Single Y축인 경우)
                if event.ydata is not None:
                    text_parts.append(f"Left Y: {event.ydata:.4f}")

            # Y값 (Right Axis) - Double Y축인 경우만 표시
            if hasattr(self, 'ax2') and self.ax2 is not None:
                try:
                    # 픽셀 좌표를 ax2 데이터 좌표로 변환
                    _, y_right = self.ax2.transData.inverted().transform((event.x, event.y))
                    text_parts.append(f"Right Y: {y_right:.4f}")
                except Exception as e:
                    # 변환 실패 시 표시하지 않음
                    pass
            
            tooltip_text = "\n".join(text_parts)
            self._update_hover_display(target_x, event, tooltip_text, is_freeform=True)
            return

        # 2. 데이터 스냅 (Snap to Data) 처리
        # 모든 라인에서 X 데이터를 가져와 통합
        all_lines = self.ax.get_lines()
        if hasattr(self, 'ax2') and self.ax2:
            all_lines += self.ax2.get_lines()
            
        if not all_lines:
            return

        # 첫 번째 라인의 데이터를 기준으로 가장 가까운 인덱스 찾기
        line = all_lines[0]
        x_data = line.get_xdata()
        if len(x_data) == 0:
            return

        try:
            import numpy as np
            # x_data가 datetime인 경우 처리
            if isinstance(x_data[0], (pd.Timestamp, datetime)):
                import matplotlib.dates as mdates
                x_data_nums = mdates.date2num(x_data)
                idx = np.abs(x_data_nums - x_mouse).argmin()
            else:
                idx = np.abs(x_data - x_mouse).argmin()
            
            target_x = x_data[idx]
            
            # 툴팁 텍스트 구성
            text_parts = []
            
            # X값 포맷팅
            if isinstance(target_x, (pd.Timestamp, datetime)):
                text_parts.append(f"X: {target_x.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                text_parts.append(f"X: {target_x:.4f}")
            
            # Y값들 수집
            # 왼쪽 축 (ax)
            left_parts = []
            for l in self.ax.get_lines():
                y_d = l.get_ydata()
                if idx < len(y_d):
                    val = y_d[idx]
                    if not np.isnan(val):
                        left_parts.append(f"{l.get_label()}: {val:.4f}")
            
            if left_parts:
                text_parts.append("\n[Left Y]")
                text_parts.extend(left_parts)
                
            # 오른쪽 축 (ax2)
            if hasattr(self, 'ax2') and self.ax2:
                right_parts = []
                for l in self.ax2.get_lines():
                    y_d = l.get_ydata()
                    if idx < len(y_d):
                        val = y_d[idx]
                        if not np.isnan(val):
                            right_parts.append(f"{l.get_label()}: {val:.4f}")
                
                if right_parts:
                    text_parts.append("\n[Right Y]")
                    text_parts.extend(right_parts)

            tooltip_text = "\n".join(text_parts)
            self._update_hover_display(target_x, event, tooltip_text)

        except Exception as e:
            print(f"Hover error: {e}")

    def _update_hover_display(self, target_x, event, tooltip_text, is_freeform=False):
        """Hover 어노테이션 및 사이드바 텍스트 업데이트 내부 함수"""
        # 사이드바 텍스트 업데이트 및 표시 여부 결정
        is_active = self.data_cursor_active.get()
        if is_active:
            self.data_cursor_text.set(tooltip_text)
        else:
            self.data_cursor_text.set("데이터 커서 비활성")

        # 어노테이션 생성 또는 업데이트
        if self.hover_anno is None:
            self.hover_anno = self.ax.annotate(
                tooltip_text,
                xy=(event.x, event.y),
                xytext=(15, 15),
                xycoords='figure pixels',
                textcoords="offset points",
                bbox=dict(boxstyle="round", fc="#ffffe0", alpha=0.9, edgecolor="gray"), # 노란색 톤 박스
                fontsize=9,
                zorder=100
            )
        else:
            self.hover_anno.set_text(tooltip_text)
            self.hover_anno.xy = (event.x, event.y)
        
        # 전체 활성화 여부에 따라 가시성 제어
        self.hover_anno.set_visible(is_active)

        # 수직선 생성 또는 업데이트
        if self.hover_line is None:
            self.hover_line = self.ax.axvline(target_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5, zorder=1)
        else:
            self.hover_line.set_xdata([target_x, target_x])
            
        # 자유형 커서이거나 데이터 커서 비활성일 때는 수직선 숨기기
        if is_freeform or not is_active:
            self.hover_line.set_visible(False)
        else:
            self.hover_line.set_visible(True)

        self.plot_canvas.draw_idle()

    def on_save(self) -> None:
        """이미지 저장 - Plot Image 폴더에 자동으로 저장"""
        try:
            # 현재 플롯이 있는지 확인 (lines 또는 collections)
            has_lines = hasattr(self.ax, 'lines') and self.ax.lines
            has_collections = hasattr(self.ax, 'collections') and self.ax.collections
            
            if not has_lines and not has_collections:
                messagebox.showwarning('경고', '먼저 플롯을 그려주세요.')
                return
            
            # 이미지 저장 전 Hover 표시 숨기기
            if self.hover_anno:
                self.hover_anno.set_visible(False)
            if self.hover_line:
                self.hover_line.set_visible(False)
            self.plot_canvas.draw()
            
            # 현재 플롯의 제목 가져오기
            title = self.ax.get_title() if self.ax.get_title() else "Plot"
            
            # 이미지 저장 모듈을 사용하여 저장
            success = self.image_saver.save_plot_image(self.figure, title)
            
            if success:
                # 저장 성공 - 팝업 없이 조용히 완료
                pass
            
        except Exception as exc:
            messagebox.showerror('저장 오류', f'이미지 저장 중 오류가 발생했습니다: {exc}')

