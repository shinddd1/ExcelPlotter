"""
드래그 앤 드롭 기능을 처리하는 모듈
엑셀 파일을 프로그램 내로 드래그하여 자동으로 로드하는 기능을 제공합니다.
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys
from typing import Callable, Optional
import pandas as pd


class DragDropHandler:
    """드래그 앤 드롭 기능을 처리하는 클래스"""
    
    def __init__(self, root: tk.Tk, on_file_dropped: Callable[[str], None]) -> None:
        """
        드래그 앤 드롭 핸들러 초기화
        
        Args:
            root: Tkinter 루트 윈도우
            on_file_dropped: 파일이 드롭되었을 때 호출될 콜백 함수
        """
        self.root = root
        self.on_file_dropped = on_file_dropped
        self._setup_drag_drop()
    
    def _setup_drag_drop(self) -> None:
        """드래그 앤 드롭 이벤트 바인딩 설정"""
        try:
            # Windows에서 드래그 앤 드롭 지원
            if sys.platform == "win32":
                self._setup_windows_drag_drop()
            else:
                # 다른 플랫폼에서는 기본 Tkinter 드래그 앤 드롭 사용
                self._setup_tkinter_drag_drop()
        except Exception as e:
            print(f"드래그 앤 드롭 설정 오류: {e}")
            # 드래그 앤 드롭이 실패해도 프로그램은 계속 실행
    
    def _setup_windows_drag_drop(self) -> None:
        """Windows 전용 드래그 앤 드롭 설정"""
        try:
            import win32gui
            import win32con
            
            # 윈도우 핸들 가져오기
            hwnd = self.root.winfo_id()
            
            # 드래그 앤 드롭 메시지 등록
            win32gui.DragAcceptFiles(hwnd, True)
            
            # 윈도우 프로시저 오버라이드
            self._original_wndproc = win32gui.SetWindowLong(
                hwnd, 
                win32con.GWL_WNDPROC, 
                self._wndproc
            )
            
            print("Windows 드래그 앤 드롭 설정 완료")
            
        except ImportError:
            print("win32gui가 설치되지 않음. 기본 드래그 앤 드롭을 사용합니다.")
            self._setup_tkinter_drag_drop()
        except Exception as e:
            print(f"Windows 드래그 앤 드롭 설정 오류: {e}")
            self._setup_tkinter_drag_drop()
    
    def _setup_tkinter_drag_drop(self) -> None:
        """Tkinter 기본 드래그 앤 드롭 설정"""
        # 모든 위젯에 드래그 앤 드롭 이벤트 바인딩
        self._bind_drag_drop_to_widget(self.root)
        
        # 마우스 이벤트 바인딩
        self.root.bind('<Button-1>', self._on_click)
        self.root.bind('<B1-Motion>', self._on_drag)
        self.root.bind('<ButtonRelease-1>', self._on_release)
        
        # 파일 드롭 이벤트
        self.root.bind('<Drop>', self._on_drop)
        self.root.bind('<Enter>', self._on_enter)
        self.root.bind('<Leave>', self._on_leave)
        
        print("Tkinter 드래그 앤 드롭 설정 완료")
    
    def _bind_drag_drop_to_widget(self, widget) -> None:
        """위젯에 드래그 앤 드롭 이벤트 바인딩"""
        try:
            # 드래그 앤 드롭 이벤트 바인딩
            widget.bind('<Button-1>', self._on_click)
            widget.bind('<B1-Motion>', self._on_drag)
            widget.bind('<ButtonRelease-1>', self._on_release)
            widget.bind('<Drop>', self._on_drop)
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)
            
            # 모든 자식 위젯에도 재귀적으로 바인딩
            for child in widget.winfo_children():
                self._bind_drag_drop_to_widget(child)
                
        except Exception as e:
            print(f"위젯 드래그 앤 드롭 바인딩 오류: {e}")
    
    def _wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Windows 윈도우 프로시저"""
        try:
            import win32gui
            import win32con
            
            if msg == win32con.WM_DROPFILES:
                # 파일이 드롭됨
                self._handle_windows_drop(wparam)
                return 0
            else:
                # 다른 메시지는 원래 프로시저로 전달
                return win32gui.CallWindowProc(self._original_wndproc, hwnd, msg, wparam, lparam)
        except Exception as e:
            print(f"윈도우 프로시저 오류: {e}")
            return 0
    
    def _handle_windows_drop(self, wparam: int) -> None:
        """Windows에서 파일 드롭 처리"""
        try:
            import win32gui
            import win32api
            
            # 드롭된 파일 경로 가져오기
            file_count = win32gui.DragQueryFile(wparam, 0xFFFFFFFF, None, 0)
            
            if file_count > 0:
                # 첫 번째 파일만 처리 (여러 파일 드롭 시)
                file_path = win32gui.DragQueryFile(wparam, 0, None, 0)
                file_path = file_path.replace('\\', '/')  # 경로 구분자 통일
                
                # 파일 확장자 확인
                if self._is_excel_file(file_path):
                    self._process_dropped_file(file_path)
                else:
                    messagebox.showwarning(
                        '잘못된 파일 형식', 
                        'Excel 파일(.xlsx, .xls)만 드래그할 수 있습니다.'
                    )
            
            # 드롭 핸들 해제
            win32gui.DragFinish(wparam)
            
        except Exception as e:
            print(f"Windows 드롭 처리 오류: {e}")
            messagebox.showerror('드롭 오류', f'파일 드롭 처리 중 오류가 발생했습니다: {e}')
    
    def _on_click(self, event) -> None:
        """마우스 클릭 이벤트"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def _on_drag(self, event) -> None:
        """드래그 이벤트"""
        # 드래그 거리 계산
        if hasattr(self, 'drag_start_x'):
            dx = abs(event.x - self.drag_start_x)
            dy = abs(event.y - self.drag_start_y)
            
            # 최소 드래그 거리 확인
            if dx > 5 or dy > 5:
                self.is_dragging = True
    
    def _on_release(self, event) -> None:
        """마우스 릴리즈 이벤트"""
        if hasattr(self, 'is_dragging') and self.is_dragging:
            # 드래그가 끝났을 때의 처리
            pass
        self.is_dragging = False
    
    def _on_drop(self, event) -> None:
        """파일 드롭 이벤트 (Tkinter)"""
        try:
            # Tkinter의 드롭 이벤트에서 파일 경로 추출
            if hasattr(event, 'data'):
                file_path = event.data.strip()
                if self._is_excel_file(file_path):
                    self._process_dropped_file(file_path)
        except Exception as e:
            print(f"Tkinter 드롭 처리 오류: {e}")
    
    def _on_enter(self, event) -> None:
        """마우스 진입 이벤트"""
        # 드래그 앤 드롭 영역 진입 시 시각적 피드백
        self.root.configure(cursor='hand2')
    
    def _on_leave(self, event) -> None:
        """마우스 이탈 이벤트"""
        # 드래그 앤 드롭 영역 이탈 시 커서 복원
        self.root.configure(cursor='')
    
    def _is_excel_file(self, file_path: str) -> bool:
        """파일이 Excel 파일인지 확인"""
        if not file_path or not os.path.exists(file_path):
            return False
        
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path.lower())
        return ext in ['.xlsx', '.xls']
    
    def _process_dropped_file(self, file_path: str) -> None:
        """드롭된 파일 처리"""
        try:
            # 파일 존재 확인
            if not os.path.exists(file_path):
                messagebox.showerror('파일 오류', '파일을 찾을 수 없습니다.')
                return
            
            # 파일 크기 확인 (100MB 제한)
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                messagebox.showwarning(
                    '파일 크기 초과', 
                    '파일 크기가 너무 큽니다. (최대 100MB)'
                )
                return
            
            # 파일 읽기 가능 여부 확인
            try:
                # 파일이 Excel 파일인지 빠른 확인
                pd.read_excel(file_path, nrows=1)
            except Exception as e:
                messagebox.showerror(
                    '파일 읽기 오류', 
                    f'Excel 파일을 읽을 수 없습니다:\n{str(e)}'
                )
                return
            
            # 성공적으로 파일을 처리할 수 있음
            print(f"드롭된 파일 처리: {file_path}")
            
            # 메인 앱에 파일 경로 전달
            self.on_file_dropped(file_path)
            
            # 성공 메시지
            filename = os.path.basename(file_path)
            messagebox.showinfo(
                '파일 로드 성공', 
                f'Excel 파일이 성공적으로 로드되었습니다:\n{filename}'
            )
            
        except Exception as e:
            print(f"파일 처리 오류: {e}")
            messagebox.showerror(
                '파일 처리 오류', 
                f'파일 처리 중 오류가 발생했습니다:\n{str(e)}'
            )
    
    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            if hasattr(self, '_original_wndproc') and sys.platform == "win32":
                import win32gui
                import win32con
                win32gui.SetWindowLong(
                    self.root.winfo_id(), 
                    win32con.GWL_WNDPROC, 
                    self._original_wndproc
                )
        except Exception as e:
            print(f"드래그 앤 드롭 정리 오류: {e}")


def create_drag_drop_handler(root: tk.Tk, on_file_dropped: Callable[[str], None]) -> DragDropHandler:
    """
    드래그 앤 드롭 핸들러를 생성하는 팩토리 함수
    
    Args:
        root: Tkinter 루트 윈도우
        on_file_dropped: 파일이 드롭되었을 때 호출될 콜백 함수
        
    Returns:
        DragDropHandler: 생성된 드래그 앤 드롭 핸들러
    """
    return DragDropHandler(root, on_file_dropped)
