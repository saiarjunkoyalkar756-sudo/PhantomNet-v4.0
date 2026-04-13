from logging.config import fileConfig
import sys
import os
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv # Import load_dotenv

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import sys
import os
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend_api.shared.database import Base
target_metadata = Base.metadata

# Call load_dotenv() to ensure environment variables are loaded
load_dotenv()

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
    # Dynamically construct the URL from environment variables
    # This ensures that Alembic picks up the correct DB connection details
    # when run directly on the host.
    # db_user = os.getenv("DB_USER", "phantomnet")
    # db_password = os.getenv("DB_PASSWORD")
    # db_host = os.getenv("DB_HOST", "localhost")
    # db_port = os.getenv("DB_PORT", "5432")
    # db_name = os.getenv("DB_NAME", "phantomnet_db")
    # sqlalchemy_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    sqlalchemy_url = "sqlite:///maindb.db"

    # Update the config object with the dynamically constructed URL
    # This ensures engine_from_config uses the correct URL
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)

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
