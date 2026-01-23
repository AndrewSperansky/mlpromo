from app.db.session import SessionLocal
from app.seeds.products import seed_products
from app.seeds.promos import seed_promos
from app.seeds.promo_positions import seed_promo_positions


def run():
    db = SessionLocal()
    try:
        products = seed_products(db)
        promos = seed_promos(db)
        seed_promo_positions(db, promos, products)
        print("✅ Seed completed successfully")
    finally:
        db.close()


if __name__ == "__main__":
    run()


#========================================
# Запуск:
# python -m seeds.run
#========================================