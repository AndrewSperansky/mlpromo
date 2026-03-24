# scripts/validate_dataset.py
# запуск: python scripts/validate_dataset.py "D:/promo_dataset_real.csv"


import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = ["PromoID", "SKU", "RegularPrice", "Date", "SalesQty_Promo"]

def validate_csv(file_path: str):
    path = Path(file_path)
    if not path.is_file():
        print(f"❌ Файл не найден: {file_path}")
        return False

    errors = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("❌ CSV пустой")
            return False

        n_cols = len(header)
        print(f"✅ Заголовок содержит {n_cols} колонок: {header}")

        # проверка обязательных колонок
        for col in REQUIRED_COLUMNS:
            if col not in header:
                errors.append(f"❌ Отсутствует обязательная колонка: {col}")

        for i, row in enumerate(reader, start=2):
            # проверка количества колонок
            if len(row) != n_cols:
                errors.append(f"❌ Строка {i}: ожидается {n_cols} колонок, найдено {len(row)}")

            # проверка пустых обязательных полей
            row_dict = dict(zip(header, row))
            for col in REQUIRED_COLUMNS:
                val = row_dict.get(col, "").strip()
                if val == "":
                    errors.append(f"❌ Строка {i}: обязательное поле '{col}' пустое")

    if errors:
        print("❌ Ошибки при проверке CSV:")
        for e in errors:
            print("   " + e)
        return False
    else:
        print("✅ CSV прошел проверку!")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python validate_dataset.py path/to/dataset.csv")
        sys.exit(1)

    file_path = sys.argv[1]
    valid = validate_csv(file_path)
    sys.exit(0 if valid else 1)