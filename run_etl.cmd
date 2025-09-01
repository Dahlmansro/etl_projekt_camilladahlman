@echo off
chcp 65001 >NUL

set "CONDA_ROOT=C:\Users\CD\anaconda3"
set "ENV_NAME=etl_vader"
set "PROJ=C:\Users\CD\python_2\etl_vader"

call "%CONDA_ROOT%\condabin\conda.bat" activate %ENV_NAME%

cd /d "%PROJ%"
python -u "%PROJ%\src\main.py"

exit /b %ERRORLEVEL%