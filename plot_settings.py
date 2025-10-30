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
    
    def _schedule_update(self):
        """디바운싱을 사용하여 그래프 업데이트를 스케줄링 - 강화된 안전성"""
        try:
            # 기존 타이머 취소
            if self.update_timer:
                self.window.after_cancel(self.update_timer)
                self.update_timer = None
            
            # 업데이트 중이면 스케줄링 건너뜀
            if hasattr(self, 'is_updating') and self.is_updating:
                print("이미 업데이트 중입니다. 스케줄링 건너뜀.")
                return
            
            # 디바운싱 지연 시간 증가 (더 안전하게)
            delay_ms = int(self.update_delay * 1000) + 100  # 추가 100ms 지연
            print(f"그래프 업데이트 스케줄링: {delay_ms}ms 후")
            
            self.update_timer = self.window.after(delay_ms, self._update_plot)
            
        except Exception as e:
            print(f"업데이트 스케줄링 오류: {e}")
    
    def _update_plot(self):
        """실제 그래프 업데이트 수행 - 타임아웃 및 안전한 처리"""
        try:
            if self.is_updating:
                print("이미 업데이트 중입니다. 건너뜀.")
                return
            
            self.is_updating = True
            print("그래프 업데이트 시작...")
            
            # 타임아웃 설정 (5초)
            timeout_timer = self.window.after(5000, self._force_update_timeout)
            
            try:
                settings = self._collect_settings()
                print(f"설정 수집 완료: {len(settings)} 항목")
                
                # 설정 유효성 검사
                if self._validate_settings(settings):
                    print("설정 유효성 검사 통과")
                    
                    # 메인 앱의 그래프 업데이트 (안전한 처리)
                    self._safe_apply_plot_settings(settings)
                    print("실시간 그래프 업데이트 완료")
                else:
                    print("설정 유효성 검사 실패")
                    
            finally:
                # 타임아웃 타이머 취소
                if timeout_timer:
                    self.window.after_cancel(timeout_timer)
                
        except Exception as e:
            print(f"실시간 업데이트 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_updating = False
            print("그래프 업데이트 플래그 해제")
    
    def _force_update_timeout(self):
        """업데이트 타임아웃 강제 종료"""
        print("그래프 업데이트 타임아웃! 강제 종료")
        self.is_updating = False
    
    def _safe_apply_plot_settings(self, settings):
        """안전한 그래프 설정 적용"""
        try:
            print("그래프 설정 적용 시작...")
            
            # 시간축 데이터 유효성 검사
            if self._is_timestamp_axis(settings):
                self._validate_timestamp_data(settings)
            
            # 메인 앱의 그래프 업데이트
            self.main_app.apply_plot_settings(settings)
            print("그래프 설정 적용 완료")
            
        except Exception as e:
            print(f"그래프 설정 적용 오류: {e}")
            # 기본 설정으로 fallback
            self._apply_fallback_settings()
    
    def _is_timestamp_axis(self, settings):
        """시간축인지 확인"""
        try:
            axis_type = self.main_app.axis_type_var.get()
            return axis_type == 'datetime'
        except:
            return False
    
    def _validate_timestamp_data(self, settings):
        """시간축 데이터 유효성 검사"""
        try:
            xlim_min = settings.get('xlim_min')
            xlim_max = settings.get('xlim_max')
            
            if xlim_min and xlim_max:
                # 시간 형식 검사
                import re
                time_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
                
                if not re.match(time_pattern, str(xlim_min)) or not re.match(time_pattern, str(xlim_max)):
                    print(f"잘못된 시간 형식: {xlim_min}, {xlim_max}")
                    raise ValueError("잘못된 시간 형식")
                
                print(f"시간 형식 검사 통과: {xlim_min} ~ {xlim_max}")
                
        except Exception as e:
            print(f"시간축 데이터 유효성 검사 실패: {e}")
            raise
    
    def _apply_fallback_settings(self):
        """기본 설정으로 fallback"""
        try:
            print("기본 설정으로 fallback 적용")
            # 기본 설정으로 그래프 업데이트
            # 여기서는 단순히 현재 그래프를 유지
            pass
        except Exception as e:
            print(f"Fallback 설정 적용 오류: {e}")
    
    def _is_timestamp_column_name(self, column_name: str) -> bool:
        """컬럼 이름이 시간 관련인지 확인"""
        time_keywords = ['timestamp', 'time', 'date', 'datetime', 'ts']
        column_lower = column_name.lower()
        return any(keyword in column_lower for keyword in time_keywords)
        
    def _get_current_settings(self):
        """현재 그래프 설정 가져오기"""
        try:
            # 메인 앱의 축 타입 선택을 확인
            x_col = self.main_app.x_combo.get()
            current_sheet = self.main_app.sheet_combo.get()
            is_timestamp = False
            
            # X 컬럼 이름에 따라 축 타입 자동 결정
            if x_col and self._is_timestamp_column_name(x_col):
                is_timestamp = True
                print(f"플롯 설정: X 컬럼 '{x_col}' - 시간축 모드로 자동 설정")
            else:
                is_timestamp = False
                print(f"플롯 설정: X 컬럼 '{x_col}' - 숫자축 모드로 자동 설정")
            
            # 메인 앱의 축 타입도 동기화
            if hasattr(self.main_app, 'axis_type_var'):
                axis_type = 'datetime' if is_timestamp else 'numeric'
                self.main_app.axis_type_var.set(axis_type)
                print(f"메인 앱의 축 타입도 '{axis_type}'로 동기화")
            
            # 사용자가 수정한 X축 범위가 있는지 확인
            if not hasattr(self.main_app, '_user_modified_x_range'):
                self.main_app._user_modified_x_range = False
            
            if not hasattr(self.main_app, '_saved_x_range'):
                self.main_app._saved_x_range = {}
            
            # 현재 시트와 X축 컬럼을 키로 사용
            range_key = f"{current_sheet}_{x_col}"
            
            if self.main_app._user_modified_x_range and range_key in self.main_app._saved_x_range:
                # 사용자가 수정한 값이 있으면 그것을 사용
                saved_range = self.main_app._saved_x_range[range_key]
                actual_x_min = saved_range['min']
                actual_x_max = saved_range['max']
                print(f"저장된 사용자 범위 사용: {actual_x_min} ~ {actual_x_max}")
            else:
                # 처음이거나 저장된 값이 없으면 실제 데이터 범위 사용
                if is_timestamp and x_col and current_sheet and current_sheet in self.main_app.df_map:
                    df = self.main_app.df_map[current_sheet]
                    if x_col in df.columns:
                        try:
                            # main_app의 _parse_datetime_column 메서드 사용
                            x_data = self.main_app._parse_datetime_column(df, x_col).dropna()
                            if not x_data.empty:
                                actual_x_min = x_data.min()
                                actual_x_max = x_data.max()
                                print(f"초기 시간 범위 설정: {actual_x_min} ~ {actual_x_max}")
                            else:
                                actual_x_min = pd.Timestamp('2025-01-01')
                                actual_x_max = pd.Timestamp('2025-12-31')
                        except Exception as e:
                            print(f"시간 데이터 파싱 오류: {e}")
                            actual_x_min = pd.Timestamp('2025-01-01')
                            actual_x_max = pd.Timestamp('2025-12-31')
                    else:
                        actual_x_min = pd.Timestamp('2025-01-01')
                        actual_x_max = pd.Timestamp('2025-12-31')
                elif x_col and current_sheet and current_sheet in self.main_app.df_map:
                    df = self.main_app.df_map[current_sheet]
                    if x_col in df.columns:
                        try:
                            x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
                            if not x_data.empty:
                                actual_x_min = float(x_data.min())
                                actual_x_max = float(x_data.max())
                                print(f"초기 숫자 범위 설정: {actual_x_min} ~ {actual_x_max}")
                            else:
                                actual_x_min = 0.0
                                actual_x_max = 10.0
                        except Exception as e:
                            print(f"숫자 데이터 파싱 오류: {e}")
                            actual_x_min = 0.0
                            actual_x_max = 10.0
                    else:
                        actual_x_min = 0.0
                        actual_x_max = 10.0
                else:
                    actual_x_min = 0.0
                    actual_x_max = 10.0
            
            # 현재 플롯에서 설정 추출
            fig = self.main_app.figure
            ax = fig.axes[0] if fig and fig.axes else None
            
            if ax:
                # 기본 설정
                self.settings = {
                    'plot_type': 'line',  # line, scatter, both
                    'line_style': '-',   # -, --, -., :
                    'marker': 'o',       # o, s, ^, v, etc.
                    'color': '#1f77b4', # 기본 색상
                    'line_width': 1.5,
                    'marker_size': 6,
                    'title': ax.get_title() or '',
                    'xlabel': ax.get_xlabel() or '',
                    'ylabel': ax.get_ylabel() or '',
                    'xlim_min': actual_x_min,
                    'xlim_max': actual_x_max,
                    'ylim_min': ax.get_ylim()[0],
                    'ylim_max': ax.get_ylim()[1],
                'x_ticks': 1,  # 간격 단위 (기본값: 1)
                'y_ticks': 1,  # 간격 단위 (기본값: 1)
                'x_tick_fontsize': 12,  # 나중에 실제 값으로 업데이트됨
                'y_tick_fontsize': 12,  # 나중에 실제 값으로 업데이트됨
                'xlabel_fontsize': ax.xaxis.label.get_fontsize() or 16,
                'ylabel_fontsize': ax.yaxis.label.get_fontsize() or 16,
                'title_fontsize': ax.title.get_fontsize() or 14,
                'is_timestamp': is_timestamp,  # Timestamp 여부 추가
                }
                
                # 현재 플롯 라인에서 실제 설정값 추출
                lines = ax.get_lines()
                if lines:
                    line = lines[0]
                    # 색상, 선 스타일, 마커 등 추출
                    self.settings['color'] = to_hex(line.get_color())
                    self.settings['line_style'] = line.get_linestyle()
                    self.settings['marker'] = line.get_marker() if line.get_marker() != 'None' else 'o'
                    self.settings['line_width'] = line.get_linewidth()
                    self.settings['marker_size'] = line.get_markersize()
                    
                    # 플롯 타입 결정
                    if line.get_marker() != 'None' and line.get_linestyle() != 'None':
                        self.settings['plot_type'] = 'both'
                    elif line.get_marker() != 'None':
                        self.settings['plot_type'] = 'scatter'
                    else:
                        self.settings['plot_type'] = 'line'
                
                # 산점도인 경우 마커 설정 추출
                collections = ax.collections
                if collections and not lines:
                    collection = collections[0]
                    self.settings['color'] = to_hex(collection.get_facecolor()[0])
                    # 마커 크기는 scatter의 's' 인자로 저장되므로 제곱근을 취함
                    sizes = collection.get_sizes()
                    if sizes and len(sizes) > 0:
                        self.settings['marker_size'] = (sizes[0] ** 0.5) if sizes[0] > 0 else 6
                    self.settings['plot_type'] = 'scatter'
                
                # Y축 컬럼별 스타일 정보 추출
                self.settings['y_colors'] = {}
                self.settings['y_line_widths'] = {}
                self.settings['y_line_styles'] = {}
                self.settings['y_markers'] = {}
                self.settings['y_marker_sizes'] = {}
                self.settings['y_plot_types'] = {}
                
                if lines:
                    for i, line in enumerate(lines):
                        label = line.get_label()
                        if label and label != '_nolegend_':
                            self.settings['y_colors'][label] = to_hex(line.get_color())
                            self.settings['y_line_widths'][label] = line.get_linewidth()
                            self.settings['y_line_styles'][label] = line.get_linestyle()
                            self.settings['y_markers'][label] = line.get_marker() if line.get_marker() != 'None' else 'o'
                            self.settings['y_marker_sizes'][label] = line.get_markersize()
                            # 플롯 타입 추정
                            if line.get_marker() != 'None' and line.get_linestyle() != 'None':
                                self.settings['y_plot_types'][label] = 'both'
                            elif line.get_marker() != 'None':
                                self.settings['y_plot_types'][label] = 'scatter'
                            else:
                                self.settings['y_plot_types'][label] = 'line'
                elif collections:
                    for i, collection in enumerate(collections):
                        label = collection.get_label()
                        if label and label != '_nolegend_':
                            self.settings['y_colors'][label] = to_hex(collection.get_facecolor()[0])
                            # scatter의 경우 기본값 사용
                            self.settings['y_line_widths'][label] = 1.0
                            self.settings['y_line_styles'][label] = '-'
                            self.settings['y_markers'][label] = 'o'
                            sizes = collection.get_sizes()
                            self.settings['y_marker_sizes'][label] = (sizes[0] ** 0.5) if sizes and len(sizes) > 0 else 6.0
                            self.settings['y_plot_types'][label] = 'scatter'
                
                # 축 범위와 틱 수 추출
                try:
                    x_ticks = ax.get_xticks()
                    y_ticks = ax.get_yticks()
                    self.settings['x_ticks'] = len(x_ticks) if len(x_ticks) > 0 else 5
                    self.settings['y_ticks'] = len(y_ticks) if len(y_ticks) > 0 else 5
                except:
                    self.settings['x_ticks'] = 5
                    self.settings['y_ticks'] = 5
                
                # 폰트 크기 추출
                try:
                    # X축 틱 폰트 크기
                    x_tick_labels = ax.get_xticklabels()
                    if x_tick_labels:
                        self.settings['x_tick_fontsize'] = x_tick_labels[0].get_fontsize()
                    else:
                        self.settings['x_tick_fontsize'] = 12
                    
                    # Y축 틱 폰트 크기
                    y_tick_labels = ax.get_yticklabels()
                    if y_tick_labels:
                        self.settings['y_tick_fontsize'] = y_tick_labels[0].get_fontsize()
                    else:
                        self.settings['y_tick_fontsize'] = 12
                except:
                    self.settings['x_tick_fontsize'] = 12
                    self.settings['y_tick_fontsize'] = 12
        except Exception as e:
            print(f"현재 설정 가져오기 오류: {e}")
            import traceback
            traceback.print_exc()
            # 기본값 설정
            self.settings = {
                'plot_type': 'line',
                'line_style': '-',
                'marker': 'o',
                'color': '#1f77b4',
                'line_width': 1.5,
                'marker_size': 6,
                'title': '',
                'xlabel': '',
                'ylabel': '',
                'xlim_min': actual_x_min,
                'xlim_max': actual_x_max,
                'ylim_min': 0,
                'ylim_max': 10,
                'x_ticks': 1,  # 간격 단위 (기본값: 1)
                'y_ticks': 1,  # 간격 단위 (기본값: 1)
                'x_tick_fontsize': 12,
                'y_tick_fontsize': 12,
                'xlabel_fontsize': 16,
                'ylabel_fontsize': 16,
                'title_fontsize': 14,
                'is_timestamp': False,
            }
    
    def _build_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 플롯 스타일 섹션
        self._build_plot_style_section(scrollable_frame)
        
        # 축 설정 섹션
        self._build_axis_section(scrollable_frame)
        
        # 제목 및 레이블 섹션
        self._build_labels_section(scrollable_frame)
        
        # 버튼 프레임
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text='적용', command=self._apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='취소', command=self._cancel_settings).pack(side=tk.RIGHT, padx=5)
        
        # 캔버스와 스크롤바 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _build_plot_style_section(self, parent):
        """플롯 스타일 섹션"""
        style_frame = ttk.LabelFrame(parent, text='플롯 스타일', padding=10)
        style_frame.pack(fill=tk.X, pady=5)
        
        # Y축 컬럼별 스타일 선택
        self._build_y_color_section(style_frame)
    
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
        
        # 각 Y축 컬럼에 대한 스타일 선택
        self.y_color_vars = {}
        self.y_line_width_vars = {}
        self.y_line_style_vars = {}
        self.y_marker_vars = {}
        self.y_marker_size_vars = {}
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
            color_var.trace('w', lambda *args: self._schedule_update())
            
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
            line_width_var.trace('w', lambda *args: self._schedule_update())
            
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
            line_style_var.trace('w', lambda *args: self._schedule_update())
            
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
            marker_var.trace('w', lambda *args: self._schedule_update())
            
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
            plot_type_var.trace('w', lambda *args: self._schedule_update())
            
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
            marker_size_var.trace('w', lambda *args: self._schedule_update())
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
        self.ylim_min_var.trace('w', lambda *args: self._schedule_update())
        self.ylim_max_var.trace('w', lambda *args: self._schedule_update())
        ttk.Entry(ylim_frame, textvariable=self.ylim_min_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(ylim_frame, text='~').pack(side=tk.LEFT)
        ttk.Entry(ylim_frame, textvariable=self.ylim_max_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ylim_frame, text='자동', command=self._auto_ylim).pack(side=tk.LEFT, padx=5)
        
        # Y축 간격 (공통)
        yticks_frame = ttk.Frame(axis_frame)
        yticks_frame.pack(fill=tk.X, pady=2)
        ttk.Label(yticks_frame, text='Y축 간격 단위:').pack(side=tk.LEFT)
        
        self.y_ticks_var = tk.IntVar(value=self.settings['y_ticks'])
        self.y_ticks_var.trace('w', lambda *args: self._schedule_update())
        yticks_entry = ttk.Entry(yticks_frame, textvariable=self.y_ticks_var, width=8)
        yticks_entry.pack(side=tk.LEFT, padx=5)
    
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
        
        self.xlim_min_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_numeric_var, width=8)
        self.xlim_min_entry.pack(side=tk.LEFT, padx=2)
        self.xlim_min_entry.bind('<KeyRelease>', self._on_x_range_modified)
        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)
        self.xlim_max_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_numeric_var, width=8)
        self.xlim_max_entry.pack(side=tk.LEFT, padx=2)
        self.xlim_max_entry.bind('<KeyRelease>', self._on_x_range_modified)
        
        # 자동 버튼 제거 (처음 값만 자동 세팅)
        
        # X축 간격
        xticks_frame = ttk.Frame(parent)
        xticks_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xticks_frame, text='X축 간격 단위:').pack(side=tk.LEFT)
        
        self.x_ticks_var = tk.IntVar(value=self.settings['x_ticks'])
        self.x_ticks_var.trace('w', lambda *args: self._schedule_update())
        xticks_entry = ttk.Entry(xticks_frame, textvariable=self.x_ticks_var, width=8)
        xticks_entry.pack(side=tk.LEFT, padx=5)
        
        # 초기 상태: 입력 활성화 (수동)
    
    def _build_timestamp_axis_tab(self, parent):
        """시간 축 탭 구성"""
        # 자동/수동 모드 제거: 처음 로드 시 자동값만 채우고 항상 수동 입력
        
        # X축 시간 범위 (수동 입력)
        xlim_frame = ttk.Frame(parent)
        xlim_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xlim_frame, text='X축 시간 범위:').pack(side=tk.LEFT)
        
        print(f"시간축 탭 생성 - xlim_min: {self.settings['xlim_min']}, xlim_max: {self.settings['xlim_max']}")
        self.xlim_min_timestamp_var = tk.StringVar(value=self._format_datetime(self.settings['xlim_min']))
        self.xlim_max_timestamp_var = tk.StringVar(value=self._format_datetime(self.settings['xlim_max']))
        
        self.xlim_min_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_min_timestamp_var, width=20)
        self.xlim_min_entry.pack(side=tk.LEFT, padx=2)
        # 시간축 포맷팅 비활성화 - 단순한 입력만 받음
        self.xlim_min_entry.bind('<KeyRelease>', self._on_timestamp_range_modified_simple)
        ttk.Label(xlim_frame, text='~').pack(side=tk.LEFT)
        self.xlim_max_entry = ttk.Entry(xlim_frame, textvariable=self.xlim_max_timestamp_var, width=20)
        self.xlim_max_entry.pack(side=tk.LEFT, padx=2)
        self.xlim_max_entry.bind('<KeyRelease>', self._on_timestamp_range_modified_simple)
        
        # 자동 버튼 제거 (처음 값만 자동 세팅)
        
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
        
        self.x_ticks_var = tk.IntVar(value=self.settings['x_ticks'])
        self.x_ticks_var.trace('w', lambda *args: self._schedule_update())
        xticks_entry = ttk.Entry(ticks_count_frame, textvariable=self.x_ticks_var, width=8)
        xticks_entry.pack(side=tk.LEFT, padx=5)
        
        # 시간 간격 단위 설정
        interval_frame = ttk.Frame(xticks_frame)
        interval_frame.pack(fill=tk.X, pady=2)
        ttk.Label(interval_frame, text='시간 간격 단위:').pack(side=tk.LEFT)
        
        self.time_interval_unit = tk.StringVar(value=self.settings.get('time_interval_unit', 'minutes'))
        self.time_interval_unit.trace('w', lambda *args: self._schedule_update())
        interval_combo = ttk.Combobox(interval_frame, textvariable=self.time_interval_unit, width=12, state='readonly')
        interval_combo['values'] = ['seconds', 'minutes', 'hours', 'days']
        interval_combo.pack(side=tk.LEFT, padx=5)
        
        # 시간 간격 값 설정
        interval_value_frame = ttk.Frame(xticks_frame)
        interval_value_frame.pack(fill=tk.X, pady=2)
        ttk.Label(interval_value_frame, text='간격 값:').pack(side=tk.LEFT)
        
        self.time_interval_value = tk.IntVar(value=self.settings.get('time_interval_value', 1))
        self.time_interval_value.trace('w', lambda *args: self._schedule_update())
        interval_value_entry = ttk.Entry(interval_value_frame, textvariable=self.time_interval_value, width=8)
        interval_value_entry.pack(side=tk.LEFT, padx=5)
        
        # 시간 형식 설정
        format_frame = ttk.Frame(xticks_frame)
        format_frame.pack(fill=tk.X, pady=2)
        ttk.Label(format_frame, text='시간 표시 형식:').pack(side=tk.LEFT)
        
        self.time_format = tk.StringVar(value=self.settings.get('time_format', '시:분:초:밀리초'))
        self.time_format.trace('w', lambda *args: self._schedule_update())
        format_combo = ttk.Combobox(format_frame, textvariable=self.time_format, width=15, state='readonly')
        format_combo['values'] = ['시:분:초:밀리초', '시:분:초', '시:분', '년-월-일 시:분:초', '년-월-일 시:분']
        format_combo.pack(side=tk.LEFT, padx=5)
        
        # 초기 상태 설정: 입력 활성화 (수동)
        try:
            self.xlim_min_entry.config(state='normal')
            self.xlim_max_entry.config(state='normal')
        except Exception:
            pass
        
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
        
    # 자동/수동 모드 제거됨 - 입력은 항상 활성화 상태 유지
        
    # 자동/수동 모드 제거됨
        
    # 자동/수동 모드 제거됨 - 입력은 항상 활성화 상태 유지
        
    # 자동/수동 모드 제거됨
        
    def _on_x_range_modified(self, event):
        """숫자 축 범위 수정 감지"""
        self.main_app._user_modified_x_range = True
        self._save_current_x_range()
        print("사용자가 숫자 축 범위를 수정했습니다.")
        # 실시간 업데이트 스케줄링
        self._schedule_update()
        
    def _on_timestamp_range_modified(self, event):
        """시간 축 범위 수정 감지 - 강화된 디바운싱"""
        try:
            # 무한 루프 방지 (더 강력한 체크)
            if hasattr(self, '_timestamp_processing') and self._timestamp_processing:
                print("시간축 처리 중입니다. 건너뜀.")
                return
                
            if hasattr(self, '_global_formatting') and self._global_formatting:
                print("전역 포맷팅 중입니다. 건너뜀.")
                return
                
            self._timestamp_processing = True
            print("시간축 범위 수정 감지")
            
            self.main_app._user_modified_x_range = True
            
            # 시간 포맷팅 실행 (별도 처리)
            try:
                self._format_timestamp_input(event)
            except Exception as e:
                print(f"시간 포맷팅 오류: {e}")
            
            # X축 범위 저장
            try:
                self._save_current_x_range()
            except Exception as e:
                print(f"X축 범위 저장 오류: {e}")
            
            print("사용자가 시간 축 범위를 수정했습니다.")
            
            # 실시간 업데이트 스케줄링 (디바운싱)
            self._schedule_update()
            
        except Exception as e:
            print(f"시간축 범위 수정 처리 오류: {e}")
        finally:
            # 처리 완료 후 플래그 해제 (지연)
            self.window.after(200, lambda: self._reset_timestamp_processing())
    
    def _reset_timestamp_processing(self):
        """시간축 처리 플래그 리셋"""
        try:
            self._timestamp_processing = False
            print("시간축 처리 플래그 해제")
        except:
            pass
    
    def _on_timestamp_range_modified_simple(self, event):
        """시간축 범위 수정 감지 - 기존 main_app.py와 동일한 단순 처리"""
        try:
            print("시간축 범위 수정 감지")
            self.main_app._user_modified_x_range = True
            self._save_current_x_range()
            
            # 디바운싱된 업데이트
            self._schedule_update()
            
        except Exception as e:
            print(f"시간축 범위 수정 처리 오류: {e}")
        
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
        
    def _build_labels_section(self, parent):
        """제목 및 레이블 섹션"""
        labels_frame = ttk.LabelFrame(parent, text='제목 및 레이블', padding=10)
        labels_frame.pack(fill=tk.X, pady=5)
        
        # 그래프 제목
        title_frame = ttk.Frame(labels_frame)
        title_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_frame, text='그래프 제목:').pack(side=tk.LEFT)
        
        self.title_var = tk.StringVar(value=self.settings['title'])
        self.title_var.trace('w', lambda *args: self._schedule_update())
        ttk.Entry(title_frame, textvariable=self.title_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # X축 레이블
        xlabel_frame = ttk.Frame(labels_frame)
        xlabel_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xlabel_frame, text='X축 레이블:').pack(side=tk.LEFT)
        
        self.xlabel_var = tk.StringVar(value=self.settings['xlabel'])
        self.xlabel_var.trace('w', lambda *args: self._schedule_update())
        ttk.Entry(xlabel_frame, textvariable=self.xlabel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Y축 레이블
        ylabel_frame = ttk.Frame(labels_frame)
        ylabel_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ylabel_frame, text='Y축 레이블:').pack(side=tk.LEFT)
        
        self.ylabel_var = tk.StringVar(value=self.settings['ylabel'])
        self.ylabel_var.trace('w', lambda *args: self._schedule_update())
        ttk.Entry(ylabel_frame, textvariable=self.ylabel_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 글자 크기 설정 섹션
        font_frame = ttk.LabelFrame(parent, text='글자 크기 설정', padding=10)
        font_frame.pack(fill=tk.X, pady=5)
        
        # 제목 글자 크기
        title_font_frame = ttk.Frame(font_frame)
        title_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_font_frame, text='제목 글자 크기:').pack(side=tk.LEFT)
        
        self.title_fontsize_var = tk.IntVar(value=self.settings['title_fontsize'])
        self.title_fontsize_var.trace('w', lambda *args: self._schedule_update())
        title_fontsize_entry = ttk.Entry(title_font_frame, textvariable=self.title_fontsize_var, width=8)
        title_fontsize_entry.pack(side=tk.LEFT, padx=5)
        
        # X축 레이블 글자 크기
        xlabel_font_frame = ttk.Frame(font_frame)
        xlabel_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xlabel_font_frame, text='X축 레이블 글자 크기:').pack(side=tk.LEFT)
        
        self.xlabel_fontsize_var = tk.IntVar(value=self.settings['xlabel_fontsize'])
        self.xlabel_fontsize_var.trace('w', lambda *args: self._schedule_update())
        xlabel_fontsize_entry = ttk.Entry(xlabel_font_frame, textvariable=self.xlabel_fontsize_var, width=8)
        xlabel_fontsize_entry.pack(side=tk.LEFT, padx=5)
        
        # Y축 레이블 글자 크기
        ylabel_font_frame = ttk.Frame(font_frame)
        ylabel_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ylabel_font_frame, text='Y축 레이블 글자 크기:').pack(side=tk.LEFT)
        
        self.ylabel_fontsize_var = tk.IntVar(value=self.settings['ylabel_fontsize'])
        self.ylabel_fontsize_var.trace('w', lambda *args: self._schedule_update())
        ylabel_fontsize_entry = ttk.Entry(ylabel_font_frame, textvariable=self.ylabel_fontsize_var, width=8)
        ylabel_fontsize_entry.pack(side=tk.LEFT, padx=5)
        
        # X축 숫자 글자 크기
        xtick_font_frame = ttk.Frame(font_frame)
        xtick_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(xtick_font_frame, text='X축 숫자 글자 크기:').pack(side=tk.LEFT)
        
        self.x_tick_fontsize_var = tk.IntVar(value=self.settings['x_tick_fontsize'])
        self.x_tick_fontsize_var.trace('w', lambda *args: self._schedule_update())
        xtick_fontsize_entry = ttk.Entry(xtick_font_frame, textvariable=self.x_tick_fontsize_var, width=8)
        xtick_fontsize_entry.pack(side=tk.LEFT, padx=5)
        
        # Y축 숫자 글자 크기
        ytick_font_frame = ttk.Frame(font_frame)
        ytick_font_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ytick_font_frame, text='Y축 숫자 글자 크기:').pack(side=tk.LEFT)
        
        self.y_tick_fontsize_var = tk.IntVar(value=self.settings['y_tick_fontsize'])
        self.y_tick_fontsize_var.trace('w', lambda *args: self._schedule_update())
        ytick_fontsize_entry = ttk.Entry(ytick_font_frame, textvariable=self.y_tick_fontsize_var, width=8)
        ytick_fontsize_entry.pack(side=tk.LEFT, padx=5)
        
    def _choose_color(self):
        """색상 선택"""
        color = colorchooser.askcolor(title="색상 선택", color=self.color_var.get())
        if color[1]:  # 사용자가 색상을 선택한 경우
            self.color_var.set(color[1])
    
    def _format_datetime(self, value):
        """datetime 값을 문자열로 포맷팅"""
        try:
            if hasattr(value, 'strftime'):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, (int, float)):
                # Unix timestamp인 경우
                import datetime
                dt = datetime.datetime.fromtimestamp(value)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return str(value)
        except:
            return str(value)
    
    def _parse_datetime(self, value):
        """문자열을 datetime으로 파싱"""
        try:
            import datetime
            if isinstance(value, str):
                # 다양한 형식 시도
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d',
                    '%m/%d/%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S'
                ]
                for fmt in formats:
                    try:
                        return datetime.datetime.strptime(value, fmt)
                    except:
                        continue
                # 자동 파싱 시도
                return pd.to_datetime(value)
            return value
        except:
            return value

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
            
            self.xlim_min_timestamp_var.set(self._format_datetime(x_min))
            self.xlim_max_timestamp_var.set(self._format_datetime(x_max))
            
            print(f"시간축 자동 범위 설정: {x_min} ~ {x_max}")
            
        except Exception as e:
            messagebox.showerror('오류', f'자동 범위 설정 중 오류가 발생했습니다: {e}')
            print(f"시간축 자동 범위 설정 오류: {e}")

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


    def _auto_xlim(self):
        """X축 범위 자동 설정 (기존 호환성)"""
        try:
            # 현재 선택된 시트의 데이터 가져오기
            current_sheet = self.main_app.sheet_combo.get()
            if not current_sheet or current_sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터를 찾을 수 없습니다.')
                return

            df = self.main_app.df_map[current_sheet]
            if df is not None and not df.empty:
                x_col = self.main_app.x_combo.get()
                if x_col and x_col in df.columns:
                    # X 컬럼 이름에 따라 처리
                    if self.main_app._detect_datetime_column(df, x_col):
                        # 시간축 모드
                        x_data = self.main_app._parse_datetime_column(df, x_col).dropna()
                        if not x_data.empty:
                            margin = (x_data.max() - x_data.min()) * 0.05
                            min_time = x_data.min() - pd.Timedelta(seconds=margin.total_seconds())
                            max_time = x_data.max() + pd.Timedelta(seconds=margin.total_seconds())
                            self.xlim_min_timestamp_var.set(self._format_datetime(min_time))
                            self.xlim_max_timestamp_var.set(self._format_datetime(max_time))
                            print(f"자동 시간 범위 설정: {min_time} ~ {max_time}")
                    else:
                        # 숫자축 모드
                        x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
                        if not x_data.empty:
                            margin = (x_data.max() - x_data.min()) * 0.05
                            self.xlim_min_numeric_var.set(x_data.min() - margin)
                            self.xlim_max_numeric_var.set(x_data.max() + margin)
                            print(f"자동 숫자 범위 설정: {x_data.min() - margin} ~ {x_data.max() + margin}")
                else:
                    # 기존 방식 (하위 호환성)
                    if self.settings.get('is_timestamp', False):
                        # Timestamp인 경우 - main_app의 파싱 로직 사용
                        x_data = self.main_app._parse_datetime_column(df, x_col).dropna()
                        if not x_data.empty:
                            margin = (x_data.max() - x_data.min()) * 0.05
                            min_time = x_data.min() - pd.Timedelta(seconds=margin.total_seconds())
                            max_time = x_data.max() + pd.Timedelta(seconds=margin.total_seconds())
                            self.xlim_min_timestamp_var.set(self._format_datetime(min_time))
                            self.xlim_max_timestamp_var.set(self._format_datetime(max_time))
                            print(f"자동 시간 범위 설정: {min_time} ~ {max_time}")
                    else:
                        # 숫자인 경우
                        x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
                        if not x_data.empty:
                            margin = (x_data.max() - x_data.min()) * 0.05
                            self.xlim_min_numeric_var.set(x_data.min() - margin)
                            self.xlim_max_numeric_var.set(x_data.max() + margin)
                            print(f"자동 숫자 범위 설정: {x_data.min() - margin} ~ {x_data.max() + margin}")
        except Exception as e:
            print(f"X축 자동 범위 설정 오류: {e}")

    def _auto_ylim(self):
        """Y축 범위 자동 설정"""
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
            
    def _get_preview_data(self, settings):
        """미리보기용 데이터 가져오기"""
        try:
            # 현재 선택된 시트와 컬럼 정보 가져오기
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            y_selection = self.main_app.y_listbox.curselection()
            
            if (current_sheet and current_sheet in self.main_app.df_map and 
                x_col and y_selection and len(y_selection) > 0):
                
                df = self.main_app.df_map[current_sheet]
                y_col = self.main_app.y_listbox.get(y_selection[0])
                
                if x_col in df.columns and y_col in df.columns:
                    # 실제 데이터 사용 - X 컬럼 이름에 따라 처리
                    if x_col and self._is_timestamp_column_name(x_col):
                        # 시간축 모드
                        x_data = self.main_app._parse_datetime_column(df, x_col).dropna()
                        y_data = pd.to_numeric(df[y_col], errors='coerce').dropna()
                    else:
                        # 숫자축 모드
                        x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
                        y_data = pd.to_numeric(df[y_col], errors='coerce').dropna()
                    
                    # 공통 인덱스로 정렬
                    common_idx = x_data.index.intersection(y_data.index)
                    if len(common_idx) > 0:
                        x_data = x_data.loc[common_idx]
                        y_data = y_data.loc[common_idx]
                        
                        # 데이터가 너무 많으면 샘플링
                        if len(x_data) > 100:
                            step = len(x_data) // 100
                            x_data = x_data.iloc[::step]
                            y_data = y_data.iloc[::step]
                        
                        return x_data, y_data
            
            # 실제 데이터를 사용할 수 없는 경우 샘플 데이터 사용
            if settings.get('is_timestamp', False):
                # 시간 축 샘플 데이터
                import datetime
                start_time = datetime.datetime.now() - datetime.timedelta(hours=1)
                x = [start_time + datetime.timedelta(minutes=i) for i in range(0, 60, 2)]
                y = np.sin(np.linspace(0, 4*np.pi, len(x)))
            else:
                # 숫자 축 샘플 데이터
                x = np.linspace(0, 10, 50)
                y = np.sin(x)
            
            return x, y
            
        except Exception as e:
            print(f"미리보기 데이터 가져오기 오류: {e}")
            # 기본 샘플 데이터
            x = np.linspace(0, 10, 50)
            y = np.sin(x)
            return x, y
            
    def _preview_plot(self):
        """미리보기 플롯"""
        try:
            # 설정 수집
            settings = self._collect_settings()
            
            # 임시 플롯 생성
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # 실제 데이터 사용 (가능한 경우)
            x, y = self._get_preview_data(settings)
            
            # 플롯 타입에 따라 그리기
            if settings['plot_type'] == 'line':
                ax.plot(x, y, linestyle=settings['line_style'], 
                       color=settings['color'], linewidth=settings['line_width'])
            elif settings['plot_type'] == 'scatter':
                ax.scatter(x, y, marker=settings['marker'], 
                          color=settings['color'], s=settings['marker_size']**2)
            else:  # both
                ax.plot(x, y, linestyle=settings['line_style'], 
                       color=settings['color'], linewidth=settings['line_width'],
                       marker=settings['marker'], markersize=settings['marker_size'])
            
            # 축 설정
            try:
                if settings.get('is_timestamp', False):
                    # 시간 축인 경우
                    import matplotlib.dates as mdates
                    
                    # 시간 축 포맷터 설정
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(x)//10)))
                    
                    # 사용자가 지정한 시간 범위 사용
                    if isinstance(settings['xlim_min'], str):
                        xlim_min = pd.to_datetime(settings['xlim_min'])
                        xlim_max = pd.to_datetime(settings['xlim_max'])
                        
                        # matplotlib의 날짜 변환 사용
                        xlim_min_num = mdates.date2num(xlim_min)
                        xlim_max_num = mdates.date2num(xlim_max)
                        
                        ax.set_xlim(xlim_min_num, xlim_max_num)
                    else:
                        # 데이터 기반 범위 사용
                        ax.set_xlim(x.min(), x.max())
                    
                    ax.set_ylim(settings['ylim_min'], settings['ylim_max'])
                    # Y축: 간격 단위로 틱 생성 (끝값 제외)
                    try:
                        y_start = float(settings['ylim_min'])
                        y_end = float(settings['ylim_max'])
                        y_step = max(1e-12, float(settings['y_ticks']))
                        y_ticks = np.arange(y_start, y_end, y_step)
                        ax.set_yticks(y_ticks)
                    except Exception:
                        pass
                else:
                    # 숫자 축인 경우 (안전한 변환)
                    try:
                        if isinstance(settings['xlim_min'], str):
                            xlim_min = float(0)
                            xlim_max = float(10)
                        else:
                            xlim_min = float(settings['xlim_min'])
                            xlim_max = float(settings['xlim_max'])
                    except (ValueError, TypeError):
                        # 변환 실패 시 기본값 사용
                        print("미리보기에서 X축 범위 변환 실패, 기본값 사용")
                        xlim_min = float(0)
                        xlim_max = float(10)
                    
                    ax.set_xlim(xlim_min, xlim_max)
                    ax.set_ylim(settings['ylim_min'], settings['ylim_max'])
                    # X축: 간격 단위로 틱 생성, 시작/끝 포함
                    try:
                        x_start = float(xlim_min)
                        x_end = float(xlim_max)
                        x_step = max(1e-12, float(settings['x_ticks']))
                        x_ticks = np.arange(x_start, x_end, x_step)
                        if len(x_ticks) == 0 or abs(x_ticks[0] - x_start) > 1e-9:
                            x_ticks = np.insert(x_ticks, 0, x_start)
                        if len(x_ticks) == 0 or abs(x_ticks[-1] - x_end) > 1e-9:
                            x_ticks = np.append(x_ticks, x_end)
                        ax.set_xticks(x_ticks)
                    except Exception:
                        pass

                    # Y축: 간격 단위로 틱 생성, 시작/끝 포함
                    try:
                        y_start = float(settings['ylim_min'])
                        y_end = float(settings['ylim_max'])
                        y_step = max(1e-12, float(settings['y_ticks']))
                        y_ticks = np.arange(y_start, y_end, y_step)
                        if len(y_ticks) == 0 or abs(y_ticks[0] - y_start) > 1e-9:
                            y_ticks = np.insert(y_ticks, 0, y_start)
                        if len(y_ticks) == 0 or abs(y_ticks[-1] - y_end) > 1e-9:
                            y_ticks = np.append(y_ticks, y_end)
                        ax.set_yticks(y_ticks)
                    except Exception:
                        pass
            except Exception as e:
                print(f"축 설정 오류: {e}")
                # 기본값 사용
                ax.set_xlim(x.min() if hasattr(x, 'min') else 0, x.max() if hasattr(x, 'max') else 10)
                ax.set_ylim(y.min() if hasattr(y, 'min') else 0, y.max() if hasattr(y, 'max') else 1)
            
            # 제목 및 레이블
            ax.set_title(settings['title'], fontsize=settings['title_fontsize'])
            ax.set_xlabel(settings['xlabel'], fontsize=settings['xlabel_fontsize'])
            ax.set_ylabel(settings['ylabel'], fontsize=settings['ylabel_fontsize'])
            
            # 축 숫자 글자 크기 설정
            ax.tick_params(axis='x', labelsize=settings['x_tick_fontsize'])
            ax.tick_params(axis='y', labelsize=settings['y_tick_fontsize'])
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror('오류', f'미리보기 생성 중 오류가 발생했습니다: {e}')
            
    def _convert_korean_time_format(self, korean_format: str) -> str:
        """한글 시간 형식을 matplotlib 형식으로 변환"""
        format_mapping = {
            '시:분:초:밀리초': '%H:%M:%S.%f',
            '시:분:초': '%H:%M:%S',
            '시:분': '%H:%M',
            '년-월-일 시:분:초': '%Y-%m-%d %H:%M:%S',
            '년-월-일 시:분': '%Y-%m-%d %H:%M'
        }
        return format_mapping.get(korean_format, '%H:%M:%S.%f')
    
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
            'ylim_max': self.ylim_max_var.get(),
            'x_ticks': self.x_ticks_var.get(),
            'y_ticks': self.y_ticks_var.get(),
            'title_fontsize': self.title_fontsize_var.get(),
            'xlabel_fontsize': self.xlabel_fontsize_var.get(),
            'ylabel_fontsize': self.ylabel_fontsize_var.get(),
            'x_tick_fontsize': self.x_tick_fontsize_var.get(),
            'y_tick_fontsize': self.y_tick_fontsize_var.get(),
            'is_timestamp': self.settings.get('is_timestamp', False),
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
        
        # 원본 설정 저장 (취소 시 복원용)
        if self.original_settings is None:
            self.original_settings = settings.copy()
            print("원본 설정 저장 완료")
        
        return settings
        
    def _cancel_settings(self):
        """설정 취소 - 원본 설정으로 복원"""
        try:
            if self.original_settings is not None:
                print("원본 설정으로 복원 중...")
                # 원본 설정을 메인 앱에 적용
                self.main_app.apply_plot_settings(self.original_settings)
                print("원본 설정 복원 완료")
            else:
                print("원본 설정이 없어 복원할 수 없습니다.")
            
            # 창 닫기
            self.window.destroy()
            
        except Exception as e:
            print(f"설정 취소 중 오류: {e}")
            # 오류가 발생해도 창은 닫기
            self.window.destroy()

    def _apply_settings(self):
        """설정 적용"""
        try:
            settings = self._collect_settings()
            
            # 입력값 검증
            if not self._validate_settings(settings):
                return
            
            # 현재 X축 범위 저장
            self._save_current_x_range()
            
            # 메인 앱에 설정 전달
            self.main_app.apply_plot_settings(settings)
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror('오류', f'설정 적용 중 오류가 발생했습니다: {e}')
    
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
