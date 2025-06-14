@echo off
REM Activar entorno virtual (editá esta línea si usás uno)
call .venv\Scripts\activate

REM Ir al directorio del proyecto (editá según corresponda)
cd mcpchat

REM Correr el servidor en todas las interfaces (puerto 8000)
python manage.py runserver 0.0.0.0:8000

pause
