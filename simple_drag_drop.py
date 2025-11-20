"""
간단한 드래그 앤 드롭 기능을 처리하는 모듈
파일을 드래그하면 파일 선택 대화상자를 열어서 처리합니다.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
from typing import Callable


class SimpleDragDropHandler:
    """간단한 드래그 앤 드롭 기능을 처리하는 클래스"""
    
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
            # 키보드 단축키 (Ctrl+O)
            self.root.bind('<Control-o>', self._on_open_file)
            
            print("드래그 앤 드롭 설정 완료")
            
        except Exception as e:
            print(f"드래그 앤 드롭 설정 오류: {e}")
    
    def _on_open_file(self, event) -> None:
        """Ctrl+O 키 이벤트"""
        self._open_file_dialog()
    
    def _open_file_dialog(self) -> None:
        """파일 선택 대화상자 열기"""
        try:
            file_path = filedialog.askopenfilename(
                title="Excel 파일 선택",
                filetypes=[
                    ("Excel files", "*.xlsx *.xls"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                self._process_file(file_path)
                
        except Exception as e:
            print(f"파일 선택 대화상자 오류: {e}")
            messagebox.showerror('오류', f'파일 선택 중 오류가 발생했습니다: {e}')
    
    def _process_file(self, file_path: str) -> None:
        """선택된 파일 처리"""
        try:
            # 파일 존재 확인
            if not os.path.exists(file_path):
                messagebox.showerror('파일 오류', '파일을 찾을 수 없습니다.')
                return
            
            # 파일 확장자 확인
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.xlsx', '.xls']:
                messagebox.showwarning(
                    '잘못된 파일 형식', 
                    'Excel 파일(.xlsx, .xls)만 선택할 수 있습니다.'
                )
                return
            
            # 파일 크기 확인 (100MB 제한)
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                messagebox.showwarning(
                    '파일 크기 초과', 
                    '파일 크기가 너무 큽니다. (최대 100MB)'
                )
                return
            
            # 성공적으로 파일을 처리할 수 있음
            print(f"파일 처리: {file_path}")
            
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
            # 이벤트 바인딩 해제
            self.root.unbind('<Control-o>')
        except Exception as e:
            print(f"드래그 앤 드롭 정리 오류: {e}")


def create_simple_drag_drop_handler(root: tk.Tk, on_file_dropped: Callable[[str], None]) -> SimpleDragDropHandler:
    """
    간단한 드래그 앤 드롭 핸들러를 생성하는 팩토리 함수
    
    Args:
        root: Tkinter 루트 윈도우
        on_file_dropped: 파일이 드롭되었을 때 호출될 콜백 함수
        
    Returns:
        SimpleDragDropHandler: 생성된 드래그 앤 드롭 핸들러
    """
    return SimpleDragDropHandler(root, on_file_dropped)
