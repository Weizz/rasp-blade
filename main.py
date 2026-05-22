import asyncio
import os
import threading
import tkinter as tk
from tkinter import font

from bleak import BleakClient, BleakScanner

BEY_DATA_CHAR_UUID = "55c4f002-f8eb-11ec-b939-0242ac120002"
SCAN_TIMEOUT = 5.0


class RaspberryPiApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Raspberry Pi Application')
        self.stop_event = threading.Event()
        self.power_value = None
        self.ble_thread = None
        self.blink_job = None
        self.blink_state = False

        self.setup_window()
        self.create_widgets()
        self.root.after(200, self.start_ble)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def setup_window(self):
        """設置窗口為全螢幕，480x320解析度"""
        self.root.attributes('-fullscreen', True)
        self.root.geometry('480x320')
        self.root.configure(bg='#F4E7E1')
        self.root.resizable(False, False)

    def create_widgets(self):
        """創建 UI 組件"""
        top_frame = tk.Frame(self.root, bg='#F4E7E1', height=56)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        top_frame.pack_propagate(False)

        self.close_label = tk.Label(
            top_frame,
            bg='#F4E7E1',
            cursor='hand2',
        )
        self.close_label.pack(side=tk.LEFT)
        self.close_label.bind('<Button-1>', lambda _: self.close_app())

        icon_frame = tk.Frame(top_frame, bg='#F4E7E1', width=52, height=52)
        icon_frame.pack(side=tk.LEFT, padx=(8, 0))
        icon_frame.pack_propagate(False)

        self.icon_label = tk.Label(
            icon_frame,
            bg='#F4E7E1',
            width=52,
            height=52,
        )
        self.icon_label.pack(fill=tk.BOTH, expand=True)

        icon_frame2 = tk.Frame(top_frame, bg='#F4E7E1', width=52, height=52)
        icon_frame2.pack(side=tk.LEFT, padx=(8, 0))
        icon_frame2.pack_propagate(False)

        self.icon_label2 = tk.Label(
            icon_frame2,
            bg='#F4E7E1',
            width=52,
            height=52,
        )
        self.icon_label2.pack(fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(self.root, bg='#F4E7E1')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.power_label = tk.Label(
            main_frame,
            text='--',
            font=('Helvetica', 72),
            bg='#F4E7E1',
            fg='#521C0D',
        )
        self.power_label.pack(pady=(10, 0))

        history_frame = tk.Frame(main_frame, bg='#F4E7E1')
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(36, 0))

        history_container = tk.Frame(history_frame, bg='#F4E7E1')
        history_container.pack(fill=tk.BOTH, expand=True, anchor='center')

        history_scrollbar = tk.Scrollbar(history_container)

        self.history_text = tk.Text(
            history_container,
            bg='#F4E7E1',
            fg='#8A939C',
            font=('Helvetica', 48),
            wrap=tk.WORD,
            yscrollcommand=history_scrollbar.set,
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
            state=tk.DISABLED,
            height=1,
            width=5,
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        history_scrollbar.config(command=self.history_text.yview)

        self.history_text_tag = 'center'
        self.history_text.tag_config(self.history_text_tag, justify=tk.CENTER)

        self.load_icons()
        self.close_label.config(image=self.icon_images['off'])
        self.set_scanning_icon()
        self.set_status_icon('disconnected')

    def load_icons(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_images = {
            'off': tk.PhotoImage(file=os.path.join(base_dir, 'off.png')),
            'link': tk.PhotoImage(file=os.path.join(base_dir, 'link.png')),
            'alert': tk.PhotoImage(file=os.path.join(base_dir, 'alert.png')),
            'link-off': tk.PhotoImage(file=os.path.join(base_dir, 'link-off.png')),
            'connected': tk.PhotoImage(file=os.path.join(base_dir, 'connected.png')),
            'disconnected': tk.PhotoImage(file=os.path.join(base_dir, 'disconnected.png')),
        }

    def set_icon(self, name: str, blink: bool = False):
        self.root.after(0, lambda: self._set_icon_main(name, blink))

    def set_status_icon(self, name: str):
        icon = self.icon_images.get(name)
        self.root.after(0, lambda: self.icon_label2.config(image=icon, text=''))

    def _set_icon_main(self, name: str, blink: bool = False):
        self.stop_blink()
        if blink:
            self.blink_state = False
            self._blink_icon(name)
        else:
            icon = self.icon_images.get(name)
            self.icon_label.config(image=icon, text='')

    def _blink_icon(self, name: str):
        if self.stop_event.is_set():
            return
        icon = self.icon_images.get(name)
        if self.blink_state:
            self.icon_label.config(image=icon, text='')
        else:
            self.icon_label.config(image='', text='')
        self.blink_state = not self.blink_state
        self.blink_job = self.root.after(500, lambda: self._blink_icon(name))

    def stop_blink(self):
        if self.blink_job is not None:
            self.root.after_cancel(self.blink_job)
            self.blink_job = None
        self.blink_state = False

    def set_scanning_icon(self):
        self.set_icon('link', blink=True)

    def set_connected_icon(self):
        self.set_icon('link', blink=False)

    def set_error_icon(self):
        self.set_icon('alert', blink=False)

    def set_disconnected_icon(self):
        self.set_icon('link-off', blink=False)

    def schedule_reconnect(self):
        if not self.stop_event.is_set():
            self.root.after(1000, self.start_ble)

    def start_ble(self):
        if self.ble_thread and self.ble_thread.is_alive():
            return
        self.set_scanning_icon()
        self.ble_thread = threading.Thread(target=self.ble_worker, daemon=True)
        self.ble_thread.start()

    def update_power_value(self, value: int):
        self.power_value = value
        color = self.get_power_color(value)
        self.root.after(0, lambda: self.power_label.config(text=f'{value}', fg=color))
        if value != 0:
            self.add_history_entry(f'{value}')

    def get_power_color(self, value: int) -> str:
        if value <= 5000:
            return '#521C0D'
        if value <= 7000:
            return '#7B3A17'
        if value <= 10000:
            return '#B25A24'
        if value <= 12000:
            return '#E47A32'
        return '#FF9B45'

    def add_history_entry(self, entry: str):
        self.history_text.config(state=tk.NORMAL)
        start = '1.0'
        self.history_text.insert(start, entry + '\n')
        self.history_text.tag_add(self.history_text_tag, start, self.history_text.index('1.0 lineend'))
        self.history_text.see('1.0')
        self.history_text.config(state=tk.DISABLED)

    def ble_worker(self):
        try:
            asyncio.run(self.ble_main())
        except Exception:
            self.set_error_icon()

    async def ble_main(self):
        target_device = None
        while not target_device and not self.stop_event.is_set():
            devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
            target_device = next(
                (device for device in devices if device.name == 'BEYBLADE_TOOL01'),
                None,
            )
            if not target_device:
                await asyncio.sleep(1)

        if self.stop_event.is_set() or not target_device:
            return

        self.set_connected_icon()
        
        try:
            async with BleakClient(
                target_device.address, 
                disconnected_callback=lambda c: self.on_ble_disconnect()
            ) as client:
                
                if not client.is_connected:
                    self.set_error_icon()
                    return

                self.set_connected_icon()
                await client.start_notify(BEY_DATA_CHAR_UUID, self.notification_handler)

                # 定時檢查 stop_event，若外部要求關閉，則跳出迴圈
                while client.is_connected and not self.stop_event.is_set():
                    await asyncio.sleep(0.2)

                # 當跳出迴圈（代表使用者關閉程式或手動關閉），確保執行停止通知
                await client.stop_notify(BEY_DATA_CHAR_UUID)
                
        except Exception as e:
            print(f"BLE 異常: {e}")
            self.set_error_icon()
            if not self.stop_event.is_set():
                self.schedule_reconnect()

    def notification_handler(self, sender, data: bytearray):
        if data[0] == 0xB5:
            value = int.from_bytes(data[15:17], byteorder='little')
            self.update_power_value(value)
        if data[0] == 0xA0:
            if len(data) >= 4:
                if data[3] != 0x00:
                    self.set_status_icon('connected')
                    self.update_power_value(0)
                else:
                    self.set_status_icon('disconnected')

    def close_app(self):
        # 1. 設定停止旗標，讓 ble_main 內部的迴圈看見並準備退出
        self.stop_event.set()
        self.stop_blink()
        
        # 2. 建立一個安全關閉的檢查函式（避免阻塞 Tkinter 主執行緒）
        def wait_and_exit():
            if self.ble_thread and self.ble_thread.is_alive():
                # 如果藍牙執行緒還活著，等它最多 2 秒（讓它跑完 disconnect）
                print("正在等待藍牙執行緒安全關閉...")
                self.ble_thread.join(timeout=2.0)
            
            # 3. 藍牙安全釋放後，回到主執行緒關閉視窗
            print("所有資源釋放完畢，關閉視窗。")
            self.root.after(0, self.root.destroy)

        # 開一個臨時執行緒去等待，才不會讓 GUI 畫面在點擊關閉時瞬間凍結卡死
        threading.Thread(target=wait_and_exit, daemon=True).start()


def main():
    root = tk.Tk()
    app = RaspberryPiApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
