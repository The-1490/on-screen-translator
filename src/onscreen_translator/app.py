"""Tkinter GUI: live screen region, image, video, text."""
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
from . import pipeline, translate

TICK_MS = 1500


class RegionPicker(tk.Toplevel):
    def __init__(self, master, on_done):
        super().__init__(master)
        self.on_done = on_done
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.attributes("-topmost", True)
        self.configure(bg="black", cursor="cross")
        self.c = tk.Canvas(self, bg="black", highlightthickness=0)
        self.c.pack(fill="both", expand=True)
        self.c.bind("<ButtonPress-1>", self.down)
        self.c.bind("<B1-Motion>", self.move)
        self.c.bind("<ButtonRelease-1>", self.up)
        self.bind("<Escape>", lambda e: self._cancel())
        self.focus_force()
        self.r = None

    def _cancel(self):
        self.destroy()
        self.on_done(None)

    def down(self, e):
        self.x0, self.y0 = e.x_root, e.y_root
        self.r = self.c.create_rectangle(e.x, e.y, e.x, e.y, outline="red", width=2)

    def move(self, e):
        if self.r:
            self.c.coords(self.r, self.x0 - self.winfo_rootx(), self.y0 - self.winfo_rooty(), e.x, e.y)

    def up(self, e):
        if not self.r:
            return
        x1, y1 = min(self.x0, e.x_root), min(self.y0, e.y_root)
        w, h = abs(e.x_root - self.x0), abs(e.y_root - self.y0)
        self.destroy()
        self.on_done({"left": x1, "top": y1, "width": w, "height": h} if w > 20 and h > 20 else None)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("On-Screen Translator (any -> English)")
        self.geometry("900x650")
        bar = tk.Frame(self)
        bar.pack(fill="x", padx=6, pady=6)
        for text, cmd in [("Select screen region (live)", self.pick), ("Stop live", self.stop),
                          ("Open image", self.open_image), ("Open video", self.open_video),
                          ("Translate text box", self.translate_text)]:
            tk.Button(bar, text=text, command=cmd).pack(side="left", padx=3)
        self.status = tk.StringVar(value="Ready. First use of a language downloads its pack (internet needed once).")
        tk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=6)
        self.view = tk.Label(self, bg="#222")
        self.view.pack(fill="both", expand=True, padx=6, pady=4)
        self.text = scrolledtext.ScrolledText(self, height=7)
        self.text.pack(fill="x", padx=6, pady=4)
        self.region, self.live, self.busy = None, False, False

    def show(self, img):
        img = img.copy()
        img.thumbnail((max(self.view.winfo_width(), 400), max(self.view.winfo_height(), 300)))
        self._tk = ImageTk.PhotoImage(img)
        self.view.configure(image=self._tk)

    def run_bg(self, fn, done):
        def work():
            try:
                r = fn()
            except Exception as ex:
                r = ex
            self.after(0, lambda: done(r))
        threading.Thread(target=work, daemon=True).start()

    def pick(self):
        self.live = False
        self.withdraw()
        self.after(250, lambda: RegionPicker(self, self._picked))

    def _picked(self, region):
        self.deiconify()
        if not region:
            self.status.set("Selection cancelled.")
            return
        self.region, self.live = region, True
        self.status.set("Live translating region... (move this window away from the region)")
        self.tick()

    def stop(self):
        self.live = False
        self.status.set("Stopped.")

    def tick(self):
        if not self.live:
            return
        if not self.busy:
            self.busy = True

            def grab():
                import mss
                with mss.mss() as s:
                    sh = s.grab(self.region)
                return pipeline.translate_image(Image.frombytes("RGB", sh.size, sh.bgra, "raw", "BGRX"))

            def done(r):
                self.busy = False
                if isinstance(r, Exception):
                    self.status.set("Error: %s" % r)
                    return
                self.show(r[0])
                self.log(r[1])
            self.run_bg(grab, done)
        self.after(TICK_MS, self.tick)

    def log(self, pairs):
        self.text.delete("1.0", "end")
        for o, e in pairs:
            self.text.insert("end", "%s  ->  %s\n" % (o, e))

    def open_image(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if not p:
            return
        self.status.set("Translating image...")

        def done(r):
            if isinstance(r, Exception):
                messagebox.showerror("Error", str(r))
                return
            self.show(r[0])
            self.log(r[1])
            self.status.set("Done.")
            if messagebox.askyesno("Save", "Save translated image?"):
                f = filedialog.asksaveasfilename(defaultextension=".png")
                if f:
                    r[0].save(f)
        self.run_bg(lambda: pipeline.translate_image(Image.open(p)), done)

    def open_video(self):
        p = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov *.webm")])
        if not p:
            return
        dst = filedialog.asksaveasfilename(defaultextension=".mp4", title="Save translated video as")
        if not dst:
            return
        self.status.set("Translating video (can take a while)...")

        def prog(i):
            self.after(0, lambda: self.status.set("Translating video... frame %d" % i))

        def done(r):
            if isinstance(r, Exception):
                messagebox.showerror("Error", str(r))
                self.status.set("Failed.")
            else:
                self.status.set("Done: %d frames -> %s" % (r, dst))
        self.run_bg(lambda: pipeline.translate_video(p, dst, progress=prog), done)

    def translate_text(self):
        t = self.text.get("1.0", "end").strip()
        if not t:
            return
        self.status.set("Translating text...")

        def done(r):
            self.status.set("Done.")
            if isinstance(r, Exception):
                messagebox.showerror("Error", str(r))
            else:
                self.text.insert("end", "\n\n[English]\n" + r)
        self.run_bg(lambda: translate.to_english(t), done)


def main():
    App().mainloop()
