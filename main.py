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
        self.max_value = None
        self.ble_thread = None
        self.blink_job = None
        self.blink_state = False

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
        top_frame = tk.Frame(self.root, bg='white', height=56)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        top_frame.pack_propagate(False)

        icon_frame = tk.Frame(top_frame, bg='white', width=48, height=48)
        icon_frame.pack(side=tk.LEFT)
        icon_frame.pack_propagate(False)

        self.icon_label = tk.Label(
            icon_frame,
            bg='white',
            width=48,
            height=48,
        )
        self.icon_label.pack(fill=tk.BOTH, expand=True)

        icon_frame2 = tk.Frame(top_frame, bg='white', width=48, height=48)
        icon_frame2.pack(side=tk.LEFT, padx=(8, 0))
        icon_frame2.pack_propagate(False)

        self.icon_label2 = tk.Label(
            icon_frame2,
            bg='white',
            width=48,
            height=48,
        )
        self.icon_label2.pack(fill=tk.BOTH, expand=True)

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

        status_font = font.Font(family='Helvetica', size=18)
        self.max_label = tk.Label(
            main_frame,
            text='等待資料...',
            font=status_font,
            bg='white',
            fg='black',
        )
        self.max_label.pack(pady=(10, 0))

        self.load_icons()
        self.set_scanning_icon()
        self.set_status_icon('disconnected')

    def load_icons(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_images = {
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
            self.root.after(5000, self.start_ble)

    def start_ble(self):
        if self.ble_thread and self.ble_thread.is_alive():
            return
        self.set_scanning_icon()
        self.ble_thread = threading.Thread(target=self.ble_worker, daemon=True)
        self.ble_thread.start()

    def update_max_value(self, value: int):
        self.max_value = value
        self.root.after(0, lambda: self.max_label.config(text=f'最大值: {value}'))

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
            if not self.stop_event.is_set():
                self.set_error_icon()
            return

        self.set_connected_icon()
        try:
            async with BleakClient(target_device.address) as client:
                if not client.is_connected:
                    self.set_error_icon()
                    return

                self.set_connected_icon()
                try:
                    await client.start_notify(BEY_DATA_CHAR_UUID, self.notification_handler)
                    print('start_notify: registered for', BEY_DATA_CHAR_UUID)
                    # ensure second status icon reflects connection when notifications start
                    self.set_status_icon('connected')
                except Exception as exc:
                    print('start_notify failed:', exc)
                    self.set_error_icon()
                    if not self.stop_event.is_set():
                        self.root.after(5000, self.start_ble)
                    return

                while client.is_connected and not self.stop_event.is_set():
                    await asyncio.sleep(1)

                if not client.is_connected and not self.stop_event.is_set():
                    self.set_disconnected_icon()
                    self.schedule_reconnect()

                await client.stop_notify(BEY_DATA_CHAR_UUID)
        except Exception:
            self.set_error_icon()
            if not self.stop_event.is_set():
                self.root.after(5000, self.start_ble)

    def notification_handler(self, sender, data: bytearray):
        print('notification_handler called, sender=', sender, 'len=', len(data) if data is not None else 0)
        if not data:
            return
        if 0xB0 <= data[0] <= 0xB5 and len(data) > 2:
            parsed_values = []
            for i in range(1, len(data) - 1, 2):
                parsed_values.append(int.from_bytes(data[i:i + 2], byteorder='little'))

            if parsed_values:
                packet_max = max(parsed_values)
                self.update_max_value(packet_max)
        # secondary connected/disconnected indicator based on 0x00
        if data[0] == 0x00:
            self.set_status_icon('connected')
            self.update_max_value(0)
        else:
            self.set_status_icon('disconnected')

    def close_app(self):
        self.stop_event.set()
        self.stop_blink()
        self.root.quit()


def main():
    root = tk.Tk()
    app = RaspberryPiApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
