@echo off
setlocal

REM === 可在此处填写你的BMC配置 ===
set BMC_URL=http://192.168.1.100/
set BMC_USER=admin
set BMC_PASS=admin
set BROWSER=edge
set HEADLESS=1

REM === 切换到脚本所在目录 ===
cd /d %~dp0

REM === 使用本地虚拟环境运行脚本（请先按README步骤创建.venv并安装依赖）===
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe bmc_collect.py
) else (
    echo 未发现 .venv\Scripts\python.exe，请先创建虚拟环境并安装依赖。
    echo 例如：
    echo   py -3 -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    exit /b 2
)

endlocal
exit /b %ERRORLEVEL% 