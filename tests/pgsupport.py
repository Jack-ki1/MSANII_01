"""Run the whole suite against PostgreSQL by exporting MSANII_TEST_PG_URL, e.g.
   MSANII_TEST_PG_URL='postgresql://postgres@localhost:55432/msanii_test?host=/tmp' python -m pytest
Each test starts from a freshly rebuilt `public` schema built from supabase_schema.sql. Without the variable the suite uses SQLite."""
import os
PG_URL = os.getenv("MSANII_TEST_PG_URL")

def prepare():
    """Call from setUp BEFORE create_app. Returns True when running on PostgreSQL."""
    if not PG_URL:
        os.environ.pop("SUPABASE_DB_URL", None); os.environ.pop("DATABASE_URL", None); os.environ.pop("POSTGRES_URL", None)
        return False
    import psycopg2
    import importlib; dbmod = importlib.import_module("msanii.db")        # `msanii.db` the module (the package also exports a function called db)
    dbmod.reset_pool(); os.environ["SUPABASE_DB_URL"] = PG_URL
    raw = psycopg2.connect(PG_URL); raw.autocommit = True
    with raw.cursor() as c: c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    raw.close(); dbmod.apply_pg_schema(os.path.join(os.path.dirname(__file__), "..", "supabase_schema.sql"))
    return True
