--
-- PostgreSQL database dump
--

\restrict ZAu0zT9lWqNMXn7PwBasXvHyycmnuSnDeoOEFKSXl4gWE3eV2kX1Hjzeg9PAfVB

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg13+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: dataset_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_versions (
    id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    row_count integer NOT NULL,
    target_column text DEFAULT 'SalesQty_Promo'::text NOT NULL,
    status text DEFAULT 'READY'::text NOT NULL,
    comment text
);


--
-- Name: industrial_dataset_raw; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.industrial_dataset_raw (
    id bigint NOT NULL,
    dataset_version_id uuid NOT NULL,
    "PromoID" text,
    "SKU" text,
    "SKU_Level2" text,
    "SKU_Level3" text,
    "SKU_Level4" text,
    "SKU_Level5" text,
    "Category" text,
    "Supplier" text,
    "Region" text,
    "StoreID" text,
    "Store_Location_Type" text,
    "Store_ABC" text,
    "Date" date,
    "WeekNumber" integer,
    "DayOfWeek" integer,
    "RegularPrice" numeric,
    "PromoPrice" numeric,
    "PurchasePriceBefore" numeric,
    "PurchasePricePromo" numeric,
    "PromoMechanics" text,
    "PercentPriceDrop" numeric,
    "VolumeRegular" numeric,
    "HistoricalSalesPromo" numeric,
    "SalesQty_Fact" numeric,
    "SalesQty_PrevModel" numeric,
    "SalesQty_Promo" numeric,
    "FM_Regular" numeric,
    "FM_Promo" numeric,
    "TurnoverBefore" numeric,
    "TurnoverPromo" numeric,
    "SeasonCoef_Week" numeric,
    "SeasonCoef_Day" numeric,
    "ManualCoefficientFlag" boolean,
    "IsNewSKU" boolean,
    "IsAnalogSKU" boolean,
    "PreviousPromoID" text,
    "PromoStatus" text,
    "MarketingCarrier" text,
    "MarketingMaterial" text,
    "FormatAssortment" text
);


--
-- Name: industrial_dataset_raw_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.industrial_dataset_raw_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: industrial_dataset_raw_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.industrial_dataset_raw_id_seq OWNED BY public.industrial_dataset_raw.id;


--
-- Name: ml_model; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ml_model (
    name character varying(100) NOT NULL,
    algorithm character varying(50) NOT NULL,
    version character varying(50) NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    trained_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    model_type character varying DEFAULT 'regression'::character varying NOT NULL,
    target character varying DEFAULT 'sales_qty'::character varying NOT NULL,
    features json,
    metrics json,
    model_path text,
    is_deleted boolean DEFAULT false NOT NULL,
    dataset_version_id uuid NOT NULL,
    trained_rows_count integer DEFAULT 0 NOT NULL
);


--
-- Name: ml_model_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ml_model_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ml_model_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ml_model_id_seq OWNED BY public.ml_model.id;


--
-- Name: ml_prediction_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ml_prediction_audit (
    id integer NOT NULL,
    request_id uuid NOT NULL,
    model_id character varying(100) NOT NULL,
    model_version text,
    prediction_value double precision,
    features jsonb,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: ml_prediction_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ml_prediction_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ml_prediction_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ml_prediction_audit_id_seq OWNED BY public.ml_prediction_audit.id;


--
-- Name: ml_prediction_request; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ml_prediction_request (
    id uuid NOT NULL,
    source text NOT NULL,
    payload jsonb NOT NULL,
    received_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ml_prediction_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ml_prediction_result (
    id bigint NOT NULL,
    request_id uuid NOT NULL,
    model_id text NOT NULL,
    model_version text NOT NULL,
    prediction_value double precision NOT NULL,
    shap_values jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ml_prediction_result_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ml_prediction_result_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ml_prediction_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ml_prediction_result_id_seq OWNED BY public.ml_prediction_result.id;


--
-- Name: model_activation_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_activation_history (
    id bigint NOT NULL,
    model_id integer NOT NULL,
    activated_at timestamp with time zone DEFAULT now(),
    activated_by character varying(50)
);


--
-- Name: model_activation_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_activation_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_activation_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_activation_history_id_seq OWNED BY public.model_activation_history.id;


--
-- Name: prediction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prediction (
    id integer NOT NULL,
    ml_model_id integer NOT NULL,
    predicted_sales_qty double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    promo_code character varying,
    sku character varying,
    date date,
    features jsonb,
    fallback_used boolean DEFAULT false NOT NULL
);


--
-- Name: prediction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.prediction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: prediction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.prediction_id_seq OWNED BY public.prediction.id;


--
-- Name: industrial_dataset_raw id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.industrial_dataset_raw ALTER COLUMN id SET DEFAULT nextval('public.industrial_dataset_raw_id_seq'::regclass);


--
-- Name: ml_model id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_model ALTER COLUMN id SET DEFAULT nextval('public.ml_model_id_seq'::regclass);


--
-- Name: ml_prediction_audit id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_prediction_audit ALTER COLUMN id SET DEFAULT nextval('public.ml_prediction_audit_id_seq'::regclass);


--
-- Name: ml_prediction_result id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_prediction_result ALTER COLUMN id SET DEFAULT nextval('public.ml_prediction_result_id_seq'::regclass);


--
-- Name: model_activation_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_activation_history ALTER COLUMN id SET DEFAULT nextval('public.model_activation_history_id_seq'::regclass);


--
-- Name: prediction id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction ALTER COLUMN id SET DEFAULT nextval('public.prediction_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: dataset_versions dataset_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_versions
    ADD CONSTRAINT dataset_versions_pkey PRIMARY KEY (id);


--
-- Name: industrial_dataset_raw industrial_dataset_raw_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.industrial_dataset_raw
    ADD CONSTRAINT industrial_dataset_raw_pkey PRIMARY KEY (id);


--
-- Name: ml_prediction_audit ml_prediction_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_prediction_audit
    ADD CONSTRAINT ml_prediction_audit_pkey PRIMARY KEY (id);


--
-- Name: ml_prediction_request ml_prediction_request_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_prediction_request
    ADD CONSTRAINT ml_prediction_request_pkey PRIMARY KEY (id);


--
-- Name: ml_prediction_result ml_prediction_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_prediction_result
    ADD CONSTRAINT ml_prediction_result_pkey PRIMARY KEY (id);


--
-- Name: model_activation_history model_activation_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_activation_history
    ADD CONSTRAINT model_activation_history_pkey PRIMARY KEY (id);


--
-- Name: ml_model pk_ml_model; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_model
    ADD CONSTRAINT pk_ml_model PRIMARY KEY (id);


--
-- Name: prediction pk_prediction; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction
    ADD CONSTRAINT pk_prediction PRIMARY KEY (id);


--
-- Name: idx_dataset_versions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dataset_versions_created_at ON public.dataset_versions USING btree (created_at);


--
-- Name: idx_history_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_history_date ON public.model_activation_history USING btree (activated_at DESC);


--
-- Name: idx_history_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_history_model ON public.model_activation_history USING btree (model_id);


--
-- Name: idx_industrial_dataset_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_industrial_dataset_version ON public.industrial_dataset_raw USING btree (dataset_version_id);


--
-- Name: idx_industrial_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_industrial_date ON public.industrial_dataset_raw USING btree ("Date");


--
-- Name: idx_industrial_sku; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_industrial_sku ON public.industrial_dataset_raw USING btree ("SKU");


--
-- Name: idx_industrial_store; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_industrial_store ON public.industrial_dataset_raw USING btree ("StoreID");


--
-- Name: idx_ml_audit_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_audit_created ON public.ml_prediction_audit USING btree (created_at DESC);


--
-- Name: idx_ml_audit_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_audit_model ON public.ml_prediction_audit USING btree (model_id);


--
-- Name: idx_ml_model_dataset_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_model_dataset_version_id ON public.ml_model USING btree (dataset_version_id);


--
-- Name: idx_only_one_active_model; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_only_one_active_model ON public.ml_model USING btree (is_active) WHERE (is_active = true);


--
-- Name: ix_prediction_ml_model_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_prediction_ml_model_id ON public.prediction USING btree (ml_model_id);


--
-- Name: uq_ml_model_name_version; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ml_model_name_version ON public.ml_model USING btree (name, version);


--
-- Name: ml_model fk_ml_model_dataset_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_model
    ADD CONSTRAINT fk_ml_model_dataset_version FOREIGN KEY (dataset_version_id) REFERENCES public.dataset_versions(id) ON DELETE RESTRICT;


--
-- Name: prediction fk_prediction_ml_model_id_ml_model; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction
    ADD CONSTRAINT fk_prediction_ml_model_id_ml_model FOREIGN KEY (ml_model_id) REFERENCES public.ml_model(id);


--
-- Name: industrial_dataset_raw industrial_dataset_raw_dataset_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.industrial_dataset_raw
    ADD CONSTRAINT industrial_dataset_raw_dataset_version_id_fkey FOREIGN KEY (dataset_version_id) REFERENCES public.dataset_versions(id) ON DELETE CASCADE;


--
-- Name: ml_prediction_result ml_prediction_result_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_prediction_result
    ADD CONSTRAINT ml_prediction_result_request_id_fkey FOREIGN KEY (request_id) REFERENCES public.ml_prediction_request(id);


--
-- Name: model_activation_history model_activation_history_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_activation_history
    ADD CONSTRAINT model_activation_history_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ml_model(id);


--
-- PostgreSQL database dump complete
--

\unrestrict ZAu0zT9lWqNMXn7PwBasXvHyycmnuSnDeoOEFKSXl4gWE3eV2kX1Hjzeg9PAfVB

