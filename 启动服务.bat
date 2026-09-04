@echo off
chcp 65001 >nul
rem =====================================================
rem “易”生伴 - Windows 一键启动脚本（双击本文件即可）
rem
rem 会依次：
rem   1. 检查并启动 MySQL 服务（服务名 MySQL80 或 MySQL）
rem   2. 检查数据库 yishengban（缺失时提示导入）
rem   3. 检查后端虚拟环境和依赖（缺失时自动安装）
rem   4. 在两个独立窗口启动后端(8000)和前端(5173)
rem
rem 停止服务：关闭弹出的两个黑窗口即可
rem 前提：已安装 Python 3.10+、Node.js 18+、MySQL 8（root 无密码）
rem =====================================================
title 易生伴启动器
cd /d "%~dp0"

echo ==========================================
echo   易生伴 - 高校健康教育多智能体情境训练
echo ==========================================

rem ---------- 1. MySQL ----------
echo [1/4] 检查 MySQL ...
sc query MySQL80 2>nul | findstr /i RUNNING >nul
if errorlevel 1 (
    sc query MySQL 2>nul | findstr /i RUNNING >nul
    if errorlevel 1 (
        echo   尝试启动 MySQL 服务（需要管理员权限，失败请手动启动）...
        net start MySQL80 2>nul || net start MySQL 2>nul
    )
)
sc query MySQL80 2>nul | findstr /i RUNNING >nul
if errorlevel 1 (
    sc query MySQL 2>nul | findstr /i RUNNING >nul
    if errorlevel 1 (
        echo   [警告] MySQL 未在运行！请先启动 MySQL 服务后重新双击本脚本
        pause
        exit /b 1
    )
)
echo   √ MySQL 已在运行

rem 检查数据库是否已初始化
mysql -u root -e "USE yishengban" >nul 2>&1
if errorlevel 1 (
    echo   首次使用：导入 database\init.sql ...
    mysql -u root < "database\init.sql" >nul 2>&1
    if errorlevel 1 (
        echo   [警告] 数据库导入失败，请手动执行: mysql -u root ^< database\init.sql
        pause
        exit /b 1
    )
    echo   √ 数据库初始化完成（测试账号 test/123456）
)

rem ---------- 2. 后端依赖 ----------
echo [2/4] 检查后端环境 ...
if not exist "backend\.env" (
    echo   [错误] 缺少 backend\.env 配置文件（数据库/大模型 API 配置），无法启动
    pause
    exit /b 1
)
if not exist "backend\venv\Scripts\python.exe" (
    echo   首次使用：创建虚拟环境并安装依赖（约1-2分钟）...
    pushd backend
    python -m venv venv
    venv\Scripts\pip install -q -r requirements.txt
    popd
)
echo   √ 后端环境就绪

rem ---------- 3. 后端 API ----------
echo [3/4] 启动后端 API（端口 8000，独立窗口）...
start "南医健康伙伴-后端API" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

rem 等待后端就绪
timeout /t 5 /nobreak >nul

rem ---------- 4. 前端 ----------
echo [4/4] 启动前端页面（端口 5173，独立窗口）...
if not exist "frontend\node_modules" (
    echo   首次使用：安装前端依赖（约1-2分钟）...
    pushd frontend
    call npm install --no-audit --no-fund
    popd
)
start "南医健康伙伴-前端页面" cmd /k "cd /d "%~dp0frontend" && npx vite --port 5173"

timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo √ 启动完成！浏览器将自动打开 http://localhost:5173
echo   测试账号: test / 123456
echo   停止服务: 关闭"南医健康伙伴-后端API"和"南医健康伙伴-前端页面"两个窗口
echo.
echo 本窗口可以关闭。
pause
