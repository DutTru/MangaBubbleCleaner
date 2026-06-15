# Manga Bubble Cleaner

A simple desktop tool for detecting manga speech bubbles and removing text inside them while preserving the bubble borders.

---

# 🇻🇳 Tiếng Việt

## Giới thiệu

Manga Bubble Cleaner là công cụ hỗ trợ làm sạch trang truyện tranh bằng cách:

* Phát hiện bong bóng thoại (speech bubbles)
* Xóa chữ bên trong bong bóng
* Giữ nguyên viền bong bóng
* Xử lý hàng loạt nhiều trang truyện cùng lúc
* Xuất ảnh kết quả và ảnh debug để kiểm tra

Mục tiêu của dự án là hỗ trợ dịch truyện, redraw manga và chuẩn bị trang truyện cho việc chèn bản dịch mới.

---

## Tính năng

✅ Phát hiện bong bóng thoại tự động

✅ Xóa chữ trong bong bóng

✅ Giữ nguyên hình dạng và viền bong bóng

✅ Xem trước kết quả trực tiếp

✅ Tinh chỉnh tham số phát hiện

✅ Xử lý cả thư mục ảnh

✅ Xuất ảnh debug để kiểm tra vùng nhận diện

---

## Cách sử dụng

### Test một ảnh

1. Nhấn **Chọn ảnh để test**
2. Chọn một trang manga
3. Nhấn **Test**
4. Điều chỉnh các tham số nếu cần

### Xử lý hàng loạt

1. Nhấn **Chọn thư mục ảnh & xử lý**
2. Chọn thư mục chứa các trang manga
3. Chương trình sẽ tạo thư mục:

output_no_text

4. Kết quả sẽ được lưu tại đây

---

## Các thư viện sử dụng

* Python 3
* OpenCV
* NumPy
* Pillow
* Tkinter

---

## Đóng gói EXE

Cài đặt PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name="MangaBubbleCleaner" main.py
```

---

## Lưu ý

Đây là phiên bản thử nghiệm.

Độ chính xác phụ thuộc vào:

* Chất lượng ảnh manga
* Kiểu bong bóng thoại
* Độ tương phản giữa chữ và nền

Một số trang truyện có thể cần tinh chỉnh tham số để đạt kết quả tốt nhất.

---

# 🇬🇧 English

## Overview

Manga Bubble Cleaner is a desktop application designed to automatically detect manga speech bubbles and remove text inside them while preserving the original bubble borders.

The tool is intended for manga translators, redrawers, and scanlation teams.

---

## Features

✅ Automatic speech bubble detection

✅ Text removal inside bubbles

✅ Preserve bubble borders

✅ Real-time preview

✅ Adjustable detection parameters

✅ Batch processing

✅ Optional debug output

---

## How To Use

### Test Single Image

1. Click **Select Test Image**
2. Choose a manga page
3. Click **Test**
4. Adjust parameters if necessary

### Batch Processing

1. Click **Select Folder & Process**
2. Choose a folder containing manga pages
3. The program creates:

output_no_text

4. Processed images will be saved there

---

## Requirements

* Python 3
* OpenCV
* NumPy
* Pillow
* Tkinter

---

## Build EXE

Install PyInstaller:

```bash
pip install pyinstaller
```

Build executable:

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name="MangaBubbleCleaner" main.py
```

---

## Disclaimer

This project is experimental.

Detection accuracy depends on:

* Manga image quality
* Bubble shape and style
* Contrast between text and background

Some pages may require manual parameter adjustments for optimal results.

---

## License

Free for personal and educational use.

Feel free to modify and improve the project.
