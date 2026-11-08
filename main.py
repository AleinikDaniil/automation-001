import os
import pandas as pd 

folder_path = "./temp_data" #заменить на ./data

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
    except UnicodeDecodeError:
        print(f"⚠ Ошибка кодировки (не текст или не UTF-8): {name}")
        continue
    except pd.errors.ParserError:
        print(f"⚠ Ошибка парсинга (битые данные или неверный разделитель): {name}")
        continue
    except Exception as e:
        print(f"⚠ Неизвестная ошибка при чтении {name}: {e}")
        continue

    if probe.empty:
        print(f"⚠ Только заголовок, без данных: {name}")
        continue

    valid_files.append(name)

if not valid_files:
    raise ValueError(f"Не осталось валидных CSV: {folder_path}")

print(f"✓ Валидных файлов: {len(valid_files)}\n" + "\n".join(valid_files))

# чтение валидных файлов
data_frames = []

for name in valid_files:
    full_path = os.path.join(folder_path, name)

    try:
        df = pd.read_csv(full_path)
    except Exception as e:
        print(f"⚠ Не удалось прочитать {name}: {e}")
        continue

    data_frames.append(df)

print(f"Прочитано файлов: {len(data_frames)}")

for i, df in enumerate(data_frames):
    print(f"  Файл {i+1}: {len(df)} строк, {len(df.columns)} колонок")

# обьединение в одну таблицу
final_df = pd.concat(data_frames, ignore_index="True")
print(f"✓ Всего строк в объединенной таблице: {len(final_df)}")

# создаем новую колонку и помещаем туда выручку
final_df["revenue"] = final_df["quantity"] * final_df["price"]

report = final_df.groupby("product").agg(
    total_quantity = ("quantity", "sum"),
    total_revenue = ("revenue", "sum")
).reset_index()

print(report)


# определяем общую выручку и самый прибыльный товары
total_company_revenue = report["total_revenue"].sum()
print(f"Общая выручка компании: {total_company_revenue:.2f}")

sorted_report = report.sort_values(by="total_revenue", ascending=False)

best_product = sorted_report.iloc[0]
print(f"Самый прибыльный товар: {best_product['product']} (выручка: {best_product['total_revenue']:.2f})")

# Создаем маленькую табличку с одной строкой "ИТОГО"
total_row = pd.DataFrame([{
    "product": "ИТОГО",
    "total_quantity": report["total_quantity"].sum(),
    "total_revenue": total_company_revenue
}])

# Приклеиваем эту строку в самый низ нашей таблицы report
final_report = pd.concat([report, total_row], ignore_index=True)

os.makedirs("reports", exist_ok=True)
final_report.to_csv("reports/sales_report.csv", index=False)