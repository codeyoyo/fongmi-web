#!/bin/bash
echo "========================================"
echo "   FongMi TV Web - 启动中..."
echo "========================================"
echo ""

if [ ! -f "frontend/dist/index.html" ]; then
    echo "[前端] 未检测到构建产物，正在构建..."
    cd frontend && npm run build && cd ..
    echo ""
fi

echo "[后端] 启动 http://localhost:8000"
echo ""
echo "请在浏览器中打开: http://localhost:8000"
echo ""
python main.py
