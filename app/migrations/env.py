from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import DB_USER, DB_PASS, DB_HOST, DB_NAME
from app.models import Base  # Импортируем общий Base

config = context.config

# Настройка SQLAlchemy URL
sqlalchemy_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
config.set_main_option("sqlalchemy.url", sqlalchemy_url)

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Настройка target_metadata
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
