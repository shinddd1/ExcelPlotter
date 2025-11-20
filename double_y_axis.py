"""
Double Y축 설정 모듈
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np


class DoubleYAxisSettings:
    """Double Y축 설정을 위한 클래스"""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.window = None
        
        # Double Y축 설정
        self.use_double_y = tk.BooleanVar(value=False)
        self.left_y_columns = []
        self.right_y_columns = []
        
        # 오른쪽 Y축 범위 설정
        self.right_ylim_min = tk.DoubleVar(value=0)
        self.right_ylim_max = tk.DoubleVar(value=10)
        
        # Y축 색상 (축 눈금, 레이블 색상만)
        self.left_axis_color = tk.StringVar(value='#000000')   # 검은색 (기본)
        self.right_axis_color = tk.StringVar(value='#000000')  # 검은색 (기본)
        
        # Y축 타이틀
        self.right_ylabel = tk.StringVar(value='')  # 오른쪽 Y축 타이틀
    
    def show_settings_window(self):
        """Double Y축 설정 창 표시"""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title('Double Y축 설정')
        self.window.geometry('500x600')
        self.window.transient(self.parent)
        
        self._build_ui()
    
    def _build_ui(self):
        """UI 구성"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Double Y축 활성화 체크박스
        enable_frame = ttk.Frame(main_frame)
        enable_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(
            enable_frame, 
            text='Double Y축 사용', 
            variable=self.use_double_y,
            command=self._on_double_y_toggle
        ).pack(side=tk.LEFT)
        
        # 왼쪽 Y축 설정
        left_frame = ttk.LabelFrame(main_frame, text='왼쪽 Y축 (Primary)', padding=10)
        left_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 왼쪽 Y축 컬럼 선택
        ttk.Label(left_frame, text='왼쪽 Y축 컬럼:').pack(anchor=tk.W)
        
        left_list_frame = ttk.Frame(left_frame)
        left_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        left_scrollbar = ttk.Scrollbar(left_list_frame)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.left_y_listbox = tk.Listbox(
            left_list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=left_scrollbar.set,
            height=6,
            exportselection=False  # 선택 유지를 위해 추가
        )
        self.left_y_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.config(command=self.left_y_listbox.yview)
        # 선택 변경 이벤트 바인딩
        self.left_y_listbox.bind('<<ListboxSelect>>', self._on_left_selection_changed)
        
        # 왼쪽 Y축 색상 설정
        left_axis_color_frame = ttk.Frame(left_frame)
        left_axis_color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(left_axis_color_frame, text='Y축 색상:').pack(side=tk.LEFT)
        ttk.Entry(left_axis_color_frame, textvariable=self.left_axis_color, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_axis_color_frame, text='선택', command=self._choose_left_axis_color, width=6).pack(side=tk.LEFT)
        
        # 오른쪽 Y축 설정
        right_frame = ttk.LabelFrame(main_frame, text='오른쪽 Y축 (Secondary)', padding=10)
        right_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 오른쪽 Y축 컬럼 선택
        ttk.Label(right_frame, text='오른쪽 Y축 컬럼:').pack(anchor=tk.W)
        
        right_list_frame = ttk.Frame(right_frame)
        right_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        right_scrollbar = ttk.Scrollbar(right_list_frame)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.right_y_listbox = tk.Listbox(
            right_list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=right_scrollbar.set,
            height=6,
            exportselection=False  # 선택 유지를 위해 추가
        )
        self.right_y_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scrollbar.config(command=self.right_y_listbox.yview)
        # 선택 변경 이벤트 바인딩
        self.right_y_listbox.bind('<<ListboxSelect>>', self._on_right_selection_changed)
        
        # 오른쪽 Y축 타이틀
        right_ylabel_frame = ttk.Frame(right_frame)
        right_ylabel_frame.pack(fill=tk.X, pady=5)
        ttk.Label(right_ylabel_frame, text='Y축 타이틀:').pack(side=tk.LEFT)
        ttk.Entry(right_ylabel_frame, textvariable=self.right_ylabel, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 오른쪽 Y축 색상 설정
        right_axis_color_frame = ttk.Frame(right_frame)
        right_axis_color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(right_axis_color_frame, text='Y축 색상:').pack(side=tk.LEFT)
        ttk.Entry(right_axis_color_frame, textvariable=self.right_axis_color, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_axis_color_frame, text='선택', command=self._choose_right_axis_color, width=6).pack(side=tk.LEFT)
        
        # 오른쪽 Y축 범위
        range_frame = ttk.Frame(right_frame)
        range_frame.pack(fill=tk.X, pady=5)
        ttk.Label(range_frame, text='Y축 범위:').pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.right_ylim_min, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(range_frame, text='~').pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.right_ylim_max, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(range_frame, text='자동', command=self._auto_right_ylim).pack(side=tk.LEFT, padx=5)
        
        # 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text='적용', command=self._apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='취소', command=self._close_window).pack(side=tk.RIGHT, padx=5)
        
        # 초기 데이터 로드
        self._load_columns()
    
    def _load_columns(self):
        """현재 선택된 시트의 컬럼 로드"""
        try:
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                return
            
            df = self.main_app.df_map[sheet]
            columns = list(df.columns)
            
            # X축 컬럼 제외
            x_col = self.main_app.x_combo.get()
            if x_col in columns:
                columns.remove(x_col)
            
            # 리스트박스 업데이트
            self.left_y_listbox.delete(0, tk.END)
            self.right_y_listbox.delete(0, tk.END)
            
            for col in columns:
                self.left_y_listbox.insert(tk.END, col)
                self.right_y_listbox.insert(tk.END, col)
            
            # 기존 선택 복원
            for i, col in enumerate(columns):
                if col in self.left_y_columns:
                    self.left_y_listbox.selection_set(i)
                if col in self.right_y_columns:
                    self.right_y_listbox.selection_set(i)
                    
        except Exception as e:
            print(f"컬럼 로드 오류: {e}")
    
    def _on_left_selection_changed(self, event):
        """왼쪽 Y축 선택 변경 시 즉시 저장"""
        try:
            selected_indices = self.left_y_listbox.curselection()
            self.left_y_columns = [self.left_y_listbox.get(i) for i in selected_indices]
            print(f"왼쪽 Y축 선택: {self.left_y_columns}")
        except Exception as e:
            print(f"왼쪽 선택 변경 오류: {e}")
    
    def _on_right_selection_changed(self, event):
        """오른쪽 Y축 선택 변경 시 즉시 저장"""
        try:
            selected_indices = self.right_y_listbox.curselection()
            self.right_y_columns = [self.right_y_listbox.get(i) for i in selected_indices]
            print(f"오른쪽 Y축 선택: {self.right_y_columns}")
        except Exception as e:
            print(f"오른쪽 선택 변경 오류: {e}")
    
    def _on_double_y_toggle(self):
        """Double Y축 토글"""
        if self.use_double_y.get():
            print("Double Y축 활성화")
        else:
            print("Double Y축 비활성화")
    
    def _choose_left_axis_color(self):
        """왼쪽 Y축 색상 선택"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(title='왼쪽 Y축 색상 선택', color=self.left_axis_color.get())
        if color[1]:
            self.left_axis_color.set(color[1])
    
    def _choose_right_axis_color(self):
        """오른쪽 Y축 색상 선택"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(title='오른쪽 Y축 색상 선택', color=self.right_axis_color.get())
        if color[1]:
            self.right_axis_color.set(color[1])
    
    def _auto_right_ylim(self):
        """오른쪽 Y축 범위 자동 설정"""
        try:
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터를 찾을 수 없습니다.')
                return
            
            df = self.main_app.df_map[sheet]
            
            # 선택된 오른쪽 Y축 컬럼들의 범위 계산
            right_indices = self.right_y_listbox.curselection()
            if not right_indices:
                messagebox.showwarning('경고', '오른쪽 Y축 컬럼을 선택하세요.')
                return
            
            right_cols = [self.right_y_listbox.get(i) for i in right_indices]
            
            all_data = []
            for col in right_cols:
                if col in df.columns:
                    data = pd.to_numeric(df[col], errors='coerce').dropna()
                    all_data.extend(data.values)
            
            if all_data:
                y_min = float(np.min(all_data))
                y_max = float(np.max(all_data))
                
                # 여백 추가
                y_range = y_max - y_min
                if y_range > 0:
                    margin = y_range * 0.05
                    y_min -= margin
                    y_max += margin
                
                self.right_ylim_min.set(y_min)
                self.right_ylim_max.set(y_max)
                
                print(f"오른쪽 Y축 자동 범위: {y_min} ~ {y_max}")
            else:
                messagebox.showwarning('경고', '유효한 데이터가 없습니다.')
                
        except Exception as e:
            messagebox.showerror('오류', f'자동 범위 설정 중 오류: {e}')
    
    def _apply_settings(self):
        """설정 적용"""
        try:
            # 선택된 컬럼은 이미 이벤트 핸들러에서 저장됨
            # 유효성 검사만 수행
            if self.use_double_y.get():
                if not self.left_y_columns and not self.right_y_columns:
                    messagebox.showwarning('경고', '최소 하나의 Y축 컬럼을 선택하세요.')
                    return
            
            print(f"적용할 설정 - 왼쪽: {self.left_y_columns}, 오른쪽: {self.right_y_columns}")
            
            # 메인 앱에 적용
            self._apply_to_main_app()
            
            self._close_window()
            
        except Exception as e:
            messagebox.showerror('오류', f'설정 적용 중 오류: {e}')
    
    def _close_window(self):
        """설정 창 닫기"""
        if self.window is not None:
            self.window.destroy()
            self.window = None
    
    def _apply_to_main_app(self):
        """메인 앱에 Double Y축 설정 적용"""
        try:
            if not self.use_double_y.get():
                # Double Y축 비활성화 - 일반 플롯
                print("일반 플롯 모드")
                
                # 기존 오른쪽 Y축 제거
                if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None:
                    try:
                        self.main_app.ax2.clear()
                        self.main_app.ax2.remove()
                    except:
                        pass
                    self.main_app.ax2 = None
                
                # Figure의 추가 axes 제거
                while len(self.main_app.figure.axes) > 1:
                    try:
                        self.main_app.figure.axes[-1].remove()
                    except:
                        break
                
                # 일반 플롯 재적용
                if hasattr(self.main_app, 'current_plot_settings'):
                    self.main_app.apply_plot_settings(self.main_app.current_plot_settings)
                
                return
            
            # Double Y축 플롯 그리기
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                return
            
            df = self.main_app.df_map[sheet]
            x_col = self.main_app.x_combo.get()
            
            if not x_col:
                messagebox.showwarning('경고', 'X축 컬럼을 선택하세요.')
                return
            
            # 데이터 변환
            x = None
            left_ymap = {}
            right_ymap = {}
            
            if self.left_y_columns:
                x, left_ymap = self.main_app._apply_transforms(df, x_col, self.left_y_columns)
            
            if self.right_y_columns:
                if x is None:
                    x, right_ymap = self.main_app._apply_transforms(df, x_col, self.right_y_columns)
                else:
                    _, right_ymap = self.main_app._apply_transforms(df, x_col, self.right_y_columns)
            
            if x is None:
                messagebox.showwarning('경고', '유효한 데이터가 없습니다.')
                return
            
            # 기존 플롯 완전히 클리어
            self.main_app.ax.clear()
            
            # 기존 오른쪽 Y축 완전히 제거
            if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None:
                try:
                    self.main_app.ax2.clear()  # 먼저 클리어
                    self.main_app.ax2.remove()  # 그 다음 제거
                except Exception as e:
                    print(f"ax2 제거 중 오류: {e}")
                self.main_app.ax2 = None
            
            # Figure의 모든 axes 확인 및 정리
            while len(self.main_app.figure.axes) > 1:
                try:
                    self.main_app.figure.axes[-1].remove()
                except:
                    break
            
            # Plot Settings에서 스타일 정보 가져오기 (있으면)
            plot_settings = getattr(self.main_app, 'current_plot_settings', {})
            
            # 왼쪽 Y축 플롯 (Plot Settings의 스타일 적용)
            if left_ymap:
                for name, series in left_ymap.items():
                    # Plot Settings의 스타일 적용
                    color = plot_settings.get('y_colors', {}).get(name, None)
                    line_width = plot_settings.get('y_line_widths', {}).get(name, 2)
                    line_style = plot_settings.get('y_line_styles', {}).get(name, '-')
                    marker = plot_settings.get('y_markers', {}).get(name, 'None')
                    marker_size = plot_settings.get('y_marker_sizes', {}).get(name, 6)
                    
                    # 플롯 그리기
                    if color:
                        self.main_app.ax.plot(x, series, label=f'{name} (L)', 
                                            color=color, linewidth=line_width, 
                                            linestyle=line_style, marker=marker if marker != 'None' else None,
                                            markersize=marker_size)
                    else:
                        self.main_app.ax.plot(x, series, label=f'{name} (L)', linewidth=line_width)
                
                # Y축 색상 사용 (축 눈금, 레이블만)
                self.main_app.ax.set_ylabel('Left Y-axis', color=self.left_axis_color.get(), fontsize=14)
                self.main_app.ax.tick_params(axis='y', labelcolor=self.left_axis_color.get())
                
                # 왼쪽 Y축 범위는 자동 설정 (autoscale)
                self.main_app.ax.autoscale(axis='y')
            
            # 오른쪽 Y축 생성 및 플롯 (Plot Settings의 스타일 적용)
            if right_ymap:
                ax2 = self.main_app.ax.twinx()
                for name, series in right_ymap.items():
                    # Plot Settings의 스타일 적용
                    color = plot_settings.get('y_colors', {}).get(name, None)
                    line_width = plot_settings.get('y_line_widths', {}).get(name, 2)
                    line_style = plot_settings.get('y_line_styles', {}).get(name, '--')
                    marker = plot_settings.get('y_markers', {}).get(name, 'None')
                    marker_size = plot_settings.get('y_marker_sizes', {}).get(name, 6)
                    
                    # 플롯 그리기
                    if color:
                        ax2.plot(x, series, label=f'{name} (R)', 
                                color=color, linewidth=line_width, 
                                linestyle=line_style, marker=marker if marker != 'None' else None,
                                markersize=marker_size)
                    else:
                        ax2.plot(x, series, label=f'{name} (R)', linewidth=line_width, linestyle='--')
                
                # Y축 색상 및 타이틀 사용
                ylabel_text = self.right_ylabel.get() if self.right_ylabel.get() else 'Right Y-axis'
                ax2.set_ylabel(ylabel_text, color=self.right_axis_color.get(), fontsize=14)
                ax2.tick_params(axis='y', labelcolor=self.right_axis_color.get())
                
                # 오른쪽 Y축 범위 설정 (독립적으로)
                ax2.set_ylim(self.right_ylim_min.get(), self.right_ylim_max.get())
                
                # 오른쪽 Y축 저장
                self.main_app.ax2 = ax2
            
            # X축 설정
            axis_type = self.main_app.axis_type_var.get()
            if axis_type == 'datetime':
                self.main_app.ax.set_xlabel(f'{x_col}', fontsize=16)
                import matplotlib.dates as mdates
                self.main_app.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                self.main_app.ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(x)//10)))
                import matplotlib.pyplot as plt
                plt.setp(self.main_app.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            else:
                self.main_app.ax.set_xlabel(x_col, fontsize=16)
            
            # 제목
            self.main_app.ax.set_title(f'{sheet} - Double Y-axis Plot', fontsize=14)
            
            # 범례
            if left_ymap or right_ymap:
                lines1, labels1 = self.main_app.ax.get_legend_handles_labels()
                if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None:
                    lines2, labels2 = self.main_app.ax2.get_legend_handles_labels()
                    self.main_app.ax.legend(lines1 + lines2, labels1 + labels2, loc='best')
                else:
                    self.main_app.ax.legend()
            
            self.main_app.ax.grid(True, alpha=0.3)
            self.main_app.figure.tight_layout()
            self.main_app.plot_canvas.draw()
            
            print("Double Y축 플롯 완료")
            
        except Exception as e:
            print(f"Double Y축 플롯 오류: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror('오류', f'Double Y축 플롯 생성 중 오류: {e}')
    
    def get_settings(self):
        """현재 Double Y축 설정 반환"""
        return {
            'use_double_y': self.use_double_y.get(),
            'left_y_columns': self.left_y_columns,
            'right_y_columns': self.right_y_columns,
            'left_axis_color': self.left_axis_color.get(),
            'right_axis_color': self.right_axis_color.get(),
            'right_ylabel': self.right_ylabel.get(),
            'right_ylim_min': self.right_ylim_min.get(),
            'right_ylim_max': self.right_ylim_max.get()
        }

