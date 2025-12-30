import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class ThemeManager:
    """테마 관리 클래스"""
    
    def __init__(self, plot_settings_window):
        self.settings_window = plot_settings_window
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.themes_file = os.path.join(self.app_dir, "themes.json")
        self.themes = self._load_themes_from_file()
        
    def _load_themes_from_file(self):
        """파일에서 테마 로드"""
        if os.path.exists(self.themes_file):
            try:
                with open(self.themes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"테마 파일 로드 오류: {e}")
                return {}
        return {}
        
    def _save_themes_to_file(self):
        """테마를 파일에 저장"""
        try:
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(self.themes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"테마 파일 저장 오류: {e}")
            
    def show_theme_window(self):
        """테마 관리 창 표시"""
        window = tk.Toplevel(self.settings_window.window)
        window.title("테마 관리")
        window.geometry("600x500")  # 너비 1.5배 (400 -> 600)
        window.transient(self.settings_window.window)
        
        # 메인 프레임 (좌우 분할)
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽: 테마 목록
        left_frame = ttk.LabelFrame(main_frame, text="저장된 테마", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        scrollbar = ttk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(left_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # 테마 목록 채우기
        for name in sorted(self.themes.keys()):
            listbox.insert(tk.END, name)
            
        # 오른쪽: 상세 정보 및 버튼
        right_frame = ttk.Frame(main_frame, width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        
        # 버튼 프레임
        btn_frame = ttk.LabelFrame(right_frame, text="동작", padding=10)
        btn_frame.pack(fill=tk.X, pady=5)
        
        def apply_theme():
            selection = listbox.curselection()
            if not selection:
                return
            name = listbox.get(selection[0])

            # 현재 탭 모드 확인
            current_tab_index = self.settings_window.main_notebook.index(self.settings_window.main_notebook.select())
            # 0: Single Y, 1: Double Y, 2: Error Bar

            # 테마 모드 확인
            is_theme_double_y = name.startswith("[Double Y] ")
            is_theme_single_y = name.startswith("[Single Y] ")
            is_theme_error_bar = name.startswith("[Error Bar] ")

            # 모드 불일치 경고 - 적용 차단
            if is_theme_double_y and current_tab_index != 1:
                messagebox.showwarning("경고",
                    f"'{name}'은 Double Y축 테마입니다.\n\nDouble Y축 탭에서만 적용 가능합니다.\n\nDouble Y축 탭으로 전환 후 다시 시도하세요.")
                return
            elif is_theme_single_y and current_tab_index != 0:
                messagebox.showwarning("경고",
                    f"'{name}'은 Single Y축 테마입니다.\n\nSingle Y축 탭에서만 적용 가능합니다.\n\nSingle Y축 탭으로 전환 후 다시 시도하세요.")
                return
            elif is_theme_error_bar and current_tab_index != 2:
                messagebox.showwarning("경고",
                    f"'{name}'은 Error Bar 테마입니다.\n\nError Bar 탭에서만 적용 가능합니다.\n\nError Bar 탭으로 전환 후 다시 시도하세요.")
                return

            self.apply_theme_to_ui(name)
            messagebox.showinfo("성공", f"'{name}' 테마가 적용되었습니다.\n'적용' 버튼을 눌러 그래프에 반영하세요.")
            window.destroy()
            
        def save_current_theme():
            # 현재 탭 모드 확인
            current_tab_index = self.settings_window.main_notebook.index(self.settings_window.main_notebook.select())
            # 0: Single Y, 1: Double Y, 2: Error Bar

            if current_tab_index == 2:
                mode_prefix = "[Error Bar] "
                mode_name = "Error Bar"
            elif current_tab_index == 1:
                mode_prefix = "[Double Y] "
                mode_name = "Double Y축"
            else:
                mode_prefix = "[Single Y] "
                mode_name = "Single Y축"

            # 안내 메시지와 함께 테마 이름 입력 받기
            prompt_msg = f"새 테마 이름을 입력하세요.\n현재 모드: {mode_name}\n\n'{mode_prefix}'가 자동으로 추가됩니다."
            name = simpledialog.askstring("테마 저장", prompt_msg, parent=window)

            if name:
                # 이미 접두사가 있는지 확인
                if not name.startswith("[Single Y] ") and not name.startswith("[Double Y] ") and not name.startswith("[Error Bar] "):
                    name = mode_prefix + name

                if name in self.themes:
                    if not messagebox.askyesno("확인", f"'{name}' 테마가 이미 존재합니다. 덮어쓰시겠습니까?"):
                        return

                # 현재 UI 설정 수집 (현재 활성화된 탭 기준)
                settings = self.settings_window._collect_settings()

                # 모드별 플래그 저장
                if current_tab_index == 2:
                    settings['is_error_bar_mode'] = True
                elif current_tab_index == 1:
                    settings['is_double_y_mode'] = True

                self.themes[name] = settings
                self._save_themes_to_file()

                # 리스트박스 갱신
                listbox.delete(0, tk.END)
                for n in sorted(self.themes.keys()):
                    listbox.insert(tk.END, n)

                messagebox.showinfo("성공", f"'{name}' 테마가 저장되었습니다.")
                    
        def delete_theme():
            selection = listbox.curselection()
            if not selection:
                return
            name = listbox.get(selection[0])
            if messagebox.askyesno("확인", f"'{name}' 테마를 삭제하시겠습니까?"):
                del self.themes[name]
                self._save_themes_to_file()
                # 리스트박스 갱신
                listbox.delete(0, tk.END)
                for n in sorted(self.themes.keys()):
                    listbox.insert(tk.END, n)

        ttk.Button(btn_frame, text="선택한 테마 적용", command=apply_theme).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="현재 설정을 새 테마로 저장", command=save_current_theme).pack(fill=tk.X, pady=5)
        ttk.Separator(btn_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="선택한 테마 삭제", command=delete_theme).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="닫기", command=window.destroy).pack(fill=tk.X, pady=5)

    def apply_theme_to_ui(self, theme_name):
        """테마 설정을 UI에 반영"""
        if theme_name not in self.themes:
            return

        settings = self.themes[theme_name]
        sw = self.settings_window

        try:
            # 1. 탭 전환 (Single/Double Y/Error Bar)
            is_error_bar = settings.get('is_error_bar_mode', False)
            is_double_y = settings.get('use_double_y', False) or settings.get('is_double_y_mode', False)

            if is_error_bar:
                sw.main_notebook.select(sw.error_bar_tab)
                target_settings = sw.error_bar_settings
                # Error Bar 테마 적용
                self._apply_error_bar_theme(target_settings, settings)
                return
            elif is_double_y:
                sw.main_notebook.select(sw.double_y_tab)
                target_settings = sw.double_y_settings
            else:
                sw.main_notebook.select(sw.single_y_tab)
                target_settings = sw.single_y_settings
            
            # 2. 관련 설정 딕셔너리 업데이트 (UI 빌드 시 참조용)
            if hasattr(target_settings, 'settings'):
                target_settings.settings.update(settings)

            # 3. 컬럼 선택 업데이트 (스타일 UI 생성 전에 수행)
            if is_double_y:
                if 'left_y_columns' in settings:
                    target_settings.left_y_columns = settings['left_y_columns']
                    if hasattr(target_settings, 'left_y_listbox'):
                        lb = target_settings.left_y_listbox
                        lb.selection_clear(0, tk.END)
                        for i in range(lb.size()):
                            if lb.get(i) in settings['left_y_columns']:
                                lb.selection_set(i)
                            
                if 'right_y_columns' in settings:
                    target_settings.right_y_columns = settings['right_y_columns']
                    if hasattr(target_settings, 'right_y_listbox'):
                        lb = target_settings.right_y_listbox
                        lb.selection_clear(0, tk.END)
                        for i in range(lb.size()):
                            if lb.get(i) in settings['right_y_columns']:
                                lb.selection_set(i)
                
                # Double Y 스타일 UI 갱신 (여기서 변수들이 생성됨)
                if hasattr(target_settings, '_update_plot_styles'):
                    target_settings._update_plot_styles()
            else:
                if 'y_columns' in settings and hasattr(sw.main_app, 'y_listbox'):
                    lb = sw.main_app.y_listbox
                    lb.selection_clear(0, tk.END)
                    all_items = lb.get(0, tk.END)
                    for i, item in enumerate(all_items):
                        if item in settings['y_columns']:
                            lb.selection_set(i)
                
                # Single Y 스타일 UI 갱신 (여기서 변수들이 생성됨)
                if hasattr(target_settings, '_refresh_style_ui'):
                    target_settings._refresh_style_ui()

            # 4. 공통 설정 적용 (제목, 레이블 등)
            if hasattr(target_settings, 'title_var') and 'title' in settings:
                target_settings.title_var.set(settings['title'])
            if hasattr(target_settings, 'xlabel_var') and 'xlabel' in settings:
                target_settings.xlabel_var.set(settings['xlabel'])
            
            if is_double_y:
                if 'left_ylabel' in settings: target_settings.left_ylabel.set(settings['left_ylabel'])
                if 'right_ylabel' in settings: target_settings.right_ylabel.set(settings['right_ylabel'])
            else:
                if hasattr(target_settings, 'ylabel_var') and 'ylabel' in settings:
                    target_settings.ylabel_var.set(settings['ylabel'])

            # 5. 폰트 크기
            font_size_maps = [
                ('title_fontsize', 'title_fontsize_var'),
                ('label_fontsize', 'label_fontsize_var'),
                ('xlabel_fontsize', 'xlabel_fontsize_var'),
                ('ylabel_fontsize', 'ylabel_fontsize_var'),
                ('tick_fontsize', 'tick_fontsize_var'),
                ('x_tick_fontsize', 'x_tick_fontsize_var'),
                ('y_tick_fontsize', 'y_tick_fontsize_var')
            ]
            for key, var_name in font_size_maps:
                if key in settings and hasattr(target_settings, var_name):
                    getattr(target_settings, var_name).set(settings[key])

            # 6. 축 범위 및 간격
            if hasattr(target_settings, 'xlim_min_numeric_var') and 'xlim_min' in settings:
                target_settings.xlim_min_numeric_var.set(settings['xlim_min'])
            if hasattr(target_settings, 'xlim_max_numeric_var') and 'xlim_max' in settings:
                target_settings.xlim_max_numeric_var.set(settings['xlim_max'])
            if hasattr(target_settings, 'x_ticks_var') and 'x_ticks' in settings:
                target_settings.x_ticks_var.set(settings['x_ticks'])
                
            if not is_double_y:
                if 'ylim_min' in settings: target_settings.ylim_min_var.set(settings['ylim_min'])
                if 'ylim_max' in settings: target_settings.ylim_max_var.set(settings['ylim_max'])
                if 'y_ticks' in settings: target_settings.y_ticks_var.set(settings['y_ticks'])
            else:
                if 'left_ylim_min' in settings: target_settings.left_ylim_min.set(settings['left_ylim_min'])
                if 'left_ylim_max' in settings: target_settings.left_ylim_max.set(settings['left_ylim_max'])
                if 'left_y_ticks' in settings: target_settings.left_y_ticks_var.set(settings['left_y_ticks'])
                if 'right_ylim_min' in settings: target_settings.right_ylim_min.set(settings['right_ylim_min'])
                if 'right_ylim_max' in settings: target_settings.right_ylim_max.set(settings['right_ylim_max'])
                if 'right_y_ticks' in settings: target_settings.right_y_ticks_var.set(settings['right_y_ticks'])
                if 'left_axis_color' in settings: target_settings.left_axis_color.set(settings['left_axis_color'])
                if 'right_axis_color' in settings: target_settings.right_axis_color.set(settings['right_axis_color'])

            # 7. 상세 스타일 설정 (re-apply to the variables created in Step 3)
            style_maps = [
                ('y_colors', 'y_color_vars'),
                ('y_line_widths', 'y_line_width_vars'),
                ('y_line_styles', 'y_line_style_vars'),
                ('y_markers', 'y_marker_vars'),
                ('y_marker_sizes', 'y_marker_size_vars'),
                ('y_plot_types', 'y_plot_type_vars' if not is_double_y else 'y_plot_types'),
                ('y_alphas', 'y_alpha_vars'),
                ('y_zorders', 'y_zorder_vars')
            ]
            
            for settings_key, var_dict_name in style_maps:
                if settings_key in settings and hasattr(target_settings, var_dict_name):
                    saved_dict = settings[settings_key]
                    target_dict = getattr(target_settings, var_dict_name)
                    for col, val in saved_dict.items():
                        if col in target_dict:
                            target_dict[col].set(val)

            # 8. 그리드
            if hasattr(target_settings, 'grid_var') and 'grid' in settings:
                target_settings.grid_var.set(settings['grid'])

        except Exception as e:
            print(f"테마 적용 중 오류: {e}")
            messagebox.showwarning("경고", f"일부 설정을 적용하는 중 오류가 발생했습니다: {e}")

    def _apply_error_bar_theme(self, target_settings, settings):
        """Error Bar 테마 설정을 UI에 반영"""
        try:
            # 데이터 모드
            if hasattr(target_settings, 'data_mode_var') and 'data_mode' in settings:
                target_settings.data_mode_var.set(settings['data_mode'])
                target_settings._on_mode_changed()

            # 스타일 설정
            style_vars = [
                ('color', 'color_var'),
                ('ecolor', 'ecolor_var'),
                ('capsize', 'capsize_var'),
                ('capthick', 'capthick_var'),
                ('line_width', 'line_width_var'),
                ('marker', 'marker_var'),
                ('marker_size', 'marker_size_var'),
            ]
            for key, var_name in style_vars:
                if key in settings and hasattr(target_settings, var_name):
                    getattr(target_settings, var_name).set(settings[key])

            # 축 범위
            axis_vars = [
                ('xlim_min', 'xlim_min_var'),
                ('xlim_max', 'xlim_max_var'),
                ('ylim_min', 'ylim_min_var'),
                ('ylim_max', 'ylim_max_var'),
                ('x_ticks', 'x_ticks_var'),
                ('y_ticks', 'y_ticks_var'),
            ]
            for key, var_name in axis_vars:
                if key in settings and hasattr(target_settings, var_name):
                    getattr(target_settings, var_name).set(settings[key])

            # 레이블
            label_vars = [
                ('title', 'title_var'),
                ('xlabel', 'xlabel_var'),
                ('ylabel', 'ylabel_var'),
            ]
            for key, var_name in label_vars:
                if key in settings and hasattr(target_settings, var_name):
                    getattr(target_settings, var_name).set(settings[key])

            # 범례 위치
            if 'legend_loc' in settings and hasattr(target_settings, 'legend_loc_var'):
                # legend_loc을 display 값으로 변환
                loc_map = {
                    'best': '최적 위치(Auto)',
                    'upper right': '오른쪽 위',
                    'upper left': '왼쪽 위',
                    'lower left': '왼쪽 아래',
                    'lower right': '오른쪽 아래',
                    'center left': '왼쪽 중간',
                    'center right': '오른쪽 중간',
                    'lower center': '아래 중간',
                    'upper center': '위 중간',
                    'center': '중앙'
                }
                display_val = loc_map.get(settings['legend_loc'], '최적 위치(Auto)')
                target_settings.legend_loc_var.set(display_val)

            # 폰트 크기
            font_vars = [
                ('title_fontsize', 'title_fontsize_var'),
                ('xlabel_fontsize', 'xlabel_fontsize_var'),
                ('ylabel_fontsize', 'ylabel_fontsize_var'),
                ('x_tick_fontsize', 'x_tick_fontsize_var'),
                ('y_tick_fontsize', 'y_tick_fontsize_var'),
            ]
            for key, var_name in font_vars:
                if key in settings and hasattr(target_settings, var_name):
                    getattr(target_settings, var_name).set(settings[key])

            # 색상 미리보기 업데이트
            if hasattr(target_settings, '_update_color_preview'):
                target_settings._update_color_preview()
            if hasattr(target_settings, '_update_ecolor_preview'):
                target_settings._update_ecolor_preview()

        except Exception as e:
            print(f"Error Bar 테마 적용 중 오류: {e}")
