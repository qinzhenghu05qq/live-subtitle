# LiveSubtitle (Windows)

实时英文识别 + 中文翻译，**完全离线**、装上即用。Mac 版的 Windows 平替。

- ASR：Vosk 英文小模型（设备端流式）
- 翻译：Argos Translate（en → zh，离线 NMT）
- UI：Tkinter 浮窗，置顶 / 半透明 / 可拖 / 可缩放 / 麦克风增益 1×–30× 软限幅

> 体积：安装包约 200–300 MB（已包含两份模型，分发对象**无需联网**）。

---

## 一键打包（在 Windows 机器上执行一次）

### 1. 准备环境（只需一次）

- **Python 3.10 / 3.11 / 3.12**：到 https://www.python.org/downloads/windows/ 安装 64-bit 版，**勾选** "Add python.exe to PATH" 与 "py launcher"。
- **Inno Setup 6**：到 https://jrsoftware.org/isinfo.php 安装。安装包就是它生成的。

### 2. 把整个 `live-subtitle-win` 目录拷到 Windows 机上，双击 `build.bat`

脚本会自动：

1. 建虚拟环境 `.venv`
2. 安装依赖（vosk / sounddevice / numpy / argostranslate / pyinstaller）
3. 联网下载 Vosk 英文模型 (~40 MB) + Argos en→zh 模型 (~110 MB) 到本地
4. 用 PyInstaller 把所有东西（含模型）打成 `dist\LiveSubtitle\`
5. 用 Inno Setup 把上一步的产物压成单个安装包 `dist\LiveSubtitleSetup.exe`

完成后把 `dist\LiveSubtitleSetup.exe` 发给别人。**对方双击安装、运行即可，全程不联网。**

> 如果没装 Inno Setup，脚本会跳过最后一步，把可移植版输出到 `dist\LiveSubtitle\`，整个目录打包成 zip 也能发别人（解压后双击 `LiveSubtitle.exe`）。

---

## 使用

1. 启动后桌面下方出现一条半透明黑色字幕条。
2. 点击左上角红色圆点 → 开始监听（变绿）。Windows 第一次会弹麦克风权限，允许。
3. 上排灰字 = 英文识别；下排白字 = 中文翻译。
4. 拖空白处可移动；右下角 ◢ 可拖拽缩放；标题栏滑块调麦克风增益（远场对话调高）。
5. 点 ✕ 关闭。

---

## 故障排查

- **弹"找不到麦克风"**：Windows 设置 → 隐私 → 麦克风 → 允许桌面应用使用麦克风。
- **识别一直没反应**：确认正在对的麦克风（Windows 任务栏喇叭图标 → 设置 → 输入设备），把增益拉高试试。
- **首次启动卡几秒**：Argos 在 `%APPDATA%\LiveSubtitle\` 写一个标志、把内置模型注册到 `%LOCALAPPDATA%\argos-translate\` 是一次性的，再启动就快。
- **Defender / SmartScreen 警告**：因为没有花钱买代码签名证书，Windows 会提示"未知发布者"。点"更多信息"→"仍要运行"即可，分发给同事时记得告诉他们这一步。

---

## 文件清单

```
live-subtitle-win/
├── app.py                  # 主程序
├── requirements.txt        # Python 依赖
├── download_models.py      # 打包前预下载 Vosk + Argos 模型
├── LiveSubtitle.spec       # PyInstaller 配置
├── installer.iss           # Inno Setup 配置
├── build.bat               # 一键打包脚本
└── README.md               # 本文件
```
