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

    def _detect_datetime_column(self, df: pd.DataFrame, column: str) -> bool:
        """컬럼이 시간 데이터인지 감지 (컬럼 이름과 내용 모두 고려)"""
        try:
            # 컬럼 이름이 시간 관련 키워드를 포함하는지 확인
            time_keywords = ['timestamp', 'time', 'date', 'datetime', 'ts']
            column_lower = column.lower()
            has_time_keyword = any(keyword in column_lower for keyword in time_keywords)
            
            # 샘플 데이터로 시간 형식 테스트
            sample_data = df[column].dropna().head(10)
            if len(sample_data) == 0:
                return False
            
            # 컬럼 이름에 시간 키워드가 있으면 더 관대하게 판단
            if has_time_keyword:
                print(f"컬럼 '{column}'에 시간 키워드 감지됨")
                
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
            
            # 컬럼 이름에 시간 키워드가 있으면 더 관대하게 판단
            if has_time_keyword:
                if success_count > 0:
                    print(f"컬럼 '{column}': 시간 키워드 + 형식 매치로 시간 데이터로 판단")
                    return True
            else:
                # 시간 키워드가 없으면 더 엄격하게 판단
                if success_count > 0:
                    # 자동 파싱도 시도해보기
                    try:
                        pd.to_datetime(sample_data.iloc[0])
                        print(f"컬럼 '{column}': 형식 매치 + 자동 파싱으로 시간 데이터로 판단")
                        return True
                    except:
                        pass
                    
            # 자동 파싱 시도 (컬럼 이름에 시간 키워드가 있는 경우에만)
            if has_time_keyword:
                try:
                    pd.to_datetime(sample_data.iloc[0])
                    print(f"컬럼 '{column}': 시간 키워드 + 자동 파싱으로 시간 데이터로 판단")
                    return True
                except:
                    pass
                    
            print(f"컬럼 '{column}': 숫자 데이터로 판단")
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

        ttk.Label(select_frame, text='Y 컬럼(복수 선택)').grid(row=2, column=0, sticky=tk.W)
        self.y_listbox = tk.Listbox(select_frame, selectmode=tk.MULTIPLE, width=27, height=4, exportselection=False)
        self.y_listbox.grid(row=2, column=1, sticky=tk.W, padx=6)
        self.y_listbox.bind('<<ListboxSelect>>', lambda e: self._schedule_auto_refresh())

        # 시간 데이터 감지 상태 표시
        self.datetime_status_var = tk.StringVar(value='')
        self.datetime_status_label = ttk.Label(select_frame, textvariable=self.datetime_status_var, foreground='blue')
        self.datetime_status_label.grid(row=3, column=1, sticky=tk.W, padx=6)

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

        # 줌 컨트롤 섹션
        zoom_frame = ttk.LabelFrame(left_panel, text='줌 컨트롤', padding=8)
        zoom_frame.pack(fill=tk.X, pady=(0, 8))

        # 줌 모드 상태 변수
        self.zoom_mode = tk.BooleanVar(value=False)
        self.zoom_active = False
        self.zoom_start_x = None
        self.zoom_start_y = None
        self.zoom_end_x = None
        self.zoom_end_y = None
        self.zoom_rectangle = None  # 드래그 사각형 객체
        self.zoom_stack = []  # 줌 스택 (여러 번 줌인 가능)
        self.zoom_cids = []  # 이벤트 연결 ID 저장

        # 줌 버튼들
        zoom_buttons = ttk.Frame(zoom_frame)
        zoom_buttons.pack(fill=tk.X)
        
        self.zoom_button = ttk.Button(zoom_buttons, text='🔍 줌 모드', command=self._toggle_zoom_mode)
        self.zoom_button.pack(side=tk.LEFT)
        
        ttk.Button(zoom_buttons, text='줌 리셋', command=self._reset_zoom).pack(side=tk.LEFT, padx=4)
        ttk.Button(zoom_buttons, text='줌 아웃', command=self._zoom_out).pack(side=tk.LEFT, padx=4)
        
        # 줌 상태 표시
        self.zoom_status_var = tk.StringVar(value='줌 모드: 비활성')
        self.zoom_status_label = ttk.Label(zoom_frame, textvariable=self.zoom_status_var, foreground='gray')
        self.zoom_status_label.pack(pady=(4, 0))

        # 플롯 컨트롤 섹션
        plot_controls = ttk.Frame(left_panel)
        plot_controls.pack(fill=tk.X)

        ttk.Button(plot_controls, text='이미지 저장', command=self.on_save).pack(side=tk.LEFT)

        # === 오른쪽 패널 구성 ===
        # 플롯 섹션
        plot_frame = ttk.LabelFrame(right_panel, text='플롯', padding=8)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # Matplotlib Figure 생성
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Canvas 생성
        self.plot_canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 더블클릭 이벤트 바인딩
        self.plot_canvas.mpl_connect('button_press_event', self._on_plot_double_click)
        self._last_click_time = 0

        # 초기 플롯
        self.ax.text(0.5, 0.5, '데이터를 로드하고 플롯을 그려주세요', 
                    ha='center', va='center', transform=self.ax.transAxes, fontsize=14)
        self.ax.set_title('Excel Plotter')
        self.plot_canvas.draw()

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
        if self.zoom_mode.get():
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
        """그래프 설정 적용 - 기존 플롯 로직을 활용하여 새로 그리기"""
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
            y_indices = self.y_listbox.curselection()
            if not y_indices:
                messagebox.showwarning('경고', 'Y 컬럼을 하나 이상 선택하세요.')
                return
            y_cols = [self.y_listbox.get(i) for i in y_indices]

            # 데이터 변환 적용
            print(f"변환 전 데이터 정보:")
            print(f"  X축 컬럼: {x_col}")
            print(f"  Y축 컬럼들: {y_cols}")
            print(f"  DataFrame 크기: {df.shape}")
            print(f"  X축 데이터 샘플: {df[x_col].head().tolist()}")
            for y_col in y_cols:
                print(f"  Y축 '{y_col}' 데이터 샘플: {df[y_col].head().tolist()}")
            
            x, ymap = self._apply_transforms(df, x_col, y_cols)
            
            print(f"변환 후 데이터 정보:")
            print(f"  X축 데이터 크기: {len(x)}")
            print(f"  X축 데이터 샘플: {x.head().tolist()}")
            print(f"  Y축 맵 크기: {len(ymap)}")
            for name, series in ymap.items():
                print(f"  Y축 '{name}' 크기: {len(series)}, 샘플: {series.head().tolist()}")

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
            
            # 설정에 따라 플롯 그리기
            for name, series in ymap.items():
                # Y축 컬럼별 스타일 설정
                color = settings.get('y_colors', {}).get(name, settings['color'])
                line_width = settings.get('y_line_widths', {}).get(name, settings['line_width'])
                line_style = settings.get('y_line_styles', {}).get(name, settings['line_style'])
                marker = settings.get('y_markers', {}).get(name, settings['marker'])
                marker_size = settings.get('y_marker_sizes', {}).get(name, settings['marker_size'])
                plot_type = settings.get('y_plot_types', {}).get(name, settings['plot_type'])
                
                if plot_type == 'line':
                    self.ax.plot(x, series, label=name, 
                               linestyle=line_style,
                               color=color,
                               linewidth=line_width)
                elif plot_type == 'scatter':
                    self.ax.scatter(x, series, label=name,
                                  marker=marker,
                                  color=color,
                                  s=marker_size**2)
                else:  # both
                    self.ax.plot(x, series, label=name,
                               linestyle=line_style,
                               color=color,
                               linewidth=line_width,
                               marker=marker,
                               markersize=marker_size)
            
            # 축 범위 설정 - 선택된 축 타입에 따라 처리
            axis_type = self.axis_type_var.get()
            if axis_type == 'datetime':
                # 시간축인 경우 - 사용자 지정 시간 범위 사용
                try:
                    import matplotlib.dates as mdates
                    
                    # 시간 축 포맷터 설정
                    time_format = settings.get('time_format', '%H:%M:%S.%f')
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter(time_format))
                    
                    # 시간 간격 설정
                    interval_unit = settings.get('time_interval_unit', 'minutes')
                    interval_value = settings.get('time_interval_value', 1)
                    
                    if interval_unit == 'seconds':
                        locator = mdates.SecondLocator(interval=interval_value)
                    elif interval_unit == 'minutes':
                        locator = mdates.MinuteLocator(interval=interval_value)
                    elif interval_unit == 'hours':
                        locator = mdates.HourLocator(interval=interval_value)
                    elif interval_unit == 'days':
                        locator = mdates.DayLocator(interval=interval_value)
                    else:
                        locator = mdates.MinuteLocator(interval=interval_value)
                    
                    # 사용자가 지정한 시간 범위 사용
                    xlim_min = pd.to_datetime(settings['xlim_min'])
                    xlim_max = pd.to_datetime(settings['xlim_max'])
                    
                    # matplotlib의 날짜 변환 사용
                    xlim_min_num = mdates.date2num(xlim_min)
                    xlim_max_num = mdates.date2num(xlim_max)
                    
                    self.ax.set_xlim(xlim_min_num, xlim_max_num)
                    
                    # Locator로 틱 생성 후, 시작/끝 제외하고 표시
                    try:
                        tick_vals = locator.tick_values(xlim_min_num, xlim_max_num)
                        tick_vals = np.array(tick_vals, dtype=float)
                        # 시작/끝 제외
                        inner_ticks = tick_vals[1:-1] if tick_vals.size > 2 else np.array([])
                        self.ax.xaxis.set_major_locator(mdates.FixedLocator(inner_ticks))
                    except Exception:
                        # 실패 시 기본 locator 사용
                        self.ax.xaxis.set_major_locator(locator)
                    
                    print(f"시간 축 사용자 지정 범위 설정: {xlim_min} ~ {xlim_max}")
                    print(f"시간 간격: {interval_value} {interval_unit}, 형식: {time_format}")
                except Exception as e:
                    print(f"Timestamp 축 설정 오류: {e}")
                    # 기본 범위 사용
                    self.ax.set_xlim(x.min(), x.max())
            else:
                # 숫자축인 경우 - 사용자 지정 범위 사용
                try:
                    xlim_min = float(settings['xlim_min'])
                    xlim_max = float(settings['xlim_max'])
                    self.ax.set_xlim(xlim_min, xlim_max)
                    print(f"숫자 축 범위 설정: {xlim_min} ~ {xlim_max}")
                except Exception as e:
                    print(f"숫자 범위 설정 오류: {e}")
                    # 기본 범위 사용
                    self.ax.set_xlim(x.min(), x.max())
            
            self.ax.set_ylim(settings['ylim_min'], settings['ylim_max'])
            
            # 축 간격 설정 - 선택된 축 타입에 따라 처리
            if axis_type == 'datetime':
                # 시간축인 경우 - 시간 축은 이미 위에서 설정됨
                print(f"시간 축 틱은 자동으로 설정됨")
            else:
                # 숫자축인 경우: [min, max] 를 간격(step)으로 쪼개고 시작/끝 포함
                try:
                    x_start = float(settings['xlim_min'])
                    x_end = float(settings['xlim_max'])
                    x_step = max(1e-12, float(settings['x_ticks']))
                    x_ticks = np.arange(x_start, x_end, x_step)
                    if len(x_ticks) == 0 or abs(x_ticks[0] - x_start) > 1e-9:
                        x_ticks = np.insert(x_ticks, 0, x_start)
                    if len(x_ticks) == 0 or abs(x_ticks[-1] - x_end) > 1e-9:
                        x_ticks = np.append(x_ticks, x_end)
                    # X축: 시작/끝 틱은 숨기고 내부 틱만 표시
                    show_ticks = x_ticks[1:-1] if len(x_ticks) > 2 else np.array([])
                    self.ax.set_xticks(show_ticks)
                except Exception:
                    pass
            
            # Y축: [min, max] 간격(step)으로, 시작/끝 포함
            try:
                y_start = float(settings['ylim_min'])
                y_end = float(settings['ylim_max'])
                y_step = max(1e-12, float(settings['y_ticks']))
                y_ticks = np.arange(y_start, y_end, y_step)
                if len(y_ticks) == 0 or abs(y_ticks[0] - y_start) > 1e-9:
                    y_ticks = np.insert(y_ticks, 0, y_start)
                if len(y_ticks) == 0 or abs(y_ticks[-1] - y_end) > 1e-9:
                    y_ticks = np.append(y_ticks, y_end)
                self.ax.set_yticks(y_ticks)
            except Exception:
                pass
            
            # 제목 및 레이블 설정
            if settings['title']:
                self.ax.set_title(settings['title'], fontsize=settings['title_fontsize'])
            else:
                self.ax.set_title('Excel Plotter')
                
            if settings['xlabel']:
                self.ax.set_xlabel(settings['xlabel'], fontsize=settings['xlabel_fontsize'])
            else:
                # 기본 X축 레이블 설정 - 선택된 축 타입에 따라 처리
                if axis_type == 'datetime':
                    self.ax.set_xlabel(f'{x_col}', fontsize=settings['xlabel_fontsize'])
                    # 시간 축 포맷팅
                    import matplotlib.dates as mdates
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                    self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(x)//10)))
                    plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                else:
                    self.ax.set_xlabel(x_col, fontsize=settings['xlabel_fontsize'])
            
            if settings['ylabel']:
                self.ax.set_ylabel(settings['ylabel'], fontsize=settings['ylabel_fontsize'])
            else:
                # 기본 Y축 레이블 설정
                if len(y_cols) == 1:
                    self.ax.set_ylabel(y_cols[0], fontsize=settings['ylabel_fontsize'])
                else:
                    self.ax.set_ylabel('Values', fontsize=settings['ylabel_fontsize'])
            
            # 축 숫자 글자 크기 설정
            self.ax.tick_params(axis='x', labelsize=settings['x_tick_fontsize'])
            self.ax.tick_params(axis='y', labelsize=settings['y_tick_fontsize'])
            
            # 범례 표시 (여러 Y축이 있는 경우)
            if len(ymap) > 1:
                self.ax.legend()
            
            # 그리드 표시
            self.ax.grid(True, alpha=0.3)
            
            # 캔버스 새로고침
            self.plot_canvas.draw()
            
        except Exception as e:
            messagebox.showerror('오류', f'그래프 설정 적용 중 오류가 발생했습니다: {e}')
            print(f"상세 오류: {e}")
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
        """컬럼 이름이 시간 관련인지 확인"""
        time_keywords = ['timestamp', 'time', 'date', 'datetime', 'ts']
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
            x = work[x_col]
        else:
            # 숫자축 모드: 숫자로 변환
            print(f"숫자축 모드로 처리: {x_col}")
            if x_col not in work.columns:
                raise ValueError(f'컬럼 없음: {x_col}')
            work[x_col] = pd.to_numeric(work[x_col], errors='coerce')
            x = work[x_col]

        # Y 컬럼들을 숫자로 변환
        for c in y_cols:
            if c not in work.columns:
                raise ValueError(f'컬럼 없음: {c}')
            work[c] = pd.to_numeric(work[c], errors='coerce')

        # 결측값 제거
        work = work.dropna(subset=[x_col] + y_cols)

        ymap: dict[str, pd.Series] = {}
        for c in y_cols:
            ymap[c] = work[c]
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

            # 기존 플롯 클리어
            self.ax.clear()
            
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
            self.ax.grid(True, alpha=0.3)
            
            # 레이아웃 조정
            self.figure.tight_layout()
            
            # Canvas 업데이트
            self.plot_canvas.draw()
            
        except Exception as exc:
            messagebox.showerror('플롯 오류', str(exc))

    def on_save(self) -> None:
        """이미지 저장 - Plot Image 폴더에 자동으로 저장"""
        try:
            # 현재 플롯이 있는지 확인
            if not hasattr(self.ax, 'lines') or not self.ax.lines:
                messagebox.showwarning('경고', '먼저 플롯을 그려주세요.')
                return
            
            # 현재 플롯의 제목 가져오기
            title = self.ax.get_title() if self.ax.get_title() else "Plot"
            
            # 이미지 저장 모듈을 사용하여 저장
            success = self.image_saver.save_plot_image(self.figure, title)
            
            if success:
                # 저장 성공 - 팝업 없이 조용히 완료
                pass
            
        except Exception as exc:
            messagebox.showerror('저장 오류', f'이미지 저장 중 오류가 발생했습니다: {exc}')

    def _toggle_zoom_mode(self) -> None:
        """줌 모드 토글"""
        self.zoom_mode.set(not self.zoom_mode.get())
        
        if self.zoom_mode.get():
            self.zoom_status_var.set('줌 모드: 활성 - 영역을 드래그하세요')
            self.zoom_status_label.config(foreground='red')
            self.zoom_button.config(text='🔍 줌 모드 (활성)')
            
            # 마우스 이벤트 바인딩
            if hasattr(self, 'plot_canvas'):
                # 기존 연결 해제
                self._disconnect_zoom_events()
                
                # 새 이벤트 연결
                cid1 = self.plot_canvas.mpl_connect('button_press_event', self._on_zoom_press)
                cid2 = self.plot_canvas.mpl_connect('motion_notify_event', self._on_zoom_motion)
                cid3 = self.plot_canvas.mpl_connect('button_release_event', self._on_zoom_release)
                
                self.zoom_cids = [cid1, cid2, cid3]
        else:
            self.zoom_status_var.set('줌 모드: 비활성')
            self.zoom_status_label.config(foreground='gray')
            self.zoom_button.config(text='🔍 줌 모드')
            
            # 드래그 사각형 제거
            if self.zoom_rectangle is not None:
                self.zoom_rectangle.remove()
                self.zoom_rectangle = None
                if hasattr(self, 'plot_canvas'):
                    self.plot_canvas.draw()
            
            # 마우스 이벤트 해제
            self._disconnect_zoom_events()
    
    def _disconnect_zoom_events(self) -> None:
        """줌 이벤트 연결 해제"""
        if hasattr(self, 'plot_canvas') and self.zoom_cids:
            for cid in self.zoom_cids:
                try:
                    self.plot_canvas.mpl_disconnect(cid)
                except:
                    pass
            self.zoom_cids = []

    def _on_zoom_press(self, event) -> None:
        """줌 드래그 시작"""
        if not self.zoom_mode.get() or event.inaxes != self.ax:
            return
            
        self.zoom_active = True
        self.zoom_start_x = event.xdata
        self.zoom_start_y = event.ydata
        
        # 현재 축 범위를 줌 스택에 저장 (첫 번째 드래그일 때만)
        if not self.zoom_stack:
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()
            self.zoom_stack.append((current_xlim, current_ylim))

    def _on_zoom_motion(self, event) -> None:
        """줌 드래그 중"""
        if not self.zoom_mode.get() or not self.zoom_active or event.inaxes != self.ax:
            return
            
        self.zoom_end_x = event.xdata
        self.zoom_end_y = event.ydata
        
        # 드래그 사각형 그리기/업데이트
        if (self.zoom_start_x is not None and self.zoom_start_y is not None and 
            self.zoom_end_x is not None and self.zoom_end_y is not None):
            
            # 기존 사각형 제거
            if self.zoom_rectangle is not None:
                self.zoom_rectangle.remove()
            
            # 새 사각형 그리기
            width = abs(self.zoom_end_x - self.zoom_start_x)
            height = abs(self.zoom_end_y - self.zoom_start_y)
            x = min(self.zoom_start_x, self.zoom_end_x)
            y = min(self.zoom_start_y, self.zoom_end_y)
            
            self.zoom_rectangle = self.ax.add_patch(
                plt.Rectangle((x, y), width, height, 
                            fill=False, edgecolor='red', linewidth=2, alpha=0.7)
            )
            self.plot_canvas.draw()

    def _on_zoom_release(self, event) -> None:
        """줌 드래그 종료"""
        if not self.zoom_mode.get() or not self.zoom_active or event.inaxes != self.ax:
            return
            
        self.zoom_active = False
        
        if self.zoom_start_x is not None and self.zoom_end_x is not None:
            # 드래그된 영역으로 줌
            x_min = min(self.zoom_start_x, self.zoom_end_x)
            x_max = max(self.zoom_start_x, self.zoom_end_x)
            y_min = min(self.zoom_start_y, self.zoom_end_y)
            y_max = max(self.zoom_start_y, self.zoom_end_y)
            
            # 현재 축 범위 대비 최소 크기 체크 (1% 이상)
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()
            x_range = current_xlim[1] - current_xlim[0]
            y_range = current_ylim[1] - current_ylim[0]
            
            min_x_size = x_range * 0.01  # 1%
            min_y_size = y_range * 0.01  # 1%
            
            if abs(x_max - x_min) > min_x_size and abs(y_max - y_min) > min_y_size:
                # 현재 범위를 스택에 저장
                self.zoom_stack.append((current_xlim, current_ylim))
                
                # 줌 적용
                self.ax.set_xlim(x_min, x_max)
                self.ax.set_ylim(y_min, y_max)
                self.plot_canvas.draw()
                
                print(f"줌 적용: X({x_min:.3f}, {x_max:.3f}), Y({y_min:.3f}, {y_max:.3f})")
            else:
                print(f"줌 무시: 영역이 너무 작음 (최소 {min_x_size:.3f} x {min_y_size:.3f})")
        
        # 드래그 사각형 제거
        if self.zoom_rectangle is not None:
            self.zoom_rectangle.remove()
            self.zoom_rectangle = None
            self.plot_canvas.draw()
        
        # 변수 초기화
        self.zoom_start_x = None
        self.zoom_start_y = None
        self.zoom_end_x = None
        self.zoom_end_y = None

    def _reset_zoom(self) -> None:
        """줌 리셋"""
        if self.zoom_stack:
            # 원본 범위로 복원
            original_xlim, original_ylim = self.zoom_stack[0]
            self.ax.set_xlim(original_xlim)
            self.ax.set_ylim(original_ylim)
            self.plot_canvas.draw()
            
            # 줌 스택 초기화
            self.zoom_stack = []
            print("줌 리셋 완료")
        else:
            print("리셋할 원본 범위가 없습니다.")
    
    def _zoom_out(self) -> None:
        """줌 아웃 (이전 단계로)"""
        if len(self.zoom_stack) > 1:
            # 마지막 줌 단계 제거
            self.zoom_stack.pop()
            
            # 이전 범위로 복원
            prev_xlim, prev_ylim = self.zoom_stack[-1]
            self.ax.set_xlim(prev_xlim)
            self.ax.set_ylim(prev_ylim)
            self.plot_canvas.draw()
            
            print(f"줌 아웃: X({prev_xlim[0]:.3f}, {prev_xlim[1]:.3f}), Y({prev_ylim[0]:.3f}, {prev_ylim[1]:.3f})")
        else:
            print("줌 아웃할 단계가 없습니다.")
