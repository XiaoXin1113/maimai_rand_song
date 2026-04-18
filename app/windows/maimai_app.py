import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType, Song
from core.group_blacklist import group_blacklist

class MaimaiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("maimai随机选歌工具 - Windows桌面版")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)
        
        self.song_manager = SongManager()
        self.song_selector = SongSelector(self.song_manager)
        
        self.setup_styles()
        self.create_menu()
        self.create_main_frame()
        self.load_genres()
        self.update_stats()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 16, 'bold'), foreground='#667eea')
        style.configure('Header.TLabel', font=('Microsoft YaHei UI', 11, 'bold'), foreground='#333')
        style.configure('Info.TLabel', font=('Microsoft YaHei UI', 10), foreground='#666')
        style.configure('Primary.TButton', font=('Microsoft YaHei UI', 11, 'bold'), padding=10)
        style.configure('Card.TFrame', background='#f8f9fa')
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新数据库", command=self.refresh_database)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        tool_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tool_menu)
        tool_menu.add_command(label="黑名单管理", command=self.open_blacklist_window)
        tool_menu.add_command(label="数据库统计", command=self.show_database_stats)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="使用说明", command=self.show_help)
        
    def create_main_frame(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="🎵 maimai随机选歌工具", style='Title.TLabel').pack(side=tk.LEFT)
        
        version_label = ttk.Label(header_frame, text="Alpha-0.0.3", style='Info.TLabel')
        version_label.pack(side=tk.RIGHT)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.LabelFrame(content_frame, text="选歌条件", padding="15")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.create_selection_form(left_frame)
        
        right_frame = ttk.LabelFrame(content_frame, text="选歌结果", padding="15")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_result_panel(right_frame)
        
    def create_selection_form(self, parent):
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(form_frame, text="难度:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.difficulty_var = tk.StringVar(value="")
        difficulty_combo = ttk.Combobox(form_frame, textvariable=self.difficulty_var, width=15, state='readonly')
        difficulty_combo['values'] = ('', 'Easy', 'Basic', 'Advanced', 'Expert', 'Master', 'Re:Master')
        difficulty_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        
        ttk.Label(form_frame, text="歌曲类型:", style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.song_type_var = tk.StringVar(value="")
        song_type_combo = ttk.Combobox(form_frame, textvariable=self.song_type_var, width=15, state='readonly')
        song_type_combo['values'] = ('', '标准 (STD)', 'DX')
        song_type_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=10)
        
        ttk.Label(form_frame, text="流派:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.genre_var = tk.StringVar(value="")
        self.genre_combo = ttk.Combobox(form_frame, textvariable=self.genre_var, width=15, state='readonly')
        self.genre_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=10)
        
        level_frame = ttk.LabelFrame(parent, text="等级范围", padding="10")
        level_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(level_frame, text="最低等级:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.min_level_var = tk.StringVar(value="")
        min_level_entry = ttk.Entry(level_frame, textvariable=self.min_level_var, width=10)
        min_level_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        ttk.Label(level_frame, text="(如: 14.0, 14+, 14)", style='Info.TLabel').grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(level_frame, text="最高等级:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_level_var = tk.StringVar(value="")
        max_level_entry = ttk.Entry(level_frame, textvariable=self.max_level_var, width=10)
        max_level_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=10)
        ttk.Label(level_frame, text="(如: 14.5, 14+, 14)", style='Info.TLabel').grid(row=1, column=2, sticky=tk.W)
        
        count_frame = ttk.Frame(parent)
        count_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(count_frame, text="随机次数:", style='Header.TLabel').pack(side=tk.LEFT)
        self.count_var = tk.StringVar(value="1")
        count_spinbox = ttk.Spinbox(count_frame, from_=1, to=50, textvariable=self.count_var, width=5)
        count_spinbox.pack(side=tk.LEFT, padx=10)
        ttk.Label(count_frame, text="(可重复)", style='Info.TLabel').pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=20)
        
        select_btn = ttk.Button(btn_frame, text="🎲 随机选歌", command=self.select_random, style='Primary.TButton')
        select_btn.pack(fill=tk.X, pady=5)
        
        clear_btn = ttk.Button(btn_frame, text="清空条件", command=self.clear_criteria)
        clear_btn.pack(fill=tk.X, pady=5)
        
        stats_frame = ttk.LabelFrame(parent, text="数据库统计", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="加载中...", style='Info.TLabel')
        self.stats_label.pack()
        
    def create_result_panel(self, parent):
        self.result_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=('Microsoft YaHei UI', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, "请设置条件后点击\"随机选歌\"\n\n")
        self.result_text.config(state=tk.DISABLED)
        
        self.result_text.tag_configure('title', font=('Microsoft YaHei UI', 12, 'bold'), foreground='#667eea')
        self.result_text.tag_configure('header', font=('Microsoft YaHei UI', 10, 'bold'), foreground='#333')
        self.result_text.tag_configure('info', font=('Microsoft YaHei UI', 10), foreground='#666')
        self.result_text.tag_configure('level', font=('Microsoft YaHei UI', 10), foreground='#e74c3c')
        
    def load_genres(self):
        genres = set()
        for song in self.song_manager.get_all_songs():
            if song.genre:
                genres.add(song.genre)
        self.genre_combo['values'] = ('',) + tuple(sorted(genres))
        
    def update_stats(self):
        songs = self.song_manager.get_all_songs()
        total_songs = len(songs)
        total_charts = sum(len(song.charts) for song in songs)
        self.stats_label.config(text=f"总歌曲: {total_songs} | 总谱面: {total_charts}")
        
    def parse_level_input(self, level_str: str) -> tuple:
        if not level_str:
            return None, None
            
        level_str = level_str.strip()
        has_plus = "+" in level_str
        level_str_clean = level_str.replace("+", "")
        has_decimal = "." in level_str_clean
        
        try:
            level = float(level_str_clean)
        except ValueError:
            return None, None
            
        if has_plus:
            level_int = int(level)
            min_level = level_int + 0.6
            max_level = level_int + 0.9
        elif not has_decimal and level == int(level):
            level_int = int(level)
            min_level = level_int + 0.0
            max_level = level_int + 0.5
        else:
            min_level = level - 0.05
            max_level = level + 0.05
            
        return min_level, max_level
        
    def select_random(self):
        difficulty_map = {
            'Easy': Difficulty.EASY,
            'Basic': Difficulty.BASIC,
            'Advanced': Difficulty.ADVANCED,
            'Expert': Difficulty.EXPERT,
            'Master': Difficulty.MASTER,
            'Re:Master': Difficulty.REMASTER
        }
        
        type_map = {
            '标准 (STD)': SongType.STANDARD,
            'DX': SongType.DX
        }
        
        diff_value = self.difficulty_var.get()
        type_value = self.song_type_var.get()
        
        min_level, max_level = None, None
        min_str = self.min_level_var.get().strip()
        max_str = self.max_level_var.get().strip()
        
        if min_str:
            min_level, _ = self.parse_level_input(min_str)
        if max_str:
            _, max_level = self.parse_level_input(max_str)
            
        try:
            count = int(self.count_var.get())
        except ValueError:
            count = 1
            
        criteria = SelectionCriteria(
            min_level=min_level,
            max_level=max_level,
            difficulty=difficulty_map.get(diff_value) if diff_value else None,
            song_type=type_map.get(type_value) if type_value else None,
            genre=self.genre_var.get() if self.genre_var.get() else None,
            count=count
        )
        
        result = self.song_selector.select_random(criteria)
        self.display_results(result)
        
    def display_results(self, result):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        if not result.songs:
            self.result_text.insert(tk.END, "没有找到符合条件的歌曲\n", 'info')
            self.result_text.config(state=tk.DISABLED)
            return
            
        self.result_text.insert(tk.END, f"共找到 {result.total_available} 首符合条件的歌曲\n\n", 'header')
        
        for i, song in enumerate(result.songs, 1):
            self.result_text.insert(tk.END, f"【{i}】{song.title}\n", 'title')
            self.result_text.insert(tk.END, f"    艺术家: {song.artist}\n", 'info')
            self.result_text.insert(tk.END, f"    类型: {song.type.value.upper()}\n", 'info')
            
            if song.genre:
                self.result_text.insert(tk.END, f"    流派: {song.genre}\n", 'info')
            if song.bpm:
                self.result_text.insert(tk.END, f"    BPM: {song.bpm}\n", 'info')
                
            self.result_text.insert(tk.END, "    谱面:\n", 'header')
            
            charts_by_type = {}
            for chart in song.charts:
                type_key = chart.type.value.upper()
                if type_key not in charts_by_type:
                    charts_by_type[type_key] = []
                charts_by_type[type_key].append(chart)
                
            for chart_type, charts in charts_by_type.items():
                chart_info = []
                for c in charts:
                    if c.internal_level:
                        level_str = f"{c.level} ({c.internal_level})"
                    else:
                        level_str = c.level
                    chart_info.append(f"{c.difficulty.value} {level_str}")
                self.result_text.insert(tk.END, f"      {chart_type}: {' | '.join(chart_info)}\n", 'level')
                
            self.result_text.insert(tk.END, "\n")
            
        self.result_text.config(state=tk.DISABLED)
        
    def clear_criteria(self):
        self.difficulty_var.set("")
        self.song_type_var.set("")
        self.genre_var.set("")
        self.min_level_var.set("")
        self.max_level_var.set("")
        self.count_var.set("1")
        
    def refresh_database(self):
        self.song_manager.load_songs()
        self.load_genres()
        self.update_stats()
        messagebox.showinfo("成功", "数据库已刷新")
        
    def open_blacklist_window(self):
        blacklist_window = tk.Toplevel(self.root)
        blacklist_window.title("黑名单管理")
        blacklist_window.geometry("500x400")
        
        frame = ttk.Frame(blacklist_window, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="群号黑名单", style='Header.TLabel').pack(anchor=tk.W)
        
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        blacklist_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        blacklist_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=blacklist_listbox.yview)
        
        for entry in group_blacklist.get_all():
            blacklist_listbox.insert(tk.END, f"{entry.group_id} - {entry.group_name or '未知'} ({entry.reason or '无原因'})")
            
        add_frame = ttk.Frame(frame)
        add_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(add_frame, text="群号:").grid(row=0, column=0, sticky=tk.W)
        group_id_entry = ttk.Entry(add_frame, width=15)
        group_id_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(add_frame, text="群名:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        group_name_entry = ttk.Entry(add_frame, width=15)
        group_name_entry.grid(row=0, column=3, padx=5)
        
        def add_to_blacklist():
            try:
                group_id = int(group_id_entry.get())
                group_name = group_name_entry.get() or None
                if not group_blacklist.is_blocked(group_id):
                    group_blacklist.add_group(group_id, group_name)
                    blacklist_listbox.insert(tk.END, f"{group_id} - {group_name or '未知'}")
                    group_id_entry.delete(0, tk.END)
                    group_name_entry.delete(0, tk.END)
                else:
                    messagebox.showwarning("警告", "该群已在黑名单中")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的群号")
                
        def remove_from_blacklist():
            selection = blacklist_listbox.curselection()
            if selection:
                group_id = int(blacklist_listbox.get(selection[0]).split(" - ")[0])
                group_blacklist.remove_group(group_id)
                blacklist_listbox.delete(selection[0])
                
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="添加", command=add_to_blacklist).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=remove_from_blacklist).pack(side=tk.LEFT, padx=5)
        
    def show_database_stats(self):
        songs = self.song_manager.get_all_songs()
        total_songs = len(songs)
        total_charts = sum(len(song.charts) for song in songs)
        
        difficulty_counts = {}
        type_counts = {'STD': 0, 'DX': 0}
        
        for song in song_manager.get_all_songs():
            for chart in song.charts:
                diff = chart.difficulty.value
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
                if chart.type == SongType.STANDARD:
                    type_counts['STD'] += 1
                else:
                    type_counts['DX'] += 1
                    
        stats_window = tk.Toplevel(self.root)
        stats_window.title("数据库统计")
        stats_window.geometry("400x350")
        
        frame = ttk.Frame(stats_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="数据库统计信息", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 15))
        ttk.Label(frame, text=f"总歌曲数: {total_songs}", style='Header.TLabel').pack(anchor=tk.W, pady=5)
        ttk.Label(frame, text=f"总谱面数: {total_charts}", style='Header.TLabel').pack(anchor=tk.W, pady=5)
        
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(frame, text="谱面类型分布:", style='Header.TLabel').pack(anchor=tk.W, pady=5)
        ttk.Label(frame, text=f"  STD: {type_counts['STD']}", style='Info.TLabel').pack(anchor=tk.W)
        ttk.Label(frame, text=f"  DX: {type_counts['DX']}", style='Info.TLabel').pack(anchor=tk.W)
        
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(frame, text="难度分布:", style='Header.TLabel').pack(anchor=tk.W, pady=5)
        for diff in ['Easy', 'Basic', 'Advanced', 'Expert', 'Master', 'Re:Master']:
            count = difficulty_counts.get(diff, 0)
            ttk.Label(frame, text=f"  {diff}: {count}", style='Info.TLabel').pack(anchor=tk.W)
            
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("400x250")
        
        frame = ttk.Frame(about_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="🎵 maimai随机选歌工具", style='Title.TLabel').pack(pady=10)
        ttk.Label(frame, text="Windows桌面版 - Alpha-0.0.3", style='Info.TLabel').pack()
        ttk.Label(frame, text="\n一款用于maimai游戏的随机选歌工具\n支持精确难度筛选、多条件组合查询", style='Info.TLabel').pack(pady=10)
        ttk.Label(frame, text="© 2024", style='Info.TLabel').pack()
        
    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x400")
        
        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=('Microsoft YaHei UI', 10))
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_content = """使用说明

【等级输入规则】
• 整数输入 (如 14): 匹配 14.0 ~ 14.5
• 带加号输入 (如 14+): 匹配 14.6 ~ 14.9
• 小数输入 (如 14.7): 精确匹配 14.65 ~ 14.75

【选歌条件】
• 难度: 选择谱面难度 (Easy ~ Re:Master)
• 歌曲类型: 标准(STD) 或 DX
• 流派: 选择歌曲流派
• 等级范围: 设置最低和最高等级
• 随机次数: 随机抽取的次数 (可重复)

【功能说明】
• 随机选歌: 根据条件随机选择歌曲
• 清空条件: 重置所有筛选条件
• 刷新数据库: 重新加载数据库文件
• 黑名单管理: 管理QQ群黑名单
• 数据库统计: 查看数据库详细信息

【快捷键】
• Ctrl+R: 随机选歌
• Ctrl+C: 清空条件
• F5: 刷新数据库
"""
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = MaimaiApp(root)
    
    root.bind('<Control-r>', lambda e: app.select_random())
    root.bind('<Control-c>', lambda e: app.clear_criteria())
    root.bind('<F5>', lambda e: app.refresh_database())
    
    root.mainloop()


if __name__ == "__main__":
    main()
