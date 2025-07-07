#!/bin/bash

# AI旅行规划助手启动脚本

echo "🚀 启动AI旅行规划助手..."
echo "📍 项目路径: $(pwd)"
echo "🔧 前端文件: streamlit_app.py"
echo "🤖 智能体文件: travel_agent.py"
echo ""

# 检查必要文件是否存在
if [ ! -f "travel_agent.py" ]; then
    echo "❌ 错误: travel_agent.py 文件不存在"
    exit 1
fi

if [ ! -f "streamlit_app.py" ]; then
    echo "❌ 错误: streamlit_app.py 文件不存在"
    exit 1
fi

echo "✅ 文件检查完成"
echo "🌐 正在启动Streamlit服务器..."
echo ""

# 启动Streamlit应用
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo ""
echo "🛑 服务器已停止"
