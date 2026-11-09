import os
import pandas as pd 

folder_path = "./data" #заменить на ./data
all_errors = []

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

# Наш золотой стандарт (эталон)
required_cols = {"product", "quantity", "price"}

for name in valid_files:
    full_path = os.path.join(folder_path, name)

    try:
        df = pd.read_csv(full_path, on_bad_lines='skip')
    except Exception as e:
        print(f"⚠ Не удалось прочитать {name}: {e}")
        continue


    # внедрение проверки на отсутствие обязательных столбцов
    current_cols = set(df.columns)

    if not required_cols.issubset(current_cols):
        # находим каких именно не хватает
        missing = required_cols - current_cols
        error_msg = f"Файл '{name}': пропущен весь файл. Причина: отсутствуют колонки {missing}."
        all_errors.append(error_msg)
        print(f"⚠ {error_msg}")
        continue


    # внедрение проверки на пустые значения
    # Список колонок, где не должно быть пустоты
    cols_to_check = ["product", "quantity", "price"]
    is_nan_table = df[cols_to_check].isna() # превращает в таблицу из True(NaN)/False
    row_has_nan = is_nan_table.any(axis=1) # превращем таблицу в один столбец из True(NaN)/False
    nan_count = row_has_nan.sum() # суммируем полуенный столбец чтобы узнать сколько в нем True

    if nan_count > 0:
        print(f"\n⚠ В файле {name} найдено строк с пустыми значениями: {nan_count}")

        bad_indices = df[row_has_nan].index

        for idx in bad_indices:
            row_data = df.loc[idx]

            product_val = row_data.get("product", "НЕТ")
            quantity_val = row_data.get("quantity", "НЕТ")
            price_val = row_data.get("price", "НЕТ")

            empty_fields = []
            if pd.isna(row_data.get("product")):
                empty_fields.append("product")
            if pd.isna(row_data.get("quantity")):
                empty_fields.append("quantity")
            if pd.isna(row_data.get("price")):
                empty_fields.append("price")

            reason = f"пустые поля: {', '.join(empty_fields)}"

            print(f"   ❌ Строка {idx}: Товар '{product_val}', Кол-во: {quantity_val}, Цена: {price_val} | Причина: {reason}")

            error_msg = f"Файл '{name}', строка {idx}: пустые поля ({', '.join(empty_fields)}). Данные: {row_data.to_dict()}"
            all_errors.append(error_msg)

        # оставляем только строки без пустот (~ инвертирует True/False)
        df = df[~row_has_nan].copy()

        df["product"] = df["product"].astype(str).str.strip()
    empty_product = (df["product"] == "")

    if empty_product.any():
        print(f"\n⚠ В файле {name} найдено строк с пустым названием товара: {empty_product.sum()}")
        
        # 1. СНАЧАЛА находим индексы и выводим их в лог
        bad_indices = df[empty_product].index
        
        for idx in bad_indices:
            row_data = df.loc[idx]
            quantity_val = row_data.get("quantity", "НЕТ")
            price_val = row_data.get("price", "НЕТ")
            
            print(f"   ❌ Строка {idx}: Товар (пробелы), Кол-во: {quantity_val}, Цена: {price_val} | Причина: название товара состоит из пробелов")
            
            error_msg = f"Файл '{name}', строка {idx}: пустое название товара (пробелы). Данные: {row_data.to_dict()}"
            all_errors.append(error_msg)

        # 2. ТОЛЬКО ПОТОМ удаляем строки
        df = df[~empty_product].copy()


        # внедрение проверки на некорректные цены или количества
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    quantity_is_nan = df["quantity"].isna()
    quantity_is_less_or_equal_zero = (df["quantity"] <= 0)
    bad_quantity = quantity_is_nan | quantity_is_less_or_equal_zero

    price_is_nan = df["price"].isna()
    price_is_less_or_equal_zero = (df["price"] <= 0)
    bad_price = price_is_nan | price_is_less_or_equal_zero

    bad_rows = bad_quantity | bad_price
    bad_count = bad_rows.sum()

    if bad_count > 0:
        print(f"\n⚠ В файле {name} найдено строк с некорректными/отрицательными значениями: {bad_count}")
        
        # 1. СНАЧАЛА находим индексы и пишем лог
        bad_indices = df[bad_rows].index
        
        for idx in bad_indices:
            row_data = df.loc[idx]
            product_val = row_data.get("product", "НЕТ")
            quantity_val = row_data.get("quantity", "НЕТ")
            price_val = row_data.get("price", "НЕТ")
            
            # Определяем точную причину для этой конкретной строки
            reasons = []
            # Проверяем quantity
            if pd.isna(quantity_val):
                reasons.append("quantity не является числом")
            elif quantity_val <= 0:
                reasons.append(f"quantity <= 0 ({quantity_val})")
                
            # Проверяем price
            if pd.isna(price_val):
                reasons.append("price не является числом")
            elif price_val <= 0:
                reasons.append(f"price <= 0 ({price_val})")
            
            reason_text = " | ".join(reasons)
            
            print(f"   ❌ Строка {idx}: Товар '{product_val}', Кол-во: {quantity_val}, Цена: {price_val} | Причина: {reason_text}")
            
            error_msg = f"Файл '{name}', строка {idx}: {reason_text}. Данные: {row_data.to_dict()}"
            all_errors.append(error_msg)

        # 2. ТОЛЬКО ПОТОМ удаляем строки
        df = df[~bad_rows].copy()


    data_frames.append(df)

if not data_frames:
    raise ValueError("Ни в одном файле не найдены обязательные колонки (product, quantity, price).")

print(f"Прочитано файлов: {len(data_frames)}")

for i, df in enumerate(data_frames):
    print(f"  Файл {i+1}: {len(df)} строк, {len(df.columns)} колонок")

# обьединение в одну таблицу
final_df = pd.concat(data_frames, ignore_index=True)
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

final_report["total_revenue"] = final_report["total_revenue"].round(2)

os.makedirs("reports", exist_ok=True)
final_report.to_csv("reports/sales_report.csv", index=False)

# Сохраняем лог ошибок в файл
if all_errors:
    with open("reports/errors.log", "w", encoding="utf-8") as f:
        for error in all_errors:
            f.write(error + "\n")
    print("\n⚠ Были найдены ошибки. Подробности в файле errors.log")
else:
    print("\n✓ Ошибок не найдено. Все файлы обработаны успешно.")