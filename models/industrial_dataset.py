# models/industrial_dataset.py


from sqlalchemy import Column, BigInteger, Text, Integer, Numeric, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class IndustrialDatasetRaw(Base):
    __tablename__ = "industrial_dataset_raw"

    id = Column(BigInteger, primary_key=True, index=True)

    PromoID = Column(Text)
    SKU = Column(Text)
    SKU_Level2 = Column(Text)
    SKU_Level3 = Column(Text)
    SKU_Level4 = Column(Text)
    SKU_Level5 = Column(Text)
    Category = Column(Text)
    Supplier = Column(Text)
    Region = Column(Text)
    StoreID = Column(Text)
    Store_Location_Type = Column(Text)
    Store_ABC = Column(Text)

    Date = Column(Date)
    WeekNumber = Column(Integer)
    DayOfWeek = Column(Integer)

    RegularPrice = Column(Numeric)
    PromoPrice = Column(Numeric)
    PurchasePriceBefore = Column(Numeric)
    PurchasePricePromo = Column(Numeric)

    PromoMechanics = Column(Text)
    PercentPriceDrop = Column(Numeric)

    VolumeRegular = Column(Numeric)
    HistoricalSalesPromo = Column(Numeric)
    SalesQty_Fact = Column(Numeric)
    SalesQty_PrevModel = Column(Numeric)
    SalesQty_Promo = Column(Numeric)

    FM_Regular = Column(Numeric)
    FM_Promo = Column(Numeric)
    TurnoverBefore = Column(Numeric)
    TurnoverPromo = Column(Numeric)

    SeasonCoef_Week = Column(Numeric)
    SeasonCoef_Day = Column(Numeric)

    ManualCoefficientFlag = Column(Boolean)
    IsNewSKU = Column(Boolean)
    IsAnalogSKU = Column(Boolean)

    PreviousPromoID = Column(Text)
    PromoStatus = Column(Text)
    MarketingCarrier = Column(Text)
    MarketingMaterial = Column(Text)
    FormatAssortment = Column(Text)

