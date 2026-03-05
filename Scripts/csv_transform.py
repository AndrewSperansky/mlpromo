import pandas as pd


# ====== 1. ПУТЬ К ФАЙЛУ ======
INPUT_FILE = r"D:\raw_promo.csv"
OUTPUT_FILE = r"D:\ml_ready_dataset.csv"


def clean_numeric(series):
    """
    Удаляет неразрывные пробелы, обычные пробелы,
    заменяет запятые на точки и приводит к float
    """
    series = series.astype(str)
    series = series.str.replace("\u00A0", "", regex=False)
    series = series.str.replace(" ", "", regex=False)
    series = series.str.replace(",", ".", regex=False)
    return pd.to_numeric(series, errors="coerce")


def main():

    print("Reading file...")

    # если будет ошибка кодировки — поменяй на encoding="cp1251"
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")

    print("Rows loaded:", len(df))

    # ====== 2. Очистка строк ======
    df["PromoID"] = df["PromoID"].astype(str).str.strip()
    df["SKU"] = df["SKU"].astype(str).str.strip()

    # ====== 3. Числовые колонки ======
    df["PercentPriceDrop"] = clean_numeric(df["PercentPriceDrop"])
    df["PromoPrice"] = clean_numeric(df["PromoPrice"])
    df["HistoricalSalesPromo"] = clean_numeric(df["HistoricalSalesPromo"])
    df["SalesQty_Fact"] = clean_numeric(df["SalesQty_Fact"])

    # ====== 4. Формирование ML dataset ======
    ml_df = pd.DataFrame({
        "promo_code": df["PromoID"],
        "sku": df["SKU"],
        "discount": df["PercentPriceDrop"] / 100.0,
        "price": df["PromoPrice"],
        "baseline_sales": df["HistoricalSalesPromo"],
        "uplift": df["SalesQty_Fact"]
    })

    # ====== 5. Удаляем мусор ======
    ml_df = ml_df.dropna()

    ml_df = ml_df[
        (ml_df["price"] > 0) &
        (ml_df["baseline_sales"] >= 0)
    ]

    print("Rows after cleaning:", len(ml_df))

    # ====== 6. Сохраняем ======
    ml_df.to_csv(OUTPUT_FILE, index=False)

    print("ML-ready dataset saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()