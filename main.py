import os
import pandas as pd 

folder_path = "./data"

# проверка на существование пути
if not os.path.exists(folder_path):
    raise FileNotFoundError(f"Путь не существует: {folder_path}")

# проверка на то что это папка
if not os.path.isdir(folder_path):
    raise NotADirectoryError(f"Это не папка: {folder_path}")

# проверка на то что папка не пуста
if not os.listdir(folder_path):
    raise FileNotFoundError(f"Папка пуста: {folder_path}")

# проверка на то что в папке есть .csv и создание списка только с ними
items = os.listdir(folder_path)
csv_files = []
for f in items:
    if f.lower().endswith(".csv") and os.path.isfile(os.path.join(folder_path, f)):
        csv_files.append(f)

if not csv_files:
    raise FileNotFoundError(f"В папке нет CSV-файлов: {folder_path}")


# проверка на пустоту файлов
valid_files = []

for name in csv_files:
    full_path = os.path.join(folder_path, name)

    try:
        probe = pd.read_csv(full_path, nrows=1, dtype="str")
    except pd.errors.EmptyDataError:
        print(f"⚠ Пустой файл (0 байт): {name}")
        continue

    if probe.empty:
        print(f"⚠ Только заголовок, без данных: {name}")
        continue

    valid_files.append(name)

if not valid_files:
    raise ValueError(f"Не осталось валидных CSV: {folder_path}")

print(f"✓ Валидных файлов: {len(valid_files)}")