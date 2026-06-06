"""LiveSubtitle Windows: 实时英文识别 + 中文翻译，全离线。"""
import json
import os
import queue
import sys
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
import tkinter as tk

import vosk
vosk.SetLogLevel(-1)

import argostranslate.package
import argostranslate.translate


# ---------- 资源路径（兼容 PyInstaller） ----------
def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, rel)


VOSK_MODEL_DIR = resource_path("models/vosk-en")
ARGOS_PKG_DIR = resource_path("argos-packages")


# ---------- 首次启动：把内置 argos 包安装到用户目录 ----------
def ensure_argos_installed() -> None:
    appdata = Path(os.environ.get("APPDATA", str(Path.home())))
    flag = appdata / "LiveSubtitle" / "argos-en_zh.installed"
    flag.parent.mkdir(parents=True, exist_ok=True)
    if flag.exists():
        return
    if not os.path.isdir(ARGOS_PKG_DIR):
        return
    for f in os.listdir(ARGOS_PKG_DIR):
        if f.endswith(".argosmodel"):
            argostranslate.package.install_from_path(os.path.join(ARGOS_PKG_DIR, f))
    flag.touch()


# ---------- ASR ----------
class Recognizer:
    SAMPLE_RATE = 16000

    def __init__(self, on_partial, on_final, on_error):
        self.on_partial = on_partial
        self.on_final = on_final
        self.on_error = on_error
        self.model = vosk.Model(VOSK_MODEL_DIR)
        self.rec = vosk.KaldiRecognizer(self.model, self.SAMPLE_RATE)
        self.gain = 5.0
        self._stream = None
        self._running = False

    def set_gain(self, g: float) -> None:
        self.gain = max(1.0, min(30.0, float(g)))

    def _callback(self, indata, frames, time_info, status):
        if status:
            # 丢点采样不致命
            pass
        if not self._running:
            return
        # indata: int16 (frames, channels)
        if indata.ndim > 1:
            mono = indata[:, 0]
        else:
            mono = indata
        x = mono.astype(np.float32) / 32768.0
        if self.gain != 1.0:
            y = x * self.gain
            y = y / (1.0 + np.abs(y))  # 软限幅
        else:
            y = x
        out = (y * 32767.0).astype(np.int16).tobytes()
        try:
            if self.rec.AcceptWaveform(out):
                r = json.loads(self.rec.Result())
                t = (r.get("text") or "").strip()
                if t:
                    self.on_final(t)
            else:
                r = json.loads(self.rec.PartialResult())
                t = (r.get("partial") or "").strip()
                if t:
                    self.on_partial(t)
        except Exception as e:
            self.on_error(str(e))

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        try:
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=2000,
                callback=self._callback,
            )
            self._stream.start()
        except Exception:
            self._running = False
            raise

    def stop(self) -> None:
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        # 重置识别器，避免下一次拿到旧累积
        self.rec = vosk.KaldiRecognizer(self.model, self.SAMPLE_RATE)


# ---------- 翻译 ----------
class Translator:
    def __init__(self):
        self._cache_in = ""
        self._cache_out = ""

    def translate(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        if text == self._cache_in:
            return self._cache_out
        try:
            r = argostranslate.translate.translate(text, "en", "zh")
        except Exception as e:
            return f"翻译失败: {e}"
        self._cache_in = text
        self._cache_out = r or ""
        return self._cache_out


# ---------- UI ----------
class App:
    BG = "#000000"
    FG_PRIMARY = "#ffffff"
    FG_SECONDARY = "#bbbbbb"
    FG_DIM = "#999999"

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("LiveSubtitle")
        root.configure(bg=self.BG)
        root.attributes("-topmost", True)
        root.overrideredirect(True)        # 无标题栏
        root.attributes("-alpha", 0.82)     # 整体半透明

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w, h = 600, 200
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{sh - h - 80}")
        root.minsize(280, 80)

        # 容器
        outer = tk.Frame(root, bg=self.BG, bd=0, highlightthickness=0)
        outer.pack(fill="both", expand=True)

        # 标题栏
        title = tk.Frame(outer, bg=self.BG, height=32)
        title.pack(fill="x", side="top")
        title.pack_propagate(False)

        self.btn_mic = tk.Button(
            title, text="●", bg=self.BG, fg="#ff5555", activebackground=self.BG,
            relief="flat", bd=0, font=("Segoe UI Symbol", 14),
            command=self.toggle_mic, cursor="hand2",
        )
        self.btn_mic.pack(side="left", padx=(10, 6))

        self.lbl_status = tk.Label(
            title, text="未启动 · 点圆点开始", bg=self.BG, fg=self.FG_SECONDARY,
            font=("Microsoft YaHei", 9),
        )
        self.lbl_status.pack(side="left")

        self.btn_close = tk.Button(
            title, text="✕", bg=self.BG, fg=self.FG_SECONDARY, activebackground=self.BG,
            relief="flat", bd=0, font=("Segoe UI", 11),
            command=root.destroy, cursor="hand2",
        )
        self.btn_close.pack(side="right", padx=(4, 10))

        self.gain_var = tk.DoubleVar(value=5.0)
        self.lbl_gain = tk.Label(
            title, text="增益 5.0x", bg=self.BG, fg=self.FG_SECONDARY,
            font=("Microsoft YaHei", 9), width=10, anchor="e",
        )
        self.lbl_gain.pack(side="right")
        self.scale_gain = tk.Scale(
            title, from_=1, to=30, resolution=0.5, orient="horizontal",
            variable=self.gain_var, showvalue=False, length=130,
            bg=self.BG, fg=self.FG_SECONDARY, troughcolor="#333333",
            highlightthickness=0, bd=0, sliderlength=14, sliderrelief="flat",
            command=self.on_gain_changed,
        )
        self.scale_gain.pack(side="right", padx=4)

        # 字幕区
        body = tk.Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True, padx=12, pady=(2, 6))

        self.lbl_en = tk.Label(
            body, text="（点击红圆点开始监听英文）",
            bg=self.BG, fg=self.FG_DIM, font=("Segoe UI", 10),
            wraplength=580, justify="left", anchor="nw",
        )
        self.lbl_en.pack(fill="x", pady=(2, 4))

        self.lbl_zh = tk.Label(
            body, text="",
            bg=self.BG, fg=self.FG_PRIMARY, font=("Microsoft YaHei", 14, "bold"),
            wraplength=580, justify="left", anchor="nw",
        )
        self.lbl_zh.pack(fill="both", expand=True)

        # 拖动整窗
        for w_ in (outer, title, body, self.lbl_en, self.lbl_zh, self.lbl_status):
            w_.bind("<Button-1>", self._drag_start)
            w_.bind("<B1-Motion>", self._drag_motion)

        # 右下角缩放手柄
        self.grip = tk.Label(
            outer, text="◢", bg=self.BG, fg="#666666",
            font=("Segoe UI Symbol", 12), cursor="size_nw_se",
        )
        self.grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
        self.grip.bind("<Button-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_motion)

        # 跟随窗口宽度调字幕换行
        root.bind("<Configure>", self._on_configure)

        # 后端
        self._q: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._partial_text = ""
        self._final_text = ""
        self._displayed_en = ""
        self._last_translated_en = ""
        self.translator = Translator()
        self.recognizer = Recognizer(self._on_partial, self._on_final, self._on_error)
        self.is_listening = False

        # 周期任务
        self.root.after(50, self._poll)
        self.root.after(450, self._translate_tick)

    # ---- 拖动 ----
    def _drag_start(self, e):
        self._drag_dx = e.x_root - self.root.winfo_x()
        self._drag_dy = e.y_root - self.root.winfo_y()

    def _drag_motion(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_dx}+{e.y_root - self._drag_dy}")

    # ---- 缩放 ----
    def _resize_start(self, e):
        self._rs = (e.x_root, e.y_root, self.root.winfo_width(), self.root.winfo_height())

    def _resize_motion(self, e):
        sx, sy, sw, sh = self._rs
        nw = max(280, sw + (e.x_root - sx))
        nh = max(80, sh + (e.y_root - sy))
        self.root.geometry(f"{nw}x{nh}")

    def _on_configure(self, e):
        try:
            wrap = max(120, e.width - 28)
            self.lbl_en.configure(wraplength=wrap)
            self.lbl_zh.configure(wraplength=wrap)
        except Exception:
            pass

    # ---- 增益 ----
    def on_gain_changed(self, v):
        g = float(v)
        self.recognizer.set_gain(g)
        self.lbl_gain.configure(text=f"增益 {g:.1f}x")

    # ---- 麦克风开关 ----
    def toggle_mic(self):
        if self.is_listening:
            self.is_listening = False
            self.recognizer.stop()
            self.lbl_status.configure(text="已停止 · 点圆点继续")
            self.btn_mic.configure(fg="#ff5555")
        else:
            try:
                self.recognizer.start()
            except Exception as e:
                self.lbl_status.configure(text=f"启动失败：{e}")
                return
            self.is_listening = True
            self.lbl_status.configure(text="正在监听（离线）")
            self.btn_mic.configure(fg="#33dd66")

    # ---- ASR 回调（在采音线程里跑） ----
    def _on_partial(self, text: str):
        self._q.put(("partial", text))

    def _on_final(self, text: str):
        self._q.put(("final", text))

    def _on_error(self, msg: str):
        self._q.put(("error", msg))

    def _poll(self):
        try:
            while True:
                kind, text = self._q.get_nowait()
                if kind == "partial":
                    self._partial_text = text
                    show = (self._final_text + " " + text).strip() if self._final_text else text
                    self._displayed_en = show
                    self.lbl_en.configure(text=show)
                elif kind == "final":
                    self._final_text = text
                    self._partial_text = ""
                    self._displayed_en = text
                    self.lbl_en.configure(text=text)
                elif kind == "error":
                    self.lbl_status.configure(text=f"识别异常：{text}")
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    # ---- 翻译节流 ----
    def _translate_tick(self):
        text = self._displayed_en
        if text and text != self._last_translated_en and not text.startswith("（"):
            self._last_translated_en = text
            threading.Thread(target=self._do_translate, args=(text,), daemon=True).start()
        self.root.after(450, self._translate_tick)

    def _do_translate(self, text: str):
        r = self.translator.translate(text)
        self.root.after(0, lambda: self.lbl_zh.configure(text=r))


def main():
    try:
        ensure_argos_installed()
    except Exception as e:
        print(f"[warn] ensure_argos_installed: {e}", file=sys.stderr)
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
