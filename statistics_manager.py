import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

class StatisticsManager:
    """통계 기능 관리 클래스"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        # self.ax = main_app.ax  # 동적 참조를 위해 제거
        self.plot_canvas = main_app.plot_canvas
        
        # 상태 변수
        self.stats_mode = tk.BooleanVar(value=False)
        self.selection_active = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selection_rectangle = None
        self.cids = []
        
        # UI 요소
        self.stats_button = None
        self.status_label = None
        
    def create_ui(self, parent_frame):
        """통계 컨트롤 UI 생성"""
        stats_frame = ttk.LabelFrame(parent_frame, text='통계 분석', padding=8)
        stats_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 통계 모드 토글 버튼
        self.stats_button = ttk.Button(
            stats_frame,
            text='📊 통계 모드',
            command=self.toggle_mode
        )
        self.stats_button.pack(side=tk.LEFT, padx=2)
        
        # 상태 표시
        self.status_label = ttk.Label(
            stats_frame,
            text='비활성',
            foreground='gray'
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        return stats_frame

    def toggle_mode(self):
        """통계 모드 토글"""
        # 줌 모드가 켜져있다면 끄기
        if hasattr(self.main_app, 'zoom_manager') and self.main_app.zoom_manager.zoom_mode.get():
            self.main_app.zoom_manager.toggle_zoom_mode()
            
        self.stats_mode.set(not self.stats_mode.get())
        
        if self.stats_mode.get():
            self.status_label.config(text='영역을 드래그하세요', foreground='blue')
            self.stats_button.config(text='📊 통계 모드 (활성)')
            self._connect_events()
        else:
            self.status_label.config(text='비활성', foreground='gray')
            self.stats_button.config(text='📊 통계 모드')
            self._disconnect_events()
            self._clear_selection()

    def _connect_events(self):
        """이벤트 연결"""
        self._disconnect_events()
        cid1 = self.plot_canvas.mpl_connect('button_press_event', self._on_press)
        cid2 = self.plot_canvas.mpl_connect('motion_notify_event', self._on_motion)
        cid3 = self.plot_canvas.mpl_connect('button_release_event', self._on_release)
        self.cids = [cid1, cid2, cid3]
        print(f"Stats Events Connected: {self.cids}")
        self.plot_canvas.draw_idle()

    def _disconnect_events(self):
        """이벤트 해제"""
        for cid in self.cids:
            try:
                self.plot_canvas.mpl_disconnect(cid)
            except:
                pass
        self.cids = []

    def _on_press(self, event):
        """드래그 시작"""
        print(f"Stats Press: {event.xdata}, {event.ydata}, inaxes={event.inaxes}")
        
        # 좌클릭만 허용
        if event.button != 1:
            return

        ax = self.main_app.ax
        ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
        
        if not self.stats_mode.get():
            print("Stats Mode is OFF")
            return
            
        if event.inaxes not in [ax, ax2] or event.inaxes is None:
            print("Stats: Click outside axes")
            return
            
        self.selection_active = True
        self.start_x = event.xdata
        self.start_y = event.ydata
        self._clear_selection()

    def _on_motion(self, event):
        """드래그 중"""
        ax = self.main_app.ax
        ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
        
        if not self.selection_active:
            return
            
        if event.inaxes not in [ax, ax2]:
            return
            
        self.end_x = event.xdata
        self.end_y = event.ydata
        self._draw_rectangle(event.inaxes)

    def _on_release(self, event):
        """드래그 종료 및 계산"""
        if not self.selection_active:
            return
            
        self.selection_active = False
        self.end_x = event.xdata
        self.end_y = event.ydata
        
        if self.start_x is None or self.end_x is None:
            return
            
        # 최소 크기 체크
        ax = self.main_app.ax
        if abs(self.end_x - self.start_x) < (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.01:
            return
            
        # 통계 계산 및 팝업 표시
        x_min = min(self.start_x, self.end_x)
        x_max = max(self.start_x, self.end_x)
        self.calculate_and_show_stats(x_min, x_max)
        
        # 선택 영역 유지 (사용자가 확인 후 닫거나 모드 끌 때까지)

    def _draw_rectangle(self, ax=None):
        """선택 영역 그리기"""
        if self.selection_rectangle:
            self.selection_rectangle.remove()
            
        if ax is None:
            ax = self.main_app.ax
            
        width = abs(self.end_x - self.start_x)
        height = abs(self.end_y - self.start_y)
        x = min(self.start_x, self.end_x)
        y = min(self.start_y, self.end_y)
        
        self.selection_rectangle = ax.add_patch(
            plt.Rectangle((x, y), width, height, fill=True, facecolor='green', alpha=0.2, edgecolor='green')
        )
        self.plot_canvas.draw()

    def _clear_selection(self):
        """선택 영역 지우기"""
        if self.selection_rectangle:
            self.selection_rectangle.remove()
            self.selection_rectangle = None
            self.plot_canvas.draw()

    def calculate_and_show_stats(self, x_min, x_max):
        """통계 계산 및 결과창 표시"""
        try:
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                return
                
            df = self.main_app.df_map[sheet]
            x_col = self.main_app.x_combo.get()
            
            # X축 데이터 필터링
            if self.main_app.axis_type_var.get() == 'datetime':
                import matplotlib.dates as mdates
                x_min_date = mdates.num2date(x_min).replace(tzinfo=None)
                x_max_date = mdates.num2date(x_max).replace(tzinfo=None)
                x_data = pd.to_datetime(df[x_col], errors='coerce')
                mask = (x_data >= x_min_date) & (x_data <= x_max_date)
            else:
                x_data = pd.to_numeric(df[x_col], errors='coerce')
                mask = (x_data >= x_min) & (x_data <= x_max)
                
            filtered_df = df[mask]
            
            if filtered_df.empty:
                messagebox.showinfo('알림', '선택된 영역에 데이터가 없습니다.')
                return

            # 결과창 생성
            popup = tk.Toplevel(self.main_app.root)
            popup.title(f"통계 분석 ({x_min:.2f} ~ {x_max:.2f})")
            popup.geometry("500x600")
            
            # 메인 프레임
            main_frame = ttk.Frame(popup)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 스크롤바
            scrollbar = ttk.Scrollbar(main_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 텍스트 위젯 (고정폭 글꼴 사용)
            text_widget = tk.Text(main_frame, wrap=tk.NONE, yscrollcommand=scrollbar.set, font=("Consolas", 10))
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=text_widget.yview)
            
            # 선택된 Y 컬럼들에 대해 통계 계산
            y_cols = []
            current_settings = getattr(self.main_app, 'current_plot_settings', {})
            
            if current_settings:
                if current_settings.get('use_double_y', False):
                    y_cols.extend(current_settings.get('left_y_columns', []))
                    y_cols.extend(current_settings.get('right_y_columns', []))
                else:
                    y_cols.extend(current_settings.get('y_columns', []))
            
            if not y_cols:
                y_indices = self.main_app.y_listbox.curselection()
                y_cols = [self.main_app.y_listbox.get(i) for i in y_indices]
            
            y_cols = list(set(y_cols))
            
            # 보고서 텍스트 구성
            report_text = []
            report_text.append(f"통계 분석 보고서")
            report_text.append(f"분석 범위: {x_min:.4f} ~ {x_max:.4f}")
            report_text.append("-" * 50)
            report_text.append("")

            for col in y_cols:
                if col not in filtered_df.columns:
                    continue
                    
                y_data = pd.to_numeric(filtered_df[col], errors='coerce').dropna()
                if y_data.empty:
                    continue
                
                # 기본 통계량 계산
                v_min = y_data.min()
                v_max = y_data.max()
                v_mean = y_data.mean()
                v_median = y_data.median()
                v_std = y_data.std()
                v_p2p = v_max - v_min
                v_rms = np.sqrt(np.mean(y_data**2))
                
                # 가우스 신뢰구간 (95%)
                ci_low = v_mean - 1.96 * v_std
                ci_high = v_mean + 1.96 * v_std

                # Local Max (Peaks)
                peaks, _ = find_peaks(y_data)
                local_maxs = y_data.iloc[peaks].values if len(peaks) > 0 else []
                max_coords = ", ".join([f"{v:.4f}" for v in sorted(local_maxs, reverse=True)[:5]])
                
                # 텍스트 형식으로 데이터 구성
                report_text.append(f"[{col}]")
                report_text.append(f"  평균 (Mean)       : {v_mean:.4f}")
                report_text.append(f"  중간값 (Median)    : {v_median:.4f}")
                report_text.append(f"  표준편차 (Std Dev) : {v_std:.4f}")
                report_text.append(f"  신뢰구간 (95% CI)  : [{ci_low:.4f} ~ {ci_high:.4f}]")
                report_text.append(f"  최소 (Min)         : {v_min:.4f}")
                report_text.append(f"  최대 (Max)         : {v_max:.4f}")
                report_text.append(f"  Peak-to-Peak      : {v_p2p:.4f}")
                report_text.append(f"  RMS               : {v_rms:.4f}")
                if local_maxs:
                    report_text.append(f"  Local Max (Top 5) : {len(local_maxs)}개 ({max_coords})")
                else:
                    report_text.append(f"  Local Max (Top 5) : 0개")
                report_text.append("")
                report_text.append("-" * 40)
                report_text.append("")

            # 텍스트 위젯에 내용 삽입
            text_widget.insert(tk.END, "\n".join(report_text))
            
            # 읽기 전용으로 설정
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror('오류', f'통계 계산 중 오류: {e}')
            import traceback
            traceback.print_exc()
        finally:
            # 통계 모드 자동 종료
            self.toggle_mode()
