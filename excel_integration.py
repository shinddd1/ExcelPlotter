"""
Excel 통합 모듈
xlwings를 사용한 Excel 연결 및 데이터 처리
"""

import pandas as pd
import xlwings as xw
from typing import Optional, Callable
import threading
import time


class ExcelIntegration:
    """Excel 통합 클래스"""
    
    def __init__(self):
        self.app = None
        self.workbook = None
        self.worksheet = None
        self.is_connected = False
        self.monitoring_thread = None
        self.monitoring_active = False
        self.monitoring_callback = None
        
    def connect_to_excel(self, file_path: Optional[str] = None) -> bool:
        """Excel에 연결"""
        try:
            # Excel 앱 연결
            self.app = xw.App(visible=True)
            
            if file_path:
                # 기존 파일 열기
                self.workbook = self.app.books.open(file_path)
            else:
                # 새 파일 생성
                self.workbook = self.app.books.add()
            
            self.worksheet = self.workbook.sheets.active
            self.is_connected = True
            
            return True
            
        except Exception as e:
            print(f"Excel 연결 실패: {e}")
            if self.app:
                try:
                    self.app.quit()
                except:
                    pass
            self.app = None
            self.workbook = None
            self.worksheet = None
            self.is_connected = False
            return False
    
    def load_data_from_excel(self) -> Optional[pd.DataFrame]:
        """Excel에서 데이터 로드"""
        if not self.is_connected or not self.worksheet:
            return None
            
        try:
            # 사용된 범위 가져오기 (더 안전한 방법)
            try:
                used_range = self.worksheet.used_range
                if not used_range:
                    return pd.DataFrame()
            except:
                # used_range가 실패하면 A1부터 시작해서 데이터 찾기
                return self._load_data_safely()
            
            # 데이터를 pandas DataFrame으로 변환
            data = used_range.value
            
            if isinstance(data, list):
                if data and isinstance(data[0], list):
                    # 2차원 배열인 경우
                    df = pd.DataFrame(data[1:], columns=data[0])
                else:
                    # 1차원 배열인 경우
                    df = pd.DataFrame(data)
            else:
                # 단일 값인 경우
                df = pd.DataFrame([[data]])
            
            # 열 이름 정리
            df.columns = [str(col) if col is not None else f"Column_{i}" for i, col in enumerate(df.columns)]
            
            return df
            
        except Exception as e:
            print(f"Excel 데이터 로드 실패: {e}")
            # 안전한 방법으로 다시 시도
            return self._load_data_safely()
    
    def _load_data_safely(self) -> Optional[pd.DataFrame]:
        """안전한 방법으로 Excel 데이터 로드"""
        try:
            print("안전한 방법으로 Excel 데이터 로드 시작")
            # A1부터 시작해서 데이터가 있는 범위 찾기
            max_row = 1000  # 최대 행 수
            max_col = 50    # 최대 열 수
            
            data_rows = []
            headers = []
            
            # 헤더 읽기 (첫 번째 행)
            print("헤더 읽기 시작")
            for col in range(max_col):
                try:
                    col_letter = chr(ord('A') + col)
                    cell_value = self.worksheet.range(f"{col_letter}1").value
                    print(f"셀 {col_letter}1 값: {cell_value}")
                    if cell_value is not None and str(cell_value).strip():
                        headers.append(str(cell_value).strip())
                        print(f"헤더 추가: {str(cell_value).strip()}")
                    else:
                        print(f"빈 셀 발견, 헤더 읽기 중단")
                        break
                except Exception as e:
                    print(f"헤더 읽기 오류 (열 {col}): {e}")
                    break
            
            print(f"읽은 헤더: {headers}")
            if not headers:
                print("헤더가 없음")
                return pd.DataFrame()
            
            # 데이터 행 읽기
            print("데이터 행 읽기 시작")
            for row in range(2, max_row + 1):
                row_data = []
                has_data = False
                
                for col in range(len(headers)):
                    try:
                        col_letter = chr(ord('A') + col)
                        cell_value = self.worksheet.range(f"{col_letter}{row}").value
                        row_data.append(cell_value)
                        if cell_value is not None and str(cell_value).strip():
                            has_data = True
                    except Exception as e:
                        print(f"데이터 읽기 오류 (행 {row}, 열 {col}): {e}")
                        row_data.append(None)
                
                if has_data:
                    data_rows.append(row_data)
                    if len(data_rows) <= 5:  # 처음 5행만 로그 출력
                        print(f"행 {row} 데이터: {row_data}")
                else:
                    print(f"행 {row}에 데이터 없음, 읽기 중단")
                    break
            
            print(f"읽은 데이터 행 수: {len(data_rows)}")
            if not data_rows:
                print("데이터 행이 없음")
                return pd.DataFrame()
            
            # DataFrame 생성
            df = pd.DataFrame(data_rows, columns=headers)
            print(f"생성된 DataFrame: {len(df)}행 x {len(df.columns)}열")
            print(f"컬럼 이름: {list(df.columns)}")
            return df
            
        except Exception as e:
            print(f"안전한 데이터 로드도 실패: {e}")
            return None
    
    def save_data_to_excel(self, df: pd.DataFrame, start_cell: str = "A1"):
        """데이터를 Excel에 저장"""
        if not self.is_connected or not self.worksheet:
            return False
            
        try:
            # 헤더 저장
            self.worksheet.range(start_cell).value = df.columns.tolist()
            
            # 데이터 저장
            data_start_cell = f"{start_cell[0]}{int(start_cell[1:]) + 1}"
            self.worksheet.range(data_start_cell).value = df.values.tolist()
            
            return True
            
        except Exception as e:
            print(f"Excel 데이터 저장 실패: {e}")
            return False
    
    def start_monitoring(self, callback: Callable[[pd.DataFrame], None], interval_ms: int = 1000):
        """Excel 변경 모니터링 시작"""
        if not self.is_connected:
            return False
            
        self.monitoring_callback = callback
        self.monitoring_active = True
        
        def monitor():
            last_data = None
            while self.monitoring_active:
                try:
                    current_data = self.load_data_from_excel()
                    if current_data is not None and not current_data.equals(last_data):
                        if self.monitoring_callback:
                            self.monitoring_callback(current_data)
                        last_data = current_data
                except Exception as e:
                    print(f"모니터링 오류: {e}")
                
                time.sleep(interval_ms / 1000.0)
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        self.monitoring_thread = None
        self.monitoring_callback = None
    
    def disconnect(self):
        """Excel 연결 해제"""
        try:
            # 모니터링 중지
            self.stop_monitoring()
            
            # 워크북 저장
            if self.workbook:
                self.workbook.save()
            
            # Excel 앱 종료
            if self.app:
                self.app.quit()
                
        except Exception as e:
            print(f"Excel 연결 해제 오류: {e}")
        finally:
            self.app = None
            self.workbook = None
            self.worksheet = None
            self.is_connected = False
    
    def get_status(self) -> dict:
        """연결 상태 반환"""
        return {
            'is_connected': self.is_connected,
            'workbook_name': self.workbook.name if self.workbook else None,
            'worksheet_name': self.worksheet.name if self.worksheet else None,
            'is_monitoring': self.monitoring_active
        }
