# promo_calculator.py  Python-скрипт (работает с CSV/таблицей)
import csv
from decimal import Decimal

def compute_row(row):
    SKU = row['SKU']
    base = Decimal(row['BasePrice'])
    promo = Decimal(row['PromoPrice'])
    base_sales = Decimal(row['BaseSales'])
    elasticity = Decimal(row.get('Elasticity', '0.5'))
    cost = Decimal(row.get('CostPerUnit', '0'))

    # new sales (simple linear elasticity)
    new_sales = base_sales * (1 + elasticity * ((base - promo) / base))
    revenue_before = base_sales * base
    revenue_after = new_sales * promo
    profit_before = base_sales * (base - cost)
    profit_after = new_sales * (promo - cost)

    return {
        'SKU': SKU,
        'NewSales': float(new_sales),
        'RevenueBefore': float(revenue_before),
        'RevenueAfter': float(revenue_after),
        'ProfitBefore': float(profit_before),
        'ProfitAfter': float(profit_after),
    }

def run(input_csv, output_csv):
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [compute_row(r) for r in reader]

    fieldnames = ['SKU','NewSales','RevenueBefore','RevenueAfter','ProfitBefore','ProfitAfter']
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == '__main__':
    # пример: run('promo_input.csv','promo_output.csv')
    run('promo_input.csv','promo_output.csv')

### Скрипт прост — можно расширить: учесть пороговые штуки, ограничение бюджета промо, разный тип акции, сезонность и т.д ###
