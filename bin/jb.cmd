@echo off
rem Windows shim: runs bin/jb under Git Bash. Usage is identical:  bin\jb status
set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%BASH%" (
  echo jb: Git Bash not found. Install Git for Windows or run bin/jb from a bash shell. 1>&2
  exit /b 1
)
"%BASH%" "%~dp0jb" %*
