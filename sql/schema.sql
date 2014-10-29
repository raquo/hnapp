--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: hnapp; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE hnapp WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_CA.UTF-8' LC_CTYPE = 'en_CA.UTF-8';


\connect hnapp

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: kind; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE kind AS ENUM (
    'story',
    'comment'
);


--
-- Name: subkind; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE subkind AS ENUM (
    'link',
    'ask',
    'show',
    'poll',
    'job',
    'comment'
);


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: item; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE item (
    id integer NOT NULL,
    root_id integer,
    parent_id integer,
    title character varying(2044),
    body text,
    raw_body text,
    url text,
    domain character varying(2044),
    author character varying(2044),
    score smallint,
    num_comments smallint NOT NULL,
    child_ids text,
    date_posted timestamp without time zone NOT NULL,
    date_updated timestamp without time zone NOT NULL,
    date_entered_fp timestamp without time zone,
    date_left_fp timestamp without time zone,
    deleted smallint NOT NULL,
    dead smallint NOT NULL,
    kind kind NOT NULL,
    subkind subkind NOT NULL,
    title_tsv tsvector,
    body_tsv tsvector
);


--
-- Name: lock; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE lock (
    name character varying(2044) NOT NULL,
    expires_at timestamp without time zone
);


--
-- Name: lost_item; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE lost_item (
    id integer NOT NULL,
    reason character varying(2044) NOT NULL,
    traceback text,
    date_found timestamp without time zone NOT NULL,
    response text
);


--
-- Name: status; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE status (
    name character varying(30) NOT NULL,
    number integer,
    text text,
    date timestamp without time zone
);


--
-- Name: item_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY item
    ADD CONSTRAINT item_pkey PRIMARY KEY (id);


--
-- Name: lock_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY lock
    ADD CONSTRAINT lock_pkey PRIMARY KEY (name);


--
-- Name: missed_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY lost_item
    ADD CONSTRAINT missed_item_pkey PRIMARY KEY (id);


--
-- Name: status_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY status
    ADD CONSTRAINT status_pkey PRIMARY KEY (name);


--
-- Name: index_body_tsv; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_body_tsv ON item USING gin (body_tsv);


--
-- Name: index_date_entered_fp; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_date_entered_fp ON item USING btree (date_entered_fp);


--
-- Name: index_date_posted; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_date_posted ON item USING btree (date_posted);


--
-- Name: index_date_updated; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_date_updated ON item USING btree (date_updated);


--
-- Name: index_num_comments; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_num_comments ON item USING btree (num_comments);


--
-- Name: index_parent_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_parent_id ON item USING btree (parent_id);


--
-- Name: index_root_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_root_id ON item USING btree (root_id);


--
-- Name: index_score; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_score ON item USING btree (score);


--
-- Name: index_title_tsv; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX index_title_tsv ON item USING gin (title_tsv);


--
-- Name: item_body_tsv_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER item_body_tsv_update BEFORE INSERT OR UPDATE ON item FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger('body_tsv', 'pg_catalog.english', 'body');


--
-- Name: item_title_tsv_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER item_title_tsv_update BEFORE INSERT OR UPDATE ON item FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger('title_tsv', 'pg_catalog.english', 'title');


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: kind; Type: ACL; Schema: public; Owner: -
--

REVOKE ALL ON TYPE kind FROM PUBLIC;
REVOKE ALL ON TYPE kind FROM raquo;
GRANT ALL ON TYPE kind TO PUBLIC;


--
-- Name: subkind; Type: ACL; Schema: public; Owner: -
--

REVOKE ALL ON TYPE subkind FROM PUBLIC;
REVOKE ALL ON TYPE subkind FROM raquo;
GRANT ALL ON TYPE subkind TO PUBLIC;


--
-- PostgreSQL database dump complete
--

