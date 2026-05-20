# Raspberry Pi Zero W - Tkinter GUI 應用

簡單的全螢幕 Tkinter 應用程式，適用於 Raspberry Pi Zero W。

## 需求

- Raspberry Pi Zero W
- Python 3.x
- tkinter (Python標準庫)

## 安裝

### Raspberry Pi 上的安裝步驟

1. **更新系統**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

2. **安裝 Python3 和 tkinter**
   ```bash
   sudo apt-get install python3 python3-tk
   ```

3. **安裝項目依賴** (如需要)
   ```bash
   pip3 install -r requirements.txt
   ```

## 運行應用

### 普通模式
```bash
python3 main.py
```

### 全螢幕模式（生產環境）
```bash
python3 main.py
```

或使用 X11 運行：
```bash
DISPLAY=:0 python3 main.py
```

## 功能說明

- **全螢幕顯示**：應用程式以全螢幕模式運行
- **螢幕尺寸**：480×320 像素（適合 Raspberry Pi 的小螢幕）
- **居中文字**："Hello World" 文本在螢幕中央
- **關閉按鈕**：紅色 ✕ 按鈕在右上角，點擊可退出應用

## 開機自啟

若要在 Raspberry Pi 開機時自動運行此應用，編輯 `/etc/rc.local`：

```bash
sudo nano /etc/rc.local
```

在 `exit 0` 前添加：
```bash
su - pi -c "DISPLAY=:0 python3 /home/pi/path/to/main.py &"
```

## 退出應用

- 點擊右上角的關閉按鈕 ✕
- 或按 Alt+F4（如果窗口管理器支持）
- 或從終端按 Ctrl+C
