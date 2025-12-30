import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import pandas as pd
import numpy as np

class DoubleYAxisSettings:
    """Double Y축 설정을 위한 모든 UI와 로직을 포함하는 클래스"""
    
    def __init__(self, parent_tab, plot_settings_window, main_app):
        self.parent_tab = parent_tab
        self.plot_settings_window = plot_settings_window
        self.main_app = main_app
        self.settings = plot_settings_window.settings # Share settings object
        if self.settings is None:
            print("Warning: DoubleYAxisSettings received None for settings. Initializing to {}.")
            self.settings = {}

        # 변수 초기화
        self._initialize_variables()

        # UI 빌드
        self._build_ui_in_tab(self.parent_tab)

    def _initialize_variables(self):
        """Double Y축 탭에 필요한 모든 변수 초기화"""
        current_sheet = self.main_app.sheet_combo.get()
        x_col = self.main_app.x_combo.get()
        range_key = f"{current_sheet}_{x_col}"

        saved_settings = self.main_app._saved_double_y_settings.get(range_key, {})
        if saved_settings is None:
            saved_settings = {}

        # Double Y축 사용 여부
        self.use_double_y = tk.BooleanVar(value=saved_settings.get('use_double_y', False))

        self.left_y_columns = saved_settings.get('left_y_columns', [])
        self.right_y_columns = saved_settings.get('right_y_columns', [])

        self.left_axis_color = tk.StringVar(value=saved_settings.get('left_axis_color', '#000000'))
        self.right_axis_color = tk.StringVar(value=saved_settings.get('right_axis_color', '#000000'))
        self.left_axis_color.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        self.right_axis_color.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        
        self.left_ylabel = tk.StringVar(value=saved_settings.get('left_ylabel', ''))
        self.right_ylabel = tk.StringVar(value=saved_settings.get('right_ylabel', ''))

        left_ylim_min_val = saved_settings.get('left_ylim_min', 0)
        left_ylim_max_val = saved_settings.get('left_ylim_max', 10)
        self.left_ylim_min = tk.DoubleVar(value=left_ylim_min_val)
        self.left_ylim_max = tk.DoubleVar(value=left_ylim_max_val)

        right_ylim_min_val = saved_settings.get('right_ylim_min', 0)
        right_ylim_max_val = saved_settings.get('right_ylim_max', 10)
        self.right_ylim_min = tk.DoubleVar(value=right_ylim_min_val)
        self.right_ylim_max = tk.DoubleVar(value=right_ylim_max_val)

        left_y_ticks_value = saved_settings.get('left_y_ticks', 1.0)
        self.left_y_ticks_var = tk.DoubleVar(value=float(left_y_ticks_value))
        
        right_y_ticks_value = saved_settings.get('right_y_ticks', 1.0)
        self.right_y_ticks_var = tk.DoubleVar(value=float(right_y_ticks_value))

        self.grid_var = tk.BooleanVar(value=saved_settings.get('grid', False))
        
        self.title_var = tk.StringVar(value=saved_settings.get('title', ''))
        self.xlabel_var = tk.StringVar(value=saved_settings.get('xlabel', ''))
        
        self.title_fontsize_var = tk.IntVar(value=saved_settings.get('title_fontsize', 14))
        self.label_fontsize_var = tk.IntVar(value=saved_settings.get('label_fontsize', 16))
        self.tick_fontsize_var = tk.IntVar(value=saved_settings.get('tick_fontsize', 12))
        
        # 범례 위치
        self.legend_loc_var = tk.StringVar(value=saved_settings.get('legend_loc', 'upper right'))

        # 축 스케일 (Linear, Log)
        self.x_scale_var = tk.StringVar(value=saved_settings.get('x_scale', 'linear'))
        self.left_y_scale_var = tk.StringVar(value=saved_settings.get('left_y_scale', 'linear'))
        self.right_y_scale_var = tk.StringVar(value=saved_settings.get('right_y_scale', 'linear'))

        # X축 관련 변수
        self.xlim_min_numeric_var = tk.DoubleVar(value=self.settings.get('xlim_min', 0.0))
        self.xlim_max_numeric_var = tk.DoubleVar(value=self.settings.get('xlim_max', 10.0))
        
        x_ticks_value = saved_settings.get('x_ticks', 1.0)
        self.x_ticks_var = tk.DoubleVar(value=float(x_ticks_value))

        val_min = self.plot_settings_window._format_datetime(self.settings.get('xlim_min', ''))
        self.xlim_min_timestamp_var = tk.StringVar(value=val_min)
        val_max = self.plot_settings_window._format_datetime(self.settings.get('xlim_max', ''))
        self.xlim_max_timestamp_var = tk.StringVar(value=val_max)

        self.time_interval_value = tk.IntVar(value=1)
        self.time_interval_unit = tk.StringVar(value='시간')
        self.time_format = tk.StringVar(value='년-월-일 시:분')

        # 스타일 관련 변수
        self.y_color_vars = {}
        self.y_line_width_vars = {}
        self.y_line_style_vars = {}
        self.y_marker_vars = {}
        self.y_marker_size_vars = {}
        self.y_plot_types = {}
        self.y_alpha_vars = {}
        self.y_zorder_vars = {}


    # trace 제거됨 - KeyRelease 이벤트 사용

    def _on_axis_entry_modified(self, event=None):
        """축 입력 필드 수정 시 호출되는 콜백 (KeyRelease 이벤트용)"""
        if hasattr(self.plot_settings_window, '_schedule_update'):
            self.plot_settings_window._schedule_update()

    def _build_ui_in_tab(self, parent):
        """Double Y축 UI를 탭 내에 구성"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 왼쪽 Y축 설정
        left_frame = ttk.LabelFrame(scrollable_frame, text='왼쪽 Y축 (Primary)', padding=10)
        left_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        self._build_left_y_axis_controls(left_frame)

        # 오른쪽 Y축 설정
        right_frame = ttk.LabelFrame(scrollable_frame, text='오른쪽 Y축 (Secondary)', padding=10)
        right_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        self._build_right_y_axis_controls(right_frame)
        
        # 플롯 스타일 섹션
        self._build_plot_style_section(scrollable_frame)
        
        # X축 설정 섹션
        self._build_x_axis_section(scrollable_frame)
        
        # 제목 및 레이블 섹션
        self._build_labels_section(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._load_columns()
        # trace는 제거하고 KeyRelease 이벤트 사용

    def _build_left_y_axis_controls(self, parent_frame):
        """왼쪽 Y축 컨트롤 UI 빌드"""
        ttk.Label(parent_frame, text='왼쪽 Y축 컬럼:').pack(anchor=tk.W)
        
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.left_y_listbox = tk.Listbox(
            list_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, height=6, exportselection=False
        )
        self.left_y_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.left_y_listbox.yview)
        self.left_y_listbox.bind('<<ListboxSelect>>', self._on_left_selection_changed)
        
        color_frame = ttk.Frame(parent_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text='Y축 색상:').pack(side=tk.LEFT)
        ttk.Entry(color_frame, textvariable=self.left_axis_color, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text='선택', command=self._choose_left_axis_color_and_apply, width=6).pack(side=tk.LEFT)
        
        range_frame = ttk.Frame(parent_frame)
        range_frame.pack(fill=tk.X, pady=5)
        ttk.Label(range_frame, text='Y축 범위:').pack(side=tk.LEFT)
        left_ylim_min_entry = ttk.Entry(range_frame, textvariable=self.left_ylim_min, width=8)
        left_ylim_min_entry.pack(side=tk.LEFT, padx=2)
        left_ylim_min_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        ttk.Label(range_frame, text='~').pack(side=tk.LEFT)

        left_ylim_max_entry = ttk.Entry(range_frame, textvariable=self.left_ylim_max, width=8)
        left_ylim_max_entry.pack(side=tk.LEFT, padx=2)
        left_ylim_max_entry.bind('<KeyRelease>', self._on_axis_entry_modified)
        ttk.Button(range_frame, text='자동', command=lambda: self._auto_ylim('left')).pack(side=tk.LEFT, padx=5)
        
        ylabel_frame = ttk.Frame(parent_frame)
        ylabel_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ylabel_frame, text='Y축 타이틀:').pack(side=tk.LEFT)
        ttk.Entry(ylabel_frame, textvariable=self.left_ylabel, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        yticks_frame = ttk.Frame(parent_frame)
        yticks_frame.pack(fill=tk.X, pady=5)
        ttk.Label(yticks_frame, text='Y축 간격 단위:').pack(side=tk.LEFT)
        left_yticks_entry = ttk.Entry(yticks_frame, textvariable=self.left_y_ticks_var, width=10)
        left_yticks_entry.pack(side=tk.LEFT, padx=5)
        left_yticks_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        # Y축 스케일
        yscale_frame = ttk.Frame(parent_frame)
        yscale_frame.pack(fill=tk.X, pady=5)
        ttk.Label(yscale_frame, text='Y축 스케일:').pack(side=tk.LEFT)
        self.left_y_scale_var.trace('w', lambda *args: self._on_axis_entry_modified())
        ttk.Combobox(yscale_frame, textvariable=self.left_y_scale_var, values=['linear', 'log'], width=10, state='readonly').pack(side=tk.LEFT, padx=5)

    def _build_right_y_axis_controls(self, parent_frame):
        """오른쪽 Y축 컨트롤 UI 빌드"""
        ttk.Label(parent_frame, text='오른쪽 Y축 컬럼:').pack(anchor=tk.W)
        
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.right_y_listbox = tk.Listbox(
            list_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, height=6, exportselection=False
        )
        self.right_y_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.right_y_listbox.yview)
        self.right_y_listbox.bind('<<ListboxSelect>>', self._on_right_selection_changed)

        ylabel_frame = ttk.Frame(parent_frame)
        ylabel_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ylabel_frame, text='Y축 타이틀:').pack(side=tk.LEFT)
        ttk.Entry(ylabel_frame, textvariable=self.right_ylabel, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        color_frame = ttk.Frame(parent_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text='Y축 색상:').pack(side=tk.LEFT)
        ttk.Entry(color_frame, textvariable=self.right_axis_color, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text='선택', command=self._choose_right_axis_color_and_apply, width=6).pack(side=tk.LEFT)
        
        range_frame = ttk.Frame(parent_frame)
        range_frame.pack(fill=tk.X, pady=5)
        ttk.Label(range_frame, text='Y축 범위:').pack(side=tk.LEFT)

        right_ylim_min_entry = ttk.Entry(range_frame, textvariable=self.right_ylim_min, width=8)
        right_ylim_min_entry.pack(side=tk.LEFT, padx=2)
        right_ylim_min_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        ttk.Label(range_frame, text='~').pack(side=tk.LEFT)

        right_ylim_max_entry = ttk.Entry(range_frame, textvariable=self.right_ylim_max, width=8)
        right_ylim_max_entry.pack(side=tk.LEFT, padx=2)
        right_ylim_max_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        ttk.Button(range_frame, text='자동', command=lambda: self._auto_ylim('right')).pack(side=tk.LEFT, padx=5)

        yticks_frame = ttk.Frame(parent_frame)
        yticks_frame.pack(fill=tk.X, pady=5)
        ttk.Label(yticks_frame, text='Y축 간격 단위:').pack(side=tk.LEFT)
        right_yticks_entry = ttk.Entry(yticks_frame, textvariable=self.right_y_ticks_var, width=10)
        right_yticks_entry.pack(side=tk.LEFT, padx=5)
        right_yticks_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        # Y축 스케일
        yscale_frame = ttk.Frame(parent_frame)
        yscale_frame.pack(fill=tk.X, pady=5)
        ttk.Label(yscale_frame, text='Y축 스케일:').pack(side=tk.LEFT)
        self.right_y_scale_var.trace('w', lambda *args: self._on_axis_entry_modified())
        ttk.Combobox(yscale_frame, textvariable=self.right_y_scale_var, values=['linear', 'log'], width=10, state='readonly').pack(side=tk.LEFT, padx=5)

    def _load_columns(self):
        try:
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                return
            
            df = self.main_app.df_map[sheet]
            columns = [col for col in df.columns if col != self.main_app.x_combo.get()]
            
            self.left_y_listbox.delete(0, tk.END)
            self.right_y_listbox.delete(0, tk.END)
            
            for col in columns:
                self.left_y_listbox.insert(tk.END, col)
                self.right_y_listbox.insert(tk.END, col)
            
            for i, col in enumerate(columns):
                if col in self.left_y_columns:
                    self.left_y_listbox.selection_set(i)
                if col in self.right_y_columns:
                    self.right_y_listbox.selection_set(i)
        except Exception as e:
            print(f"컬럼 로드 오류: {e}")

    def _on_left_selection_changed(self, event):
        self.left_y_columns = [self.left_y_listbox.get(i) for i in self.left_y_listbox.curselection()]
        self._update_plot_styles()
    
    def _on_right_selection_changed(self, event):
        self.right_y_columns = [self.right_y_listbox.get(i) for i in self.right_y_listbox.curselection()]
        self._update_plot_styles()

    def _auto_ylim(self, side):
        try:
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터를 찾을 수 없습니다.')
                return

            df = self.main_app.df_map[sheet]

            if side == 'left':
                cols = self.left_y_columns
            else:
                cols = self.right_y_columns

            if not cols:
                messagebox.showwarning('경고', f'{side} Y축 컬럼을 선택하세요.')
                return

            all_data = [pd.to_numeric(df[col], errors='coerce').dropna().values for col in cols if col in df.columns]
            if not any(len(d) > 0 for d in all_data):
                messagebox.showwarning('경고', '유효한 데이터가 없습니다.')
                return
                
            all_data_flat = np.concatenate(all_data)
            y_min, y_max = float(np.min(all_data_flat)), float(np.max(all_data_flat))

            margin = (y_max - y_min) * 0.05 if y_max > y_min else 1
            y_min -= margin
            y_max += margin

            if side == 'left':
                self.left_ylim_min.set(y_min)
                self.left_ylim_max.set(y_max)
            else:
                self.right_ylim_min.set(y_min)
                self.right_ylim_max.set(y_max)

            self.plot_settings_window._schedule_update()
        except Exception as e:
            messagebox.showerror('오류', f'자동 범위 설정 중 오류: {e}')

    def _build_plot_style_section(self, parent):
        style_frame = ttk.LabelFrame(parent, text='플롯 스타일 (Double Y축)', padding=10)
        style_frame.pack(fill=tk.X, pady=5, padx=10)
        self.style_container = ttk.Frame(style_frame)
        self.style_container.pack(fill=tk.X)
        self._update_plot_styles()

    def _update_plot_styles(self):
        for widget in self.style_container.winfo_children():
            widget.destroy()

        all_columns = self.left_y_columns + self.right_y_columns
        if not all_columns:
            ttk.Label(self.style_container, text='Y축 컬럼을 선택하세요', foreground='gray').pack(pady=10)
            return

        current_sheet = self.main_app.sheet_combo.get()
        x_col = self.main_app.x_combo.get()
        range_key = f"{current_sheet}_{x_col}"
        saved_settings = self.main_app._saved_double_y_settings.get(range_key, {})
        
        for y_col in all_columns:
            col_frame = ttk.LabelFrame(self.style_container, text=y_col, padding=3)
            col_frame.pack(fill=tk.X, pady=2)
            
            # Init vars with default colors if not set
            if y_col not in self.y_color_vars or not self.y_color_vars[y_col].get():
                default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                idx = all_columns.index(y_col)
                default_color = default_colors[idx % len(default_colors)]
                self.y_color_vars[y_col] = tk.StringVar(value=saved_settings.get('y_colors', {}).get(y_col, default_color))
            
            if y_col not in self.y_line_width_vars:
                self.y_line_width_vars[y_col] = tk.DoubleVar(value=saved_settings.get('y_line_widths', {}).get(y_col, 2.0))
            if y_col not in self.y_line_style_vars:
                self.y_line_style_vars[y_col] = tk.StringVar(value=saved_settings.get('y_line_styles', {}).get(y_col, '-'))
            if y_col not in self.y_marker_vars:
                self.y_marker_vars[y_col] = tk.StringVar(value=saved_settings.get('y_markers', {}).get(y_col, 'None'))
            if y_col not in self.y_marker_size_vars:
                self.y_marker_size_vars[y_col] = tk.IntVar(value=saved_settings.get('y_marker_sizes', {}).get(y_col, 6))
            if y_col not in self.y_plot_types:
                self.y_plot_types[y_col] = tk.StringVar(value=saved_settings.get('y_plot_types', {}).get(y_col, 'line'))
            if y_col not in self.y_alpha_vars:
                self.y_alpha_vars[y_col] = tk.DoubleVar(value=saved_settings.get('y_alphas', {}).get(y_col, 1.0))
            if y_col not in self.y_zorder_vars:
                self.y_zorder_vars[y_col] = tk.IntVar(value=saved_settings.get('y_zorders', {}).get(y_col, 2))

            # Trace for live updates
            self.y_zorder_vars[y_col].trace('w', lambda *args: self.plot_settings_window._schedule_update())
            self.y_color_vars[y_col].trace('w', lambda *args: self.plot_settings_window._schedule_update())

            # UI elements
            # Plot Type
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='유형:', width=5).pack(side=tk.LEFT)
            ttk.Combobox(f, textvariable=self.y_plot_types[y_col], values=['line', 'scatter', 'both'], width=7, state='readonly').pack(side=tk.LEFT)
            
            # Z-Order (Layer)
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='순서:', width=5).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=self.y_zorder_vars[y_col], width=3).pack(side=tk.LEFT)

            # Color (read-only)
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='색상:', width=5).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=self.y_color_vars[y_col], width=8, state='readonly').pack(side=tk.LEFT)
            
            # Alpha
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='투명도:', width=5).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=self.y_alpha_vars[y_col], width=4).pack(side=tk.LEFT)

            # Line width
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='두께:', width=5).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=self.y_line_width_vars[y_col], width=5).pack(side=tk.LEFT)
            # Line style
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='스타일:', width=5).pack(side=tk.LEFT)
            ttk.Combobox(f, textvariable=self.y_line_style_vars[y_col], values=['-', '--', '-.', ':'], width=5, state='readonly').pack(side=tk.LEFT)
            # Marker
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='마커:', width=5).pack(side=tk.LEFT)
            ttk.Combobox(f, textvariable=self.y_marker_vars[y_col], values=['None', 'o', 's', '^', 'v', 'D', '*', 'x', '+'], width=5, state='readonly').pack(side=tk.LEFT)
            # Marker size
            f = ttk.Frame(col_frame); f.pack(side=tk.LEFT, padx=2)
            ttk.Label(f, text='크기:', width=5).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=self.y_marker_size_vars[y_col], width=5).pack(side=tk.LEFT)

    def _choose_left_axis_color_and_apply(self):
        color = colorchooser.askcolor(title='왼쪽 Y축 색상 선택', color=self.left_axis_color.get())
        if color[1]:
            self.left_axis_color.set(color[1])
            for col in self.left_y_columns:
                if col in self.y_color_vars:
                    self.y_color_vars[col].set(color[1])

    def _choose_right_axis_color_and_apply(self):
        color = colorchooser.askcolor(title='오른쪽 Y축 색상 선택', color=self.right_axis_color.get())
        if color[1]:
            self.right_axis_color.set(color[1])
            for col in self.right_y_columns:
                if col in self.y_color_vars:
                    self.y_color_vars[col].set(color[1])

    def _build_x_axis_section(self, parent):
        axis_frame = ttk.LabelFrame(parent, text='X축 설정 (Double Y축)', padding=10)
        axis_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.axis_notebook = ttk.Notebook(axis_frame)
        self.axis_notebook.pack(fill=tk.X, pady=5)
        
        numeric_tab = ttk.Frame(self.axis_notebook)
        self.axis_notebook.add(numeric_tab, text='숫자축')
        timestamp_tab = ttk.Frame(self.axis_notebook)
        self.axis_notebook.add(timestamp_tab, text='시간축')
        
        self._build_numeric_axis_tab(numeric_tab)
        self._build_timestamp_axis_tab(timestamp_tab)
        
        self._build_timestamp_axis_tab(timestamp_tab)
        
        # Grid 표시 체크박스 제거됨 (User request: default OFF, no UI)

    def _build_numeric_axis_tab(self, parent):
        xlim_frame = ttk.Frame(parent)
        xlim_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(xlim_frame, text='X축 범위:').pack(side=tk.LEFT)

        xlim_min_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_numeric_var, width=12)
        xlim_min_entry.pack(side=tk.LEFT, padx=2)
        xlim_min_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)

        xlim_max_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_numeric_var, width=12)
        xlim_max_entry.pack(side=tk.LEFT, padx=2)
        xlim_max_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        ttk.Button(xlim_frame, text='자동', command=self._auto_xlim).pack(side=tk.LEFT, padx=5)
        
        xticks_frame = ttk.Frame(parent)
        xticks_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(xticks_frame, text='X축 간격 단위:').pack(side=tk.LEFT)

        xticks_entry = ttk.Entry(xticks_frame, textvariable=self.x_ticks_var, width=10)
        xticks_entry.pack(side=tk.LEFT, padx=5)
        xticks_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        # X축 스케일
        xscale_frame = ttk.Frame(parent)
        xscale_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(xscale_frame, text='X축 스케일:').pack(side=tk.LEFT)
        self.x_scale_var.trace('w', lambda *args: self._on_axis_entry_modified())
        ttk.Combobox(xscale_frame, textvariable=self.x_scale_var, values=['linear', 'log'], width=10, state='readonly').pack(side=tk.LEFT, padx=5)

    def _build_timestamp_axis_tab(self, parent):
        xlim_frame = ttk.Frame(parent)
        xlim_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(xlim_frame, text='X축 범위:').pack(side=tk.LEFT)

        xlim_min_timestamp_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_timestamp_var, width=20)
        xlim_min_timestamp_entry.pack(side=tk.LEFT, padx=2)
        xlim_min_timestamp_entry.bind('<KeyRelease>', self._on_axis_entry_modified)

        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)

        xlim_max_timestamp_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_timestamp_var, width=20)
        xlim_max_timestamp_entry.pack(side=tk.LEFT, padx=2)
        xlim_max_timestamp_entry.bind('<KeyRelease>', self._on_axis_entry_modified)
        
        interval_frame = ttk.Frame(parent)
        interval_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(interval_frame, text='시간 간격:').pack(side=tk.LEFT)
        ttk.Entry(interval_frame, textvariable=self.time_interval_value, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Combobox(interval_frame, textvariable=self.time_interval_unit, values=['초', '분', '시간', '일'], width=8, state='readonly').pack(side=tk.LEFT, padx=2)
        
        format_frame = ttk.Frame(parent)
        format_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(format_frame, text='시간 형식:').pack(side=tk.LEFT)
        ttk.Combobox(format_frame, textvariable=self.time_format, values=['년-월-일 시:분:초', '년-월-일 시:분', '월-일 시:분', '시:분:초', '시:분'], width=20, state='readonly').pack(side=tk.LEFT, padx=2)

    def _auto_xlim(self):
        try:
            current_sheet = self.main_app.sheet_combo.get()
            df = self.main_app.df_map.get(current_sheet)
            x_col = self.main_app.x_combo.get()
            if df is None or x_col not in df.columns:
                return

            x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
            if not x_data.empty:
                margin = (x_data.max() - x_data.min()) * 0.05
                self.xlim_min_numeric_var.set(x_data.min() - margin)
                self.xlim_max_numeric_var.set(x_data.max() + margin)
        except Exception as e:
            messagebox.showerror('오류', f'X축 자동 범위 설정 중 오류: {e}')


    def _build_labels_section(self, parent):
        """제목 및 레이블 섹션 구축"""
        labels_frame = ttk.LabelFrame(parent, text='제목 및 레이블 (Double Y축)', padding=10)
        labels_frame.pack(fill=tk.X, pady=5, padx=10)

        # 그래프 제목
        title_frame = ttk.Frame(labels_frame)
        title_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_frame, text='그래프 제목:').pack(side=tk.LEFT)
        ttk.Entry(title_frame, textvariable=self.title_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # X축 레이블
        xlabel_frame = ttk.Frame(labels_frame)
        xlabel_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xlabel_frame, text='X축 레이블:').pack(side=tk.LEFT)
        ttk.Entry(xlabel_frame, textvariable=self.xlabel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

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
        
        current_loc = self.legend_loc_var.get()
        # Matplotlib 상수 -> 한글 매핑 찾기
        initial_display = next((k for k, v in self.legend_loc_map.items() if v == current_loc), '오른쪽 위')
        
        self.legend_loc_var.set(initial_display)
        self.legend_loc_var.trace('w', lambda *args: self.plot_settings_window._schedule_update())
        
        legend_combo = ttk.Combobox(legend_frame, textvariable=self.legend_loc_var, values=self.legend_loc_display_vals, state='readonly')
        legend_combo.pack(side=tk.LEFT, padx=5)

        # 글자 크기 설정
        font_frame = ttk.LabelFrame(labels_frame, text='글자 크기', padding=5)
        font_frame.pack(fill=tk.X, pady=5)

        # 제목 글자 크기
        title_font_frame = ttk.Frame(font_frame)
        title_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_font_frame, text='제목 글자 크기:').pack(side=tk.LEFT)
        ttk.Entry(title_font_frame, textvariable=self.title_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

        # 레이블 글자 크기
        label_font_frame = ttk.Frame(font_frame)
        label_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(label_font_frame, text='레이블 글자 크기:').pack(side=tk.LEFT)
        ttk.Entry(label_font_frame, textvariable=self.label_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

        # 축 숫자 글자 크기
        tick_font_frame = ttk.Frame(font_frame)
        tick_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(tick_font_frame, text='축 숫자 글자 크기:').pack(side=tk.LEFT)
        ttk.Entry(tick_font_frame, textvariable=self.tick_fontsize_var, width=8).pack(side=tk.LEFT, padx=5)

    def collect_settings(self):
        """이 탭의 모든 설정을 수집"""
        settings = {
            'use_double_y': True,
            'left_y_columns': self.left_y_columns,
            'right_y_columns': self.right_y_columns,
            'left_axis_color': self.left_axis_color.get(),
            'right_axis_color': self.right_axis_color.get(),
            'left_ylabel': self.left_ylabel.get(),
            'right_ylabel': self.right_ylabel.get(),
            'left_ylim_min': self.left_ylim_min.get(),
            'left_ylim_max': self.left_ylim_max.get(),
            'right_ylim_min': self.right_ylim_min.get(),
            'right_ylim_max': self.right_ylim_max.get(),
            'x_ticks': self.x_ticks_var.get(),
            'left_y_ticks': self.left_y_ticks_var.get(),
            'right_y_ticks': self.right_y_ticks_var.get(),
            'grid': self.grid_var.get(),
            'title': self.title_var.get(),
            'xlabel': self.xlabel_var.get(),
            'x_scale': self.x_scale_var.get(),
            'left_y_scale': self.left_y_scale_var.get(),
            'right_y_scale': self.right_y_scale_var.get(),
            'legend_loc': self.legend_loc_map.get(self.legend_loc_var.get(), 'upper right'),
            'title_fontsize': self.title_fontsize_var.get(),
            'label_fontsize': self.label_fontsize_var.get(),
            'tick_fontsize': self.tick_fontsize_var.get(),
        }

        # X-axis settings
        try:
            tab_index = self.axis_notebook.index(self.axis_notebook.select())
            if tab_index == 0: # Numeric
                settings['xlim_min'] = float(self.xlim_min_numeric_var.get())
                settings['xlim_max'] = float(self.xlim_max_numeric_var.get())
                settings['is_timestamp'] = False
            else: # Timestamp
                settings['xlim_min'] = pd.to_datetime(self.xlim_min_timestamp_var.get())
                settings['xlim_max'] = pd.to_datetime(self.xlim_max_timestamp_var.get())
                settings['is_timestamp'] = True
                settings['time_interval_value'] = self.time_interval_value.get()
                settings['time_interval_unit'] = self.time_interval_unit.get()
                settings['time_format'] = self.plot_settings_window._convert_korean_time_format(self.time_format.get())
        except Exception:
             pass # default to numeric

        # Style settings
        settings['y_colors'] = {col: var.get() for col, var in self.y_color_vars.items()}
        settings['y_line_widths'] = {col: var.get() for col, var in self.y_line_width_vars.items()}
        settings['y_line_styles'] = {col: var.get() for col, var in self.y_line_style_vars.items()}
        settings['y_markers'] = {col: var.get() for col, var in self.y_marker_vars.items()}
        settings['y_marker_sizes'] = {col: var.get() for col, var in self.y_marker_size_vars.items()}
        settings['y_plot_types'] = {col: var.get() for col, var in self.y_plot_types.items()}
        settings['y_alphas'] = {col: var.get() for col, var in self.y_alpha_vars.items()}
        settings['y_zorders'] = {col: var.get() for col, var in self.y_zorder_vars.items()}

        return settings

    def validate_settings(self, settings):
        """설정값 유효성 검사"""
        # 필수 키 존재 여부 확인 (Double Y 모드)
        if settings.get('use_double_y'):
            if 'left_y_columns' not in settings and 'right_y_columns' not in settings:
                print("Warning: Double Y 모드에서 Y축 컬럼이 선택되지 않았습니다.")
                # 필수는 아니지만 경고 로깅
        
        return True

    def _apply_to_main_app(self):
        """Double Y축 설정을 메인 앱에 적용"""
        try:
            # 설정 수집
            settings = self.collect_settings()

            # 메인 앱의 그래프 업데이트
            self.plot_settings_window._safe_apply_plot_settings(settings)

        except Exception as e:
            print(f"Double Y축 적용 중 오류: {e}")
            import traceback
            traceback.print_exc()