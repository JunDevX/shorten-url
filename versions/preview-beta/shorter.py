import threading
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.parse
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

# --- Графический интерфейс Tkinter ---


class URLShortenerApp:

  def __init__(self, root: tk.Tk):
    self.root = root
    self.root.title("URL Shortener")
    self.root.geometry("460x340")
    self.root.resizable(False, False)

    # Настройка современной темы
    self.style = ttk.Style()
    self.style.theme_use("clam")

    self._build_ui()

  def _build_ui(self):
    # Основной контейнер с отступами
    main_frame = ttk.Frame(self.root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Заголовок
    title_label = ttk.Label(
        main_frame,
        text="Сократитель ссылок",
        font=("Helvetica", 16, "bold"),
    )
    title_label.pack(anchor="w", pady=(0, 15))

    # Поле ввода URL
    ttk.Label(
        main_frame, text="Введите длинную ссылку:", font=("Helvetica", 10)
    ).pack(anchor="w")
    self.url_entry = ttk.Entry(main_frame, font=("Helvetica", 10))
    self.url_entry.pack(fill=tk.X, pady=(5, 15))
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
    self.service_combo.pack(fill=tk.X, pady=(5, 15))

    # Кнопка действия
    self.btn_shorten = ttk.Button(
        main_frame, text="Сократить", command=self.start_shortening
    )
    self.btn_shorten.pack(fill=tk.X, pady=(0, 15))

    # Поле результата и кнопка копирования
    ttk.Label(
        main_frame, text="Короткая ссылка:", font=("Helvetica", 10)
    ).pack(anchor="w")

    res_frame = ttk.Frame(main_frame)
    res_frame.pack(fill=tk.X, pady=(5, 0))

    self.result_entry = ttk.Entry(res_frame, font=("Helvetica", 10))
    self.result_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    self.btn_copy = ttk.Button(
        res_frame, text="Копировать", command=self.copy_to_clipboard
    )
    self.btn_copy.pack(side=tk.RIGHT)

    # Статус-бар
    self.status_label = ttk.Label(
        main_frame, text="", font=("Helvetica", 9), foreground="gray"
    )
    self.status_label.pack(anchor="w", pady=(10, 0))

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
    self.status_label.config(text="Обработка...", foreground="blue")
    self.result_entry.delete(0, tk.END)

    # Запускаем сетевой запрос в отдельном потоке, чтобы GUI не "зависал"
    threading.Thread(
        target=self._async_shorten, args=(url,), daemon=True
    ).start()

  def _async_shorten(self, url: str):
    selected_service = self.service_combo.get()
    shortener_func = SERVICES[selected_service]

    try:
      short_url = shortener_func(url)
      # Возвращаем результат в главный поток
      self.root.after(0, self._on_success, short_url)
    except Exception as e:
      self.root.after(0, self._on_error, str(e))

  def _on_success(self, short_url: str):
    self.result_entry.insert(0, short_url)
    self.btn_shorten.config(state="normal")
    self.status_label.config(text="Успешно сокращено!", foreground="green")

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


if __name__ == "__main__":
  root = tk.Tk()
  app = URLShortenerApp(root)
  root.mainloop()