from FileSplit import FileSplitter
import tkinter as tk
from tkinter import filedialog, ttk
import asyncio
import time

class FileSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Splitter")
        self.file_path = None
        self.output_dir = None
        self.splitter = None
        self.details_visible = False
        self.start_time = None
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self.root, text="请选择要切割的文件和输出目录。")
        self.label.pack(pady=10)

        self.select_file_button = tk.Button(self.root, text="选择文件", command=self.select_file)
        self.select_file_button.pack(pady=5)

        self.select_output_button = tk.Button(self.root, text="选择输出目录", command=self.select_output)
        self.select_output_button.pack(pady=5)

        self.start_button = tk.Button(self.root, text="开始切割", command=self.start_splitting)
        self.start_button.pack(pady=5)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.details_text = tk.Text(self.root, height=10, width=50)
        self.details_text.pack(pady=10)

        self.exit_button = tk.Button(self.root, text="退出", command=self.root.quit)
        self.exit_button.pack(pady=5)

    def select_file(self):
        self.file_path = filedialog.askopenfilename()
        self.details_text.insert(tk.END, f"已选择文件: {self.file_path}\n")
        self.details_text.see(tk.END)

    def select_output(self):
        self.output_dir = filedialog.askdirectory()
        self.details_text.insert(tk.END, f"已选择输出目录: {self.output_dir}\n")
        self.details_text.see(tk.END)

    def update_progress(self, progress, chunk_name, chunk_size):
        self.progress["value"] = progress
        if self.splitter.processed_size // self.splitter.chunk_size % 10 == 0:
            self.details_text.insert(tk.END, f"当前进度: {progress:.2f}% - 已切割 {self.splitter.processed_size // self.splitter.chunk_size} 条数据\n")
            self.details_text.see(tk.END)

    def show_summary(self):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        speed = self.splitter.total_size / elapsed_time
        self.details_text.insert(tk.END, f"文件切割完成！\n总耗时: {elapsed_time:.2f} 秒\n平均速度: {speed:.2f} 字节/秒\n")
        self.details_text.see(tk.END)

    def start_splitting(self):
        if not self.file_path or not self.output_dir:
            self.details_text.insert(tk.END, "请先选择文件和输出目录。\n")
            self.details_text.see(tk.END)
            return

        self.splitter = FileSplitter(self.file_path, self.output_dir, progress_callback=self.update_progress)
        self.start_time = time.time()
        asyncio.run(self.splitter.split())
        self.show_summary()

def main():
    root = tk.Tk()
    app = FileSplitterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()