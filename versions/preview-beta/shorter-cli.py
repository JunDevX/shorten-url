import urllib.parse
import requests

# Список доступных провайдеров для сокращения ссылок
PROVIDERS = {
    "1": "Yandex (clck.ru)",
    "2": "TinyURL",
    "3": "Is.gd",
    "4": "Сократить во всех сразу",
}


def shorten_yandex(long_url: str) -> str:
  """Сокращение через Яндекс (clck.ru)."""
  endpoint = "https://clck.ru/--"
  response = requests.get(endpoint, params={"url": long_url}, timeout=10)
  if response.status_code == 200:
    return response.text.strip()
  raise Exception(f"Код ошибки HTTP: {response.status_code}")


def shorten_tinyurl(long_url: str) -> str:
  """Сокращение через TinyURL."""
  endpoint = (
      f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
  )
  response = requests.get(endpoint, timeout=10)
  if response.status_code == 200:
    return response.text.strip()
  raise Exception(f"Код ошибки HTTP: {response.status_code}")


def shorten_isgd(long_url: str) -> str:
  """Сокращение через Is.gd."""
  endpoint = "https://is.gd/create.php"
  response = requests.get(
      endpoint, params={"format": "simple", "url": long_url}, timeout=10
  )
  if response.status_code == 200:
    return response.text.strip()
  raise Exception(f"Код ошибки HTTP: {response.status_code}")


def process_shortening(choice: str, url: str):
  """Обработка выбора пользователя."""
  if choice == "1":
    print(f"\n[Yandex] Результат: {shorten_yandex(url)}")
  elif choice == "2":
    print(f"\n[TinyURL] Результат: {shorten_tinyurl(url)}")
  elif choice == "3":
    print(f"\n[Is.gd] Результат: {shorten_isgd(url)}")
  elif choice == "4":
    print("\n--- Результаты со всех сервисов ---")
    for name, func in [
        ("Yandex", shorten_yandex),
        ("TinyURL", shorten_tinyurl),
        ("Is.gd", shorten_isgd),
    ]:
      try:
        print(f"{name: <10}: {func(url)}")
      except Exception as e:
        print(f"{name: <10}: Не удалось сократить ({e})")
  else:
    print("\nОшибка: выбран неверный пункт меню.")


def main():
  print("=" * 45)
  print("      УНИВЕРСАЛЬНЫЙ СОКРАТИТЕЛЬ ССЫЛОК")
  print("=" * 45)

  while True:
    url = input("\nВведите ссылку (или 'exit' для выхода): ").strip()

    if url.lower() in ("exit", "quit", "0"):
      print("Программа завершена.")
      break

    if not url.startswith(("http://", "https://")):
      url = "https://" + url

    print("\nВыберите сервис для сокращения:")
    for key, name in PROVIDERS.items():
      print(f" [{key}] {name}")

    choice = input("Ваш выбор (1-4): ").strip()

    try:
      process_shortening(choice, url)
    except Exception as err:
      print(f"\nПроизошла ошибка при отправке запроса: {err}")

    print("\n" + "-" * 45)


if __name__ == "__main__":
  main()