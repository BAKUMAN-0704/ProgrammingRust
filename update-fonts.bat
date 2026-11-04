@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"

echo ================================================
echo  Rebuild subset web fonts
echo ================================================
echo.

rem --- 1. pick an interpreter: py -3 first, plain python as fallback ---
set "PYCMD="
where py >nul 2>&1
if not errorlevel 1 set "PYCMD=py -3"
if not defined PYCMD (
  where python >nul 2>&1
  if not errorlevel 1 set "PYCMD=python"
)
if not defined PYCMD (
  echo [ERROR] No Python found.
  echo Install Python 3 from https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

for /f "delims=" %%i in ('%PYCMD% -c "import sys;print(sys.version.split()[0])"') do set "PYVER=%%i"
for /f "delims=" %%i in ('%PYCMD% -c "import sys;print(sys.executable)"') do set "PYEXE=%%i"
echo Interpreter : %PYVER%
echo Path        : %PYEXE%
echo.

rem --- 2. dependencies ---
%PYCMD% -c "import fontTools, brotli" >nul 2>&1
if errorlevel 1 (
  echo fonttools / brotli not found, installing ...
  %PYCMD% -m pip install --quiet --disable-pip-version-check fonttools brotli
  if errorlevel 1 (
    echo.
    echo [ERROR] pip install failed. Run it manually:
    echo   %PYCMD% -m pip install fonttools brotli
    echo.
    pause
    exit /b 1
  )
)

rem --- 3. generate the woff2 files ---
echo Generating subsets from site content ...
echo.
%PYCMD% scripts\subset-fonts.py
if errorlevel 1 (
  echo.
  echo [ERROR] Subsetting failed, see the messages above.
  echo.
  pause
  exit /b 1
)

echo.
echo Done. Output: .vitepress\theme\fonts
echo Dev server running? Refresh the page with Ctrl+F5.
echo For a production build, run: npm run build
echo.
pause
