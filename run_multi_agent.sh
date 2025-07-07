#!/bin/bash
# 多智能体AI旅行规划系统启动脚本

echo "🤖✈️ 启动多智能体AI旅行规划系统..."
echo "========================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查Streamlit是否安装
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 正在安装Streamlit..."
    pip3 install streamlit
fi

# 检查其他依赖
echo "🔍 检查依赖包..."
python3 -c "
try:
    import asyncio
    import base64
    from datetime import date
    print('✅ 基础依赖包检查通过')
except ImportError as e:
    print(f'❌ 依赖包检查失败: {e}')
    exit(1)
"

# 设置环境变量（可选）
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo ""
echo "🚀 启动多智能体旅行规划系统..."
echo "📝 请在浏览器中访问显示的URL"
echo "🔑 记得在侧边栏配置您的API密钥"
echo ""

# 启动Streamlit应用
streamlit run multi_agent_streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo ""
echo "👋 多智能体系统已关闭，感谢使用！"
