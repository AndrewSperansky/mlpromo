--
-- PostgreSQL database dump
--

\restrict qoREVmUoghiaFY2XPT4hR389qN8sYl75wiKocOAyS0OdUibNLW3DCWSKZWVp08g

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: ml_model; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ml_model (
    name character varying(100) NOT NULL,
    algorithm character varying(50) NOT NULL,
    version character varying(20) NOT NULL,
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
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public.ml_model OWNER TO postgres;

--
-- Name: ml_model_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ml_model_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ml_model_id_seq OWNER TO postgres;

--
-- Name: ml_model_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ml_model_id_seq OWNED BY public.ml_model.id;


--
-- Name: prediction; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.prediction OWNER TO postgres;

--
-- Name: prediction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.prediction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.prediction_id_seq OWNER TO postgres;

--
-- Name: prediction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.prediction_id_seq OWNED BY public.prediction.id;


--
-- Name: product; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product (
    sku character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.product OWNER TO postgres;

--
-- Name: COLUMN product.is_deleted; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.is_deleted IS '╨Ь╤П╨│╨║╨╛╨╡ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╡';


--
-- Name: COLUMN product.deleted_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.deleted_at IS '╨Т╤А╨╡╨╝╤П ╨╝╤П╨│╨║╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П (UTC)';


--
-- Name: product_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.product_id_seq OWNER TO postgres;

--
-- Name: product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.product_id_seq OWNED BY public.product.id;


--
-- Name: promo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.promo (
    code character varying(50) NOT NULL,
    start_date timestamp with time zone DEFAULT now() NOT NULL,
    end_date timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.promo OWNER TO postgres;

--
-- Name: COLUMN promo.is_deleted; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.promo.is_deleted IS '╨Ь╤П╨│╨║╨╛╨╡ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╡';


--
-- Name: COLUMN promo.deleted_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.promo.deleted_at IS '╨Т╤А╨╡╨╝╤П ╨╝╤П╨│╨║╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П (UTC)';


--
-- Name: promo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.promo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.promo_id_seq OWNER TO postgres;

--
-- Name: promo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.promo_id_seq OWNED BY public.promo.id;


--
-- Name: promo_position; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.promo_position (
    promo_id integer NOT NULL,
    product_id integer NOT NULL,
    date date NOT NULL,
    price double precision NOT NULL,
    discount double precision NOT NULL,
    sales_qty integer NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.promo_position OWNER TO postgres;

--
-- Name: COLUMN promo_position.date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.promo_position.date IS '╨Ф╨░╤В╨░ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П ╨┐╤А╨╛╨╝╨╛';


--
-- Name: COLUMN promo_position.is_deleted; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.promo_position.is_deleted IS '╨Ь╤П╨│╨║╨╛╨╡ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╡';


--
-- Name: COLUMN promo_position.deleted_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.promo_position.deleted_at IS '╨Т╤А╨╡╨╝╤П ╨╝╤П╨│╨║╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П (UTC)';


--
-- Name: promo_ml_dataset_v1; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.promo_ml_dataset_v1 AS
 SELECT pp.date,
    p.code AS promo_code,
    pr.sku,
    pp.price,
    pp.discount,
    pp.sales_qty AS target_sales_qty,
    avg(pp.sales_qty) OVER (PARTITION BY pr.id ORDER BY pp.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS avg_sales_7d,
    avg(pp.discount) OVER (PARTITION BY pr.id ORDER BY pp.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS avg_discount_7d,
    ((p.end_date)::date - pp.date) AS promo_days_left
   FROM ((public.promo_position pp
     JOIN public.promo p ON ((p.id = pp.promo_id)))
     JOIN public.product pr ON ((pr.id = pp.product_id)))
  WHERE ((pp.is_deleted = false) AND (p.is_deleted = false) AND (pr.is_deleted = false));


ALTER TABLE public.promo_ml_dataset_v1 OWNER TO postgres;

--
-- Name: promo_position_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.promo_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.promo_position_id_seq OWNER TO postgres;

--
-- Name: promo_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.promo_position_id_seq OWNED BY public.promo_position.id;


--
-- Name: ml_model id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ml_model ALTER COLUMN id SET DEFAULT nextval('public.ml_model_id_seq'::regclass);


--
-- Name: prediction id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prediction ALTER COLUMN id SET DEFAULT nextval('public.prediction_id_seq'::regclass);


--
-- Name: product id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product ALTER COLUMN id SET DEFAULT nextval('public.product_id_seq'::regclass);


--
-- Name: promo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo ALTER COLUMN id SET DEFAULT nextval('public.promo_id_seq'::regclass);


--
-- Name: promo_position id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo_position ALTER COLUMN id SET DEFAULT nextval('public.promo_position_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
7e6016d1dcbb
\.


--
-- Data for Name: ml_model; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ml_model (name, algorithm, version, id, created_at, updated_at, trained_at, is_active, model_type, target, features, metrics, model_path, is_deleted) FROM stdin;
baseline_catboost	catboost	v1	1	2026-01-12 14:43:52.486875+00	2026-01-12 14:43:52.486875+00	2026-01-12 14:43:52.486875+00	t	regression	sales_qty	\N	\N	\N	f
\.


--
-- Data for Name: prediction; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.prediction (id, ml_model_id, predicted_sales_qty, created_at, updated_at, promo_code, sku, date, features, fallback_used) FROM stdin;
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.product (sku, name, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
MILK_1L	╨Ь╨╛╨╗╨╛╨║╨╛ 1╨╗	1	2025-12-30 07:56:40.031375+00	2025-12-30 07:56:40.031375+00	f	\N
CHEESE_200G	╨б╤Л╤А 200╨│	2	2025-12-30 07:56:40.031375+00	2025-12-30 07:56:40.031375+00	f	\N
\.


--
-- Data for Name: promo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.promo (code, start_date, end_date, is_active, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
PROMO_DAIRY_JAN	2025-01-01 00:00:00+00	2025-01-31 00:00:00+00	t	1	2025-12-30 08:45:39.956942+00	2025-12-30 14:50:38.753645+00	f	\N
\.


--
-- Data for Name: promo_position; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.promo_position (promo_id, product_id, date, price, discount, sales_qty, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
1	1	2025-01-05	69.4	10.5	132	1	2025-12-30 08:45:40.027207+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-05	126.9	13	72	2	2025-12-30 08:45:40.027207+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-01	69.9	10	120	3	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-02	69.4	10.5	123	4	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-03	68.9	11	126	5	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-04	69.9	10	129	6	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-06	68.9	11	135	7	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-07	69.9	10	138	8	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-08	69.4	10.5	141	9	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-09	68.9	11	144	10	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-10	69.9	10	147	11	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-11	69.4	10.5	150	12	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-12	68.9	11	153	13	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-13	69.9	10	156	14	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	1	2025-01-14	69.4	10.5	159	15	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-01	127.4	12.5	60	16	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-02	126.9	13	63	17	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-03	126.4	13.5	66	18	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-04	127.4	12.5	69	19	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-06	126.4	13.5	75	20	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-07	127.4	12.5	78	21	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-08	126.9	13	81	22	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-09	126.4	13.5	84	23	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-10	127.4	12.5	87	24	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-11	126.9	13	90	25	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-12	126.4	13.5	93	26	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-13	127.4	12.5	96	27	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
1	2	2025-01-14	126.9	13	99	28	2025-12-30 14:50:38.831552+00	2025-12-30 14:50:38.831552+00	f	\N
\.


--
-- Name: ml_model_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ml_model_id_seq', 1, true);


--
-- Name: prediction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.prediction_id_seq', 1, false);


--
-- Name: product_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.product_id_seq', 2, true);


--
-- Name: promo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.promo_id_seq', 1, true);


--
-- Name: promo_position_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.promo_position_id_seq', 28, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: ml_model pk_ml_model; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ml_model
    ADD CONSTRAINT pk_ml_model PRIMARY KEY (id);


--
-- Name: prediction pk_prediction; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prediction
    ADD CONSTRAINT pk_prediction PRIMARY KEY (id);


--
-- Name: product pk_product; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT pk_product PRIMARY KEY (id);


--
-- Name: promo pk_promo; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo
    ADD CONSTRAINT pk_promo PRIMARY KEY (id);


--
-- Name: promo_position pk_promo_position; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo_position
    ADD CONSTRAINT pk_promo_position PRIMARY KEY (id);


--
-- Name: ml_model uq_ml_model_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ml_model
    ADD CONSTRAINT uq_ml_model_name UNIQUE (name);


--
-- Name: promo_position uq_promo_position_promo_product_date; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo_position
    ADD CONSTRAINT uq_promo_position_promo_product_date UNIQUE (promo_id, product_id, date);


--
-- Name: ix_prediction_ml_model_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_prediction_ml_model_id ON public.prediction USING btree (ml_model_id);


--
-- Name: ix_product_sku; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_product_sku ON public.product USING btree (sku);


--
-- Name: ix_promo_position_product_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_promo_position_product_id ON public.promo_position USING btree (product_id);


--
-- Name: ix_promo_position_promo_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_promo_position_promo_id ON public.promo_position USING btree (promo_id);


--
-- Name: ix_promo_promo_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_promo_promo_code ON public.promo USING btree (code);


--
-- Name: prediction fk_prediction_ml_model_id_ml_model; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prediction
    ADD CONSTRAINT fk_prediction_ml_model_id_ml_model FOREIGN KEY (ml_model_id) REFERENCES public.ml_model(id);


--
-- Name: promo_position fk_promo_position_product_id_product; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo_position
    ADD CONSTRAINT fk_promo_position_product_id_product FOREIGN KEY (product_id) REFERENCES public.product(id);


--
-- Name: promo_position fk_promo_position_promo_id_promo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.promo_position
    ADD CONSTRAINT fk_promo_position_promo_id_promo FOREIGN KEY (promo_id) REFERENCES public.promo(id);


--
-- PostgreSQL database dump complete
--

\unrestrict qoREVmUoghiaFY2XPT4hR389qN8sYl75wiKocOAyS0OdUibNLW3DCWSKZWVp08g

