from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import sys
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models_db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Load environment variables from .env
load_dotenv()

# Set the database URL from environment variables
# This ensures Alembic uses the same database as the application
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# URL-encode the password to handle special characters, and construct the URL
if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    encoded_password = quote_plus(DB_PASSWORD)
    database_url = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Escape the '%' character for the config parser by replacing it with '%%'
    escaped_database_url = database_url.replace("%", "%%")
    config.set_main_option("sqlalchemy.url", escaped_database_url)
else:
    # Raise a clear error if the environment variables are not fully set.
    raise ValueError(
        "Database connection details are not fully configured. "
        "Please ensure DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, and DB_NAME are set in your .env file."
    )


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
