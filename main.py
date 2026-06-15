"""
main.py
========
Công cụ xóa chữ trong bong bóng thoại (speech bubble) cho ảnh manga/manhwa.
Giao diện đồ họa (Tkinter) — TOÀN BỘ trong 1 file.

Tính năng:
- Các thanh trượt (slider) để tinh chỉnh trực tiếp các ngưỡng của thuật toán
  phát hiện bong bóng (area, solidity, aspect ratio, độ sáng, độ lệch chuẩn...).
- Nút "Test với 1 ảnh": chọn 1 ảnh trang truyện để xem trước kết quả
  (ảnh gốc / ảnh đã khoanh vùng bong bóng / ảnh đã xóa chữ) ngay khi kéo
  thanh trượt, để tìm bộ số phù hợp trước khi xử lý hàng loạt.
- Nút "Chọn thư mục & xử lý hàng loạt": quét toàn bộ ảnh trong thư mục,
  xử lý với bộ ngưỡng hiện tại và lưu vào thư mục con "output_no_text".

Yêu cầu cài đặt:
    pip install opencv-python pillow numpy

Chạy:
    python main.py
"""

import os
import threading
import queue

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


# ============================================================================
#  THUẬT TOÁN: phát hiện bong bóng thoại & xóa chữ
# ============================================================================

def find_bubbles(gray, img_area, params):
    """Tìm các contour là bong bóng thoại (có chữ bên trong).

    params: dict chứa các ngưỡng:
        canny_lo, canny_hi      - ngưỡng Canny edge
        area_min, area_max_pct  - diện tích tối thiểu (px) và tối đa
                                   (tỉ lệ % so với diện tích ảnh)
        solidity_min            - độ lồi tối thiểu (area / hull_area)
        aspect_min, aspect_max  - tỉ lệ W/H hợp lệ
        mean_min                - độ sáng trung bình tối thiểu bên trong
        std_min                 - độ lệch chuẩn tối thiểu bên trong
    """

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, params["canny_lo"], params["canny_hi"])

    kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edges_d = cv2.dilate(edges, kernel3, iterations=1)

    contours, _ = cv2.findContours(edges_d, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    area_max = img_area * (params["area_max_pct"] / 100.0)

    bubbles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < params["area_min"] or area > area_max:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = area / hull_area
        if solidity < params["solidity_min"]:
            continue

        aspect = w / float(h)
        if aspect < params["aspect_min"] or aspect > params["aspect_max"]:
            continue

        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        region = gray[mask == 255]

        mean_val = region.mean()
        std_val = region.std()

        if mean_val < params["mean_min"]:
            continue
        if std_val < params["std_min"]:
            continue

        bubbles.append(cnt)

    return bubbles


def erase_text(img, bubbles):
    """Xóa chữ trong các bong bóng đã phát hiện, giữ nguyên viền bong bóng."""

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = img.copy()

    fill_mask = np.zeros(gray.shape, dtype=np.uint8)
    for cnt in bubbles:
        cv2.drawContours(fill_mask, [cnt], -1, 255, -1)

    k_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fill_mask_eroded = cv2.erode(fill_mask, k_small, iterations=1)
    result[fill_mask_eroded == 255] = (255, 255, 255)

    ring = cv2.subtract(fill_mask, fill_mask_eroded)
    dark = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)[1]
    text_mask = cv2.bitwise_and(ring, dark)

    k_mid = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    text_mask = cv2.dilate(text_mask, k_mid, iterations=1)
    text_mask = cv2.bitwise_and(text_mask, fill_mask)

    inpainted = cv2.inpaint(result, text_mask, 3, cv2.INPAINT_TELEA)
    final = result.copy()
    final[text_mask == 255] = inpainted[text_mask == 255]

    return final


def draw_debug(img, bubbles):
    dbg = img.copy()
    for cnt in bubbles:
        cv2.drawContours(dbg, [cnt], -1, (0, 0, 255), 2)
    return dbg


def process_image(img, params):
    """Xử lý 1 ảnh (numpy BGR) -> (ảnh kết quả, ảnh debug, số bong bóng)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_area = gray.shape[0] * gray.shape[1]
    bubbles = find_bubbles(gray, img_area, params)
    result = erase_text(img, bubbles)
    dbg = draw_debug(img, bubbles)
    return result, dbg, len(bubbles)


# ============================================================================
#  GUI
# ============================================================================

DEFAULT_PARAMS = {
    "canny_lo": 30,
    "canny_hi": 100,
    "area_min": 3000,
    "area_max_pct": 15.0,   # %
    "solidity_min": 0.85,
    "aspect_min": 0.3,
    "aspect_max": 3.5,
    "mean_min": 200,
    "std_min": 35,
}


class BubbleEraserApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Xóa chữ trong bong bóng thoại - Manga Bubble Eraser")
        self.geometry("1180x780")
        self.minsize(1000, 650)

        # --- state ---
        self.test_image_path = tk.StringVar(value="(chưa chọn ảnh)")
        self.batch_dir = tk.StringVar(value="(chưa chọn thư mục)")
        self.save_debug = tk.BooleanVar(value=False)
        self.status_text = tk.StringVar(value="Sẵn sàng.")

        self.test_img_bgr = None  # ảnh test đang load (numpy)
        self.msg_queue = queue.Queue()

        # sliders sẽ lưu giá trị vào đây
        self.params = {k: tk.DoubleVar(value=v) for k, v in DEFAULT_PARAMS.items()}

        self._build_ui()
        self._poll_queue()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # ====== layout tổng: trái = panel tham số, phải = preview/log ======
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        # -------------------------------------------------------------
        # LEFT: bộ tham số tinh chỉnh
        # -------------------------------------------------------------
        param_box = ttk.LabelFrame(left, text="Tinh chỉnh ngưỡng phát hiện bong bóng", padding=10)
        param_box.pack(fill="x")

        self._add_slider(param_box, "canny_lo", "Canny ngưỡng thấp", 0, 200, 1)
        self._add_slider(param_box, "canny_hi", "Canny ngưỡng cao", 0, 300, 1)
        self._add_slider(param_box, "area_min", "Diện tích tối thiểu (px)", 100, 20000, 100)
        self._add_slider(param_box, "area_max_pct", "Diện tích tối đa (% trang)", 1, 50, 0.5)
        self._add_slider(param_box, "solidity_min", "Độ lồi tối thiểu (solidity)", 0.5, 1.0, 0.01)
        self._add_slider(param_box, "aspect_min", "Tỉ lệ W/H tối thiểu", 0.1, 2.0, 0.05)
        self._add_slider(param_box, "aspect_max", "Tỉ lệ W/H tối đa", 1.0, 6.0, 0.1)
        self._add_slider(param_box, "mean_min", "Độ sáng TB tối thiểu (0-255)", 100, 255, 1)
        self._add_slider(param_box, "std_min", "Độ lệch chuẩn tối thiểu", 0, 100, 1)

        btn_row = ttk.Frame(param_box)
        btn_row.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_row, text="Khôi phục mặc định", command=self.reset_params).pack(side="left")

        # -------------------------------------------------------------
        # LEFT (dưới): khu vực test 1 ảnh
        # -------------------------------------------------------------
        test_box = ttk.LabelFrame(left, text="Test với 1 ảnh trang truyện", padding=10)
        test_box.pack(fill="x", pady=(10, 0))

        ttk.Button(test_box, text="Chọn ảnh để test...", command=self.choose_test_image).pack(fill="x")
        ttk.Label(test_box, textvariable=self.test_image_path, wraplength=280).pack(anchor="w", pady=(4, 4))
        ttk.Button(test_box, text="▶ Test (chạy thuật toán)", command=self.run_test).pack(fill="x")
        self.test_info = ttk.Label(test_box, text="")
        self.test_info.pack(anchor="w", pady=(4, 0))

        # -------------------------------------------------------------
        # LEFT (dưới cùng): xử lý hàng loạt theo thư mục
        # -------------------------------------------------------------
        batch_box = ttk.LabelFrame(left, text="Xử lý hàng loạt theo thư mục", padding=10)
        batch_box.pack(fill="x", pady=(10, 0))

        ttk.Button(batch_box, text="Chọn thư mục ảnh & xử lý...", command=self.choose_and_run_batch).pack(fill="x")
        ttk.Label(batch_box, textvariable=self.batch_dir, wraplength=280).pack(anchor="w", pady=(4, 4))
        ttk.Checkbutton(
            batch_box, text="Xuất thêm ảnh debug (khoanh vùng bong bóng)",
            variable=self.save_debug
        ).pack(anchor="w")

        # -------------------------------------------------------------
        # RIGHT: preview 3 ảnh (gốc / debug / kết quả) + progress + log
        # -------------------------------------------------------------
        preview_box = ttk.LabelFrame(right, text="Xem trước", padding=5)
        preview_box.pack(fill="both", expand=True)

        cols = ttk.Frame(preview_box)
        cols.pack(fill="both", expand=True)

        col_original = ttk.LabelFrame(cols, text="Ảnh gốc")
        col_original.pack(side="left", fill="both", expand=True, padx=2)
        col_debug = ttk.LabelFrame(cols, text="Bong bóng phát hiện")
        col_debug.pack(side="left", fill="both", expand=True, padx=2)
        col_result = ttk.LabelFrame(cols, text="Sau khi xóa chữ")
        col_result.pack(side="left", fill="both", expand=True, padx=2)

        self.label_original = ttk.Label(col_original)
        self.label_original.pack(fill="both", expand=True)
        self.label_debug = ttk.Label(col_debug)
        self.label_debug.pack(fill="both", expand=True)
        self.label_result = ttk.Label(col_result)
        self.label_result.pack(fill="both", expand=True)

        # progress + log + status
        bottom = ttk.Frame(right)
        bottom.pack(fill="x", pady=(10, 0))

        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(fill="x")

        ttk.Label(bottom, textvariable=self.status_text).pack(anchor="w", pady=(5, 5))

        self.log_text = tk.Text(bottom, height=10, state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def _add_slider(self, parent, key, label_text, frm, to, step):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)

        var = self.params[key]
        value_label = ttk.Label(row, width=6, anchor="e")

        def update_label(*_):
            v = var.get()
            if step >= 1:
                value_label.config(text=f"{int(round(v))}")
            else:
                value_label.config(text=f"{v:.2f}")

        ttk.Label(row, text=label_text, width=24).pack(side="left")

        scale = ttk.Scale(
            row, from_=frm, to=to, orient="horizontal",
            variable=var, command=lambda _v: update_label()
        )
        scale.pack(side="left", fill="x", expand=True, padx=5)

        value_label.pack(side="left")
        update_label()

    def reset_params(self):
        for k, v in DEFAULT_PARAMS.items():
            self.params[k].set(v)

    def _get_params_dict(self):
        return {k: var.get() for k, var in self.params.items()}

    # ------------------------------------------------------------- test 1 ảnh
    def choose_test_image(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh trang truyện để test",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Tất cả", "*.*")],
        )
        if not path:
            return

        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Lỗi", f"Không thể đọc ảnh: {path}")
            return

        self.test_image_path.set(path)
        self.test_img_bgr = img
        self._show_image(self.label_original, img)
        self.run_test()

    def run_test(self):
        if self.test_img_bgr is None:
            messagebox.showinfo("Thông báo", "Vui lòng chọn ảnh để test trước.")
            return

        params = self._get_params_dict()
        result, dbg, n_bubbles = process_image(self.test_img_bgr, params)

        self._show_image(self.label_original, self.test_img_bgr)
        self._show_image(self.label_debug, dbg)
        self._show_image(self.label_result, result)

        self.test_info.config(text=f"Phát hiện {n_bubbles} bong bóng thoại.")

    def _show_image(self, label_widget, bgr_img, max_size=340):
        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        w, h = pil_img.size
        scale = min(max_size / w, max_size / h, 1.0)
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        pil_img = pil_img.resize(new_size, Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(pil_img)
        label_widget.configure(image=tk_img)
        label_widget.image = tk_img  # giữ tham chiếu

    # --------------------------------------------------------------- batch
    def choose_and_run_batch(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh cần xử lý")
        if not folder:
            return

        files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith(IMAGE_EXTS)
        )
        if not files:
            messagebox.showinfo("Thông báo", "Không tìm thấy ảnh nào trong thư mục này.")
            return

        out_dir = os.path.join(folder, "output_no_text")
        os.makedirs(out_dir, exist_ok=True)

        self.batch_dir.set(f"{folder}  →  kết quả: {out_dir}")

        if not messagebox.askyesno(
            "Xác nhận",
            f"Tìm thấy {len(files)} ảnh trong:\n{folder}\n\n"
            f"Xử lý với bộ tham số hiện tại và lưu vào:\n{out_dir}\n\nTiếp tục?"
        ):
            return

        params = self._get_params_dict()
        save_debug = self.save_debug.get()

        self.progress.config(value=0, maximum=len(files))
        self._clear_log()

        thread = threading.Thread(
            target=self._process_all,
            args=(folder, out_dir, files, params, save_debug),
            daemon=True,
        )
        thread.start()

    def _process_all(self, in_dir, out_dir, files, params, save_debug):
        total = len(files)
        for idx, filename in enumerate(files, start=1):
            in_path = os.path.join(in_dir, filename)
            out_path = os.path.join(out_dir, filename)

            try:
                img = cv2.imread(in_path)
                if img is None:
                    self.msg_queue.put(("log", f"[Lỗi] Không đọc được: {filename}"))
                    self.msg_queue.put(("progress", idx))
                    continue

                result, dbg, n_bubbles = process_image(img, params)
                cv2.imwrite(out_path, result)

                if save_debug:
                    base, ext = os.path.splitext(filename)
                    dbg_path = os.path.join(out_dir, f"{base}_debug{ext}")
                    cv2.imwrite(dbg_path, dbg)

                self.msg_queue.put(("log", f"[OK] {filename} — {n_bubbles} bong bóng"))
            except Exception as e:
                self.msg_queue.put(("log", f"[Lỗi] {filename}: {e}"))

            self.msg_queue.put(("progress", idx))

        self.msg_queue.put(("done", total))

    # --------------------------------------------------------------- queue
    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def _append_log(self, line):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _poll_queue(self):
        try:
            while True:
                kind, data = self.msg_queue.get_nowait()
                if kind == "log":
                    self._append_log(data)
                elif kind == "progress":
                    self.progress.config(value=data)
                    self.status_text.set(f"Đang xử lý: {data}/{int(self.progress['maximum'])}")
                elif kind == "done":
                    self.status_text.set(f"Hoàn tất! Đã xử lý {data} ảnh.")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)


if __name__ == "__main__":
    app = BubbleEraserApp()
    app.mainloop()