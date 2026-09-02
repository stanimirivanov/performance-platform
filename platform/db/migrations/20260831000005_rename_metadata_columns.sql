-- Rename `metadata` columns to `attributes` to avoid SQLAlchemy reserved attribute collision.
-- The column stores extra fields like labels, annotations, etc.

ALTER TABLE metadata.resource_snapshots RENAME COLUMN metadata TO attributes;
ALTER TABLE metadata.correlation_events RENAME COLUMN metadata TO attributes;