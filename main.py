import tkinter as tk
from tkinter import font

class RaspberryPiApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
    
    def setup_window(self):
        """設置窗口為全螢幕，480x320解析度"""
        self.root.attributes('-fullscreen', True)
        self.root.geometry('480x320')
        self.root.configure(bg='white')
        # Raspberry Pi Zero W 通常使用 4:3 或其他小螢幕
        self.root.resizable(False, False)
    
    def create_widgets(self):
        """創建 UI 組件"""
        # 主容器框架
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Hello World 標籤（居中）
        hello_font = font.Font(family='Helvetica', size=24, weight='bold')
        hello_label = tk.Label(
            main_frame, 
            text='Hello World', 
            font=hello_font, 
            bg='white', 
            fg='black'
        )
        hello_label.pack(expand=True)
        
        # 頂部框架用於放置關閉按鈕（右上角）
        top_frame = tk.Frame(self.root, bg='white', height=40)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        top_frame.pack_propagate(False)
        
        # 關閉按鈕
        close_btn = tk.Button(
            top_frame,
            text='✕',
            command=self.close_app,
            font=('Helvetica', 16, 'bold'),
            bg='red',
            fg='white',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2
        )
        close_btn.pack(side=tk.RIGHT)
    
    def close_app(self):
        """關閉應用程式"""
        self.root.quit()

def main():
    root = tk.Tk()
    root.title('Raspberry Pi Application')
    app = RaspberryPiApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
