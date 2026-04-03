--
-- PostgreSQL database dump
--

\restrict 3aONZSEeNzaM5ST90jaw0cv4WanzKPT8fPJga8MUuno3YNg6vxHsg6OAvKthmlE

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
-- Name: dataset_upload_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_upload_history (
    id bigint NOT NULL,
    batch_id uuid NOT NULL,
    uploaded_at timestamp without time zone DEFAULT now(),
    records_added integer NOT NULL,
    total_records_after integer NOT NULL,
    status character varying(50) NOT NULL,
    error_message text,
    duration_ms integer
);


--
-- Name: dataset_upload_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_upload_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_upload_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_upload_history_id_seq OWNED BY public.dataset_upload_history.id;


--
-- Name: industrial_dataset_raw; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.industrial_dataset_raw (
    id bigint NOT NULL,
    promo_id text,
    sku text,
    store_id text,
    category text,
    region text,
    store_location_type text,
    format_assortment text,
    month integer,
    week integer,
    regular_price numeric,
    promo_price numeric,
    promo_mechanics text,
    adv_carrier text,
    adv_material text,
    marketing_type text,
    analog_sku jsonb DEFAULT '[]'::jsonb,
    k_uplift numeric,
    extra_features jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    batch_id uuid
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
    is_active boolean DEFAULT false NOT NULL,
    model_type character varying DEFAULT 'regression'::character varying NOT NULL,
    target character varying DEFAULT 'sales_qty'::character varying NOT NULL,
    features json,
    metrics json,
    model_path text,
    is_deleted boolean DEFAULT false NOT NULL,
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
-- Name: dataset_upload_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_upload_history ALTER COLUMN id SET DEFAULT nextval('public.dataset_upload_history_id_seq'::regclass);


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
-- Name: dataset_upload_history dataset_upload_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_upload_history
    ADD CONSTRAINT dataset_upload_history_pkey PRIMARY KEY (id);


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
-- Name: idx_adv_carrier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_adv_carrier ON public.industrial_dataset_raw USING btree (adv_carrier);


--
-- Name: idx_adv_material; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_adv_material ON public.industrial_dataset_raw USING btree (adv_material);


--
-- Name: idx_analog_sku; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analog_sku ON public.industrial_dataset_raw USING gin (analog_sku);


--
-- Name: idx_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_batch_id ON public.industrial_dataset_raw USING btree (batch_id);


--
-- Name: idx_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category ON public.industrial_dataset_raw USING btree (category);


--
-- Name: idx_extra_features; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extra_features ON public.industrial_dataset_raw USING gin (extra_features);


--
-- Name: idx_format_assortment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_format_assortment ON public.industrial_dataset_raw USING btree (format_assortment);


--
-- Name: idx_history_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_history_date ON public.model_activation_history USING btree (activated_at DESC);


--
-- Name: idx_history_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_history_model ON public.model_activation_history USING btree (model_id);


--
-- Name: idx_k_uplift; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_k_uplift ON public.industrial_dataset_raw USING btree (k_uplift);


--
-- Name: idx_marketing_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_marketing_type ON public.industrial_dataset_raw USING btree (marketing_type);


--
-- Name: idx_ml_audit_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_audit_created ON public.ml_prediction_audit USING btree (created_at DESC);


--
-- Name: idx_ml_audit_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ml_audit_model ON public.ml_prediction_audit USING btree (model_id);


--
-- Name: idx_month_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_month_week ON public.industrial_dataset_raw USING btree (month, week);


--
-- Name: idx_only_one_active_model; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_only_one_active_model ON public.ml_model USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_promo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_promo_id ON public.industrial_dataset_raw USING btree (promo_id);


--
-- Name: idx_promo_mechanics; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_promo_mechanics ON public.industrial_dataset_raw USING btree (promo_mechanics);


--
-- Name: idx_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_region ON public.industrial_dataset_raw USING btree (region);


--
-- Name: idx_sku; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sku ON public.industrial_dataset_raw USING btree (sku);


--
-- Name: idx_sku_store_promo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sku_store_promo ON public.industrial_dataset_raw USING btree (sku, store_id, promo_id);


--
-- Name: idx_store_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_store_id ON public.industrial_dataset_raw USING btree (store_id);


--
-- Name: idx_store_location_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_store_location_type ON public.industrial_dataset_raw USING btree (store_location_type);


--
-- Name: idx_upload_history_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_upload_history_batch ON public.dataset_upload_history USING btree (batch_id);


--
-- Name: idx_upload_history_uploaded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_upload_history_uploaded_at ON public.dataset_upload_history USING btree (uploaded_at DESC);


--
-- Name: ix_prediction_ml_model_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_prediction_ml_model_id ON public.prediction USING btree (ml_model_id);


--
-- Name: uq_ml_model_name_version; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ml_model_name_version ON public.ml_model USING btree (name, version);


--
-- Name: prediction fk_prediction_ml_model_id_ml_model; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction
    ADD CONSTRAINT fk_prediction_ml_model_id_ml_model FOREIGN KEY (ml_model_id) REFERENCES public.ml_model(id);


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

\unrestrict 3aONZSEeNzaM5ST90jaw0cv4WanzKPT8fPJga8MUuno3YNg6vxHsg6OAvKthmlE

