@echo off

REM 由windows特性，请勿在参数中使用双引号
set BMC_URL=https://nps.keboe.cn/login/index
set BMC_USER=Adm1na
set BMC_PASS=admin
set BROWSER=chrome
set HEADLESS=0

REM 在设定定时任务时，windows务必将run_bmc_collect中的所有命令切换成完整路径
python bmc_collect.py

exit /b %ERRORLEVEL% 