@echo off

REM 由windows特性，请勿在参数中使用双引号
set BMC_URL=http://192.168.1.100/
set BMC_USER=admin
set BMC_PASS=admin
set BROWSER=edge
set HEADLESS=1 

python bmc_collect.py

exit /b %ERRORLEVEL% 