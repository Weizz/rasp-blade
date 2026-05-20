import asyncio
import threading
import tkinter as tk
from tkinter import font

from bleak import BleakClient, BleakScanner

BEY_DATA_CHAR_UUID = ""
SCAN_TIMEOUT = 120.0


class RaspberryPiApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Raspberry Pi Application')
        self.stop_event = threading.Event()
        self.max_value = None
        self.ble_thread = None

        self.setup_window()
        self.create_widgets()
        self.root.after(200, self.start_ble)

    def setup_window(self):
        """設置窗口為全螢幕，480x320解析度"""
        self.root.attributes('-fullscreen', True)
        self.root.geometry('480x320')
        self.root.configure(bg='white')
        self.root.resizable(False, False)

    def create_widgets(self):
        """創建 UI 組件"""
        top_frame = tk.Frame(self.root, bg='white', height=40)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        top_frame.pack_propagate(False)

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
            bd=2,
        )
        close_btn.pack(side=tk.RIGHT)

        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        hello_font = font.Font(family='Helvetica', size=24, weight='bold')
        hello_label = tk.Label(
            main_frame,
            text='BLE 連線測試',
            font=hello_font,
            bg='white',
            fg='black',
        )
        hello_label.pack(pady=(0, 20))

        status_font = font.Font(family='Helvetica', size=18)
        self.status_label = tk.Label(
            main_frame,
            text='準備中...',
            font=status_font,
            bg='white',
            fg='blue',
            justify=tk.CENTER,
            wraplength=440,
        )
        self.status_label.pack(pady=(0, 10))

        self.max_label = tk.Label(
            main_frame,
            text='等待資料...',
            font=status_font,
            bg='white',
            fg='black',
        )
        self.max_label.pack(pady=(10, 0))

    def start_ble(self):
        self.update_status('正在連接...')
        self.ble_thread = threading.Thread(target=self.ble_worker, daemon=True)
        self.ble_thread.start()

    def update_status(self, text: str):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def update_max_value(self, value: int):
        self.max_value = value
        self.root.after(0, lambda: self.max_label.config(text=f'最大值: {value}'))

    def ble_worker(self):
        try:
            asyncio.run(self.ble_main())
        except Exception as exc:
            self.update_status(f'連線錯誤：{exc}')

    async def ble_main(self):
        self.update_status('正在掃描 BLE 裝置...')
        devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)

        if not devices:
            self.update_status('未找到 BLE 裝置')
            return

        target_device = devices[0]
        device_name = target_device.name or target_device.address
        self.update_status(f'找到裝置：{device_name}\n連線中...')

        try:
            async with BleakClient(target_device.address) as client:
                if not client.is_connected:
                    self.update_status('無法連上裝置')
                    return

                self.update_status('連線成功！')
                await client.start_notify(BEY_DATA_CHAR_UUID, self.notification_handler)

                while client.is_connected and not self.stop_event.is_set():
                    await asyncio.sleep(1)

                await client.stop_notify(BEY_DATA_CHAR_UUID)
        except Exception as exc:
            self.update_status(f'連線失敗：{exc}')

    def notification_handler(self, sender, data: bytearray):
        if 0xB0 <= data[0] <= 0xB5 and len(data) > 2:
            parsed_values = []
            for i in range(1, len(data) - 1, 2):
                parsed_values.append(int.from_bytes(data[i:i + 2], byteorder='little'))

            if parsed_values:
                packet_max = max(parsed_values)
                self.update_max_value(packet_max)

    def close_app(self):
        self.stop_event.set()
        self.root.quit()


def main():
    root = tk.Tk()
    app = RaspberryPiApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
