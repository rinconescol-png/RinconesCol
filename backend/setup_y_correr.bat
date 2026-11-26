@echo off
REM ==========================================================================
REM  Setup y arranque de RinconesCol backend.
REM  IMPORTANTE: este archivo debe estar DENTRO de la carpeta backend/
REM  (al mismo nivel que main.py, requirements.txt, db/, scripts/, etc.)
REM ==========================================================================

cd /d "%~dp0"

echo.
echo ==== Nombre de tu base de datos en PostgreSQL ====
set /p DBNAME="Escribe el nombre de tu base de datos (por defecto RinconesCol): "
if "%DBNAME%"=="" set DBNAME=RinconesCol

echo.
echo ==== Usuario de PostgreSQL ====
set /p PGUSER="Usuario de PostgreSQL (por defecto postgres): "
if "%PGUSER%"=="" set PGUSER=postgres

echo.
echo ==== Corriendo migraciones contra la base "%DBNAME%" ====
echo (te va a pedir la contrasena de PostgreSQL varias veces)
echo.

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_socios.sql
if errorlevel 1 goto :error

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_convenio.sql
if errorlevel 1 goto :error

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_frontend.sql
if errorlevel 1 goto :error

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_contacto.sql
if errorlevel 1 goto :error

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_perfil.sql
if errorlevel 1 goto :error

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_atracciones_itinerario.sql
if errorlevel 1 goto :error

psql -h 127.0.0.1 -U %PGUSER% -d %DBNAME% -f db\migration_password_reset.sql
if errorlevel 1 goto :error

echo.
echo ==== Migraciones aplicadas correctamente ====
echo.

echo ==== Creando entorno virtual (si no existe) ====
if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate.bat

echo.
echo ==== Instalando dependencias (puede tardar un poco) ====
pip install -r requirements.txt

echo.
echo ==== Creando usuario administrador ====
echo (te va a pedir nombre, correo y contrasena)
python scripts\crear_admin.py

echo.
echo ==== Levantando el backend en http://127.0.0.1:8000 ====
echo (dejalo corriendo; abre el frontend en OTRA ventana/terminal)
echo.
uvicorn main:app --reload

goto :eof

:error
echo.
echo *** Hubo un error corriendo una migracion. Revisa el mensaje de arriba. ***
echo *** Verifica: el nombre de la base, el usuario, la contrasena, y que    ***
echo *** psql este en tu PATH.                                              ***
pause
