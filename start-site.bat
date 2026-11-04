@echo off
setlocal
cd /d "%~dp0"

rem ============================================================
rem  Programming Rust - local site launcher
rem  Double-click this file: it builds the site and opens the page.
rem  Keep the window open while reading; Ctrl+C stops the server.
rem ============================================================

set "PORT=5173"
set "URL=http://localhost:%PORT%/ProgrammingRust/"

rem --- 1. server already running? just open the browser ---
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>&1
if not errorlevel 1 (
  echo Site is already running, opening %URL%
  start "" "%URL%"
  exit /b 0
)

rem --- 2. make sure pandoc is reachable ---
where pandoc >nul 2>&1
if errorlevel 1 if exist "%LOCALAPPDATA%\Pandoc\pandoc.exe" set "PATH=%LOCALAPPDATA%\Pandoc;%PATH%"
where pandoc >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERROR] pandoc not found in PATH.
  echo Install it with:  winget install JohnMacFarlane.Pandoc
  echo.
  pause
  exit /b 1
)

rem --- 3. first run needs node_modules ---
if not exist "node_modules" (
  echo Installing dependencies for the first time...
  call npm ci
  if errorlevel 1 (
    echo [ERROR] npm ci failed.
    pause
    exit /b 1
  )
)

echo.
echo Building markdown from LaTeX and starting the site...
echo The browser will open automatically once it is ready.
echo Keep this window open. Press Ctrl+C to stop the server.
echo.

rem --- 4. wait for the port in background, then open the browser ---
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$u='%URL%';for($i=0;$i -lt 240;$i++){try{$r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 3;if($r.StatusCode -ge 200){Start-Process $u;break}}catch{};Start-Sleep -Milliseconds 500}"

rem --- 5. run the dev server in this window so logs stay visible ---
call npm run dev -- --port %PORT% --host 127.0.0.1

echo.
echo Server stopped.
pause
