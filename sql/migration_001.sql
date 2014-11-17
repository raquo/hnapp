BEGIN;

-- CREATE INDEX "index_domain" ---------------------------------
CREATE INDEX "index_domain" ON "public"."item" USING hash( "domain" );
-- -------------------------------------------------------------

-- CREATE INDEX "index_subkind" --------------------------------
CREATE INDEX "index_subkind" ON "public"."item" USING hash( "subkind" );
-- -------------------------------------------------------------;

COMMIT;
