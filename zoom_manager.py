"""
줌 기능 관리 모듈
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from zoom_features import ZoomFeatures


class ZoomManager:
    """줌 기능 관리 클래스"""
    
    def __init__(self, main_app):
        """
        Args:
            main_app: 메인 애플리케이션 인스턴스
        """
        self.main_app = main_app
        self.root = main_app.root
        self.ax = main_app.ax
        self.plot_canvas = main_app.plot_canvas
        
        # 줌 관련 변수
        self.zoom_mode = tk.BooleanVar(value=False)
        self.zoom_active = False
        self.zoom_start_x = None
        self.zoom_start_y = None
        self.zoom_end_x = None
        self.zoom_end_y = None
        self.zoom_rectangle = None
        self.zoom_stack = []  # 줌 히스토리
        self.zoom_cids = []  # 이벤트 연결 ID
        
        # UI 요소
        self.zoom_button = None
        self.zoom_status_var = None
        self.zoom_status_label = None
        
        # 줌 확장 기능 초기화
        self.zoom_features = ZoomFeatures(main_app)
    
    def create_zoom_controls(self, parent_frame):
        """줌 컨트롤 UI 생성
        
        Args:
            parent_frame: 부모 프레임
            
        Returns:
            줌 컨트롤 프레임
        """
        zoom_frame = ttk.Frame(parent_frame)
        zoom_frame.pack(fill=tk.X, pady=5)  # 부모 프레임에 pack 추가!
        
        # 줌 모드 토글 버튼
        self.zoom_button = ttk.Button(
            zoom_frame, 
            text='🔍 줌 모드',
            command=self.toggle_zoom_mode
        )
        self.zoom_button.pack(side=tk.LEFT, padx=2)
        
        # 줌 아웃 버튼
        zoom_out_button = ttk.Button(
            zoom_frame,
            text='↶ 줌 아웃',
            command=self.zoom_out
        )
        zoom_out_button.pack(side=tk.LEFT, padx=2)
        
        # 줌 리셋 버튼
        reset_button = ttk.Button(
            zoom_frame,
            text='⟲ 줌 리셋',
            command=self.reset_zoom
        )
        reset_button.pack(side=tk.LEFT, padx=2)
        
        # 줌 상태 표시
        self.zoom_status_var = tk.StringVar(value='줌 모드: 비활성')
        self.zoom_status_label = ttk.Label(
            zoom_frame,
            textvariable=self.zoom_status_var,
            foreground='gray'
        )
        self.zoom_status_label.pack(side=tk.LEFT, padx=10)
        
        return zoom_frame
    
    def toggle_zoom_mode(self):
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
    
    def _disconnect_zoom_events(self):
        """줌 이벤트 연결 해제"""
        if hasattr(self, 'plot_canvas') and self.zoom_cids:
            for cid in self.zoom_cids:
                try:
                    self.plot_canvas.mpl_disconnect(cid)
                except:
                    pass
            self.zoom_cids = []

    def _on_zoom_press(self, event):
        """줌 드래그 시작"""
        ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
        if not self.zoom_mode.get() or event.inaxes not in [self.ax, ax2]:
            return
            
        self.zoom_active = True
        self.zoom_start_x = event.xdata
        self.zoom_start_y = event.ydata
        
        # 현재 축 범위를 줌 스택에 저장 (첫 번째 드래그일 때만)
        if not self.zoom_stack:
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()
            ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
            ax2_ylim = ax2.get_ylim() if ax2 else None
            self.zoom_stack.append((current_xlim, current_ylim, ax2_ylim))

    def _on_zoom_motion(self, event):
        """줌 드래그 중"""
        ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
        if not self.zoom_mode.get() or not self.zoom_active or event.inaxes not in [self.ax, ax2]:
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
            
            self.zoom_rectangle = event.inaxes.add_patch(
                plt.Rectangle((x, y), width, height, 
                            fill=False, edgecolor='red', linewidth=2, alpha=0.7)
            )
            self.plot_canvas.draw()

    def _on_zoom_release(self, event):
        """줌 드래그 종료"""
        ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
        if not self.zoom_mode.get() or not self.zoom_active or event.inaxes not in [self.ax, ax2]:
            return
            
        self.zoom_active = False
        
        if self.zoom_start_x is not None and self.zoom_end_x is not None:
            # 드래그된 영역으로 줌
            x_min = min(self.zoom_start_x, self.zoom_end_x)
            x_max = max(self.zoom_start_x, self.zoom_end_x)
            y_min = min(self.zoom_start_y, self.zoom_end_y)
            y_max = max(self.zoom_start_y, self.zoom_end_y)
            
            # 현재 축 범위 대비 최소 크기 체크 (1% 이상)
            # 드래그가 발생한 축(event.inaxes)을 기준으로 범위 계산
            current_xlim = event.inaxes.get_xlim()
            current_ylim = event.inaxes.get_ylim()
            
            x_range = current_xlim[1] - current_xlim[0]
            y_range = current_ylim[1] - current_ylim[0]
            
            min_x_size = abs(x_range) * 0.01  # 1%
            min_y_size = abs(y_range) * 0.01  # 1%
            
            if abs(x_max - x_min) > min_x_size and abs(y_max - y_min) > min_y_size:
                # 현재 범위를 스택에 저장
                ax2_ylim = ax2.get_ylim() if ax2 else None
                self.zoom_stack.append((current_xlim, current_ylim, ax2_ylim))
                
                # 줌 적용
                self.ax.set_xlim(x_min, x_max)
                if event.inaxes == self.ax:
                    self.ax.set_ylim(y_min, y_max)
                elif event.inaxes == ax2:
                    ax2.set_ylim(y_min, y_max)

                self.plot_canvas.draw()

                # 줌 적용 후 plot_settings에 범위 자동 반영
                self.zoom_features.sync_zoom_to_settings_silent()

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

    def reset_zoom(self):
        """줌 리셋"""
        if self.zoom_stack:
            # 원본 범위로 복원
            original_xlim, original_ylim, original_ax2_ylim = self.zoom_stack[0]
            self.ax.set_xlim(original_xlim)
            self.ax.set_ylim(original_ylim)

            ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
            if ax2 and original_ax2_ylim:
                ax2.set_ylim(original_ax2_ylim)

            self.plot_canvas.draw()

            # 줌 리셋 후 plot_settings에 범위 자동 반영
            self.zoom_features.sync_zoom_to_settings_silent()

            # 줌 스택 초기화
            self.zoom_stack = []
            print("줌 리셋 완료")
        else:
            print("리셋할 원본 범위가 없습니다.")
    
    def zoom_out(self):
        """줌 아웃 (이전 단계로)"""
        if len(self.zoom_stack) > 1:
            # 마지막 줌 단계 제거
            self.zoom_stack.pop()

            # 이전 범위로 복원
            prev_xlim, prev_ylim, prev_ax2_ylim = self.zoom_stack[-1]
            self.ax.set_xlim(prev_xlim)
            self.ax.set_ylim(prev_ylim)

            ax2 = self.main_app.ax2 if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None else None
            if ax2 and prev_ax2_ylim:
                ax2.set_ylim(prev_ax2_ylim)

            self.plot_canvas.draw()

            # 줌 아웃 후 plot_settings에 범위 자동 반영
            self.zoom_features.sync_zoom_to_settings_silent()

            print(f"줌 아웃: X({prev_xlim[0]:.3f}, {prev_xlim[1]:.3f}), Y({prev_ylim[0]:.3f}, {prev_ylim[1]:.3f})")
        else:
            print("줌 아웃할 단계가 없습니다.")

