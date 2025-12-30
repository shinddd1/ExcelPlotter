import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np

class ZoomFeatures:
    """줌 관련 확장 기능 관리 클래스"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        
    def save_zoomed_data(self):
        """현재 줌된 구간의 데이터를 엑셀로 저장"""
        try:
            # 현재 X축 범위 가져오기
            x_min, x_max = self.main_app.ax.get_xlim()
            
            # 현재 선택된 시트와 데이터 확인
            sheet = self.main_app.sheet_combo.get()
            if not sheet or sheet not in self.main_app.df_map:
                messagebox.showwarning('경고', '데이터가 없습니다.')
                return
                
            df = self.main_app.df_map[sheet]
            x_col = self.main_app.x_combo.get()
            
            if x_col not in df.columns:
                messagebox.showwarning('경고', 'X축 컬럼을 찾을 수 없습니다.')
                return
                
            # 데이터 필터링
            # X축 데이터 타입에 따라 처리 (숫자 vs 시간)
            try:
                # 시간축인 경우
                if self.main_app.axis_type_var.get() == 'datetime':
                    # matplotlib 날짜 숫자를 datetime으로 변환
                    import matplotlib.dates as mdates
                    x_min_date = mdates.num2date(x_min).replace(tzinfo=None)
                    x_max_date = mdates.num2date(x_max).replace(tzinfo=None)
                    
                    # 데이터프레임의 X컬럼도 datetime으로 변환하여 비교
                    x_data = pd.to_datetime(df[x_col], errors='coerce')
                    mask = (x_data >= x_min_date) & (x_data <= x_max_date)
                else:
                    # 숫자축인 경우
                    x_data = pd.to_numeric(df[x_col], errors='coerce')
                    mask = (x_data >= x_min) & (x_data <= x_max)
                    
                filtered_df = df[mask].copy()
                
                if filtered_df.empty:
                    messagebox.showwarning('경고', '선택된 구간에 데이터가 없습니다.')
                    return
                    
                # 파일 저장 대화상자
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    title="줌 구간 데이터 저장"
                )
                
                if file_path:
                    filtered_df.to_excel(file_path, index=False)
                    messagebox.showinfo('성공', f'데이터가 저장되었습니다.\n행 수: {len(filtered_df)}')
                    
            except Exception as e:
                messagebox.showerror('오류', f'데이터 필터링 중 오류: {e}')
                
        except Exception as e:
            messagebox.showerror('오류', f'데이터 저장 중 오류: {e}')

    def sync_zoom_to_settings(self):
        """현재 줌된 범위를 설정에 반영 (메시지 표시)"""
        success = self.sync_zoom_to_settings_silent()
        if success:
            messagebox.showinfo('성공', '현재 화면의 범위가 설정에 저장되었습니다.\n설정 창을 열면 반영됩니다.')

    def sync_zoom_to_settings_silent(self):
        """현재 줌된 범위를 설정에 반영 (메시지 없음)"""
        try:
            # 현재 축 범위 가져오기
            x_min, x_max = self.main_app.ax.get_xlim()
            y_min, y_max = self.main_app.ax.get_ylim()

            # 시간축인 경우 변환
            if self.main_app.axis_type_var.get() == 'datetime':
                import matplotlib.dates as mdates
                x_min = mdates.num2date(x_min).replace(tzinfo=None)
                x_max = mdates.num2date(x_max).replace(tzinfo=None)

            # 설정 키 생성
            current_sheet = self.main_app.sheet_combo.get()
            x_col = self.main_app.x_combo.get()
            range_key = f"{current_sheet}_{x_col}"

            # X축 설정 저장
            self.main_app._saved_x_range[range_key] = {
                'min': x_min,
                'max': x_max
            }

            # Y축 설정 저장 (왼쪽 축)
            self.main_app._saved_y_range[range_key] = {
                'min': y_min,
                'max': y_max
            }

            # Double Y축이 활성화된 경우 오른쪽 축도 저장
            if hasattr(self.main_app, 'ax2') and self.main_app.ax2 is not None:
                y2_min, y2_max = self.main_app.ax2.get_ylim()

                # Double Y 설정 가져오기 또는 생성
                if range_key not in self.main_app._saved_double_y_settings:
                    self.main_app._saved_double_y_settings[range_key] = {}

                # 범위 업데이트
                self.main_app._saved_double_y_settings[range_key].update({
                    'left_ylim_min': y_min,
                    'left_ylim_max': y_max,
                    'right_ylim_min': y2_min,
                    'right_ylim_max': y2_max
                })

            print(f"줌 범위가 설정에 반영됨: X({x_min}, {x_max}), Y({y_min}, {y_max})")
            return True

        except Exception as e:
            print(f'설정 동기화 중 오류: {e}')
            return False
