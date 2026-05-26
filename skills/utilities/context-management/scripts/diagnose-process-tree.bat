@echo off
REM ============================================================
REM diagnose-process-tree.bat
REM
REM Diagnose the Master-Worker (Guardian-Agent) process tree
REM on Windows. Identifies Guardian and Worker processes and
REM verifies the parent-child relationship.
REM
REM Usage:
REM   diagnose-process-tree.bat
REM
REM Output:
REM   Shows all python.exe processes with their parent-child
REM   relationships and command lines.
REM ============================================================

echo ========================================
echo  Master-Worker Process Tree Diagnosis
echo ========================================
echo.

echo Step 1: All python.exe processes (PID ^<-^> ParentPID)
echo ----------------------------------------
wmic process where name='python.exe' get processid,parentprocessid
echo.

echo Step 2: Identify Guardian (look for --guardian flag)
echo ----------------------------------------
for /f "skip=1 tokens=1,2" %%a in ('wmic process where "name='python.exe'" get processid^,parentprocessid') do (
    if not "%%a"=="" (
        for /f "delims=" %%c in ('wmic process where "processid=%%a" get commandline 2^>nul ^| findstr /i "guardian"') do (
            echo GUARDIAN: PID=%%a, ParentPID=%%b
            echo   Command: %%c
            echo.
        )
    )
)

echo Step 3: Identify Worker (child of Guardian)
echo ----------------------------------------
for /f "skip=1 tokens=1,2" %%a in ('wmic process where "name='python.exe'" get processid^,parentprocessid') do (
    if not "%%a"=="" (
        for /f "delims=" %%c in ('wmic process where "processid=%%a" get commandline 2^>nul ^| findstr /i "resume"') do (
            echo WORKER (resumed): PID=%%a, ParentPID=%%b
            echo   Command: %%c
            echo.
        )
    )
)

echo Step 4: Check for restart signal file
echo ----------------------------------------
if exist "%~dp0..\..\research_agent\.restart_signal.json" (
    echo SIGNAL FILE EXISTS: research_agent\.restart_signal.json
    type "%~dp0..\..\research_agent\.restart_signal.json"
) else (
    echo No restart signal file found (clean state).
)
echo.

echo Step 5: Summary
echo ----------------------------------------
echo To verify Guardian-Worker relationship:
echo   Find the Guardian PID (has --guardian in command line)
echo   Find the Worker PID (has --resume or is child of Guardian)
echo   Confirm Worker's ParentPID = Guardian's PID
echo.
echo Done.
