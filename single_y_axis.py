"""
Single Y축 설정 모듈
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd


class SingleYAxisSettings:
    """Single Y축 설정을 위한 모든 UI와 로직을 포함하는 클래스"""

    def __init__(self, parent_tab, plot_settings_window, main_app):
        """
        Args:
            parent_tab: Tkinter Frame (single_y_tab)
            plot_settings_window: PlotSettingsWindow 인스턴스
            main_app: MainApp 인스턴스
        """
        self.parent_tab = parent_tab
        self.plot_settings_window = plot_settings_window
        self.main_app = main_app
        self.settings = plot_settings_window.settings  # 공유 설정
        if self.settings is None:
            print("Warning: SingleYAxisSettings received None for settings. Initializing to {}.")
            self.settings = {}

        # 변수 초기화
        self._initialize_variables()

        # UI 구축
        self._build_ui_in_tab(self.parent_tab)

    def _initialize_variables(self):
        """모든 Single Y축 변수 초기화"""
        # 축 범위
        self.xlim_min_numeric_var = None  # _build_numeric_axis_tab에서 초기화
        self.xlim_max_numeric_var = None
        self.xlim_min_timestamp_var = None  # _build_timestamp_axis_tab에서 초기화
        self.xlim_max_timestamp_var = None
        self.ylim_min_var = None  # _build_axis_section에서 초기화
        self.ylim_max_var = None

        # 축 간격
        self.x_ticks_var = None  # _build_numeric_axis_tab / _build_timestamp_axis_tab에서 초기화
        self.y_ticks_var = None  # _build_axis_section에서 초기화

        # 라벨/제목
        self.title_var = None  # _build_labels_section에서 초기화
        self.xlabel_var = None
        self.ylabel_var = None

        # 폰트 크기
        self.title_fontsize_var = None  # _build_labels_section에서 초기화
        self.xlabel_fontsize_var = None
        self.ylabel_fontsize_var = None
        self.x_tick_fontsize_var = None
        self.y_tick_fontsize_var = None
        
        # 범례 위치
        self.legend_loc_var = None

        # 축 스케일 (Linear, Log)
        self.x_scale_var = None
        self.y_scale_var = None

        # Y축 컬럼별 스타일 (딕셔너리)
        self.y_color_vars = {}
        self.y_line_width_vars = {}
        self.y_line_style_vars = {}
        self.y_marker_vars = {}
        self.y_marker_size_vars = {}
        self.y_plot_type_vars = {}

        # 타임스탬프 설정
        self.time_interval_unit = None  # _build_timestamp_axis_tab에서 초기화
        self.time_interval_value = None
        self.time_format = None

        # UI 참조
        self.axis_notebook = None  # _build_axis_section에서 초기화
        self.xlim_min_entry = None
        self.xlim_max_entry = None
        self.ylim_min_entry = None
        self.ylim_max_entry = None

    def _build_ui_in_tab(self, parent):
        """Single Y축 탭 UI 구축"""
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Y 컬럼 선택 섹션 (새로 추가)
        self._build_y_column_selection_section(scrollable_frame)

        # 플롯 스타일 섹션
        self._build_plot_style_section(scrollable_frame)

        # 축 설정 섹션
        self._build_axis_section(scrollable_frame)

        # 제목 및 레이블 섹션
        self._build_labels_section(scrollable_frame)

        # 캔버스와 스크롤바 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_y_column_selection_section(self, parent):
        """Y 컬럼 선택 섹션 (Main app에서 이동)"""
        y_column_frame = ttk.LabelFrame(parent, text='Y 컬럼 선택', padding=10)
        y_column_frame.pack(fill=tk.X, pady=5)

        ttk.Label(y_column_frame, text='Y 컬럼 (복수 선택 가능):', font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))

        # Y 컬럼 선택 Listbox
        self.single_y_listbox = tk.Listbox(y_column_frame, selectmode=tk.MULTIPLE, width=40, height=6, exportselection=False)
        self.single_y_listbox.pack(fill=tk.X, pady=(0, 5))

        # 현재 시트의 컬럼 목록 가져오기
        try:
            sheet = self.main_app.sheet_combo.get()
            if sheet and sheet in self.main_app.df_map:
                df = self.main_app.df_map[sheet]
                cols = list(df.columns.astype(str))

                # Listbox에 컬럼 추가
                for col in cols:
                    self.single_y_listbox.insert(tk.END, col)

                # Main app의 y_listbox에서 현재 선택된 항목 복원
                try:
                    y_indices = self.main_app.y_listbox.curselection()
                    for idx in y_indices:
                        self.single_y_listbox.select_set(idx)
                except:
                    pass
        except Exception as e:
            print(f"Y 컬럼 목록 로드 오류: {e}")

        # 선택 변경 시 Main app의 y_listbox와 동기화 + 스타일 UI 새로고침
        def on_y_selection_changed(event=None):
            try:
                # Main app의 y_listbox 선택 동기화
                self.main_app.y_listbox.selection_clear(0, tk.END)
                selected_indices = self.single_y_listbox.curselection()
                for idx in selected_indices:
                    self.main_app.y_listbox.select_set(idx)

                # 스타일 UI 새로고침
                self._refresh_style_ui()

                # 그래프 업데이트 스케줄링
                self.plot_settings_window._schedule_update()
            except Exception as e:
                print(f"Y 컬럼 선택 동기화 오류: {e}")

        self.single_y_listbox.bind('<<ListboxSelect>>', on_y_selection_changed)

    def _build_plot_style_section(self, parent):
        """플롯 스타일 섹션"""
        self.style_section_frame = ttk.LabelFrame(parent, text='플롯 스타일', padding=10)
        self.style_section_frame.pack(fill=tk.X, pady=5)

        # Y축 컬럼별 스타일 선택을 위한 컨테이너
        self.y_style_container = ttk.Frame(self.style_section_frame)
        self.y_style_container.pack(fill=tk.X)

        self._build_y_color_section(self.y_style_container)

    def _refresh_style_ui(self):
        """스타일 UI 새로고침"""
        if hasattr(self, 'y_style_container'):
            for widget in self.y_style_container.winfo_children():
                widget.destroy()
            self._build_y_color_section(self.y_style_container)

    def _build_y_color_section(self, parent):
        """Y축 컬럼별 스타일 선택 섹션"""
        # 현재 선택된 Y축 컬럼들 가져오기
        try:
            y_indices = self.main_app.y_listbox.curselection()
            if not y_indices:
                return
            y_columns = [self.main_app.y_listbox.get(i) for i in y_indices]
        except:
            return

        # Y축 스타일 설정이 없으면 기본값으로 초기화
        if 'y_colors' not in self.settings:
            self.settings['y_colors'] = {}
        if 'y_line_widths' not in self.settings:
            self.settings['y_line_widths'] = {}
        if 'y_line_styles' not in self.settings:
            self.settings['y_line_styles'] = {}
        if 'y_markers' not in self.settings:
            self.settings['y_markers'] = {}
        if 'y_marker_sizes' not in self.settings:
            self.settings['y_marker_sizes'] = {}
        if 'y_plot_types' not in self.settings:
            self.settings['y_plot_types'] = {}

        # Y축 스타일 프레임
        y_style_frame = ttk.LabelFrame(parent, text='Y축 컬럼별 스타일', padding=5)
        y_style_frame.pack(fill=tk.X, pady=5)

        # 각 Y축 컬럼에 대한 스타일 선택 (기존 값 유지)
        if not hasattr(self, 'y_color_vars'):
            self.y_color_vars = {}
        if not hasattr(self, 'y_line_width_vars'):
            self.y_line_width_vars = {}
        if not hasattr(self, 'y_line_style_vars'):
            self.y_line_style_vars = {}
        if not hasattr(self, 'y_marker_vars'):
            self.y_marker_vars = {}
        if not hasattr(self, 'y_marker_size_vars'):
            self.y_marker_size_vars = {}
        if not hasattr(self, 'y_plot_type_vars'):
            self.y_plot_type_vars = {}

        for i, y_col in enumerate(y_columns):
            # 컬럼별 스타일 프레임
            col_frame = ttk.LabelFrame(y_style_frame, text=y_col, padding=3)
            col_frame.pack(fill=tk.X, pady=2)

            # 첫 번째 행: 색상과 선 굵기
            row1_frame = ttk.Frame(col_frame)
            row1_frame.pack(fill=tk.X, pady=1)

            # 색상
            ttk.Label(row1_frame, text='색상:', width=8).pack(side=tk.LEFT)
            color_var = tk.StringVar()
            if y_col in self.settings['y_colors']:
                color_var.set(self.settings['y_colors'][y_col])
            else:
                default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                color_var.set(default_colors[i % len(default_colors)])

            self.y_color_vars[y_col] = color_var
            color_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())

            color_entry = ttk.Entry(row1_frame, textvariable=color_var, width=10)
            color_entry.pack(side=tk.LEFT, padx=2)

            color_button = ttk.Button(row1_frame, text='색상',
                                   command=lambda col=y_col: self._choose_y_color(col))
            color_button.pack(side=tk.LEFT, padx=2)

            # 색상 미리보기
            preview_frame = tk.Frame(row1_frame, width=20, height=15, relief=tk.SUNKEN, bd=1)
            preview_frame.pack(side=tk.LEFT, padx=2)
            preview_frame.pack_propagate(False)

            # 선 굵기
            ttk.Label(row1_frame, text='선 굵기:', width=8).pack(side=tk.LEFT, padx=(10, 0))
            line_width_var = tk.DoubleVar()
            if y_col in self.settings['y_line_widths']:
                line_width_var.set(self.settings['y_line_widths'][y_col])
            else:
                line_width_var.set(self.settings.get('line_width', 1.0))

            self.y_line_width_vars[y_col] = line_width_var
            line_width_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())

            line_width_entry = ttk.Entry(row1_frame, textvariable=line_width_var, width=6)
            line_width_entry.pack(side=tk.LEFT, padx=2)

            # 두 번째 행: 선 스타일과 마커
            row2_frame = ttk.Frame(col_frame)
            row2_frame.pack(fill=tk.X, pady=1)

            # 선 스타일
            ttk.Label(row2_frame, text='선 스타일:', width=8).pack(side=tk.LEFT)
            line_style_var = tk.StringVar()
            if y_col in self.settings['y_line_styles']:
                line_style_var.set(self.settings['y_line_styles'][y_col])
            else:
                line_style_var.set(self.settings.get('line_style', '-'))

            self.y_line_style_vars[y_col] = line_style_var
            line_style_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())

            line_style_combo = ttk.Combobox(row2_frame, textvariable=line_style_var, width=8, state='readonly')
            line_style_combo['values'] = ['-', '--', '-.', ':']
            line_style_combo.pack(side=tk.LEFT, padx=2)

            # 마커 스타일
            ttk.Label(row2_frame, text='마커:', width=8).pack(side=tk.LEFT, padx=(10, 0))
            marker_var = tk.StringVar()
            if y_col in self.settings['y_markers']:
                marker_var.set(self.settings['y_markers'][y_col])
            else:
                marker_var.set(self.settings.get('marker', 'o'))

            self.y_marker_vars[y_col] = marker_var
            marker_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())

            marker_combo = ttk.Combobox(row2_frame, textvariable=marker_var, width=8, state='readonly')
            marker_combo['values'] = ['o', 's', '^', 'v', 'D', 'p', '*', '+', 'x', 'None']
            marker_combo.pack(side=tk.LEFT, padx=2)

            # 세 번째 행: 플롯 타입과 마커 크기
            row3_frame = ttk.Frame(col_frame)
            row3_frame.pack(fill=tk.X, pady=1)

            # 플롯 타입
            ttk.Label(row3_frame, text='플롯 타입:', width=8).pack(side=tk.LEFT)
            plot_type_var = tk.StringVar()
            if y_col in self.settings['y_plot_types']:
                plot_type_var.set(self.settings['y_plot_types'][y_col])
            else:
                plot_type_var.set(self.settings.get('plot_type', 'line'))

            self.y_plot_type_vars[y_col] = plot_type_var
            plot_type_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())

            plot_type_combo = ttk.Combobox(row3_frame, textvariable=plot_type_var, width=8, state='readonly')
            plot_type_combo['values'] = ['line', 'scatter', 'both']
            plot_type_combo.pack(side=tk.LEFT, padx=2)

            # 마커 크기 (기본값 20, 사용자 수정 가능)
            ttk.Label(row3_frame, text='마커 크기:', width=8).pack(side=tk.LEFT, padx=(10, 0))
            marker_size_var = tk.DoubleVar()
            if y_col in self.settings['y_marker_sizes']:
                marker_size_var.set(self.settings['y_marker_sizes'][y_col])
            else:
                marker_size_var.set(20.0)
            self.y_marker_size_vars[y_col] = marker_size_var
            marker_size_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
            marker_size_entry = ttk.Entry(row3_frame, textvariable=marker_size_var, width=6)
            marker_size_entry.pack(side=tk.LEFT, padx=2)

            # 색상 미리보기 업데이트 함수
            def update_preview(col=y_col):
                try:
                    color = color_var.get()
                    preview_frame.config(bg=color)
                except:
                    preview_frame.config(bg='white')

            color_var.trace('w', lambda *args: update_preview())
            update_preview()  # 초기 미리보기 설정

    def _choose_y_color(self, column_name):
        """Y축 컬럼별 색상 선택"""
        try:
            from tkinter import colorchooser
            current_color = self.y_color_vars[column_name].get()
            color = colorchooser.askcolor(title=f'{column_name} 색상 선택', color=current_color)
            if color[1]:  # 사용자가 색상을 선택한 경우
                self.y_color_vars[column_name].set(color[1])
        except Exception as e:
            print(f"색상 선택 오류: {e}")

    def _build_axis_section(self, parent):
        """축 설정 섹션"""
        axis_frame = ttk.LabelFrame(parent, text='축 설정', padding=10)
        axis_frame.pack(fill=tk.X, pady=5)

        # 탭 컨트롤 생성
        self.axis_notebook = ttk.Notebook(axis_frame)
        self.axis_notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 변경 이벤트 바인딩
        self.axis_notebook.bind('<<NotebookTabChanged>>', self._on_axis_tab_changed)

        # 숫자 축 탭
        numeric_frame = ttk.Frame(self.axis_notebook)
        self.axis_notebook.add(numeric_frame, text='숫자 축')

        # 시간 축 탭
        timestamp_frame = ttk.Frame(self.axis_notebook)
        self.axis_notebook.add(timestamp_frame, text='시간 축')

        # 현재 설정에 따라 적절한 탭 선택
        if self.settings.get('is_timestamp', False):
            self.axis_notebook.select(1)  # 시간 축 탭 선택
        else:
            self.axis_notebook.select(0)  # 숫자 축 탭 선택

        # 숫자 축 설정
        self._build_numeric_axis_tab(numeric_frame)

        # 시간 축 설정
        self._build_timestamp_axis_tab(timestamp_frame)

        # 탭 활성화/비활성화 설정
        self._update_tab_availability()

        # Y축 범위 (공통)
        ylim_frame = ttk.Frame(axis_frame)
        ylim_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ylim_frame, text='Y축 범위:').pack(side=tk.LEFT)

        self.ylim_min_var = tk.DoubleVar(value=self.settings['ylim_min'])
        self.ylim_max_var = tk.DoubleVar(value=self.settings['ylim_max'])
        # trace 제거: KeyRelease 이벤트로 대체하여 입력 충돌 방지

        self.ylim_min_entry = ttk.Entry(ylim_frame, textvariable=self.ylim_min_var, width=8)
        self.ylim_min_entry.pack(side=tk.LEFT, padx=2)
        self.ylim_min_entry.bind('<KeyRelease>', self._on_x_range_modified)

        ttk.Label(ylim_frame, text='~').pack(side=tk.LEFT)

        self.ylim_max_entry = ttk.Entry(ylim_frame, textvariable=self.ylim_max_var, width=8)
        self.ylim_max_entry.pack(side=tk.LEFT, padx=2)
        self.ylim_max_entry.bind('<KeyRelease>', self._on_x_range_modified)

        ttk.Button(ylim_frame, text='자동', command=self._auto_ylim_single).pack(side=tk.LEFT, padx=5)

        # Y축 간격 (공통)
        yticks_frame = ttk.Frame(axis_frame)
        yticks_frame.pack(fill=tk.X, pady=2)
        ttk.Label(yticks_frame, text='Y축 간격 단위:').pack(side=tk.LEFT)

        # y_ticks_var가 없으면 생성, 있으면 재사용
        if not hasattr(self, 'y_ticks_var') or self.y_ticks_var is None:
            y_ticks_value = self.settings.get('y_ticks', 1)
            print(f"[공통] Y축 간격 단위 초기값: {y_ticks_value}")
            self.y_ticks_var = tk.IntVar(value=int(y_ticks_value))
            # trace 제거: KeyRelease 이벤트로 대체하여 입력 충돌 방지
        else:
            print(f"[공통] 기존 y_ticks_var 재사용: {self.y_ticks_var.get()}")

        yticks_entry = ttk.Entry(yticks_frame, textvariable=self.y_ticks_var, width=8)
        yticks_entry.pack(side=tk.LEFT, padx=5)
        yticks_entry.bind('<KeyRelease>', self._on_x_range_modified)

        # Y축 스케일
        yscale_frame = ttk.Frame(axis_frame)
        yscale_frame.pack(fill=tk.X, pady=2)
        ttk.Label(yscale_frame, text='Y축 스케일:').pack(side=tk.LEFT)
        
        self.y_scale_var = tk.StringVar(value=self.settings.get('y_scale', 'linear'))
        self.y_scale_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        
        yscale_combo = ttk.Combobox(yscale_frame, textvariable=self.y_scale_var, values=['linear', 'log'], width=10, state='readonly')
        yscale_combo.pack(side=tk.LEFT, padx=5)

    def _build_numeric_axis_tab(self, parent):
        """숫자 축 탭 구성"""
        # 자동/수동 모드 제거: 처음 로드 시 자동값만 채우고 항상 수동 입력

        # X축 범위 (수동 입력)
        xlim_frame = ttk.Frame(parent)
        xlim_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xlim_frame, text='X축 범위:').pack(side=tk.LEFT)

        print(f"숫자축 탭 생성 - xlim_min: {self.settings['xlim_min']}, xlim_max: {self.settings['xlim_max']}")
        self.xlim_min_numeric_var = tk.DoubleVar(value=self.settings['xlim_min'])
        self.xlim_max_numeric_var = tk.DoubleVar(value=self.settings['xlim_max'])
        # trace 제거: KeyRelease 이벤트로 대체하여 입력 충돌 방지

        self.xlim_min_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_numeric_var, width=8)
        self.xlim_min_entry.pack(side=tk.LEFT, padx=2)
        self.xlim_min_entry.bind('<KeyRelease>', self._on_x_range_modified)
        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)
        self.xlim_max_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_numeric_var, width=8)
        self.xlim_max_entry.pack(side=tk.LEFT, padx=2)
        self.xlim_max_entry.bind('<KeyRelease>', self._on_x_range_modified)

        # 자동 버튼 추가
        ttk.Button(xlim_frame, text='자동', command=self._auto_xlim_numeric).pack(side=tk.LEFT, padx=5)

        # X축 간격
        xticks_frame = ttk.Frame(parent)
        xticks_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xticks_frame, text='X축 간격 단위:').pack(side=tk.LEFT)

        # x_ticks_var가 없으면 생성, 있으면 재사용
        if not hasattr(self, 'x_ticks_var') or self.x_ticks_var is None:
            x_ticks_value = self.settings.get('x_ticks', 1)
            print(f"[숫자축 탭] X축 간격 단위 초기값: {x_ticks_value}")
            self.x_ticks_var = tk.IntVar(value=int(x_ticks_value))
            # trace 제거: KeyRelease 이벤트로 대체하여 입력 충돌 방지
        else:
            print(f"[숫자축 탭] 기존 x_ticks_var 재사용: {self.x_ticks_var.get()}")

        xticks_entry = ttk.Entry(xticks_frame, textvariable=self.x_ticks_var, width=8)
        xticks_entry.pack(side=tk.LEFT, padx=5)
        xticks_entry.bind('<KeyRelease>', self._on_x_range_modified)

        # X축 스케일
        xscale_frame = ttk.Frame(parent)
        xscale_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xscale_frame, text='X축 스케일:').pack(side=tk.LEFT)
        
        self.x_scale_var = tk.StringVar(value=self.settings.get('x_scale', 'linear'))
        self.x_scale_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        
        xscale_combo = ttk.Combobox(xscale_frame, textvariable=self.x_scale_var, values=['linear', 'log'], width=10, state='readonly')
        xscale_combo.pack(side=tk.LEFT, padx=5)

        # 초기 상태: 입력 활성화 (수동)

    def _build_timestamp_axis_tab(self, parent):
        """시간 축 탭 구성"""
        # 자동/수동 모드 제거: 처음 로드 시 자동값만 채우고 항상 수동 입력

        # X축 시간 범위 (수동 입력)
        xlim_frame = ttk.Frame(parent)
        xlim_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xlim_frame, text='X축 시간 범위:').pack(side=tk.LEFT)

        print(f"시간축 탭 생성 - xlim_min: {self.settings['xlim_min']}, xlim_max: {self.settings['xlim_max']}")
        self.xlim_min_timestamp_var = tk.StringVar(value=self.plot_settings_window._format_datetime(self.settings['xlim_min']))
        self.xlim_max_timestamp_var = tk.StringVar(value=self.plot_settings_window._format_datetime(self.settings['xlim_max']))

        self.xlim_min_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_timestamp_var, width=20)
        self.xlim_min_entry.pack(side=tk.LEFT, padx=2)
        # 시간축 포맷팅 비활성화 - 단순한 입력만 받음
        self.xlim_min_entry.bind('<KeyRelease>', self._on_timestamp_range_modified_simple)
        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)
        self.xlim_max_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_timestamp_var, width=20)
        self.xlim_max_entry.pack(side=tk.LEFT, padx=2)
        self.xlim_max_entry.bind('<KeyRelease>', self._on_timestamp_range_modified_simple)

        # 자동 버튼 추가
        ttk.Button(xlim_frame, text='자동', command=self._auto_xlim_timestamp).pack(side=tk.LEFT, padx=5)

        # 시간 형식 안내
        format_label = ttk.Label(parent, text='시간 형식: YYYY-MM-DD 시:분:초 (숫자만 입력하면 자동 포맷팅)', font=('Arial', 9), foreground='gray')
        format_label.pack(pady=2)

        # X축 간격 설정
        xticks_frame = ttk.LabelFrame(parent, text='X축 시간 간격 설정', padding=5)
        xticks_frame.pack(fill=tk.X, pady=5)

        # 간격 수 설정
        ticks_count_frame = ttk.Frame(xticks_frame)
        ticks_count_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ticks_count_frame, text='간격 단위:').pack(side=tk.LEFT)

        # x_ticks_var가 없으면 생성, 있으면 재사용
        if not hasattr(self, 'x_ticks_var') or self.x_ticks_var is None:
            x_ticks_value = self.settings.get('x_ticks', 1)
            print(f"[시간축 탭] X축 간격 단위 초기값: {x_ticks_value}")
            self.x_ticks_var = tk.IntVar(value=int(x_ticks_value))
            # trace 제거: KeyRelease 이벤트로 대체하여 입력 충돌 방지
        else:
            print(f"[시간축 탭] 기존 x_ticks_var 재사용: {self.x_ticks_var.get()}")

        xticks_entry = ttk.Entry(ticks_count_frame, textvariable=self.x_ticks_var, width=8)
        xticks_entry.pack(side=tk.LEFT, padx=5)
        xticks_entry.bind('<KeyRelease>', self._on_x_range_modified)

        # 시간 간격 단위 설정
        interval_frame = ttk.Frame(xticks_frame)
        interval_frame.pack(fill=tk.X, pady=2)
        ttk.Label(interval_frame, text='시간 간격 단위:').pack(side=tk.LEFT)

        self.time_interval_unit = tk.StringVar(value=self.settings.get('time_interval_unit', 'days'))
        self.time_interval_unit.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        interval_combo = ttk.Combobox(interval_frame, textvariable=self.time_interval_unit, width=12, state='readonly')
        interval_combo['values'] = ['seconds', 'minutes', 'hours', 'days']
        interval_combo.pack(side=tk.LEFT, padx=5)

        # 시간 간격 값 설정
        interval_value_frame = ttk.Frame(xticks_frame)
        interval_value_frame.pack(fill=tk.X, pady=2)
        ttk.Label(interval_value_frame, text='간격 값:').pack(side=tk.LEFT)

        self.time_interval_value = tk.IntVar(value=self.settings.get('time_interval_value', 1))
        self.time_interval_value.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        interval_value_entry = ttk.Entry(interval_value_frame, textvariable=self.time_interval_value, width=8)
        interval_value_entry.pack(side=tk.LEFT, padx=5)

        # 시간 형식 설정
        format_frame = ttk.Frame(xticks_frame)
        format_frame.pack(fill=tk.X, pady=2)
        ttk.Label(format_frame, text='시간 표시 형식:').pack(side=tk.LEFT)

        self.time_format = tk.StringVar(value=self.settings.get('time_format', 'YYYYMMDD_HHMM'))
        self.time_format.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        format_combo = ttk.Combobox(format_frame, textvariable=self.time_format, width=15, state='readonly')
        format_combo['values'] = ['시:분:초:밀리초', '시:분:초', '시:분', '년-월-일 시:분:초', '년-월-일 시:분', 'YYYYMMDD_HHMM']
        format_combo.pack(side=tk.LEFT, padx=5)

        # 초기 상태 설정: 입력 활성화 (수동)
        try:
            self.xlim_min_entry.config(state='normal')
            self.xlim_max_entry.config(state='normal')
        except Exception:
            pass

    def _build_labels_section(self, parent):
        """제목 및 레이블 섹션"""
        labels_frame = ttk.LabelFrame(parent, text='제목 및 레이블', padding=10)
        labels_frame.pack(fill=tk.X, pady=5)

        # 그래프 제목
        title_frame = ttk.Frame(labels_frame)
        title_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_frame, text='그래프 제목:').pack(side=tk.LEFT)

        self.title_var = tk.StringVar(value=self.settings['title'])
        self.title_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        ttk.Entry(title_frame, textvariable=self.title_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # X축 레이블
        xlabel_frame = ttk.Frame(labels_frame)
        xlabel_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xlabel_frame, text='X축 레이블:').pack(side=tk.LEFT)

        self.xlabel_var = tk.StringVar(value=self.settings['xlabel'])
        self.xlabel_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        ttk.Entry(xlabel_frame, textvariable=self.xlabel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Y축 레이블
        ylabel_frame = ttk.Frame(labels_frame)
        ylabel_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ylabel_frame, text='Y축 레이블:').pack(side=tk.LEFT)

        self.ylabel_var = tk.StringVar(value=self.settings['ylabel'])
        self.ylabel_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        ttk.Entry(ylabel_frame, textvariable=self.ylabel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 범례 위치
        legend_frame = ttk.Frame(labels_frame)
        legend_frame.pack(fill=tk.X, pady=2)
        ttk.Label(legend_frame, text='범례 위치:').pack(side=tk.LEFT)
        
        legend_options = {
            'best': '최적 위치(Auto)',
            'upper right': '오른쪽 위',
            'upper left': '왼쪽 위',
            'lower left': '왼쪽 아래',
            'lower right': '오른쪽 아래',
            'center left': '왼쪽 중간',
            'center right': '오른쪽 중간',
            'lower center': '아래 중간',
            'upper center': '위 중간',
            'center': '중앙'
        }
        
        # 한글 -> matplotlib loc 이름 맵핑
        self.legend_loc_map = {v: k for k, v in legend_options.items()}
        self.legend_loc_display_vals = list(legend_options.values())
        
        current_loc = self.settings.get('legend_loc', 'best')
        initial_display = legend_options.get(current_loc, '최적 위치(Auto)')
        
        self.legend_loc_var = tk.StringVar(value=initial_display)
        self.legend_loc_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        
        legend_combo = ttk.Combobox(legend_frame, textvariable=self.legend_loc_var, values=self.legend_loc_display_vals, state='readonly')
        legend_combo.pack(side=tk.LEFT, padx=5)

        # 글자 크기 설정 섹션
        font_frame = ttk.LabelFrame(parent, text='글자 크기 설정', padding=10)
        font_frame.pack(fill=tk.X, pady=5)

        # 제목 글자 크기
        title_font_frame = ttk.Frame(font_frame)
        title_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_font_frame, text='제목 글자 크기:').pack(side=tk.LEFT)

        self.title_fontsize_var = tk.IntVar(value=self.settings['title_fontsize'])
        self.title_fontsize_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        title_fontsize_entry = ttk.Entry(title_font_frame, textvariable=self.title_fontsize_var, width=8)
        title_fontsize_entry.pack(side=tk.LEFT, padx=5)

        # X축 레이블 글자 크기
        xlabel_font_frame = ttk.Frame(font_frame)
        xlabel_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xlabel_font_frame, text='X축 레이블 글자 크기:').pack(side=tk.LEFT)

        self.xlabel_fontsize_var = tk.IntVar(value=self.settings['xlabel_fontsize'])
        self.xlabel_fontsize_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        xlabel_fontsize_entry = ttk.Entry(xlabel_font_frame, textvariable=self.xlabel_fontsize_var, width=8)
        xlabel_fontsize_entry.pack(side=tk.LEFT, padx=5)

        # Y축 레이블 글자 크기
        ylabel_font_frame = ttk.Frame(font_frame)
        ylabel_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ylabel_font_frame, text='Y축 레이블 글자 크기:').pack(side=tk.LEFT)

        self.ylabel_fontsize_var = tk.IntVar(value=self.settings['ylabel_fontsize'])
        self.ylabel_fontsize_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        ylabel_fontsize_entry = ttk.Entry(ylabel_font_frame, textvariable=self.ylabel_fontsize_var, width=8)
        ylabel_fontsize_entry.pack(side=tk.LEFT, padx=5)

        # X축 숫자 글자 크기
        xtick_font_frame = ttk.Frame(font_frame)
        xtick_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xtick_font_frame, text='X축 숫자 글자 크기:').pack(side=tk.LEFT)

        self.x_tick_fontsize_var = tk.IntVar(value=self.settings['x_tick_fontsize'])
        self.x_tick_fontsize_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        xtick_fontsize_entry = ttk.Entry(xtick_font_frame, textvariable=self.x_tick_fontsize_var, width=8)
        xtick_fontsize_entry.pack(side=tk.LEFT, padx=5)

        # Y축 숫자 글자 크기
        ytick_font_frame = ttk.Frame(font_frame)
        ytick_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ytick_font_frame, text='Y축 숫자 글자 크기:').pack(side=tk.LEFT)

        self.y_tick_fontsize_var = tk.IntVar(value=self.settings['y_tick_fontsize'])
        self.y_tick_fontsize_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        ytick_fontsize_entry = ttk.Entry(ytick_font_frame, textvariable=self.y_tick_fontsize_var, width=8)
        ytick_fontsize_entry.pack(side=tk.LEFT, padx=5)

    # ========== 이벤트 핸들러 ==========

    def _on_axis_tab_changed(self, event):
        """축 설정 탭 변경 시 호출"""
        selected_tab = self.axis_notebook.index(self.axis_notebook.select())
        print(f"축 설정 탭 변경: {selected_tab}")

        # 탭 인덱스에 따라 축 타입 결정
        if selected_tab == 0:  # 숫자 축 탭
            axis_type = 'numeric'
            print("숫자축 모드로 설정됨")
        else:  # 시간 축 탭
            axis_type = 'datetime'
            print("시간축 모드로 설정됨")

        # 메인 앱의 축 타입 업데이트
        if hasattr(self.main_app, 'axis_type_var'):
            self.main_app.axis_type_var.set(axis_type)
            print(f"메인 앱의 축 타입도 '{axis_type}'로 업데이트됨")

        # 탭 활성화/비활성화 업데이트
        self._update_tab_availability()
        # 자동 채우기 금지: 사용자 입력을 유지 (초기 오픈 시에만 채움)

    def _on_x_range_modified(self, event):
        """숫자 축 범위 수정 감지"""
        print("사용자가 숫자 축 범위를 수정했습니다.")
        # 실시간 업데이트 스케줄링
        self.plot_settings_window._schedule_update()

    def _on_y_range_modified(self, event):
        """Y축 범위 수정 감지"""
        print("사용자가 Y축 범위를 수정했습니다.")
        # 실시간 업데이트 스케줄링
        self.plot_settings_window._schedule_update()

    def _on_timestamp_range_modified_simple(self, event):
        """시간축 범위 수정 감지 - 기존 main_app.py와 동일한 단순 처리"""
        try:
            print("시간축 범위 수정 감지")
            # Saving is centralized in _apply_settings

            # 디바운싱된 업데이트
            self.plot_settings_window._schedule_update()

        except Exception as e:
            print(f"시간축 범위 수정 처리 오류: {e}")

    # ========== 자동 계산 메서드 ==========

    def _auto_xlim_numeric(self):
        """숫자축 X축 범위 자동 설정"""
        try:
            # 현재 선택된 시트의 데이터 가져오기
            current_sheet = self.main_app.sheet_combo.get()
            if not current_sheet or current_sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터를 찾을 수 없습니다.')
                return

            df = self.main_app.df_map[current_sheet]
            x_col = self.main_app.x_combo.get()

            if not x_col or x_col not in df.columns:
                messagebox.showwarning('경고', 'X축 컬럼을 선택하세요.')
                return

            # 숫자 데이터로 변환
            x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
            if x_data.empty:
                messagebox.showwarning('경고', '유효한 숫자 데이터가 없습니다.')
                return

            # 범위 설정
            x_min = float(x_data.min())
            x_max = float(x_data.max())

            # 약간의 여백 추가
            x_range = x_max - x_min
            if x_range > 0:
                margin = x_range * 0.05
                x_min -= margin
                x_max += margin

            self.xlim_min_numeric_var.set(x_min)
            self.xlim_max_numeric_var.set(x_max)

            print(f"숫자축 자동 범위 설정: {x_min} ~ {x_max}")

        except Exception as e:
            messagebox.showerror('오류', f'자동 범위 설정 중 오류가 발생했습니다: {e}')
            print(f"숫자축 자동 범위 설정 오류: {e}")

    def _auto_xlim_timestamp(self):
        """시간축 X축 범위 자동 설정"""
        try:
            # 현재 선택된 시트의 데이터 가져오기
            current_sheet = self.main_app.sheet_combo.get()
            if not current_sheet or current_sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터를 찾을 수 없습니다.')
                return

            df = self.main_app.df_map[current_sheet]
            x_col = self.main_app.x_combo.get()

            if not x_col or x_col not in df.columns:
                messagebox.showwarning('경고', 'X축 컬럼을 선택하세요.')
                return

            # 시간 데이터로 변환
            x_data = self.main_app._parse_datetime_column(df, x_col).dropna()
            if x_data.empty:
                messagebox.showwarning('경고', '유효한 시간 데이터가 없습니다.')
                return

            # 범위 설정
            x_min = x_data.min()
            x_max = x_data.max()

            # 약간의 여백 추가
            x_range = x_max - x_min
            if x_range.total_seconds() > 0:
                margin = x_range * 0.05
                x_min -= margin
                x_max += margin

            self.xlim_min_timestamp_var.set(self.plot_settings_window._format_datetime(x_min))
            self.xlim_max_timestamp_var.set(self.plot_settings_window._format_datetime(x_max))

            print(f"시간축 자동 범위 설정: {x_min} ~ {x_max}")

        except Exception as e:
            messagebox.showerror('오류', f'자동 범위 설정 중 오류가 발생했습니다: {e}')
            print(f"시간축 자동 범위 설정 오류: {e}")

    def _auto_ylim_single(self):
        """Single Y축 범위 자동 설정"""
        try:
            # 현재 선택된 시트의 데이터 가져오기
            current_sheet = self.main_app.sheet_combo.get()
            if not current_sheet or current_sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터를 찾을 수 없습니다.')
                return

            df = self.main_app.df_map[current_sheet]
            if df is not None and not df.empty:
                y_selection = self.main_app.y_listbox.curselection()
                if y_selection:
                    y_col = self.main_app.y_listbox.get(y_selection[0])
                    if y_col and y_col in df.columns:
                        y_data = pd.to_numeric(df[y_col], errors='coerce').dropna()
                        if not y_data.empty:
                            margin = (y_data.max() - y_data.min()) * 0.05
                            self.ylim_min_var.set(y_data.min() - margin)
                            self.ylim_max_var.set(y_data.max() + margin)
        except Exception as e:
            print(f"Y축 자동 범위 설정 오류: {e}")

    def _update_tab_availability(self):
        """탭 활성화/비활성화 업데이트 - 원본 main_app.py와 동일한 로직"""
        try:
            # 현재 axis_type 확인
            axis_type = self.main_app.axis_type_var.get()
            print(f"현재 axis_type: {axis_type}")

            # 탭 활성화/비활성화
            if axis_type == 'datetime':
                # 시간축인 경우: 시간축 탭 활성화, 숫자축 탭 비활성화
                self.axis_notebook.tab(0, state='disabled')  # 숫자축 탭 비활성화
                self.axis_notebook.tab(1, state='normal')   # 시간축 탭 활성화
                # 시간축 탭으로 전환
                self.axis_notebook.select(1)
                print("시간축 모드: 숫자축 탭 비활성화, 시간축 탭 활성화")
            else:
                # 숫자축인 경우: 숫자축 탭 활성화, 시간축 탭 비활성화
                self.axis_notebook.tab(0, state='normal')    # 숫자축 탭 활성화
                self.axis_notebook.tab(1, state='disabled') # 시간축 탭 비활성화
                # 숫자축 탭으로 전환
                self.axis_notebook.select(0)
                print("숫자축 모드: 숫자축 탭 활성화, 시간축 탭 비활성화")

        except Exception as e:
            print(f"탭 활성화/비활성화 오류: {e}")

    # ========== 헬퍼 메서드 ==========

    def _save_current_x_range(self):
        """현재 X축 범위를 저장 - 안전한 처리"""
        try:
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()

            if not current_sheet or not x_col:
                print("시트 또는 X 컬럼이 없습니다.")
                return

            range_key = f"{current_sheet}_{x_col}"

            if not hasattr(self.main_app, '_saved_x_range'):
                self.main_app._saved_x_range = {}

            # 현재 활성화된 탭 확인
            try:
                current_tab = self.axis_notebook.index('current')
            except:
                current_tab = 1  # 기본값: 시간축 탭

            if current_tab == 0:  # 숫자축 탭
                # 숫자축인 경우
                try:
                    min_val = float(self.xlim_min_numeric_var.get())
                    max_val = float(self.xlim_max_numeric_var.get())
                    print(f"숫자축 범위 저장: {min_val} ~ {max_val}")
                except Exception as e:
                    print(f"숫자축 범위 변환 오류: {e}")
                    return

            elif current_tab == 1:  # 시간축 탭
                # 시간축인 경우 - pd.to_datetime으로 변환하여 저장
                try:
                    min_val = pd.to_datetime(self.xlim_min_timestamp_var.get())
                    max_val = pd.to_datetime(self.xlim_max_timestamp_var.get())
                    print(f"시간축 범위 저장 (datetime): {min_val} ~ {max_val}")
                except Exception as e:
                    print(f"시간축 변환 오류: {e}")
                    min_val = self.xlim_min_timestamp_var.get()
                    max_val = self.xlim_max_timestamp_var.get()
                    print(f"시간축 범위 저장 (문자열): {min_val} ~ {max_val}")
            else:
                # 기본값 사용
                min_val = 0.0
                max_val = 10.0
                print(f"기본 범위 사용: {min_val} ~ {max_val}")

            self.main_app._saved_x_range[range_key] = {
                'min': min_val,
                'max': max_val
            }

        except Exception as e:
            print(f"X축 범위 저장 오류: {e}")
            import traceback
            traceback.print_exc()

    def _save_current_y_range(self):
        """현재 Y축 범위를 저장"""
        try:
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()

            if not current_sheet or not x_col:
                print("시트 또는 X 컬럼이 없습니다.")
                return

            range_key = f"{current_sheet}_{x_col}"

            if not hasattr(self.main_app, '_saved_y_range'):
                self.main_app._saved_y_range = {}

            # Y축 범위 저장
            try:
                min_val = float(self.ylim_min_var.get())
                max_val = float(self.ylim_max_var.get())
                print(f"Y축 범위 저장: {min_val} ~ {max_val}")

                self.main_app._saved_y_range[range_key] = {
                    'min': min_val,
                    'max': max_val
                }
            except Exception as e:
                print(f"Y축 범위 변환 오류: {e}")
                return

        except Exception as e:
            print(f"Y축 범위 저장 오류: {e}")
            import traceback
            traceback.print_exc()

    def _save_current_plot_styles(self, settings):
        """현재 플롯 스타일 설정 저장"""
        try:
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()

            if not current_sheet or not x_col:
                print("시트 또는 X 컬럼이 없습니다.")
                return

            range_key = f"{current_sheet}_{x_col}"

            if not hasattr(self.main_app, '_saved_plot_styles'):
                self.main_app._saved_plot_styles = {}

            # 스타일 설정 저장
            self.main_app._saved_plot_styles[range_key] = {
                'y_colors': settings.get('y_colors', {}).copy(),
                'y_line_widths': settings.get('y_line_widths', {}).copy(),
                'y_line_styles': settings.get('y_line_styles', {}).copy(),
                'y_markers': settings.get('y_markers', {}).copy(),
                'y_marker_sizes': settings.get('y_marker_sizes', {}).copy(),
                'y_plot_types': settings.get('y_plot_types', {}).copy(),
                'x_ticks': settings.get('x_ticks', 1),
                'y_ticks': settings.get('y_ticks', 1),
            }
            print(f"스타일 설정 저장: {range_key}")
            print(f"  색상: {settings.get('y_colors', {})}")
            print(f"  X축 간격: {settings.get('x_ticks', 1)}, Y축 간격: {settings.get('y_ticks', 1)}")

        except Exception as e:
            print(f"스타일 설정 저장 오류: {e}")
            import traceback
            traceback.print_exc()

    def _format_numbers_to_timestamp(self, numbers):
        """숫자 문자열을 시간 형식으로 변환"""
        try:
            # 최소 4자리 (연도)가 있어야 함
            if len(numbers) < 4:
                return numbers

            # 기본값으로 현재 시간 사용
            import datetime
            now = datetime.datetime.now()

            # 연도
            if len(numbers) >= 4:
                year = int(numbers[:4])
                if 1900 <= year <= 2100:  # 합리적인 연도 범위
                    remaining = numbers[4:]
                else:
                    return numbers
            else:
                return numbers

            # 월
            if len(remaining) >= 2:
                month = int(remaining[:2])
                if 1 <= month <= 12:
                    remaining = remaining[2:]
                else:
                    return f"{year}-{remaining[:2] if len(remaining) >= 2 else remaining}"
            else:
                return f"{year}-{remaining if remaining else '01'}"

            # 일
            if len(remaining) >= 2:
                day = int(remaining[:2])
                if 1 <= day <= 31:
                    remaining = remaining[2:]
                else:
                    return f"{year}-{month:02d}-{remaining[:2] if len(remaining) >= 2 else remaining}"
            else:
                return f"{year}-{month:02d}-{remaining if remaining else '01'}"

            # 시간
            if len(remaining) >= 2:
                hour = int(remaining[:2])
                if 0 <= hour <= 23:
                    remaining = remaining[2:]
                else:
                    return f"{year}-{month:02d}-{day:02d} {remaining[:2] if len(remaining) >= 2 else remaining}:00:00"
            else:
                return f"{year}-{month:02d}-{day:02d} {remaining if remaining else '00'}:00:00"

            # 분
            if len(remaining) >= 2:
                minute = int(remaining[:2])
                if 0 <= minute <= 59:
                    remaining = remaining[2:]
                else:
                    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{remaining[:2] if len(remaining) >= 2 else remaining}:00"
            else:
                return f"{year}-{month:02d}-{day:02d} {hour:02d}:{remaining if remaining else '00'}:00"

            # 초
            if len(remaining) >= 2:
                second = int(remaining[:2])
                if 0 <= second <= 59:
                    remaining = remaining[2:]
                else:
                    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{remaining[:2] if len(remaining) >= 2 else remaining}"
            else:
                return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{remaining if remaining else '00'}"

            # 최종 결과
            return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

        except Exception as e:
            print(f"숫자-시간 변환 오류: {e}")
            return numbers

    # ========== 설정 관리 메서드 ==========

    def _convert_korean_time_format(self, korean_format: str) -> str:
        """한글 시간 형식을 matplotlib 형식으로 변환"""
        format_mapping = {
            '시:분:초:밀리초': '%H:%M:%S.%f',
            '시:분:초': '%H:%M:%S',
            '시:분': '%H:%M',
            '년-월-일 시:분:초': '%Y-%m-%d %H:%M:%S',
            '년-월-일 시:분': '%Y-%m-%d %H:%M',
            'YYYYMMDD_HHMM': '%Y%m%d_%H%M'
        }
        return format_mapping.get(korean_format, '%Y%m%d_%H%M')

    def _collect_settings(self):
        """현재 설정 수집"""
        settings = {
            'plot_type': 'line',  # 기본값, 실제로는 Y축 컬럼별로 설정됨
            'line_style': '-',    # 기본값, 실제로는 Y축 컬럼별로 설정됨
            'marker': 'o',        # 기본값, 실제로는 Y축 컬럼별로 설정됨
            'color': '#1f77b4',   # 기본값, 실제로는 Y축 컬럼별로 설정됨
            'line_width': 1.0,    # 기본값, 실제로는 Y축 컬럼별로 설정됨
            'marker_size': 6.0,   # 기본값, 실제로는 Y축 컬럼별로 설정됨
            'title': self.title_var.get(),
            'xlabel': self.xlabel_var.get(),
            'ylabel': self.ylabel_var.get(),
            'ylim_min': self.ylim_min_var.get(),
            'ylim_max': float(self.ylim_max_var.get()),
            'x_ticks': float(self.x_ticks_var.get()) if self.x_ticks_var and self.x_ticks_var.get() else 1,
            'y_ticks': float(self.y_ticks_var.get()) if self.y_ticks_var and self.y_ticks_var.get() else 1,
            'x_scale': self.x_scale_var.get() if self.x_scale_var else 'linear',
            'y_scale': self.y_scale_var.get() if self.y_scale_var else 'linear',
            'legend_loc': self.legend_loc_map.get(self.legend_loc_var.get(), 'best'),
            'title_fontsize': int(self.title_fontsize_var.get()),
            'xlabel_fontsize': self.xlabel_fontsize_var.get(),
            'ylabel_fontsize': self.ylabel_fontsize_var.get(),
            'x_tick_fontsize': self.x_tick_fontsize_var.get(),
            'y_tick_fontsize': self.y_tick_fontsize_var.get(),
            'is_timestamp': self.settings.get('is_timestamp', False),
            'y_columns': [self.main_app.y_listbox.get(i) for i in self.main_app.y_listbox.curselection()] if hasattr(self.main_app, 'y_listbox') else [],
        }

        # Y축 스타일 정보 수집
        if hasattr(self, 'y_color_vars'):
            settings['y_colors'] = {}
            for column_name, color_var in self.y_color_vars.items():
                settings['y_colors'][column_name] = color_var.get()

        if hasattr(self, 'y_line_width_vars'):
            settings['y_line_widths'] = {}
            for column_name, width_var in self.y_line_width_vars.items():
                settings['y_line_widths'][column_name] = width_var.get()

        if hasattr(self, 'y_line_style_vars'):
            settings['y_line_styles'] = {}
            for column_name, style_var in self.y_line_style_vars.items():
                settings['y_line_styles'][column_name] = style_var.get()

        if hasattr(self, 'y_marker_vars'):
            settings['y_markers'] = {}
            for column_name, marker_var in self.y_marker_vars.items():
                settings['y_markers'][column_name] = marker_var.get()

        if hasattr(self, 'y_marker_size_vars'):
            settings['y_marker_sizes'] = {}
            for column_name, marker_size_var in self.y_marker_size_vars.items():
                # 사용자 입력값 반영 (기본값은 UI에서 20.0으로 세팅됨)
                settings['y_marker_sizes'][column_name] = marker_size_var.get()

        if hasattr(self, 'y_plot_type_vars'):
            settings['y_plot_types'] = {}
            for column_name, plot_type_var in self.y_plot_type_vars.items():
                settings['y_plot_types'][column_name] = plot_type_var.get()

        # 시간축 관련 설정 수집
        if hasattr(self, 'time_interval_unit'):
            settings['time_interval_unit'] = self.time_interval_unit.get()
        if hasattr(self, 'time_interval_value'):
            settings['time_interval_value'] = self.time_interval_value.get()
        if hasattr(self, 'time_format'):
            # 한글 형식을 matplotlib 형식으로 변환
            korean_format = self.time_format.get()
            settings['time_format'] = self._convert_korean_time_format(korean_format)

        # X축 범위 처리 - 현재 선택된 탭에 따라 처리
        try:
            selected_tab = self.axis_notebook.select()
            tab_index = self.axis_notebook.index(selected_tab)

            # axis_type 설정 (원본 main_app.py와 동일)
            if tab_index == 1:  # 시간축 탭
                self.main_app.axis_type_var.set('datetime')
            else:  # 숫자축 탭
                self.main_app.axis_type_var.set('numeric')

            if tab_index == 0:  # 숫자축 탭
                # 항상 입력값 사용 (창 초기화 시 자동값으로 채워짐)
                settings['xlim_min'] = float(self.xlim_min_numeric_var.get())
                settings['xlim_max'] = float(self.xlim_max_numeric_var.get())

            elif tab_index == 1:  # 시간축 탭
                # 항상 입력값 사용 (창 초기화 시 자동값으로 채워짐)
                settings['xlim_min'] = pd.to_datetime(self.xlim_min_timestamp_var.get())
                settings['xlim_max'] = pd.to_datetime(self.xlim_max_timestamp_var.get())

        except Exception as e:
            print(f"X축 범위 처리 오류: {e}")
            # 기본값 사용
            settings['xlim_min'] = 0.0
            settings['xlim_max'] = 10.0

        return settings

    def _validate_settings(self, settings):
        """설정값 검증"""
        try:
            # 선 두께 검증
            if not (0.5 <= settings['line_width'] <= 10.0):
                messagebox.showerror('오류', '선 두께는 0.5~10.0 범위여야 합니다.')
                return False

            # 마커 크기 검증
            if not (1 <= settings['marker_size'] <= 50):
                messagebox.showerror('오류', '마커 크기는 1~50 범위여야 합니다.')
                return False

            # 축 간격 단위 검증 (제한 완전 해제 - 0보다 큰 값만 확인)
            if settings['x_ticks'] <= 0:
                messagebox.showerror('오류', 'X축 간격 단위는 0보다 커야 합니다.')
                return False

            if settings['y_ticks'] <= 0:
                messagebox.showerror('오류', 'Y축 간격 단위는 0보다 커야 합니다.')
                return False

            # 글자 크기 검증
            if not (8 <= settings['title_fontsize'] <= 30):
                messagebox.showerror('오류', '제목 글자 크기는 8~30 범위여야 합니다.')
                return False

            if not (8 <= settings['xlabel_fontsize'] <= 24):
                messagebox.showerror('오류', 'X축 레이블 글자 크기는 8~24 범위여야 합니다.')
                return False

            if not (8 <= settings['ylabel_fontsize'] <= 24):
                messagebox.showerror('오류', 'Y축 레이블 글자 크기는 8~24 범위여야 합니다.')
                return False

            if not (6 <= settings['x_tick_fontsize'] <= 20):
                messagebox.showerror('오류', 'X축 숫자 글자 크기는 6~20 범위여야 합니다.')
                return False

            if not (6 <= settings['y_tick_fontsize'] <= 20):
                messagebox.showerror('오류', 'Y축 숫자 글자 크기는 6~20 범위여야 합니다.')
                return False

            # 축 범위 검증
            if settings['xlim_min'] >= settings['xlim_max']:
                messagebox.showerror('오류', 'X축 최솟값은 최댓값보다 작아야 합니다.')
                return False

            if settings['ylim_min'] >= settings['ylim_max']:
                messagebox.showerror('오류', 'Y축 최솟값은 최댓값보다 작아야 합니다.')
                return False

            return True

        except Exception as e:
            messagebox.showerror('오류', f'설정 검증 중 오류가 발생했습니다: {e}')
            return False

    def collect_settings(self):
        """설정을 딕셔너리로 반환"""
        return self._collect_settings()


    def validate_settings(self, settings):
        """설정값 검증"""
        return self._validate_settings(settings)
