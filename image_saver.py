"""
이미지 저장 모듈
Plot Image 폴더에 오늘날짜+타이틀로 이미지를 저장하는 기능을 제공합니다.
"""

import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
from PIL import Image


class ImageSaver:
    """이미지 저장을 담당하는 클래스"""
    
    def __init__(self, app_directory: str):
        """
        ImageSaver 초기화
        
        Args:
            app_directory: 앱이 실행되는 디렉토리 경로
        """
        self.app_directory = app_directory
        self.plot_image_dir = os.path.join(app_directory, "Plot Image")
        
        # Plot Image 폴더가 없으면 생성
        self._ensure_plot_image_directory()
    
    def _ensure_plot_image_directory(self) -> None:
        """Plot Image 폴더가 존재하는지 확인하고 없으면 생성"""
        try:
            if not os.path.exists(self.plot_image_dir):
                os.makedirs(self.plot_image_dir)
                print(f"Plot Image 폴더 생성: {self.plot_image_dir}")
        except Exception as e:
            print(f"폴더 생성 오류: {e}")
    
    def save_plot_image(self, figure: plt.Figure, title: str = "Plot") -> bool:
        """
        플롯 이미지를 저장하고 클립보드에 복사합니다.
        
        Args:
            figure: matplotlib Figure 객체
            title: 그래프 제목 (파일명에 사용)
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 현재 날짜와 시간 가져오기
            now = datetime.now()
            date_str = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S")
            
            # 파일명 생성 (제목에서 특수문자 제거)
            safe_title = self._sanitize_filename(title)
            filename = f"{date_str}_{time_str}_{safe_title}.png"
            
            # 전체 파일 경로
            filepath = os.path.join(self.plot_image_dir, filename)
            
            # 이미지 저장
            figure.savefig(filepath, dpi=300, bbox_inches='tight', 
                          facecolor='white', edgecolor='none')
            
            # 클립보드에 복사
            self._copy_to_clipboard(figure)
            
            print(f"이미지 저장 완료: {filepath}")
            print("클립보드에도 복사되었습니다.")
            return True
            
        except Exception as e:
            error_msg = f'이미지 저장 중 오류가 발생했습니다: {e}'
            print(error_msg)
            messagebox.showerror('저장 오류', error_msg)
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        파일명에서 특수문자를 제거하여 안전한 파일명으로 변환
        
        Args:
            filename: 원본 파일명
            
        Returns:
            str: 안전한 파일명
        """
        # Windows에서 사용할 수 없는 문자들
        invalid_chars = '<>:"/\\|?*'
        
        # 특수문자 제거
        safe_filename = filename
        for char in invalid_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # 연속된 언더스코어를 하나로 변경
        while '__' in safe_filename:
            safe_filename = safe_filename.replace('__', '_')
        
        # 앞뒤 언더스코어 제거
        safe_filename = safe_filename.strip('_')
        
        # 빈 문자열이면 기본값 사용
        if not safe_filename:
            safe_filename = "Plot"
        
        return safe_filename
    
    def _copy_to_clipboard(self, figure: plt.Figure) -> None:
        """
        matplotlib Figure를 클립보드에 복사
        
        Args:
            figure: matplotlib Figure 객체
        """
        try:
            # Figure를 메모리 버퍼에 PNG로 저장
            buffer = io.BytesIO()
            figure.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                          facecolor='white', edgecolor='none')
            buffer.seek(0)
            
            # PIL Image로 변환
            image = Image.open(buffer)
            
            # 클립보드에 복사
            self._copy_image_to_clipboard(image)
            
            buffer.close()
            print("이미지가 클립보드에 복사되었습니다.")
            
        except Exception as e:
            print(f"클립보드 복사 오류: {e}")
            # 클립보드 복사 실패해도 저장은 계속 진행
    
    def _copy_image_to_clipboard(self, image: Image.Image) -> None:
        """
        PIL Image를 클립보드에 복사 (Windows 전용)
        
        Args:
            image: PIL Image 객체
        """
        try:
            import win32clipboard
            import win32con
            
            # 이미지를 클립보드 형식으로 변환
            output = io.BytesIO()
            image.save(output, 'BMP')
            data = output.getvalue()[14:]  # BMP 헤더 제거
            output.close()
            
            # 클립보드에 복사
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
        except ImportError:
            # win32clipboard가 없는 경우 대체 방법 시도
            try:
                # tkinter 클립보드 사용
                root = tk.Tk()
                root.withdraw()  # 창 숨기기
                
                # 이미지를 임시 파일로 저장
                temp_path = os.path.join(self.plot_image_dir, "temp_clipboard.png")
                image.save(temp_path)
                
                # 파일 경로를 클립보드에 복사 (이미지가 아닌 경로)
                root.clipboard_clear()
                root.clipboard_append(temp_path)
                root.destroy()
                
                print("이미지 경로가 클립보드에 복사되었습니다.")
                
            except Exception as e2:
                print(f"대체 클립보드 복사도 실패: {e2}")
        except Exception as e:
            print(f"클립보드 복사 실패: {e}")
    
    def get_save_directory(self) -> str:
        """
        저장 디렉토리 경로를 반환
        
        Returns:
            str: Plot Image 폴더의 절대 경로
        """
        return self.plot_image_dir
    


def create_image_saver(app_directory: str) -> ImageSaver:
    """
    ImageSaver 인스턴스를 생성하는 팩토리 함수
    
    Args:
        app_directory: 앱이 실행되는 디렉토리 경로
        
    Returns:
        ImageSaver: 이미지 저장 인스턴스
    """
    return ImageSaver(app_directory)
