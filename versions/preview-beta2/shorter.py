import io
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.parse
from PIL import Image, ImageTk
import qrcode
import requests

# --- Логика работы с API ---


def shorten_yandex(long_url: str) -> str:
  endpoint = "https://clck.ru/--"
  res = requests.get(endpoint, params={"url": long_url}, timeout=10)
  if res.status_code == 200:
    return res.text.strip()
  raise Exception(f"HTTP {res.status_code}")


def shorten_tinyurl(long_url: str) -> str:
  endpoint = (
      f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
  )
  res = requests.get(endpoint, timeout=10)
  if res.status_code == 200:
    return res.text.strip()
  raise Exception(f"HTTP {res.status_code}")


def shorten_isgd(long_url: str) -> str:
  endpoint = "https://is.gd/create.php"
  res = requests.get(
      endpoint, params={"format": "simple", "url": long_url}, timeout=10
  )
  if res.status_code == 200:
    return res.text.strip()
  raise Exception(f"HTTP {res.status_code}")


SERVICES = {
    "Yandex (clck.ru)": shorten_yandex,
    "TinyURL": shorten_tinyurl,
    "Is.gd": shorten_isgd,
}

# --- Графический интерфейс ---


class URLShortenerApp:

  def __init__(self, root: tk.Tk):
    self.root = root
    self.root.title("URL Shortener + QR")
    self.root.geometry("480x580")
    self.root.resizable(False, False)

    self.current_qr_img = None  # Ссылка на объект PIL Image
    self.qr_photo_ref = None  # Ссылка на PhotoImage для предотвращения сбора мусора в Tkinter

    self.style = ttk.Style()
    self.style.theme_use("clam")

    self._build_ui()

  def _build_ui(self):
    main_frame = ttk.Frame(self.root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Заголовок
    title_label = ttk.Label(
        main_frame,
        text="Сократитель ссылок & QR-код",
        font=("Helvetica", 16, "bold"),
    )
    title_label.pack(anchor="w", pady=(0, 15))

    # Поле ввода URL
    ttk.Label(
        main_frame, text="Введите длинную ссылку:", font=("Helvetica", 10)
    ).pack(anchor="w")
    self.url_entry = ttk.Entry(main_frame, font=("Helvetica", 10))
    self.url_entry.pack(fill=tk.X, pady=(5, 10))
    self.url_entry.focus()

    # Выбор сервиса
    ttk.Label(
        main_frame, text="Выберите сервис:", font=("Helvetica", 10)
    ).pack(anchor="w")
    self.service_combo = ttk.Combobox(
        main_frame,
        values=list(SERVICES.keys()),
        state="readonly",
        font=("Helvetica", 10),
    )
    self.service_combo.current(0)
    self.service_combo.pack(fill=tk.X, pady=(5, 10))

    # Кнопка действия
    self.btn_shorten = ttk.Button(
        main_frame, text="Сократить и создать QR", command=self.start_shortening
    )
    self.btn_shorten.pack(fill=tk.X, pady=(5, 15))

    # Поле результата и кнопка копирования
    ttk.Label(
        main_frame, text="Короткая ссылка:", font=("Helvetica", 10)
    ).pack(anchor="w")

    res_frame = ttk.Frame(main_frame)
    res_frame.pack(fill=tk.X, pady=(5, 15))

    self.result_entry = ttk.Entry(res_frame, font=("Helvetica", 10))
    self.result_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    self.btn_copy = ttk.Button(
        res_frame, text="Копировать", command=self.copy_to_clipboard
    )
    self.btn_copy.pack(side=tk.RIGHT)

    # Область для отображения QR-кода
    qr_frame = ttk.LabelFrame(main_frame, text=" QR-код ", padding=10)
    qr_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    self.qr_label = ttk.Label(qr_frame, text="QR-код появится здесь")
    self.qr_label.pack(expand=True)

    self.btn_save_qr = ttk.Button(
        qr_frame,
        text="Сохранить QR в PNG",
        command=self.save_qr,
        state="disabled",
    )
    self.btn_save_qr.pack(pady=(5, 0))

    # Статус-бар
    self.status_label = ttk.Label(
        main_frame, text="", font=("Helvetica", 9), foreground="gray"
    )
    self.status_label.pack(anchor="w")

  def start_shortening(self):
    url = self.url_entry.get().strip()

    if not url:
      messagebox.showwarning("Внимание", "Пожалуйста, введите ссылку.")
      return

    if not url.startswith(("http://", "https://")):
      url = "https://" + url
      self.url_entry.delete(0, tk.END)
      self.url_entry.insert(0, url)

    # Блокируем UI на время запроса
    self.btn_shorten.config(state="disabled")
    self.btn_save_qr.config(state="disabled")
    self.status_label.config(text="Обработка...", foreground="blue")
    self.result_entry.delete(0, tk.END)

    threading.Thread(
        target=self._async_shorten, args=(url,), daemon=True
    ).start()

  def _async_shorten(self, url: str):
    selected_service = self.service_combo.get()
    shortener_func = SERVICES[selected_service]

    try:
      short_url = shortener_func(url)

      # Генерация QR-кода с помощью qrcode
      qr = qrcode.QRCode(
          version=1,
          error_correction=qrcode.constants.ERROR_CORRECT_M,
          box_size=6,
          border=2,
      )
      qr.add_data(short_url)
      qr.make(fit=True)

      img = qr.make_image(fill_color="black", back_color="white")

      self.root.after(0, self._on_success, short_url, img)
    except Exception as e:
      self.root.after(0, self._on_error, str(e))

  def _on_success(self, short_url: str, qr_img):
    self.result_entry.insert(0, short_url)

    # Сохраняем PIL Image для будущего экспорта
    self.current_qr_img = qr_img

    # Преобразуем PIL Image в формат ImageTk для Tkinter
    tk_img = ImageTk.PhotoImage(qr_img)
    self.qr_photo_ref = tk_img  # Сохраняем ссылку, чтобы Python не удалил изображение из памяти

    self.qr_label.config(image=tk_img, text="")
    self.btn_shorten.config(state="normal")
    self.btn_save_qr.config(state="normal")
    self.status_label.config(
        text="Готово! Ссылка и QR созданы.", foreground="green"
    )

  def _on_error(self, error_msg: str):
    self.btn_shorten.config(state="normal")
    self.status_label.config(text="Ошибка при сокращении", foreground="red")
    messagebox.showerror(
        "Ошибка", f"Не удалось сократить ссылку:\n{error_msg}"
    )

  def copy_to_clipboard(self):
    short_url = self.result_entry.get().strip()
    if short_url:
      self.root.clipboard_clear()
      self.root.clipboard_append(short_url)
      self.status_label.config(
          text="Ссылка скопирована в буфер!", foreground="green"
      )

  def save_qr(self):
    if not self.current_qr_img:
      return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
        title="Сохранить QR-код",
    )

    if file_path:
      try:
        self.current_qr_img.save(file_path)
        messagebox.showinfo("Успех", f"QR-код сохранен в:\n{file_path}")
      except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = URLShortenerApp(root)
  root.mainloop()