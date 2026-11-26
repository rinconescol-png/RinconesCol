import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(override=True)

PG_HOST     = os.environ["PG_HOST"]
PG_PORT     = int(os.environ["PG_PORT"])
PG_USER     = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
PG_DATABASE = os.environ["PG_DATABASE"]


class ConnectDB:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Establecer o restaurar la conexión a PostgreSQL"""
        try:
            if self.connection is None or self.connection.closed != 0:
                self.connection = psycopg2.connect(
                    host=PG_HOST,
                    port=PG_PORT,
                    user=PG_USER,
                    password=PG_PASSWORD,
                    dbname=PG_DATABASE,
                    # Fuerza UTF-8 en el cliente: en Windows psycopg2 a veces
                    # toma el codepage local (ej. cp1252) y lanza
                    # UnicodeDecodeError al leer tildes/ñ desde PostgreSQL.
                    client_encoding="UTF8",
                )
                self.connection.autocommit = False
                print("Conexión Exitosa a PostgreSQL")
        except Exception as e:
            print(f"Error al conectar: {e}")
            self.connection = None
        return self.connection

    def close_connection(self):
        """Cerrar la conexión si está activa"""
        if self.connection and self.connection.closed == 0:
            self.connection.close()
            print("Conexión cerrada")


db_conn = ConnectDB()


def get_db_connection():
    """Devuelve la conexión activa, reconectando si es necesario."""
    return db_conn.connect()
