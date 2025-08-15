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

REM === 使用当前 shell 的 Python 运行脚本（需确保 python 在 PATH 中）===
where python >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 未找到 python，请将 Python 添加到 PATH 后再试。
    exit /b 2
)
python bmc_collect.py

endlocal
exit /b %ERRORLEVEL% 