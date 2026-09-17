@echo off
setlocal EnableExtensions

title Tequaly Workforce Readiness
cd /d "%~dp0"

set "TWR_ROOT=%~dp0"
set "TWR_BACKEND_DIR=%~dp0backend"
set "TWR_FRONTEND_DIR=%~dp0frontend"
set "TWR_LOG_DIR=%~dp0logs"
set "TWR_BACKEND_PYTHON=%~dp0backend\.venv\Scripts\python.exe"
set "TWR_NODE=%~dp0.runtime\node\node.exe"
set "TWR_DATABASE_URL=sqlite:///%TWR_ROOT:\=/%backend/.local/twr-local.db"
set "TWR_FRONTEND_ORIGIN=http://127.0.0.1:3000"
set "TWR_API_HEALTH=http://127.0.0.1:8000/health"
set "TWR_WEB_HEALTH=http://127.0.0.1:3000/health"
set "TWR_APP_URL=http://127.0.0.1:3000/conexoes-mcp"

if not exist "%TWR_LOG_DIR%" mkdir "%TWR_LOG_DIR%"
if not exist "%TWR_BACKEND_DIR%\.local" mkdir "%TWR_BACKEND_DIR%\.local"

where curl.exe >nul 2>&1
if errorlevel 1 goto missing_curl

if not exist "%TWR_BACKEND_PYTHON%" goto missing_runtime
if not exist "%TWR_NODE%" goto missing_runtime
if not exist "%TWR_FRONTEND_DIR%\node_modules\next\dist\bin\next" goto missing_runtime
if not exist "%TWR_FRONTEND_DIR%\.next\BUILD_ID" goto missing_build

echo Verificando os servicos locais...
call :backend_ready
if errorlevel 1 call :start_backend
if errorlevel 1 goto startup_error

call :frontend_ready
if errorlevel 1 call :start_frontend
if errorlevel 1 goto startup_error

set /a TWR_ATTEMPT=0
:wait_for_services
call :backend_ready
set "TWR_BACKEND_STATUS=%errorlevel%"
call :frontend_ready
set "TWR_FRONTEND_STATUS=%errorlevel%"

if "%TWR_BACKEND_STATUS%"=="0" if "%TWR_FRONTEND_STATUS%"=="0" goto services_ready

set /a TWR_ATTEMPT+=1
if %TWR_ATTEMPT% GEQ 60 goto health_timeout
ping.exe -n 2 127.0.0.1 >nul
goto wait_for_services

:services_ready
echo TWR iniciado em %TWR_APP_URL%
if /i "%TWR_NO_BROWSER%"=="1" exit /b 0

set "TWR_CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%TWR_CHROME%" set "TWR_CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%TWR_CHROME%" set "TWR_CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if exist "%TWR_CHROME%" (
  start "" "%TWR_CHROME%" "%TWR_APP_URL%"
) else (
  start "" "%TWR_APP_URL%"
)
exit /b 0

:start_backend
echo Preparando banco de dados local...
pushd "%TWR_BACKEND_DIR%"
"%TWR_BACKEND_PYTHON%" -m alembic upgrade head >> "%TWR_LOG_DIR%\migration.log" 2>&1
set "TWR_MIGRATION_STATUS=%errorlevel%"
popd
if not "%TWR_MIGRATION_STATUS%"=="0" exit /b 1

echo Iniciando API...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$process = Start-Process -FilePath $env:TWR_BACKEND_PYTHON -ArgumentList @('-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port','8000') -WorkingDirectory $env:TWR_BACKEND_DIR -WindowStyle Hidden -RedirectStandardOutput ($env:TWR_LOG_DIR + '\backend.out.log') -RedirectStandardError ($env:TWR_LOG_DIR + '\backend.err.log') -PassThru; Set-Content -LiteralPath ($env:TWR_LOG_DIR + '\backend.pid') -Value $process.Id"
exit /b %errorlevel%

:start_frontend
echo Iniciando interface...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$process = Start-Process -FilePath $env:TWR_NODE -ArgumentList @('node_modules\next\dist\bin\next','start','-H','127.0.0.1','-p','3000') -WorkingDirectory $env:TWR_FRONTEND_DIR -WindowStyle Hidden -RedirectStandardOutput ($env:TWR_LOG_DIR + '\frontend.out.log') -RedirectStandardError ($env:TWR_LOG_DIR + '\frontend.err.log') -PassThru; Set-Content -LiteralPath ($env:TWR_LOG_DIR + '\frontend.pid') -Value $process.Id"
exit /b %errorlevel%

:backend_ready
curl.exe --silent --fail --max-time 2 "%TWR_API_HEALTH%" >nul 2>&1
exit /b %errorlevel%

:frontend_ready
curl.exe --silent --fail --max-time 2 "%TWR_WEB_HEALTH%" >nul 2>&1
exit /b %errorlevel%

:missing_curl
echo ERRO: o recurso curl.exe do Windows nao foi encontrado.
goto show_error

:missing_runtime
echo ERRO: os componentes offline nao estao completos nesta pasta.
goto show_error

:missing_build
echo ERRO: o build de producao do frontend nao foi encontrado.
goto show_error

:health_timeout
echo ERRO: os servicos nao ficaram prontos em 60 segundos.
goto show_error

:startup_error
echo ERRO: nao foi possivel iniciar um dos servicos.

:show_error
echo Consulte os arquivos em "%TWR_LOG_DIR%" para detalhes.
pause
exit /b 1
