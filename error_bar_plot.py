"""
Error Bar Plot 설정 모듈
- 반복 측정 데이터: 여러 Y 컬럼의 평균/표준편차 자동 계산
- 미리 계산된 데이터: Y 평균과 Y 에러 컬럼 직접 지정
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd


class ErrorBarSettings:
    """Error Bar Plot 설정을 위한 모든 UI와 로직을 포함하는 클래스"""

    def __init__(self, parent_tab, plot_settings_window, main_app):
        """
        Args:
            parent_tab: Tkinter Frame (error_bar_tab)
            plot_settings_window: PlotSettingsWindow 인스턴스
            main_app: MainApp 인스턴스
        """
        self.parent_tab = parent_tab
        self.plot_settings_window = plot_settings_window
        self.main_app = main_app
        self.settings = plot_settings_window.settings
        if self.settings is None:
            print("Warning: ErrorBarSettings received None for settings. Initializing to {}.")
            self.settings = {}

        # 변수 초기화
        self._initialize_variables()

        # UI 구축
        self._build_ui_in_tab(self.parent_tab)

    def _initialize_variables(self):
        """모든 Error Bar 변수 초기화"""
        # 데이터 모드 (repeated: 반복 측정, precalculated: 미리 계산된)
        self.data_mode_var = None

        # 반복 측정 모드용 변수
        self.y_columns_listbox = None  # 여러 Y 컬럼 선택

        # 미리 계산된 모드용 변수
        self.y_mean_var = None  # Y 평균 컬럼
        self.y_error_var = None  # Y 에러 컬럼

        # 에러바 스타일
        self.color_var = None
        self.capsize_var = None
        self.capthick_var = None
        self.line_width_var = None
        self.marker_var = None
        self.marker_size_var = None
        self.ecolor_var = None  # 에러바 색상

        # 축 범위
        self.xlim_min_var = None
        self.xlim_max_var = None
        self.ylim_min_var = None
        self.ylim_max_var = None

        # 축 간격
        self.x_ticks_var = None
        self.y_ticks_var = None

        # 라벨/제목
        self.title_var = None
        self.xlabel_var = None
        self.ylabel_var = None

        # 폰트 크기
        self.title_fontsize_var = None
        self.xlabel_fontsize_var = None
        self.ylabel_fontsize_var = None
        self.x_tick_fontsize_var = None
        self.y_tick_fontsize_var = None

        # 범례 위치
        self.legend_loc_var = None

        # 그리드
        self.show_grid_var = None

    def _build_ui_in_tab(self, parent):
        """Error Bar 탭 UI 구축"""
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

        # 데이터 모드 선택 섹션
        self._build_data_mode_section(scrollable_frame)

        # 데이터 선택 섹션 (모드에 따라 변경됨)
        self._build_data_selection_section(scrollable_frame)

        # 에러바 스타일 섹션
        self._build_errorbar_style_section(scrollable_frame)

        # 축 설정 섹션
        self._build_axis_section(scrollable_frame)

        # 제목 및 레이블 섹션
        self._build_labels_section(scrollable_frame)

        # 캔버스와 스크롤바 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _get_saved_error_bar_settings(self):
        """저장된 Error Bar 설정 가져오기"""
        try:
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"

            if not hasattr(self.main_app, '_saved_error_bar_settings'):
                self.main_app._saved_error_bar_settings = {}

            return self.main_app._saved_error_bar_settings.get(range_key, {})
        except:
            return {}

    def _save_error_bar_settings(self):
        """현재 Error Bar 설정 저장"""
        try:
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"

            if not hasattr(self.main_app, '_saved_error_bar_settings'):
                self.main_app._saved_error_bar_settings = {}

            # 현재 설정 수집
            settings = {
                'data_mode': self.data_mode_var.get() if self.data_mode_var else 'repeated',
            }

            # 반복 측정 모드 - 선택된 Y 컬럼들 저장
            if self.y_columns_listbox:
                selected_indices = self.y_columns_listbox.curselection()
                settings['y_columns'] = [self.y_columns_listbox.get(i) for i in selected_indices]

            # 미리 계산된 모드 - Y 평균/에러 컬럼 저장
            if self.y_mean_var:
                settings['y_mean_column'] = self.y_mean_var.get()
            if self.y_error_var:
                settings['y_error_column'] = self.y_error_var.get()

            # 스타일 설정 저장
            if self.color_var:
                settings['color'] = self.color_var.get()
            if self.ecolor_var:
                settings['ecolor'] = self.ecolor_var.get()
            if self.capsize_var:
                settings['capsize'] = self.capsize_var.get()
            if self.capthick_var:
                settings['capthick'] = self.capthick_var.get()
            if self.line_width_var:
                settings['line_width'] = self.line_width_var.get()
            if self.marker_var:
                settings['marker'] = self.marker_var.get()
            if self.marker_size_var:
                settings['marker_size'] = self.marker_size_var.get()

            # 축 설정 저장
            if self.xlim_min_var:
                settings['xlim_min'] = self.xlim_min_var.get()
            if self.xlim_max_var:
                settings['xlim_max'] = self.xlim_max_var.get()
            if self.ylim_min_var:
                settings['ylim_min'] = self.ylim_min_var.get()
            if self.ylim_max_var:
                settings['ylim_max'] = self.ylim_max_var.get()
            if self.x_ticks_var:
                settings['x_ticks'] = self.x_ticks_var.get()
            if self.y_ticks_var:
                settings['y_ticks'] = self.y_ticks_var.get()

            # 레이블 설정 저장
            if self.title_var:
                settings['title'] = self.title_var.get()
            if self.xlabel_var:
                settings['xlabel'] = self.xlabel_var.get()
            if self.ylabel_var:
                settings['ylabel'] = self.ylabel_var.get()
            if self.legend_loc_var:
                settings['legend_loc_display'] = self.legend_loc_var.get()

            # 폰트 크기 저장
            if self.title_fontsize_var:
                settings['title_fontsize'] = self.title_fontsize_var.get()
            if self.xlabel_fontsize_var:
                settings['xlabel_fontsize'] = self.xlabel_fontsize_var.get()
            if self.ylabel_fontsize_var:
                settings['ylabel_fontsize'] = self.ylabel_fontsize_var.get()
            if self.x_tick_fontsize_var:
                settings['x_tick_fontsize'] = self.x_tick_fontsize_var.get()
            if self.y_tick_fontsize_var:
                settings['y_tick_fontsize'] = self.y_tick_fontsize_var.get()

            self.main_app._saved_error_bar_settings[range_key] = settings
            print(f"Error Bar 설정 저장: {range_key}")
        except Exception as e:
            print(f"Error Bar 설정 저장 오류: {e}")

    def _build_data_mode_section(self, parent):
        """데이터 모드 선택 섹션"""
        mode_frame = ttk.LabelFrame(parent, text='데이터 모드 선택', padding=10)
        mode_frame.pack(fill=tk.X, pady=5)

        # 저장된 설정에서 모드 복원
        saved_settings = self._get_saved_error_bar_settings()
        saved_mode = saved_settings.get('data_mode', 'repeated')

        self.data_mode_var = tk.StringVar(value=saved_mode)

        # 라디오 버튼
        repeated_radio = ttk.Radiobutton(
            mode_frame,
            text='반복 측정 데이터 (여러 Y 컬럼의 평균/표준편차 자동 계산)',
            variable=self.data_mode_var,
            value='repeated',
            command=self._on_mode_changed
        )
        repeated_radio.pack(anchor=tk.W, pady=2)

        precalc_radio = ttk.Radiobutton(
            mode_frame,
            text='미리 계산된 데이터 (Y 평균과 Y 에러 컬럼 직접 지정)',
            variable=self.data_mode_var,
            value='precalculated',
            command=self._on_mode_changed
        )
        precalc_radio.pack(anchor=tk.W, pady=2)

        # 모드 설명 - 저장된 모드에 따라 텍스트 설정
        if saved_mode == 'repeated':
            desc_text = '각 행에서 선택한 Y 컬럼들의 평균과 표준편차를 계산하여 에러바로 표시합니다.'
        else:
            desc_text = '이미 계산된 Y 평균값과 에러값 컬럼을 직접 지정합니다.'

        self.mode_description = ttk.Label(
            mode_frame,
            text=desc_text,
            font=('Arial', 9),
            foreground='gray'
        )
        self.mode_description.pack(anchor=tk.W, pady=(5, 0))

    def _build_data_selection_section(self, parent):
        """데이터 선택 섹션"""
        self.data_selection_frame = ttk.LabelFrame(parent, text='데이터 선택', padding=10)
        self.data_selection_frame.pack(fill=tk.X, pady=5)

        # 내부 컨테이너 (모드에 따라 내용 변경)
        self.data_selection_container = ttk.Frame(self.data_selection_frame)
        self.data_selection_container.pack(fill=tk.X)

        # 저장된 모드에 따라 UI 구성
        saved_settings = self._get_saved_error_bar_settings()
        saved_mode = saved_settings.get('data_mode', 'repeated')

        if saved_mode == 'repeated':
            self._build_repeated_mode_ui()
        else:
            self._build_precalculated_mode_ui()

    def _build_repeated_mode_ui(self):
        """반복 측정 모드 UI"""
        # 기존 위젯 제거
        for widget in self.data_selection_container.winfo_children():
            widget.destroy()

        # Y 컬럼 선택 (복수 선택)
        ttk.Label(
            self.data_selection_container,
            text='Y 데이터 컬럼 선택 (Shift+클릭으로 범위 선택, Ctrl+클릭으로 개별 선택):',
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))

        # Listbox 프레임
        listbox_frame = ttk.Frame(self.data_selection_container)
        listbox_frame.pack(fill=tk.X, pady=(0, 5))

        # EXTENDED 모드: Shift+클릭으로 범위 선택, Ctrl+클릭으로 개별 추가/제거
        self.y_columns_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.EXTENDED,
            width=50,
            height=8,
            exportselection=False
        )
        self.y_columns_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.y_columns_listbox.yview)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.y_columns_listbox.configure(yscrollcommand=listbox_scrollbar.set)

        # 컬럼 목록 로드 및 저장된 선택 복원
        self._load_columns_to_listbox()

        # 선택 변경 시 설정 저장 및 업데이트
        def on_selection_changed(event=None):
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        self.y_columns_listbox.bind('<<ListboxSelect>>', on_selection_changed)

        # 안내 문구
        ttk.Label(
            self.data_selection_container,
            text='예: B, C, D, E, F, G, H 열을 선택하면 각 행에서 7개 값의 평균±표준편차를 계산합니다.',
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor=tk.W)

    def _build_precalculated_mode_ui(self):
        """미리 계산된 모드 UI"""
        # 기존 위젯 제거
        for widget in self.data_selection_container.winfo_children():
            widget.destroy()

        # 저장된 설정 가져오기
        saved_settings = self._get_saved_error_bar_settings()

        # Y 평균 컬럼 선택
        mean_frame = ttk.Frame(self.data_selection_container)
        mean_frame.pack(fill=tk.X, pady=5)

        ttk.Label(mean_frame, text='Y 평균 컬럼:', width=15).pack(side=tk.LEFT)

        self.y_mean_var = tk.StringVar(value=saved_settings.get('y_mean_column', ''))
        self.y_mean_combo = ttk.Combobox(mean_frame, textvariable=self.y_mean_var, width=30, state='readonly')
        self.y_mean_combo.pack(side=tk.LEFT, padx=5)

        # 선택 변경 시 설정 저장 및 업데이트
        def on_mean_selected(event=None):
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        self.y_mean_combo.bind('<<ComboboxSelected>>', on_mean_selected)

        # Y 에러 컬럼 선택
        error_frame = ttk.Frame(self.data_selection_container)
        error_frame.pack(fill=tk.X, pady=5)

        ttk.Label(error_frame, text='Y 에러 컬럼:', width=15).pack(side=tk.LEFT)

        self.y_error_var = tk.StringVar(value=saved_settings.get('y_error_column', ''))
        self.y_error_combo = ttk.Combobox(error_frame, textvariable=self.y_error_var, width=30, state='readonly')
        self.y_error_combo.pack(side=tk.LEFT, padx=5)

        # 선택 변경 시 설정 저장 및 업데이트
        def on_error_selected(event=None):
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        self.y_error_combo.bind('<<ComboboxSelected>>', on_error_selected)

        # 컬럼 목록 로드
        self._load_columns_to_combos()

        # 안내 문구
        ttk.Label(
            self.data_selection_container,
            text='예: Y평균 컬럼에 평균값, Y에러 컬럼에 표준편차 또는 에러값이 있는 경우 사용합니다.',
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(5, 0))

    def _load_columns_to_listbox(self):
        """Listbox에 컬럼 목록 로드 및 저장된 선택 복원"""
        try:
            sheet = self.main_app.sheet_combo.get()
            if sheet and sheet in self.main_app.df_map:
                df = self.main_app.df_map[sheet]
                cols = list(df.columns.astype(str))

                self.y_columns_listbox.delete(0, tk.END)
                for col in cols:
                    self.y_columns_listbox.insert(tk.END, col)

                # 저장된 선택 복원
                saved_settings = self._get_saved_error_bar_settings()
                saved_columns = saved_settings.get('y_columns', [])

                if saved_columns:
                    for i, col in enumerate(cols):
                        if col in saved_columns:
                            self.y_columns_listbox.select_set(i)
                    print(f"저장된 Y 컬럼 선택 복원: {saved_columns}")
        except Exception as e:
            print(f"컬럼 목록 로드 오류: {e}")

    def _load_columns_to_combos(self):
        """Combobox에 컬럼 목록 로드"""
        try:
            sheet = self.main_app.sheet_combo.get()
            if sheet and sheet in self.main_app.df_map:
                df = self.main_app.df_map[sheet]
                cols = list(df.columns.astype(str))

                self.y_mean_combo['values'] = cols
                self.y_error_combo['values'] = cols
        except Exception as e:
            print(f"컬럼 목록 로드 오류: {e}")

    def _on_mode_changed(self):
        """데이터 모드 변경 시 호출"""
        mode = self.data_mode_var.get()

        if mode == 'repeated':
            self.mode_description.config(
                text='각 행에서 선택한 Y 컬럼들의 평균과 표준편차를 계산하여 에러바로 표시합니다.'
            )
            self._build_repeated_mode_ui()
        else:
            self.mode_description.config(
                text='이미 계산된 Y 평균값과 에러값 컬럼을 직접 지정합니다.'
            )
            self._build_precalculated_mode_ui()

        # 모드 변경 시 설정 저장
        self._save_error_bar_settings()

    def _build_errorbar_style_section(self, parent):
        """에러바 스타일 섹션"""
        style_frame = ttk.LabelFrame(parent, text='에러바 스타일', padding=10)
        style_frame.pack(fill=tk.X, pady=5)

        # 저장된 설정 가져오기
        saved_settings = self._get_saved_error_bar_settings()

        # 첫 번째 행: 색상, 에러바 색상
        row1 = ttk.Frame(style_frame)
        row1.pack(fill=tk.X, pady=2)

        # 데이터 색상 (저장된 값 복원)
        saved_color = saved_settings.get('color', '#2E86AB')
        ttk.Label(row1, text='데이터 색상:', width=12).pack(side=tk.LEFT)
        self.color_var = tk.StringVar(value=saved_color)
        color_entry = ttk.Entry(row1, textvariable=self.color_var, width=10)
        color_entry.pack(side=tk.LEFT, padx=2)

        color_btn = ttk.Button(row1, text='선택', command=self._choose_color)
        color_btn.pack(side=tk.LEFT, padx=2)

        self.color_preview = tk.Frame(row1, width=20, height=15, bg=saved_color, relief=tk.SUNKEN, bd=1)
        self.color_preview.pack(side=tk.LEFT, padx=5)

        # 에러바 색상 (저장된 값 복원)
        saved_ecolor = saved_settings.get('ecolor', '#2E86AB')
        ttk.Label(row1, text='에러바 색상:', width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.ecolor_var = tk.StringVar(value=saved_ecolor)
        ecolor_entry = ttk.Entry(row1, textvariable=self.ecolor_var, width=10)
        ecolor_entry.pack(side=tk.LEFT, padx=2)

        ecolor_btn = ttk.Button(row1, text='선택', command=self._choose_ecolor)
        ecolor_btn.pack(side=tk.LEFT, padx=2)

        self.ecolor_preview = tk.Frame(row1, width=20, height=15, bg=saved_ecolor, relief=tk.SUNKEN, bd=1)
        self.ecolor_preview.pack(side=tk.LEFT, padx=5)

        # 두 번째 행: 캡 크기, 캡 두께 (저장된 값 복원)
        row2 = ttk.Frame(style_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text='캡 크기:', width=12).pack(side=tk.LEFT)
        self.capsize_var = tk.DoubleVar(value=saved_settings.get('capsize', 5.0))
        capsize_entry = ttk.Entry(row2, textvariable=self.capsize_var, width=8)
        capsize_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(row2, text='캡 두께:', width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.capthick_var = tk.DoubleVar(value=saved_settings.get('capthick', 2.0))
        capthick_entry = ttk.Entry(row2, textvariable=self.capthick_var, width=8)
        capthick_entry.pack(side=tk.LEFT, padx=2)

        # 세 번째 행: 선 굵기 (저장된 값 복원)
        row3 = ttk.Frame(style_frame)
        row3.pack(fill=tk.X, pady=2)

        ttk.Label(row3, text='선 굵기:', width=12).pack(side=tk.LEFT)
        self.line_width_var = tk.DoubleVar(value=saved_settings.get('line_width', 2.0))
        line_width_entry = ttk.Entry(row3, textvariable=self.line_width_var, width=8)
        line_width_entry.pack(side=tk.LEFT, padx=2)

        # 네 번째 행: 마커, 마커 크기 (저장된 값 복원)
        row4 = ttk.Frame(style_frame)
        row4.pack(fill=tk.X, pady=2)

        ttk.Label(row4, text='마커:', width=12).pack(side=tk.LEFT)
        self.marker_var = tk.StringVar(value=saved_settings.get('marker', 'o'))
        marker_combo = ttk.Combobox(row4, textvariable=self.marker_var, width=8, state='readonly')
        marker_combo['values'] = ['o', 's', '^', 'v', 'D', 'p', '*', '+', 'x', 'None']
        marker_combo.pack(side=tk.LEFT, padx=2)

        ttk.Label(row4, text='마커 크기:', width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.marker_size_var = tk.DoubleVar(value=saved_settings.get('marker_size', 8.0))
        marker_size_entry = ttk.Entry(row4, textvariable=self.marker_size_var, width=8)
        marker_size_entry.pack(side=tk.LEFT, padx=2)

        # 그리드 표시 기본값 False (UI 제거)
        self.show_grid_var = tk.BooleanVar(value=False)

        # 색상 변경 시 미리보기 업데이트 및 설정 저장
        def on_color_changed(*args):
            self._update_color_preview()
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        def on_ecolor_changed(*args):
            self._update_ecolor_preview()
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        self.color_var.trace('w', on_color_changed)
        self.ecolor_var.trace('w', on_ecolor_changed)

        # 스타일 변경 시 업데이트 및 설정 저장
        def on_style_changed(*args):
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        for var in [self.capsize_var, self.capthick_var, self.line_width_var, self.marker_size_var]:
            var.trace('w', on_style_changed)
        self.marker_var.trace('w', on_style_changed)

    def _choose_color(self):
        """데이터 색상 선택"""
        color = colorchooser.askcolor(title='데이터 색상 선택', color=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])

    def _choose_ecolor(self):
        """에러바 색상 선택"""
        color = colorchooser.askcolor(title='에러바 색상 선택', color=self.ecolor_var.get())
        if color[1]:
            self.ecolor_var.set(color[1])

    def _update_color_preview(self):
        """색상 미리보기 업데이트"""
        try:
            self.color_preview.config(bg=self.color_var.get())
        except:
            pass

    def _update_ecolor_preview(self):
        """에러바 색상 미리보기 업데이트"""
        try:
            self.ecolor_preview.config(bg=self.ecolor_var.get())
        except:
            pass

    def _build_axis_section(self, parent):
        """축 설정 섹션"""
        axis_frame = ttk.LabelFrame(parent, text='축 설정', padding=10)
        axis_frame.pack(fill=tk.X, pady=5)

        # 저장된 설정 가져오기
        saved_settings = self._get_saved_error_bar_settings()

        # X축 범위 (저장된 값 복원)
        xlim_frame = ttk.Frame(axis_frame)
        xlim_frame.pack(fill=tk.X, pady=2)

        ttk.Label(xlim_frame, text='X축 범위:').pack(side=tk.LEFT)

        self.xlim_min_var = tk.DoubleVar(value=saved_settings.get('xlim_min', self.settings.get('xlim_min', 0.0)))
        xlim_min_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_var, width=10)
        xlim_min_entry.pack(side=tk.LEFT, padx=2)
        xlim_min_entry.bind('<KeyRelease>', self._on_axis_modified)

        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)

        self.xlim_max_var = tk.DoubleVar(value=saved_settings.get('xlim_max', self.settings.get('xlim_max', 10.0)))
        xlim_max_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_var, width=10)
        xlim_max_entry.pack(side=tk.LEFT, padx=2)
        xlim_max_entry.bind('<KeyRelease>', self._on_axis_modified)

        ttk.Button(xlim_frame, text='자동', command=self._auto_xlim).pack(side=tk.LEFT, padx=5)

        # Y축 범위 (저장된 값 복원)
        ylim_frame = ttk.Frame(axis_frame)
        ylim_frame.pack(fill=tk.X, pady=2)

        ttk.Label(ylim_frame, text='Y축 범위:').pack(side=tk.LEFT)

        self.ylim_min_var = tk.DoubleVar(value=saved_settings.get('ylim_min', self.settings.get('ylim_min', 0.0)))
        ylim_min_entry = ttk.Entry(ylim_frame, textvariable=self.ylim_min_var, width=10)
        ylim_min_entry.pack(side=tk.LEFT, padx=2)
        ylim_min_entry.bind('<KeyRelease>', self._on_axis_modified)

        ttk.Label(ylim_frame, text='~').pack(side=tk.LEFT)

        self.ylim_max_var = tk.DoubleVar(value=saved_settings.get('ylim_max', self.settings.get('ylim_max', 10.0)))
        ylim_max_entry = ttk.Entry(ylim_frame, textvariable=self.ylim_max_var, width=10)
        ylim_max_entry.pack(side=tk.LEFT, padx=2)
        ylim_max_entry.bind('<KeyRelease>', self._on_axis_modified)

        ttk.Button(ylim_frame, text='자동', command=self._auto_ylim).pack(side=tk.LEFT, padx=5)

        # X축 간격 (저장된 값 복원)
        xticks_frame = ttk.Frame(axis_frame)
        xticks_frame.pack(fill=tk.X, pady=2)

        ttk.Label(xticks_frame, text='X축 간격 단위:').pack(side=tk.LEFT)
        self.x_ticks_var = tk.DoubleVar(value=saved_settings.get('x_ticks', 1.0))
        xticks_entry = ttk.Entry(xticks_frame, textvariable=self.x_ticks_var, width=8)
        xticks_entry.pack(side=tk.LEFT, padx=5)
        xticks_entry.bind('<KeyRelease>', self._on_axis_modified)

        # Y축 간격 (저장된 값 복원)
        yticks_frame = ttk.Frame(axis_frame)
        yticks_frame.pack(fill=tk.X, pady=2)

        ttk.Label(yticks_frame, text='Y축 간격 단위:').pack(side=tk.LEFT)
        self.y_ticks_var = tk.DoubleVar(value=saved_settings.get('y_ticks', 1.0))
        yticks_entry = ttk.Entry(yticks_frame, textvariable=self.y_ticks_var, width=8)
        yticks_entry.pack(side=tk.LEFT, padx=5)
        yticks_entry.bind('<KeyRelease>', self._on_axis_modified)

    def _build_labels_section(self, parent):
        """제목 및 레이블 섹션"""
        labels_frame = ttk.LabelFrame(parent, text='제목 및 레이블', padding=10)
        labels_frame.pack(fill=tk.X, pady=5)

        # 저장된 설정 가져오기
        saved_settings = self._get_saved_error_bar_settings()

        # 설정 저장 및 업데이트 콜백
        def on_label_changed(*args):
            self._save_error_bar_settings()
            self.plot_settings_window._schedule_update()

        # 그래프 제목 (저장된 값 복원)
        title_frame = ttk.Frame(labels_frame)
        title_frame.pack(fill=tk.X, pady=2)

        ttk.Label(title_frame, text='그래프 제목:').pack(side=tk.LEFT)
        self.title_var = tk.StringVar(value=saved_settings.get('title', self.settings.get('title', '')))
        self.title_var.trace('w', on_label_changed)
        ttk.Entry(title_frame, textvariable=self.title_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # X축 레이블 (저장된 값 복원)
        xlabel_frame = ttk.Frame(labels_frame)
        xlabel_frame.pack(fill=tk.X, pady=2)

        ttk.Label(xlabel_frame, text='X축 레이블:').pack(side=tk.LEFT)
        self.xlabel_var = tk.StringVar(value=saved_settings.get('xlabel', self.settings.get('xlabel', '')))
        self.xlabel_var.trace('w', on_label_changed)
        ttk.Entry(xlabel_frame, textvariable=self.xlabel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Y축 레이블 (저장된 값 복원)
        ylabel_frame = ttk.Frame(labels_frame)
        ylabel_frame.pack(fill=tk.X, pady=2)

        ttk.Label(ylabel_frame, text='Y축 레이블:').pack(side=tk.LEFT)
        self.ylabel_var = tk.StringVar(value=saved_settings.get('ylabel', self.settings.get('ylabel', '')))
        self.ylabel_var.trace('w', on_label_changed)
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

        self.legend_loc_map = {v: k for k, v in legend_options.items()}
        self.legend_loc_display_vals = list(legend_options.values())

        # 저장된 범례 위치 복원
        saved_legend_display = saved_settings.get('legend_loc_display', '최적 위치(Auto)')
        self.legend_loc_var = tk.StringVar(value=saved_legend_display)
        self.legend_loc_var.trace('w', on_label_changed)

        legend_combo = ttk.Combobox(legend_frame, textvariable=self.legend_loc_var,
                                   values=self.legend_loc_display_vals, state='readonly')
        legend_combo.pack(side=tk.LEFT, padx=5)

        # 글자 크기 설정 섹션
        font_frame = ttk.LabelFrame(parent, text='글자 크기 설정', padding=10)
        font_frame.pack(fill=tk.X, pady=5)

        # 제목 글자 크기 (저장된 값 복원)
        title_font_frame = ttk.Frame(font_frame)
        title_font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(title_font_frame, text='제목 글자 크기:').pack(side=tk.LEFT)
        self.title_fontsize_var = tk.IntVar(value=saved_settings.get('title_fontsize', self.settings.get('title_fontsize', 14)))
        self.title_fontsize_var.trace('w', on_label_changed)
        ttk.Entry(title_font_frame, textvariable=self.title_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

        # X축 레이블 글자 크기 (저장된 값 복원)
        xlabel_font_frame = ttk.Frame(font_frame)
        xlabel_font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(xlabel_font_frame, text='X축 레이블 글자 크기:').pack(side=tk.LEFT)
        self.xlabel_fontsize_var = tk.IntVar(value=saved_settings.get('xlabel_fontsize', self.settings.get('xlabel_fontsize', 12)))
        self.xlabel_fontsize_var.trace('w', on_label_changed)
        ttk.Entry(xlabel_font_frame, textvariable=self.xlabel_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

        # Y축 레이블 글자 크기 (저장된 값 복원)
        ylabel_font_frame = ttk.Frame(font_frame)
        ylabel_font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(ylabel_font_frame, text='Y축 레이블 글자 크기:').pack(side=tk.LEFT)
        self.ylabel_fontsize_var = tk.IntVar(value=saved_settings.get('ylabel_fontsize', self.settings.get('ylabel_fontsize', 12)))
        self.ylabel_fontsize_var.trace('w', on_label_changed)
        ttk.Entry(ylabel_font_frame, textvariable=self.ylabel_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

        # X축 숫자 글자 크기 (저장된 값 복원)
        xtick_font_frame = ttk.Frame(font_frame)
        xtick_font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(xtick_font_frame, text='X축 숫자 글자 크기:').pack(side=tk.LEFT)
        self.x_tick_fontsize_var = tk.IntVar(value=saved_settings.get('x_tick_fontsize', self.settings.get('x_tick_fontsize', 12)))
        self.x_tick_fontsize_var.trace('w', on_label_changed)
        ttk.Entry(xtick_font_frame, textvariable=self.x_tick_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

        # Y축 숫자 글자 크기 (저장된 값 복원)
        ytick_font_frame = ttk.Frame(font_frame)
        ytick_font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(ytick_font_frame, text='Y축 숫자 글자 크기:').pack(side=tk.LEFT)
        self.y_tick_fontsize_var = tk.IntVar(value=saved_settings.get('y_tick_fontsize', self.settings.get('y_tick_fontsize', 12)))
        self.y_tick_fontsize_var.trace('w', on_label_changed)
        ttk.Entry(ytick_font_frame, textvariable=self.y_tick_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

    def _on_axis_modified(self, event=None):
        """축 설정 수정 시 호출 - 설정 저장 및 업데이트"""
        self._save_error_bar_settings()
        self.plot_settings_window._schedule_update()

    def _auto_xlim(self):
        """X축 범위 자동 설정"""
        try:
            sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()

            if not sheet or not x_col:
                messagebox.showwarning('경고', '시트와 X 컬럼을 선택하세요.')
                return

            df = self.main_app.df_map[sheet]
            x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()

            if x_data.empty:
                messagebox.showwarning('경고', '유효한 X 데이터가 없습니다.')
                return

            x_min, x_max = x_data.min(), x_data.max()
            margin = (x_max - x_min) * 0.05 if x_max > x_min else 1

            self.xlim_min_var.set(x_min - margin)
            self.xlim_max_var.set(x_max + margin)

            # 설정 저장
            self._save_error_bar_settings()

        except Exception as e:
            messagebox.showerror('오류', f'X축 자동 범위 설정 오류: {e}')

    def _auto_ylim(self):
        """Y축 범위 자동 설정"""
        try:
            sheet = self.main_app.sheet_combo.get()
            if not sheet:
                messagebox.showwarning('경고', '시트를 선택하세요.')
                return

            df = self.main_app.df_map[sheet]
            mode = self.data_mode_var.get()

            if mode == 'repeated':
                # 반복 측정 모드: 선택된 Y 컬럼들의 전체 범위
                selected_indices = self.y_columns_listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning('경고', 'Y 컬럼을 선택하세요.')
                    return

                y_columns = [self.y_columns_listbox.get(i) for i in selected_indices]
                all_values = []
                for col in y_columns:
                    if col in df.columns:
                        vals = pd.to_numeric(df[col], errors='coerce').dropna()
                        all_values.extend(vals.tolist())

                if not all_values:
                    messagebox.showwarning('경고', '유효한 Y 데이터가 없습니다.')
                    return

                # 평균 + 표준편차 범위 계산
                y_data = np.array(all_values)
                y_min, y_max = y_data.min(), y_data.max()

            else:
                # 미리 계산된 모드: 평균 + 에러 범위
                y_mean_col = self.y_mean_var.get()
                y_error_col = self.y_error_var.get()

                if not y_mean_col:
                    messagebox.showwarning('경고', 'Y 평균 컬럼을 선택하세요.')
                    return

                y_mean = pd.to_numeric(df[y_mean_col], errors='coerce').dropna()
                if y_error_col and y_error_col in df.columns:
                    y_error = pd.to_numeric(df[y_error_col], errors='coerce').dropna()
                    y_min = (y_mean - y_error).min()
                    y_max = (y_mean + y_error).max()
                else:
                    y_min, y_max = y_mean.min(), y_mean.max()

            margin = (y_max - y_min) * 0.1 if y_max > y_min else 1

            self.ylim_min_var.set(y_min - margin)
            self.ylim_max_var.set(y_max + margin)

            # 설정 저장
            self._save_error_bar_settings()

        except Exception as e:
            messagebox.showerror('오류', f'Y축 자동 범위 설정 오류: {e}')

    def collect_settings(self):
        """현재 설정 수집"""
        settings = {
            'plot_mode': 'errorbar',  # Error Bar 모드 표시
            'data_mode': self.data_mode_var.get(),

            # 에러바 스타일
            'color': self.color_var.get(),
            'ecolor': self.ecolor_var.get(),
            'capsize': self.capsize_var.get(),
            'capthick': self.capthick_var.get(),
            'line_width': self.line_width_var.get(),
            'marker': self.marker_var.get(),
            'marker_size': self.marker_size_var.get(),
            'show_grid': self.show_grid_var.get(),

            # 축 설정
            'xlim_min': self.xlim_min_var.get(),
            'xlim_max': self.xlim_max_var.get(),
            'ylim_min': self.ylim_min_var.get(),
            'ylim_max': self.ylim_max_var.get(),
            'x_ticks': self.x_ticks_var.get(),
            'y_ticks': self.y_ticks_var.get(),

            # 레이블
            'title': self.title_var.get(),
            'xlabel': self.xlabel_var.get(),
            'ylabel': self.ylabel_var.get(),
            'legend_loc': self.legend_loc_map.get(self.legend_loc_var.get(), 'best'),

            # 폰트 크기
            'title_fontsize': self.title_fontsize_var.get(),
            'xlabel_fontsize': self.xlabel_fontsize_var.get(),
            'ylabel_fontsize': self.ylabel_fontsize_var.get(),
            'x_tick_fontsize': self.x_tick_fontsize_var.get(),
            'y_tick_fontsize': self.y_tick_fontsize_var.get(),
        }

        # 데이터 모드에 따른 추가 설정
        if self.data_mode_var.get() == 'repeated':
            selected_indices = self.y_columns_listbox.curselection()
            settings['y_columns'] = [self.y_columns_listbox.get(i) for i in selected_indices]
        else:
            settings['y_mean_column'] = self.y_mean_var.get() if self.y_mean_var else ''
            settings['y_error_column'] = self.y_error_var.get() if self.y_error_var else ''

        return settings

    def validate_settings(self, settings):
        """설정값 검증"""
        try:
            # 데이터 선택 검증
            if settings['data_mode'] == 'repeated':
                if not settings.get('y_columns'):
                    messagebox.showerror('오류', 'Y 데이터 컬럼을 선택하세요.')
                    return False
                if len(settings['y_columns']) < 2:
                    messagebox.showwarning('경고', '평균/표준편차 계산을 위해 2개 이상의 Y 컬럼을 선택하는 것이 좋습니다.')
            else:
                if not settings.get('y_mean_column'):
                    messagebox.showerror('오류', 'Y 평균 컬럼을 선택하세요.')
                    return False

            # 축 범위 검증
            if settings['xlim_min'] >= settings['xlim_max']:
                messagebox.showerror('오류', 'X축 최솟값은 최댓값보다 작아야 합니다.')
                return False

            if settings['ylim_min'] >= settings['ylim_max']:
                messagebox.showerror('오류', 'Y축 최솟값은 최댓값보다 작아야 합니다.')
                return False

            # 간격 검증
            if settings['x_ticks'] <= 0:
                messagebox.showerror('오류', 'X축 간격은 0보다 커야 합니다.')
                return False

            if settings['y_ticks'] <= 0:
                messagebox.showerror('오류', 'Y축 간격은 0보다 커야 합니다.')
                return False

            return True

        except Exception as e:
            messagebox.showerror('오류', f'설정 검증 오류: {e}')
            return False
