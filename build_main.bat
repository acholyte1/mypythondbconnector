@echo off
setlocal

REM === Step 1: Create virtual environment if needed ===
if not exist "venv" (
    echo Creating virtual environment...
    py -3.11 -m venv venv
)

REM === Step 2: Activate virtual environment ===
call venv\Scripts\activate

REM === Step 3: Install required packages ===
echo Installing dependencies...
pip install --upgrade pip
pip uninstall -y mysql-connector-python
pip install --upgrade --force-reinstall --only-binary :all: mysql-connector-python==8.0.33
pip install PyInstaller cryptography

REM === Step 4: Clean previous builds ===
echo Cleaning old build files...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul

REM === Step 5: Build executable with PyInstaller ===
echo Building main.exe...

pyinstaller --onefile --noconsole --hidden-import=mysql.connector --hidden-import=cryptography --exclude-module=mysql.connector.cext --exclude-module=mysql.connector.connection_cext main.py > buildlog.txt 2>&1

REM === Step 6: Check if cext.pyd was found ===
if not defined CEXT_PATH (
    echo ? cext.pyd not found! Build will likely fail.
    set "CEXT_OPTION="
) else (
    echo ? Found: %CEXT_PATH%
    set "CEXT_OPTION=--add-binary \"%CEXT_PATH%;mysql/connector/cext\""
)

REM === Step 7: Build with PyInstaller ===
echo Building main.exe...
pyinstaller --onefile --noconsole ^
  %CEXT_OPTION% ^
  --collect-submodules mysql.connector ^
  --hidden-import=cryptography ^
  main.py

echo.
echo ERRORLEVEL: %ERRORLEVEL%

REM Done
if exist "dist\main.exe" (
	echo Build complete. Check dist\main.exe
) else (
	echo Build failed.
)
pause
endlocal