--
-- promo-ml database schema
-- Source of truth: app/db/schema.sql
-- Encoding: UTF8
-- Alembic: NOT USED
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- ============================================================
-- ML MODELS REGISTRY
-- ============================================================

CREATE TABLE public.ml_model (
    id           INTEGER PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    algorithm    VARCHAR(50)  NOT NULL,
    version      VARCHAR(20)  NOT NULL,

    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    trained_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),

    is_active    BOOLEAN     NOT NULL DEFAULT false,
    is_deleted   BOOLEAN     NOT NULL DEFAULT false,

    model_type   VARCHAR     NOT NULL DEFAULT 'regression',
    target       VARCHAR     NOT NULL DEFAULT 'sales_qty',

    features     JSON,
    metrics      JSON,
    model_path   TEXT
);

CREATE SEQUENCE public.ml_model_id_seq
    START WITH 1 INCREMENT BY 1;

ALTER TABLE public.ml_model
    ALTER COLUMN id SET DEFAULT nextval('public.ml_model_id_seq');

ALTER TABLE public.ml_model
    ADD CONSTRAINT uq_ml_model_name UNIQUE (name);

-- ============================================================
-- ML PREDICTION REQUESTS
-- ============================================================

CREATE TABLE public.ml_prediction_request (
    id           UUID PRIMARY KEY,
    source       TEXT  NOT NULL,
    payload      JSONB NOT NULL,
    received_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================
-- ML PREDICTION RESULTS
-- ============================================================

CREATE TABLE public.ml_prediction_result (
    id               BIGINT PRIMARY KEY,
    request_id       UUID NOT NULL,

    model_id         TEXT NOT NULL,
    model_version    TEXT NOT NULL,

    prediction_value DOUBLE PRECISION NOT NULL,
    shap_values      JSONB,

    created_at       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE SEQUENCE public.ml_prediction_result_id_seq
    START WITH 1 INCREMENT BY 1;

ALTER TABLE public.ml_prediction_result
    ALTER COLUMN id SET DEFAULT nextval('public.ml_prediction_result_id_seq');

ALTER TABLE public.ml_prediction_result
    ADD CONSTRAINT fk_ml_prediction_result_request
        FOREIGN KEY (request_id)
        REFERENCES public.ml_prediction_request(id);

-- ============================================================
-- LEGACY / FALLBACK PREDICTIONS
-- ============================================================

CREATE TABLE public.prediction (
    id                    INTEGER PRIMARY KEY,
    ml_model_id            INTEGER NOT NULL,

    predicted_sales_qty    DOUBLE PRECISION NOT NULL,

    promo_code             VARCHAR,
    sku                    VARCHAR,
    date                   DATE,

    features               JSONB,
    fallback_used          BOOLEAN NOT NULL DEFAULT false,

    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE SEQUENCE public.prediction_id_seq
    START WITH 1 INCREMENT BY 1;

ALTER TABLE public.prediction
    ALTER COLUMN id SET DEFAULT nextval('public.prediction_id_seq');

ALTER TABLE public.prediction
    ADD CONSTRAINT fk_prediction_ml_model
        FOREIGN KEY (ml_model_id)
        REFERENCES public.ml_model(id);

CREATE INDEX ix_prediction_ml_model_id
    ON public.prediction (ml_model_id);

-- ============================================================
-- PRODUCT CATALOG
-- ============================================================

CREATE TABLE public.product (
    id          INTEGER PRIMARY KEY,
    sku         VARCHAR(50)  NOT NULL,
    name        VARCHAR(255) NOT NULL,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    is_deleted  BOOLEAN     NOT NULL DEFAULT false,
    deleted_at  TIMESTAMPTZ
);

CREATE SEQUENCE public.product_id_seq
    START WITH 1 INCREMENT BY 1;

ALTER TABLE public.product
    ALTER COLUMN id SET DEFAULT nextval('public.product_id_seq');

CREATE UNIQUE INDEX ix_product_sku
    ON public.product (sku);

COMMENT ON COLUMN public.product.is_deleted
    IS 'Мягкое удаление';

COMMENT ON COLUMN public.product.deleted_at
    IS 'Время мягкого удаления (UTC)';

-- ============================================================
-- PROMOTIONS
-- ============================================================

CREATE TABLE public.promo (
    id          INTEGER PRIMARY KEY,
    code        VARCHAR(50) NOT NULL,

    start_date  TIMESTAMPTZ NOT NULL,
    end_date    TIMESTAMPTZ NOT NULL,

    is_active   BOOLEAN     NOT NULL,
    is_deleted  BOOLEAN     NOT NULL DEFAULT false,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

CREATE SEQUENCE public.promo_id_seq
    START WITH 1 INCREMENT BY 1;

ALTER TABLE public.promo
    ALTER COLUMN id SET DEFAULT nextval('public.promo_id_seq');

CREATE UNIQUE INDEX ix_promo_code
    ON public.promo (code);

COMMENT ON COLUMN public.promo.is_deleted
    IS 'Мягкое удаление';

COMMENT ON COLUMN public.promo.deleted_at
    IS 'Время мягкого удаления (UTC)';

-- ============================================================
-- PROMO POSITIONS
-- ============================================================

CREATE TABLE public.promo_position (
    id          INTEGER PRIMARY KEY,

    promo_id    INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,

    date        DATE NOT NULL,
    price       DOUBLE PRECISION NOT NULL,
    discount    DOUBLE PRECISION NOT NULL,
    sales_qty   INTEGER NOT NULL,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    is_deleted  BOOLEAN     NOT NULL DEFAULT false,
    deleted_at  TIMESTAMPTZ
);

CREATE SEQUENCE public.promo_position_id_seq
    START WITH 1 INCREMENT BY 1;

ALTER TABLE public.promo_position
    ALTER COLUMN id SET DEFAULT nextval('public.promo_position_id_seq');

ALTER TABLE public.promo_position
    ADD CONSTRAINT fk_promo_position_promo
        FOREIGN KEY (promo_id)
        REFERENCES public.promo(id);

ALTER TABLE public.promo_position
    ADD CONSTRAINT fk_promo_position_product
        FOREIGN KEY (product_id)
        REFERENCES public.product(id);

ALTER TABLE public.promo_position
    ADD CONSTRAINT uq_promo_position_unique
        UNIQUE (promo_id, product_id, date);

CREATE INDEX ix_promo_position_promo_id
    ON public.promo_position (promo_id);

CREATE INDEX ix_promo_position_product_id
    ON public.promo_position (product_id);

COMMENT ON COLUMN public.promo_position.date
    IS 'Дата действия промо';

COMMENT ON COLUMN public.promo_position.is_deleted
    IS 'Мягкое удаление';

COMMENT ON COLUMN public.promo_position.deleted_at
    IS 'Время мягкого удаления (UTC)';

-- ============================================================
-- ML DATASET VIEW
-- ============================================================

CREATE VIEW public.promo_ml_dataset_v1 AS
SELECT
    pp.date,
    p.code AS promo_code,
    pr.sku,

    pp.price,
    pp.discount,
    pp.sales_qty AS target_sales_qty,

    AVG(pp.sales_qty)
        OVER (PARTITION BY pr.id ORDER BY pp.date
              ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
        AS avg_sales_7d,

    AVG(pp.discount)
        OVER (PARTITION BY pr.id ORDER BY pp.date
              ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
        AS avg_discount_7d,

    (p.end_date::date - pp.date) AS promo_days_left

FROM public.promo_position pp
JOIN public.promo   p  ON p.id  = pp.promo_id
JOIN public.product pr ON pr.id = pp.product_id

WHERE
    pp.is_deleted = false
    AND p.is_deleted  = false
    AND pr.is_deleted = false;
