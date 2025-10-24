#!/usr/bin/env python3
"""
Excel Plotter (SciencePlots) - 메인 실행 파일

엑셀 데이터를 로드하고 SciencePlots 스타일로 시각화하는 애플리케이션
"""

import tkinter as tk
from main_app import ExcelPlotterApp

def main():
    """메인 함수 - 기존 버전"""
    root = tk.Tk()
    app = ExcelPlotterApp(root)
    root.mainloop()


if __name__ == '__main__':
    print("기존 버전으로 실행합니다...")
    main()