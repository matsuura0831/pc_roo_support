@echo off

@REM 管理者として再実行
whoami /priv | find "SeDebugPrivilege" > nul
if %errorlevel% neq 0 (
 @powershell start-process %~0 -verb runas
 exit
)

@REM jupyterlabを起動
cd %~dp0/..
call .env/Scripts/activate
cd src
python operation.py

