"""Convertidor a Markdown - convierte Word, Excel, PDF, PowerPoint e imagenes a .md"""
import os
import sys
import threading
import queue
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from markitdown import MarkItDown

APP_TITLE = "Convertidor a Markdown"
SUPPORTED_EXT = {
    ".docx", ".doc", ".xlsx", ".xls", ".xlsm", ".pptx", ".ppt", ".pdf",
    ".csv", ".html", ".htm", ".json", ".xml", ".txt",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
}

BG = "#f4f6fa"
PANEL = "#ffffff"
ACCENT = "#2455a4"
ACCENT_DARK = "#1b3f7d"
TEXT = "#1e2530"
MUTED = "#6b7280"
OK_COLOR = "#1a7f4b"
ERR_COLOR = "#c0392b"


class ConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x560")
        self.root.minsize(640, 480)
        self.root.configure(bg=BG)

        self.files: list[str] = []
        self.dest_dir = str(Path.home() / "Documents")
        self.queue: "queue.Queue" = queue.Queue()
        self.converting = False

        self._build_style()
        self._build_ui()
        self.root.after(100, self._poll_queue)

    # ---------- UI ----------
    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 18))
        style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Muted.Panel.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))

        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                         font=("Segoe UI Semibold", 10), padding=(14, 8), borderwidth=0)
        style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("disabled", "#a9b7cc")])

        style.configure("Ghost.TButton", background=PANEL, foreground=ACCENT,
                         font=("Segoe UI", 9), padding=(10, 6), borderwidth=1)
        style.map("Ghost.TButton", background=[("active", "#eaf0fb")])

        style.configure("Chip.TButton", background="#eef1f6", foreground=TEXT,
                         font=("Segoe UI", 9), padding=(12, 7), borderwidth=0)
        style.map("Chip.TButton", background=[("active", "#e0e5ee")])

        style.configure("ChipActive.TButton", background=ACCENT, foreground="white",
                         font=("Segoe UI Semibold", 9), padding=(12, 7), borderwidth=0)
        style.map("ChipActive.TButton", background=[("active", ACCENT_DARK)])

        style.configure("TProgressbar", background=ACCENT, troughcolor="#e4e8f0",
                         bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)

    def _build_ui(self):
        pad = 18

        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=pad, pady=(pad, 8))
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Word, Excel, PowerPoint, PDF e imagenes -> Markdown, en un click.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        # File actions
        actions = ttk.Frame(self.root, style="TFrame")
        actions.pack(fill="x", padx=pad, pady=(6, 8))
        ttk.Button(actions, text="+ Agregar archivos", style="Accent.TButton",
                   command=self.add_files).pack(side="left")
        ttk.Button(actions, text="+ Agregar carpeta", style="Ghost.TButton",
                   command=self.add_folder).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Quitar seleccionado", style="Ghost.TButton",
                   command=self.remove_selected).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Limpiar lista", style="Ghost.TButton",
                   command=self.clear_files).pack(side="left", padx=(8, 0))

        # File list panel
        list_panel = ttk.Frame(self.root, style="Panel.TFrame")
        list_panel.pack(fill="both", expand=True, padx=pad, pady=(0, 8))

        columns = ("archivo", "estado")
        self.tree = ttk.Treeview(list_panel, columns=columns, show="headings", height=8)
        self.tree.heading("archivo", text="Archivo")
        self.tree.heading("estado", text="Estado")
        self.tree.column("archivo", width=480, anchor="w")
        self.tree.column("estado", width=160, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left", padx=(1, 0), pady=1)

        scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        # Destination
        dest_panel = ttk.Frame(self.root, style="Panel.TFrame")
        dest_panel.pack(fill="x", padx=pad, pady=(0, 8))
        ttk.Label(dest_panel, text="Guardar archivos convertidos en:", style="Panel.TLabel").pack(
            anchor="w", padx=14, pady=(12, 6)
        )

        chips = ttk.Frame(dest_panel, style="Panel.TFrame")
        chips.pack(fill="x", padx=14)
        self.shortcuts = {
            "Escritorio": str(Path.home() / "Desktop"),
            "Documentos": str(Path.home() / "Documents"),
            "Descargas": str(Path.home() / "Downloads"),
        }
        self.chip_buttons: dict[str, ttk.Button] = {}
        for label, path in self.shortcuts.items():
            btn = ttk.Button(chips, text=label, style="Chip.TButton",
                              command=lambda p=path: self.set_dest(p))
            btn.pack(side="left", padx=(0, 6))
            self.chip_buttons[path] = btn
        ttk.Button(chips, text="Examinar...", style="Chip.TButton",
                   command=self.choose_dest).pack(side="left")

        path_row = ttk.Frame(dest_panel, style="Panel.TFrame")
        path_row.pack(fill="x", padx=14, pady=(8, 14))
        ttk.Label(path_row, text="\U0001F4C1", style="Panel.TLabel").pack(side="left")
        self.dest_label = ttk.Label(path_row, text=self.dest_dir, style="Muted.Panel.TLabel")
        self.dest_label.pack(side="left", padx=(6, 0), fill="x", expand=True)

        # Convert row
        convert_frame = ttk.Frame(self.root, style="TFrame")
        convert_frame.pack(fill="x", padx=pad, pady=(0, 6))
        self.convert_btn = ttk.Button(convert_frame, text="Convertir a Markdown", style="Accent.TButton",
                                       command=self.start_conversion)
        self.convert_btn.pack(side="left")
        self.open_dest_btn = ttk.Button(convert_frame, text="Abrir carpeta destino", style="Ghost.TButton",
                                         command=self.open_dest, state="disabled")
        self.open_dest_btn.pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(self.root, mode="determinate", style="TProgressbar")
        self.progress.pack(fill="x", padx=pad, pady=(4, 8))

        self.status_var = tk.StringVar(value="Listo.")
        ttk.Label(self.root, textvariable=self.status_var, style="Subtitle.TLabel").pack(
            anchor="w", padx=pad, pady=(0, pad)
        )

        self.set_dest(self.dest_dir)

    # ---------- File list handling ----------
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos",
            filetypes=[
                ("Todos los soportados", " ".join(f"*{e}" for e in sorted(SUPPORTED_EXT))),
                ("Todos los archivos", "*.*"),
            ],
        )
        self._add_paths(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if not folder:
            return
        found = []
        for root_dir, _dirs, filenames in os.walk(folder):
            for name in filenames:
                if Path(name).suffix.lower() in SUPPORTED_EXT:
                    found.append(os.path.join(root_dir, name))
        self._add_paths(found)

    def _add_paths(self, paths):
        added = 0
        for p in paths:
            if p not in self.files and Path(p).suffix.lower() in SUPPORTED_EXT:
                self.files.append(p)
                self.tree.insert("", "end", iid=p, values=(os.path.basename(p), "Pendiente"))
                added += 1
        if added:
            self.status_var.set(f"{added} archivo(s) agregado(s). Total: {len(self.files)}.")

    def remove_selected(self):
        for item in self.tree.selection():
            self.tree.delete(item)
            if item in self.files:
                self.files.remove(item)

    def clear_files(self):
        self.tree.delete(*self.tree.get_children())
        self.files.clear()
        self.status_var.set("Lista vacia.")

    def choose_dest(self):
        folder = filedialog.askdirectory(title="Elegir carpeta destino", initialdir=self.dest_dir)
        if folder:
            self.set_dest(folder)

    def set_dest(self, folder: str):
        self.dest_dir = folder
        self.dest_label.configure(text=self.dest_dir)
        for path, btn in self.chip_buttons.items():
            btn.configure(style="ChipActive.TButton" if os.path.normcase(path) == os.path.normcase(folder)
                          else "Chip.TButton")

    def open_dest(self):
        if os.path.isdir(self.dest_dir):
            os.startfile(self.dest_dir)

    # ---------- Conversion ----------
    def start_conversion(self):
        if self.converting:
            return
        if not self.files:
            messagebox.showinfo(APP_TITLE, "Agrega al menos un archivo para convertir.")
            return

        Path(self.dest_dir).mkdir(parents=True, exist_ok=True)

        self.converting = True
        self.convert_btn.configure(state="disabled")
        self.open_dest_btn.configure(state="disabled")
        self.progress.configure(maximum=len(self.files), value=0)
        self.status_var.set("Convirtiendo...")

        thread = threading.Thread(target=self._convert_worker, daemon=True)
        thread.start()

    def _convert_worker(self):
        md = MarkItDown()
        for path in list(self.files):
            name = os.path.basename(path)
            try:
                result = md.convert(path)
                out_name = Path(name).stem + ".md"
                out_path = Path(self.dest_dir) / out_name
                out_path = self._unique_path(out_path)
                out_path.write_text(result.markdown, encoding="utf-8")
                self.queue.put(("ok", path, str(out_path)))
            except Exception as exc:  # noqa: BLE001
                self.queue.put(("error", path, str(exc)))
        self.queue.put(("done", None, None))

    @staticmethod
    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        stem, suffix = path.stem, path.suffix
        i = 2
        while True:
            candidate = path.with_name(f"{stem} ({i}){suffix}")
            if not candidate.exists():
                return candidate
            i += 1

    def _poll_queue(self):
        try:
            while True:
                kind, path, info = self.queue.get_nowait()
                if kind == "ok":
                    self.tree.set(path, "estado", "OK")
                    self.tree.tag_configure("ok", foreground=OK_COLOR)
                    self.tree.item(path, tags=("ok",))
                    self.progress.step(1)
                elif kind == "error":
                    self.tree.set(path, "estado", "Error")
                    self.tree.tag_configure("error", foreground=ERR_COLOR)
                    self.tree.item(path, tags=("error",))
                    self.progress.step(1)
                elif kind == "done":
                    self.converting = False
                    self.convert_btn.configure(state="normal")
                    self.open_dest_btn.configure(state="normal")
                    ok = sum(1 for i in self.tree.get_children() if self.tree.set(i, "estado") == "OK")
                    err = sum(1 for i in self.tree.get_children() if self.tree.set(i, "estado") == "Error")
                    self.status_var.set(f"Listo: {ok} convertido(s), {err} con error.")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(str(Path(__file__).with_name("icon.ico")))
    except Exception:
        pass
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
