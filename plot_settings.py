"""
그래프 설정 편집 창 - Single/Double Y축 탭 구조
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd
import threading
import time

# Single/Double Y축/Error Bar 하위 모듈
from single_y_axis import SingleYAxisSettings
from double_y_axis import DoubleYAxisSettings
from error_bar_plot import ErrorBarSettings
from theme_manager import ThemeManager


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
        self.window.geometry('900x1100')
        self.window.transient(parent)
        self.window.grab_set()

        # 테마 관리자 초기화
        self.theme_manager = ThemeManager(self)
        
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

    def _on_axis_entry_modified(self, event=None):
        """축 입력 필드 수정 시 호출되는 콜백 (KeyRelease 이벤트용)"""
        # 입력이 완료된 후 (키를 놓을 때) 업데이트 스케줄링
        self._schedule_update()

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
            
            # 사용자가 수정한 Y축 범위가 있는지 확인
            if not hasattr(self.main_app, '_user_modified_y_range'):
                self.main_app._user_modified_y_range = False
            
            if not hasattr(self.main_app, '_saved_y_range'):
                self.main_app._saved_y_range = {}
            
            # 사용자가 수정한 스타일 설정 확인
            if not hasattr(self.main_app, '_saved_plot_styles'):
                self.main_app._saved_plot_styles = {}
            
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
            
            # Y축 범위 결정 (사용자 수정 값 또는 현재 플롯 값)
            fig = self.main_app.figure
            ax = fig.axes[0] if fig and fig.axes else None
            
            # Y축 범위 가져오기
            if self.main_app._user_modified_y_range and range_key in self.main_app._saved_y_range:
                # 사용자가 수정한 Y축 범위 사용
                saved_y_range = self.main_app._saved_y_range[range_key]
                actual_y_min = saved_y_range['min']
                actual_y_max = saved_y_range['max']
                print(f"저장된 Y축 범위 사용: {actual_y_min} ~ {actual_y_max}")
            elif ax:
                # 현재 플롯의 Y축 범위 사용
                actual_y_min = ax.get_ylim()[0]
                actual_y_max = ax.get_ylim()[1]
                print(f"현재 플롯 Y축 범위 사용: {actual_y_min} ~ {actual_y_max}")
            else:
                # 기본값
                actual_y_min = 0.0
                actual_y_max = 10.0
            
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
                    'ylim_min': actual_y_min,
                    'ylim_max': actual_y_max,
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
                
                # 저장된 스타일이 있으면 먼저 로드
                if range_key in self.main_app._saved_plot_styles:
                    saved_styles = self.main_app._saved_plot_styles[range_key]
                    self.settings['y_colors'] = saved_styles.get('y_colors', {}).copy()
                    self.settings['y_line_widths'] = saved_styles.get('y_line_widths', {}).copy()
                    self.settings['y_line_styles'] = saved_styles.get('y_line_styles', {}).copy()
                    self.settings['y_markers'] = saved_styles.get('y_markers', {}).copy()
                    self.settings['y_marker_sizes'] = saved_styles.get('y_marker_sizes', {}).copy()
                    self.settings['y_plot_types'] = saved_styles.get('y_plot_types', {}).copy()
                    print(f"저장된 스타일 복원: {range_key}")
                
                # 저장된 스타일이 없으면 현재 플롯에서 추출
                if lines and not self.settings['y_colors']:
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
            else:
                print("No active plot found. Using default settings.")
                self.settings = {
                    'plot_type': 'line', 'line_style': '-', 'marker': 'o', 'color': '#1f77b4',
                    'line_width': 1.5, 'marker_size': 6, 'title': '', 'xlabel': '', 'ylabel': '',
                    'xlim_min': actual_x_min,
                    'xlim_max': actual_x_max,
                    'ylim_min': 0.0,
                    'ylim_max': 10.0,
                    'x_ticks': 1, 'y_ticks': 1,
                    'x_tick_fontsize': 12, 'y_tick_fontsize': 12,
                    'xlabel_fontsize': 16, 'ylabel_fontsize': 16,
                    'title_fontsize': 14,
                    'is_timestamp': is_timestamp,
                    'y_colors': {}, 'y_line_widths': {}, 'y_line_styles': {},
                    'y_markers': {}, 'y_marker_sizes': {}, 'y_plot_types': {}
                }
        except Exception as e:
            print(f"현재 설정 가져오기 오류: {e}")
            import traceback
            traceback.print_exc()
            # 기본값 설정 (에러 발생 시)
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
                'xlim_min': 0.0,  # 기본값 사용
                'xlim_max': 10.0,  # 기본값 사용
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
                'y_colors': {},
                'y_line_widths': {},
                'y_line_styles': {},
                'y_markers': {},
                'y_marker_sizes': {},
                'y_plot_types': {},
            }
    
    def _build_ui(self):
        """UI 구성 - Single/Double Y축 탭 구조"""
        # 메인 프레임
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Single/Double Y축 탭
        self.main_notebook = ttk.Notebook(main_frame)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)

        # Single Y축 탭
        self.single_y_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.single_y_tab, text='Single Y축')

        # Double Y축 탭
        self.double_y_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.double_y_tab, text='Double Y축')

        # Error Bar 탭
        self.error_bar_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.error_bar_tab, text='Error Bar')

        # Single Y축 설정 인스턴스화
        self.single_y_settings = SingleYAxisSettings(
            parent_tab=self.single_y_tab,
            plot_settings_window=self,
            main_app=self.main_app
        )

        # Double Y축 설정 인스턴스화
        self.double_y_settings = DoubleYAxisSettings(
            parent_tab=self.double_y_tab,
            plot_settings_window=self,
            main_app=self.main_app
        )

        # Error Bar 설정 인스턴스화
        self.error_bar_settings = ErrorBarSettings(
            parent_tab=self.error_bar_tab,
            plot_settings_window=self,
            main_app=self.main_app
        )

        # 마지막으로 선택한 탭 복원 (우선순위: 마지막 선택 탭 > 저장된 Double Y 설정)
        current_sheet = self.main_app.sheet_combo.get()
        x_col = self.main_app.x_combo.get()
        range_key = f"{current_sheet}_{x_col}"

        # 마지막 선택 탭이 저장되어 있으면 그것을 우선 사용
        if hasattr(self.main_app, '_last_selected_tab') and range_key in self.main_app._last_selected_tab:
            last_tab_index = self.main_app._last_selected_tab[range_key]
            if last_tab_index == 0:
                self.main_notebook.select(self.single_y_tab)
                print(f"마지막 선택 탭 복원: Single Y축")
            elif last_tab_index == 1:
                self.main_notebook.select(self.double_y_tab)
                print(f"마지막 선택 탭 복원: Double Y축")
            elif last_tab_index == 2:
                self.main_notebook.select(self.error_bar_tab)
                print(f"마지막 선택 탭 복원: Error Bar")
        else:
            # 마지막 선택 탭이 없으면 저장된 Double Y 설정 확인
            saved_settings = self.main_app._saved_double_y_settings.get(range_key, {})
            if saved_settings.get('use_double_y', False):
                self.main_notebook.select(self.double_y_tab)
                print(f"저장된 설정에 따라 Double Y축 탭 선택")

        # 탭 전환 이벤트 바인딩 - Single/Double Y축 자동 전환
        self.main_notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 왼쪽: 테마 버튼
        ttk.Button(button_frame, text='테마(Theme)', command=lambda: self.theme_manager.show_theme_window()).pack(side=tk.LEFT, padx=5)

        # 오른쪽: 적용/취소 버튼
        ttk.Button(button_frame, text='취소', command=self._cancel_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text='적용', command=self._apply_settings).pack(side=tk.RIGHT, padx=5)

    def _on_tab_changed(self, event=None):
        """탭 전환 시 자동으로 Single/Double Y축/Error Bar 모드 전환"""
        try:
            # 현재 선택된 탭 인덱스 확인
            current_tab_index = self.main_notebook.index(self.main_notebook.select())

            # 마지막으로 선택한 탭을 main_app에 저장
            if not hasattr(self.main_app, '_last_selected_tab'):
                self.main_app._last_selected_tab = {}

            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"
            self.main_app._last_selected_tab[range_key] = current_tab_index
            print(f"마지막 선택 탭 저장: {range_key} -> {current_tab_index}")

            # 0: Single Y축, 1: Double Y축, 2: Error Bar
            if current_tab_index == 0:  # Single Y축 탭
                print("Single Y축 탭으로 전환 - Single Y 모드 활성화")
                self._switch_to_single_y_mode()
            elif current_tab_index == 1:  # Double Y축 탭
                print("Double Y축 탭으로 전환 - Double Y 모드 활성화")
                self._switch_to_double_y_mode()
            elif current_tab_index == 2:  # Error Bar 탭
                print("Error Bar 탭으로 전환 - Error Bar 모드 활성화")
                self._switch_to_error_bar_mode()
        except Exception as e:
            print(f"탭 전환 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    def _switch_to_single_y_mode(self):
        """Single Y축 모드로 전환"""
        try:
            # Single Y축 설정 수집
            settings = self.single_y_settings.collect_settings()

            # use_double_y를 False로 설정
            settings['use_double_y'] = False

            # Y 컬럼이 선택되지 않았을 경우 조용히 종료
            # Single Y축 탭의 single_y_listbox 확인 (우선순위)
            y_indices = None
            if hasattr(self.single_y_settings, 'single_y_listbox'):
                y_indices = self.single_y_settings.single_y_listbox.curselection()

            # Single Y축 탭에 선택이 없으면 Main app의 y_listbox 확인 (호환성)
            if not y_indices:
                y_indices = self.main_app.y_listbox.curselection()

            if not y_indices:
                print("Single Y축 탭으로 전환했지만 Y 컬럼이 선택되지 않아 그래프 업데이트를 건너뜁니다.")
                # 오른쪽 축만 제거
                if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None:
                    try:
                        self.main_app.ax2.clear()
                        self.main_app.ax2.remove()
                        self.main_app.ax2 = None
                        self.main_app.plot_canvas.draw_idle()
                        print("오른쪽 Y축 제거 완료")
                    except Exception as e:
                        print(f"오른쪽 Y축 제거 오류: {e}")
                return

            # 설정 유효성 검사 (경고 메시지 표시 안 함)
            if self._validate_settings(settings):
                # 그래프 업데이트 (ax2 제거됨)
                self._safe_apply_plot_settings(settings)
                print("Single Y축 모드로 전환 완료")
        except Exception as e:
            print(f"Single Y축 모드 전환 오류: {e}")
            import traceback
            traceback.print_exc()

    def _switch_to_double_y_mode(self):
        """Double Y축 모드로 전환"""
        try:
            # Double Y축 설정 수집
            settings = self.double_y_settings.collect_settings()

            # use_double_y를 True로 설정 (이미 collect_settings에서 설정되지만 명시적으로)
            settings['use_double_y'] = True

            # 왼쪽/오른쪽 Y 컬럼이 선택되지 않았을 경우 조용히 종료
            left_cols = settings.get('left_y_columns', [])
            right_cols = settings.get('right_y_columns', [])
            if not left_cols and not right_cols:
                print("Double Y축 탭으로 전환했지만 Y 컬럼이 선택되지 않아 그래프 업데이트를 건너뜁니다.")
                return

            # 설정 유효성 검사 (경고 메시지 표시 안 함)
            if self._validate_settings(settings):
                # 그래프 업데이트 (ax2 생성됨)
                self._safe_apply_plot_settings(settings)
                print("Double Y축 모드로 전환 완료")
        except Exception as e:
            print(f"Double Y축 모드 전환 오류: {e}")
            import traceback
            traceback.print_exc()

    def _switch_to_error_bar_mode(self):
        """Error Bar 모드로 전환"""
        try:
            # Error Bar 설정 수집
            settings = self.error_bar_settings.collect_settings()

            # Y 컬럼이 선택되지 않았을 경우 조용히 종료
            if settings['data_mode'] == 'repeated':
                if not settings.get('y_columns'):
                    print("Error Bar 탭으로 전환했지만 Y 컬럼이 선택되지 않아 그래프 업데이트를 건너뜁니다.")
                    return
            else:
                if not settings.get('y_mean_column'):
                    print("Error Bar 탭으로 전환했지만 Y 평균 컬럼이 선택되지 않아 그래프 업데이트를 건너뜁니다.")
                    return

            # 설정 유효성 검사 (경고 메시지 표시 안 함)
            if self._validate_settings(settings):
                # 그래프 업데이트
                self._safe_apply_plot_settings(settings)
                print("Error Bar 모드로 전환 완료")
        except Exception as e:
            print(f"Error Bar 모드 전환 오류: {e}")
            import traceback
            traceback.print_exc()

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

    def _collect_settings(self):
        """현재 설정 수집 - 활성화된 탭에서 수집"""
        # 현재 활성화된 탭 확인
        current_tab_index = self.main_notebook.index(self.main_notebook.select())

        # Single Y축 탭 (0), Double Y축 탭 (1), Error Bar 탭 (2)
        if current_tab_index == 0:  # Single Y축
            if hasattr(self.single_y_settings, 'collect_settings'):
                return self.single_y_settings.collect_settings()
            else:
                print("Warning: Single Y 설정 수집 메서드가 없습니다")
                return {}
        elif current_tab_index == 1:  # Double Y축
            if hasattr(self.double_y_settings, 'collect_settings'):
                return self.double_y_settings.collect_settings()
            else:
                print("Warning: Double Y 설정 수집 메서드가 없습니다")
                return {}
        else:  # Error Bar
            if hasattr(self.error_bar_settings, 'collect_settings'):
                return self.error_bar_settings.collect_settings()
            else:
                print("Warning: Error Bar 설정 수집 메서드가 없습니다")
                return {}
        
    def _cancel_settings(self):
        """설정 취소 - 원본 설정으로 복원"""
        try:
            # 현재 선택된 탭 저장 (취소해도 탭 선택은 유지)
            self._save_current_tab()

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

            # 현재 선택된 탭 저장
            self._save_current_tab()

            # 현재 X축, Y축 범위 저장
            self._save_current_x_range(settings)
            self._save_current_y_range(settings)

            # 현재 스타일 설정 저장
            self._save_current_plot_styles(settings)

            # 메인 앱에 설정 전달
            self.main_app.apply_plot_settings(settings)

            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror('오류', f'설정 적용 중 오류가 발생했습니다: {e}')

    def _save_current_x_range(self, settings=None):
        """현재 X축 범위 저장"""
        try:
            if settings is None:
                settings = self._collect_settings()
            
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"
            
            if not hasattr(self.main_app, '_saved_x_range'):
                self.main_app._saved_x_range = {}
            
            self.main_app._saved_x_range[range_key] = {
                'min': settings.get('xlim_min'),
                'max': settings.get('xlim_max')
            }
        except Exception as e:
            print(f"X축 범위 저장 오류: {e}")

    def _save_current_y_range(self, settings=None):
        """현재 Y축 범위 저장"""
        try:
            if settings is None:
                settings = self._collect_settings()
            
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"
            
            if not hasattr(self.main_app, '_saved_y_range'):
                self.main_app._saved_y_range = {}
                
            # Double Y축 모드인지 확인
            if self.main_notebook.index(self.main_notebook.select()) == 1:
                # Double Y축은 별도로 저장됨 (_saved_double_y_settings)
                # 여기서는 왼쪽 축을 기본으로 저장
                self.main_app._saved_y_range[range_key] = {
                    'min': settings.get('left_ylim_min'),
                    'max': settings.get('left_ylim_max')
                }
                
                # Double Y 설정 저장
                if not hasattr(self.main_app, '_saved_double_y_settings'):
                    self.main_app._saved_double_y_settings = {}
                
                # 기존 설정 가져오기
                existing = self.main_app._saved_double_y_settings.get(range_key, {})
                if existing is None: existing = {} # Safety check
                
                # 업데이트
                existing.update(settings)
                self.main_app._saved_double_y_settings[range_key] = existing
                
            else:
                # Single Y축
                self.main_app._saved_y_range[range_key] = {
                    'min': settings.get('ylim_min'),
                    'max': settings.get('ylim_max')
                }
        except Exception as e:
            print(f"Y축 범위 저장 오류: {e}")

    def _save_current_plot_styles(self, settings=None):
        """현재 플롯 스타일 저장"""
        try:
            if settings is None:
                settings = self._collect_settings()
            
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"
            
            if not hasattr(self.main_app, '_saved_plot_styles'):
                self.main_app._saved_plot_styles = {}
            
            self.main_app._saved_plot_styles[range_key] = {
                'y_colors': settings.get('y_colors', {}),
                'y_line_widths': settings.get('y_line_widths', {}),
                'y_line_styles': settings.get('y_line_styles', {}),
                'y_markers': settings.get('y_markers', {}),
                'y_marker_sizes': settings.get('y_marker_sizes', {}),
                'y_plot_types': settings.get('y_plot_types', {})
            }
        except Exception as e:
            print(f"플롯 스타일 저장 오류: {e}")

    def _save_current_tab(self):
        """현재 선택된 탭 저장"""
        try:
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"

            if not hasattr(self.main_app, '_last_selected_tab'):
                self.main_app._last_selected_tab = {}

            current_tab_index = self.main_notebook.index(self.main_notebook.select())
            self.main_app._last_selected_tab[range_key] = current_tab_index
            print(f"현재 탭 저장 (적용/취소): {range_key} -> {current_tab_index}")
        except Exception as e:
            print(f"탭 저장 오류: {e}")

    def _validate_settings(self, settings):
        """설정값 검증 - 활성화된 탭에서 검증"""
        # 현재 활성화된 탭 확인
        current_tab_index = self.main_notebook.index(self.main_notebook.select())

        # Single Y축 탭 (0), Double Y축 탭 (1), Error Bar 탭 (2)
        if current_tab_index == 0:  # Single Y축
            if hasattr(self.single_y_settings, 'validate_settings'):
                return self.single_y_settings.validate_settings(settings)
            else:
                print("Warning: Single Y 설정 검증 메서드가 없습니다")
                return True  # 기본적으로 통과
        elif current_tab_index == 1:  # Double Y축
            if hasattr(self.double_y_settings, 'validate_settings'):
                return self.double_y_settings.validate_settings(settings)
            else:
                print("Warning: Double Y 설정 검증 메서드가 없습니다")
                return True  # 기본적으로 통과
        else:  # Error Bar
            if hasattr(self.error_bar_settings, 'validate_settings'):
                return self.error_bar_settings.validate_settings(settings)
            else:
                print("Warning: Error Bar 설정 검증 메서드가 없습니다")
                return True  # 기본적으로 통과
    
