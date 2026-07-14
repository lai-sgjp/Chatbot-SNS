@echo off
chcp 65001 >nul
echo ==========================================
echo   ChatBot SNS + NapCat 启动脚本
echo ==========================================

echo [1/3] 等待 Docker Desktop 启动...
set "DOCKER_OK=0"
for /l %%i in (1,1,30) do (
    docker info >nul 2>&1
    if not errorlevel 1 (
        set "DOCKER_OK=1"
        echo   Docker 已就绪
        goto :docker_ready
    )
    echo   等待 Docker 启动... (%%i/30)
    timeout /t 3 /nobreak >nul
)
:docker_ready
if "%DOCKER_OK%"=="0" (
    echo [错误] Docker Desktop 未启动，请先手动启动 Docker Desktop
    pause
    exit /b 1
)

echo [2/3] 启动 NapCat 容器...
docker start napcat 2>nul
if errorlevel 1 (
    echo   NapCat 容器不存在，正在创建...
    docker run -d -p 3000:3000 -p 3001:3001 -p 6099:6099 --name napcat --restart=always mlikiowa/napcat-docker
)
echo   等待 NapCat 初始化...
timeout /t 10 /nobreak >nul

echo [3/3] 启动 ChatBot...
echo ==========================================
cd /d E:\work\ChatBot_SNS
python -m bot.main
pause