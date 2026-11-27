import os
import time
import psycopg2


import os
import time
import re
import sqlite3
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import OperationalError
except ImportError:
    psycopg2 = None
    OperationalError = Exception

SQLITE_DB_PATH = Path(__file__).resolve().parent.parent / "medassist_ai.db"
_PG_AVAILABLE = None


def _check_postgres():
    global _PG_AVAILABLE
    if _PG_AVAILABLE is not None:
        return _PG_AVAILABLE

    if os.getenv("USE_SQLITE", "").lower() in ("true", "1", "yes"):
        _PG_AVAILABLE = False
        return False

    if psycopg2 is None:
        _PG_AVAILABLE = False
        return False

    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "medassist_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "psql@2026"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            connect_timeout=2,
        )
        conn.close()
        _PG_AVAILABLE = True
        return True
    except Exception:
        _PG_AVAILABLE = False
        return False


class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def _translate_query(self, query: str, has_params: bool) -> str:
        s = query
        s = re.sub(r'\bSERIAL\s+PRIMARY\s+KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', s, flags=re.IGNORECASE)
        s = re.sub(
            r"TO_CHAR\s*\(\s*DATE_TRUNC\s*\(\s*'month'\s*,\s*(\w+)\s*\)\s*,\s*'YYYY-MM'\s*\)",
            r"strftime('%Y-%m', \1)",
            s,
            flags=re.IGNORECASE
        )
        s = re.sub(
            r"DATE_TRUNC\s*\(\s*'month'\s*,\s*(\w+)\s*\)",
            r"strftime('%Y-%m', \1)",
            s,
            flags=re.IGNORECASE
        )
        s = re.sub(
            r"NOW\(\)\s*-\s*INTERVAL\s*'12 months'",
            r"datetime('now', '-12 months')",
            s,
            flags=re.IGNORECASE
        )
        if has_params:
            s = s.replace("%s", "?")
        return s

    def execute(self, query, params=None):
        translated = self._translate_query(query, params is not None)
        if params is not None:
            if isinstance(params, (tuple, list)):
                return self._cursor.execute(translated, list(params))
            else:
                return self._cursor.execute(translated, (params,))
        else:
            return self._cursor.execute(translated)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class SQLiteConnectionWrapper:
    def __init__(self, db_path=None):
        self._path = str(db_path or SQLITE_DB_PATH)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON;")

    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def get_database_connection():
    if _check_postgres():
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "medassist_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "psql@2026"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
    return SQLiteConnectionWrapper()


def init_db_tables():
    """Ensure all required database tables exist on startup with retry logic and auto-migrations."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role VARCHAR(30) NOT NULL DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patient_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            date_of_birth DATE,
            gender VARCHAR(20),
            phone VARCHAR(20),
            blood_group VARCHAR(10),
            height_cm NUMERIC(5, 2),
            weight_kg NUMERIC(5, 2),
            emergency_contact_name VARCHAR(100),
            emergency_contact_phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_patient_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS caretaker_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            phone VARCHAR(20) NOT NULL,
            profession VARCHAR(100) NOT NULL,
            organization VARCHAR(150),
            years_of_experience INTEGER,
            specialization VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_caretaker_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patient_symptoms (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            symptom_name VARCHAR(100) NOT NULL,
            severity VARCHAR(50) NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_symptom_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS disease_predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            predicted_disease VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_disease_prediction_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patient_risk_assessments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            fever VARCHAR(10),
            cough VARCHAR(10),
            fatigue VARCHAR(10),
            difficulty_breathing VARCHAR(10),
            age INTEGER,
            gender VARCHAR(20),
            blood_pressure VARCHAR(20),
            cholesterol_level VARCHAR(20),
            predicted_outcome VARCHAR(50),
            positive_model_score NUMERIC(5, 2),
            negative_model_score NUMERIC(5, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_risk_assessment_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patient_reports (
            id SERIAL PRIMARY KEY,
            patient_user_id INTEGER NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            stored_file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            file_type VARCHAR(100) NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_report_patient_user
                FOREIGN KEY (patient_user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patient_assignments (
            id SERIAL PRIMARY KEY,
            patient_user_id INTEGER NOT NULL,
            caretaker_user_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'Active',
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            CONSTRAINT fk_patient
                FOREIGN KEY (patient_user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,
            CONSTRAINT fk_caretaker
                FOREIGN KEY (caretaker_user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,
            CONSTRAINT unique_patient
                UNIQUE (patient_user_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS caretaker_care_plans (
            id SERIAL PRIMARY KEY,
            caretaker_user_id INTEGER NOT NULL,
            patient_user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            diagnosis_notes TEXT,
            medication_advice TEXT,
            dietary_lifestyle TEXT,
            priority VARCHAR(50) DEFAULT 'Standard',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_care_plan_caretaker
                FOREIGN KEY (caretaker_user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,
            CONSTRAINT fk_care_plan_patient
                FOREIGN KEY (patient_user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """
    ]

    alter_statements = [
        "ALTER TABLE caretaker_profiles ADD COLUMN IF NOT EXISTS profession VARCHAR(100);",
        "ALTER TABLE caretaker_profiles ADD COLUMN IF NOT EXISTS organization VARCHAR(150);",
        "ALTER TABLE caretaker_profiles ADD COLUMN IF NOT EXISTS years_of_experience INTEGER;",
        "ALTER TABLE caretaker_profiles ADD COLUMN IF NOT EXISTS specialization VARCHAR(100);",
        "ALTER TABLE caretaker_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(20);",
        "ALTER TABLE caretaker_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE caretaker_profiles ALTER COLUMN phone DROP NOT NULL;",
        "ALTER TABLE caretaker_profiles ALTER COLUMN profession DROP NOT NULL;",
    ]

    for attempt in range(10):
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            for stmt in statements:
                cursor.execute(stmt)
            for stmt in alter_statements:
                try:
                    cursor.execute(stmt)
                except Exception:
                    connection.rollback()
            connection.commit()
            cursor.close()
            connection.close()
            print("Database schema verified, migrated, and initialized successfully.")
            return True
        except Exception as e:
            print(f"Database connection attempt {attempt + 1}/10: {e}. Retrying in 2s...")
            time.sleep(2)

    return False