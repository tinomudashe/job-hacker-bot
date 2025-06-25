-- Drop all tables
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS job_listings;
DROP TABLE IF EXISTS alembic_version;

-- Drop any sequences
DROP SEQUENCE IF EXISTS users_id_seq;
DROP SEQUENCE IF EXISTS job_listings_id_seq;
DROP SEQUENCE IF EXISTS applications_id_seq;
DROP SEQUENCE IF EXISTS notifications_id_seq;
DROP SEQUENCE IF EXISTS documents_id_seq;
