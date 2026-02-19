import os
import psycopg
from psycopg.rows import dict_row

from ..schemas.posts import DBConfig
from .helpers import _load_json

DB_CONFIG = _load_json("db_config.json")


def _resolve_env_reference(value):
    if isinstance(value, str) and value.startswith("env:"):
        env_var = value.split("env:", 1)[1].strip()
        env_value = os.getenv(env_var)
        if not env_value:
            raise ValueError(f"Environment variable '{env_var}' is not set")
        return env_value
    return value


def get_db_connection(env: str = "local"):
    """
    Establishes and returns a new database connection and cursor using psycopg (psycopg3).

    Args:
        env (str): Environment configuration key (default: "local").
                   Must match a key in db_config.json

    Returns:
        conn: psycopg.Connection object
        cur: psycopg.Cursor object

    Raises:
        Exception: If the connection to the database fails or environment config not found.
    """
    try:
        # Get config for the specified environment
        db_config = DB_CONFIG[0].get(env)
        if not db_config:
            raise KeyError(f"Environment '{env}' not found in db_config.json")

        conn = psycopg.connect(
            host=_resolve_env_reference(db_config["host"]),
            port=_resolve_env_reference(db_config["port"]),
            dbname=_resolve_env_reference(db_config["dbname"]),
            user=_resolve_env_reference(db_config["user"]),
            password=_resolve_env_reference(db_config["password"]),
            row_factory=dict_row
        )
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        raise Exception(f"Failed to connect to the database: {e}")


def __get_cursor(envName: str):
    conn, cur = get_db_connection(env=envName)
    return conn, cur


def get_posts_from_db():
    conn, cursor = get_db_connection()
    try:
        cursor.execute("""SELECT * FROM posts""")
        posts = cursor.fetchall()
        return posts
    finally:
        conn.close()


def get_post_from_db(post_id: int):
    conn, cursor = get_db_connection()
    try:
        cursor.execute("""SELECT * FROM posts WHERE id = %s""", (post_id,))
        post = cursor.fetchone()
        return post
    finally:
        conn.close()


def create_post_in_db(post: dict):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            """INSERT INTO posts (title, content) VALUES (%s, %s) RETURNING *""",
            (post["title"], post["content"])
        )
        new_post = cursor.fetchone()
        conn.commit()
        return new_post
    finally:
        conn.close()


def update_post_in_db(post_id: int, post: dict):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            """UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING *""",
            (post["title"], post["content"], post["published"], post_id)
        )
        updated_post = cursor.fetchone()
        conn.commit()
        return updated_post
    finally:
        conn.close()


def delete_post_from_db(post_id: int):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            """DELETE FROM posts WHERE id = %s RETURNING *""",
            (post_id,)
        )
        deleted_post = cursor.fetchone()
        conn.commit()
        return deleted_post
    finally:
        conn.close()
