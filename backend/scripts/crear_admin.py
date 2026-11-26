"""
Crea (o convierte) un usuario administrador en la base de datos.

Uso:
    python scripts/crear_admin.py

Se ejecuta desde la carpeta raíz del backend (donde está main.py), porque
reutiliza la misma conexión y la misma función de hash de contraseñas
(PBKDF2-HMAC-SHA256) que usa el resto de la aplicación — así el admin creado
aquí puede iniciar sesión normalmente por POST /auth/login.
"""
import getpass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.conexion import get_db_connection
from security.security import hash_password


def main():
    print("── Crear usuario administrador ──────────────────────────")
    nombre = input("Nombre completo: ").strip()
    correo = input("Correo: ").strip()
    contrasena = getpass.getpass("Contraseña: ")

    if not nombre or not correo or not contrasena:
        print("Todos los campos son obligatorios.")
        return

    con = get_db_connection()
    if con is None:
        print("No se pudo conectar a la base de datos. Revisa tu .env")
        return

    with con.cursor() as cursor:
        cursor.execute("SELECT id, rol FROM usuarios WHERE correo = %s", (correo,))
        existente = cursor.fetchone()

        if existente:
            usuario_id, rol_actual = existente
            if rol_actual == "admin":
                print(f"El usuario '{correo}' ya es administrador (id={usuario_id}).")
                return
            cursor.execute("UPDATE usuarios SET rol = 'admin' WHERE id = %s", (usuario_id,))
            con.commit()
            print(f"Usuario existente '{correo}' (id={usuario_id}) ascendido a administrador.")
            return

        contrasena_hasheada = hash_password(contrasena)
        cursor.execute(
            """INSERT INTO usuarios (nombre, correo, contrasena, rol)
               VALUES (%s, %s, %s, 'admin') RETURNING id""",
            (nombre, correo, contrasena_hasheada),
        )
        nuevo_id = cursor.fetchone()[0]
        con.commit()
        print(f"Administrador creado con id={nuevo_id}. Ya puede iniciar sesión en /auth/login.")


if __name__ == "__main__":
    main()
