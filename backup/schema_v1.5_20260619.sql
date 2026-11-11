--
-- PostgreSQL database dump
--

\restrict TVp9ycpfkz3dJK97zJpjAaPZkrzApnozyxtSBpIFAtNfcdOVB3bwihewfjagiE9

-- Dumped from database version 15.18 (Debian 15.18-1.pgdg13+1)
-- Dumped by pg_dump version 15.18 (Debian 15.18-1.pgdg13+1)

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

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'admin',
    'ml_engineer',
    'analyst',
    'viewer'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: average_cheque; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.average_cheque (
    date date NOT NULL,
    store_code character varying(50) NOT NULL,
    store_name character varying(200),
    cheque_count integer NOT NULL,
    total_amount numeric(15,2) NOT NULL,
    average_amount numeric(15,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    week integer
);


--
-- Name: calendar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.calendar (
    date date NOT NULL,
    day_type character varying(50) NOT NULL,
    week integer NOT NULL,
    year integer NOT NULL,
    is_weekend boolean GENERATED ALWAYS AS (((day_type)::text = ANY ((ARRAY['Суббота'::character varying, 'Воскресенье'::character varying])::text[]))) STORED,
    is_holiday boolean GENERATED ALWAYS AS (((day_type)::text = ANY ((ARRAY['Праздник'::character varying, 'Предпраздничный'::character varying])::text[]))) STORED,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


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
-- Name: exchange_rates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exchange_rates (
    currency character varying(3) NOT NULL,
    date date NOT NULL,
    rate numeric(12,4) NOT NULL,
    nominal integer DEFAULT 1,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


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
-- Name: purchase_price_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.purchase_price_history (
    date date NOT NULL,
    sku character varying(50) NOT NULL,
    supplier character varying(100) NOT NULL,
    price numeric(15,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: retail_price_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.retail_price_history (
    date date NOT NULL,
    sku_code character varying(50) NOT NULL,
    price numeric(15,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    category character varying(100),
    week integer,
    sku_name character varying(200)
);


--
-- Name: sales_fact; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sales_fact (
    date date NOT NULL,
    sku_code character varying(50) NOT NULL,
    sku_name character varying(200),
    store_code character varying(50) NOT NULL,
    store_name character varying(200),
    region character varying(100),
    oblast character varying(100),
    uom character varying(20),
    quantity integer NOT NULL,
    revenue numeric(15,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    category character varying(100),
    week integer
);


--
-- Name: user_activities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_activities (
    id integer NOT NULL,
    user_id integer NOT NULL,
    action character varying(50) NOT NULL,
    resource character varying(200),
    details text,
    ip_address character varying(45),
    user_agent character varying(500),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_activities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_activities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_activities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_activities_id_seq OWNED BY public.user_activities.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    hashed_password character varying(200) NOT NULL,
    full_name character varying(100),
    role public.userrole DEFAULT 'viewer'::public.userrole,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login_at timestamp with time zone
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


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
-- Name: user_activities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activities ALTER COLUMN id SET DEFAULT nextval('public.user_activities_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: average_cheque average_cheque_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.average_cheque
    ADD CONSTRAINT average_cheque_pkey PRIMARY KEY (date, store_code);


--
-- Name: calendar calendar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calendar
    ADD CONSTRAINT calendar_pkey PRIMARY KEY (date);


--
-- Name: dataset_upload_history dataset_upload_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_upload_history
    ADD CONSTRAINT dataset_upload_history_pkey PRIMARY KEY (id);


--
-- Name: exchange_rates exchange_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT exchange_rates_pkey PRIMARY KEY (currency, date);


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
-- Name: purchase_price_history purchase_price_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_price_history
    ADD CONSTRAINT purchase_price_history_pkey PRIMARY KEY (date, sku, supplier);


--
-- Name: retail_price_history retail_price_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retail_price_history
    ADD CONSTRAINT retail_price_history_pkey PRIMARY KEY (date, sku_code);


--
-- Name: sales_fact sales_fact_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sales_fact
    ADD CONSTRAINT sales_fact_pkey PRIMARY KEY (date, sku_code, store_code);


--
-- Name: user_activities user_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activities
    ADD CONSTRAINT user_activities_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_activities_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activities_action ON public.user_activities USING btree (action);


--
-- Name: idx_activities_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activities_created_at ON public.user_activities USING btree (created_at DESC);


--
-- Name: idx_activities_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activities_user_id ON public.user_activities USING btree (user_id);


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
-- Name: idx_average_cheque_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_average_cheque_week ON public.average_cheque USING btree (week);


--
-- Name: idx_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_batch_id ON public.industrial_dataset_raw USING btree (batch_id);


--
-- Name: idx_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category ON public.industrial_dataset_raw USING btree (category);


--
-- Name: idx_exchange_rates_currency_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exchange_rates_currency_date ON public.exchange_rates USING btree (currency, date DESC);


--
-- Name: idx_exchange_rates_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exchange_rates_date ON public.exchange_rates USING btree (date);


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
-- Name: idx_purchase_price_sku_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_purchase_price_sku_date ON public.purchase_price_history USING btree (sku, date DESC);


--
-- Name: idx_purchase_price_supplier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_purchase_price_supplier ON public.purchase_price_history USING btree (supplier);


--
-- Name: idx_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_region ON public.industrial_dataset_raw USING btree (region);


--
-- Name: idx_retail_price_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_retail_price_category ON public.retail_price_history USING btree (category);


--
-- Name: idx_retail_price_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_retail_price_date ON public.retail_price_history USING btree (date);


--
-- Name: idx_retail_price_sku_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_retail_price_sku_date ON public.retail_price_history USING btree (sku_code, date DESC);


--
-- Name: idx_retail_price_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_retail_price_week ON public.retail_price_history USING btree (week);


--
-- Name: idx_sales_region_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sales_region_date ON public.sales_fact USING btree (region, date);


--
-- Name: idx_sales_sku_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sales_sku_date ON public.sales_fact USING btree (sku_code, date);


--
-- Name: idx_sales_store_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sales_store_date ON public.sales_fact USING btree (store_code, date);


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
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_is_active ON public.users USING btree (is_active);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


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

\unrestrict TVp9ycpfkz3dJK97zJpjAaPZkrzApnozyxtSBpIFAtNfcdOVB3bwihewfjagiE9

