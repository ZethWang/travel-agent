import asyncio
import os
from datetime import date
from fpdf import FPDF
import io
import base64

from agno.agent import Agent
from agno.team.team import Team
from agno.tools.mcp import MultiMCPTools
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
import streamlit as st

# 配置页面 - 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="AI 旅行规划助手",
    page_icon="✈️",
    layout="wide"
)


def create_travel_plan_pdf(travel_plan_text, source, destination, travel_dates, budget):
    """创建旅行计划的PDF文档"""
    try:
        # 创建PDF对象
        pdf = FPDF()
        pdf.add_page()
        
        # 设置字体
        pdf.set_font('Arial', 'B', 16)
        
        # 处理文本，转换为ASCII兼容格式
        def clean_text(text):
            import re
            # 移除或替换特殊字符，保留基本标点
            text = re.sub(r'[^\x00-\x7F]+', ' ', str(text))  # 移除非ASCII字符
            text = re.sub(r'\s+', ' ', text)  # 合并多个空格
            return text.strip()
        
        # 清理输入数据
        source_clean = clean_text(source)
        destination_clean = clean_text(destination)
        
        # 标题
        try:
            pdf.cell(0, 10, f'AI Travel Plan: {source_clean} to {destination_clean}', 0, 1, 'C')
        except:
            pdf.cell(0, 10, 'AI Travel Plan', 0, 1, 'C')
        pdf.ln(5)
        
        # 基本信息
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, f'From: {source_clean}', 0, 1)
        pdf.cell(0, 8, f'To: {destination_clean}', 0, 1)
        pdf.cell(0, 8, f'Dates: {travel_dates[0]} to {travel_dates[1]}', 0, 1)
        pdf.cell(0, 8, f'Budget: ${budget} USD', 0, 1)
        pdf.ln(8)
        
        # 旅行计划内容
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, 'Travel Plan Details:', 0, 1)
        pdf.ln(3)
        
        # 处理旅行计划文本
        clean_plan = clean_text(travel_plan_text)
        
        # 分行处理
        lines = clean_plan.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # 处理长行
                while len(line) > 85:
                    break_point = line.rfind(' ', 0, 85)
                    if break_point == -1:
                        break_point = 85
                    
                    try:
                        pdf.cell(0, 5, line[:break_point], 0, 1)
                    except:
                        pdf.cell(0, 5, 'Content contains special characters', 0, 1)
                    line = line[break_point:].strip()
                
                if line:
                    try:
                        pdf.cell(0, 5, line, 0, 1)
                    except:
                        pdf.cell(0, 5, 'Content contains special characters', 0, 1)
            else:
                pdf.ln(2)
        
        # 返回PDF字节数据
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        # 如果还是失败，创建一个简化版本
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'AI Travel Plan', 0, 1, 'C')
            pdf.ln(5)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 8, f'Budget: ${budget} USD', 0, 1)
            pdf.cell(0, 8, f'Date: {travel_dates[0]} to {travel_dates[1]}', 0, 1)
            pdf.ln(5)
            pdf.cell(0, 8, 'Travel plan contains special characters.', 0, 1)
            pdf.cell(0, 8, 'Please refer to the web version for full details.', 0, 1)
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e2:
            st.error(f"PDF生成失败: {str(e2)}")
            return None

def create_download_link(pdf_bytes, filename):
    """创建PDF下载链接"""
    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 下载PDF旅行计划</a>'
        return href
    return None

def create_text_download_link(text_content, filename):
    """创建文本文件下载链接"""
    try:
        # 清理文本内容
        clean_content = text_content.encode('utf-8', errors='ignore').decode('utf-8')
        b64 = base64.b64encode(clean_content.encode('utf-8')).decode()
        href = f'<a href="data:text/plain;charset=utf-8;base64,{b64}" download="{filename}">📄 下载文本版旅行计划</a>'
        return href
    except Exception as e:
        return None

# Remove dotenv import and loading since we'll use sidebar
# from dotenv import load_dotenv
# load_dotenv()

# 添加团队配置导入
try:
    from team_config import AGENT_CONFIGS, TEAM_CONFIG, WORKFLOW_CONFIG
except ImportError:
    # 如果配置文件不存在，使用默认配置
    AGENT_CONFIGS = None
    TEAM_CONFIG = {"show_chain_of_thought": True}
    WORKFLOW_CONFIG = None

def display_agent_status():
    """显示智能体团队状态和工作流程"""
    with st.expander("🤖 智能体团队状态", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔍 信息收集专家")
            st.markdown("""
            **状态**: 待命中 ⏳
            **AI模型**: GPT-4o-mini 
            **API源**: OpenAI代理 (api.openai-proxy.org)
            **专业领域**: 数据搜索与信息验证
            **工具集**: 
            - Google地图搜索
            - Google航班搜索  
            - Google酒店搜索
            - 综合信息搜索
            """)
            
        with col2:
            st.markdown("### 📋 行程规划专家") 
            st.markdown("""
            **状态**: 待命中 ⏳
            **AI模型**: GPT-3.5-turbo
            **API源**: Xi-AI (api.xi-ai.cn)
            **专业领域**: 方案整合与优化规划
            **核心能力**:
            - 需求分析
            - 数据整合
            - 行程优化
            - 预算控制
            """)
        
        st.markdown("### 🔄 预期工作流程")
        st.markdown("""
        1. **需求分析** (1-2分钟) - 解析用户需求并分解任务
        2. **信息收集** (2-3分钟) - 并行收集旅行相关数据  
        3. **方案规划** (2-3分钟) - 整合信息并制定旅行方案
        4. **协作优化** (1-2分钟) - 两个智能体协作优化最终方案
        """)

def create_progress_tracker():
    """创建进度跟踪器"""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    def update_progress(step, total_steps, message):
        progress = step / total_steps
        progress_placeholder.progress(progress)
        status_placeholder.info(f"🔄 {message}")
    
    return update_progress

async def run_agents_team(message: str):
    """使用双智能体团队运行旅行规划任务，实现功能解耦和并行处理。"""

    # 从会话状态获取 API 密钥
    searchapi_key = st.session_state.get('searchapi_key')
    openai_key = st.session_state.get('openai_key')
    gemini_key = st.session_state.get('gemini_key')
    model_provider = st.session_state.get('model_provider', 'OpenAI')

    if not searchapi_key:
        raise ValueError("🚨 缺少 SearchAPI API 密钥。请在侧边栏中输入。")
    elif model_provider == 'OpenAI' and not openai_key:
        raise ValueError("🚨 缺少 OpenAI API 密钥。请在侧边栏中输入。")
    elif model_provider == 'Gemini' and not gemini_key:
        raise ValueError("🚨 缺少 Gemini API 密钥。请在侧边栏中输入。")

    # 设置环境变量
    env = {
        **os.environ,
        "SEARCHAPI_API_KEY": searchapi_key
    }
    
    if model_provider == 'OpenAI':
        env["OPENAI_API_KEY"] = openai_key
    elif model_provider == 'Gemini':
        env["GOOGLE_API_KEY"] = gemini_key

    # 根据选择的模型提供商初始化模型
    if model_provider == 'OpenAI':
        # 为信息收集专家配置第一个模型 - 使用代理API
        research_model = OpenAIChat(
            id="gpt-4o-mini", 
            api_key=openai_key,
            base_url="https://api.openai-proxy.org/v1",
        )
        
        # 为行程规划专家配置第二个模型 - 使用新的API
        openai_key2 = os.environ.get("OPENAI_API_KEY2", "")
        planning_model = OpenAIChat(
            id="gpt-4o-mini",  # 使用xi-ai支持的模型
            api_key=openai_key2,  # 使用新的API密钥
            base_url="https://api.xi-ai.cn/v1",  # 使用新的API URL
        )
    elif model_provider == 'Gemini':
        # 为两个智能体配置相同的Gemini模型
        research_model = Gemini(id="gemini-2.0-flash-exp", api_key=gemini_key)
        planning_model = Gemini(id="gemini-2.0-flash-exp", api_key=gemini_key)

    async with MultiMCPTools(
        ["python /mnt/public/code/zzy/wzh/doremi/searchAPI-mcp/mcp_server.py"],
        env=env,
    ) as mcp_tools:
        
        # 创建双智能体团队 - 功能解耦设计
        
        # 智能体1: 信息收集专家 - 负责搜索和数据收集
        research_agent = Agent(
            tools=[mcp_tools],
            model=research_model,  # 使用第一个模型
            name="旅行信息收集专家",
            instructions="""
            作为旅行信息收集专家，你是团队中的数据搜索和信息验证专家。

            ## 核心职责：
            1. **目的地信息搜索**: 使用Google搜索收集目的地的景点、文化、气候、安全等基本信息
            2. **航班信息查询**: 使用Google航班搜索工具查找最佳航班选项和价格
            3. **住宿信息收集**: 使用Google酒店搜索工具查找符合用户偏好的住宿选项
            4. **餐饮信息搜索**: 搜索当地特色餐厅、美食推荐，考虑用户的饮食限制
            5. **交通信息获取**: 收集当地交通信息、路线规划、交通费用等
            6. **活动体验搜索**: 根据用户偏好搜索相关的活动、景点、体验项目

            ## 工作原则：
            - **全面性**: 确保收集的信息覆盖旅行的各个方面
            - **准确性**: 验证信息的时效性和准确性
            - **相关性**: 根据用户的具体需求和偏好进行定向搜索
            - **结构化**: 以清晰的格式整理搜索结果，便于规划专家使用

            ## 注意事项：
            - 专注于信息收集，不要制定具体的行程安排
            - 将搜索结果清晰地分类整理
            - 如果某些信息搜索失败，要明确说明并提供替代方案
            - 与规划专家保持信息同步，避免重复工作
            """,
            goal="""收集全面、准确的旅行相关信息，为行程规划专家提供高质量的数据支持。"""
        )
        
        # 智能体2: 行程规划专家 - 负责整合和规划
        planning_agent = Agent(
            tools=[mcp_tools],
            model=planning_model,  # 使用第二个模型
            name="行程规划专家",
            instructions="""
            作为行程规划专家，你是团队中的策略制定和方案优化专家。

            ## 核心职责：
            1. **需求分析**: 深入分析用户的旅行需求、偏好、预算和时间限制
            2. **信息整合**: 整合信息收集专家提供的所有数据
            3. **行程设计**: 制定详细的日程安排，包括时间、地点、活动安排
            4. **预算规划**: 进行成本估算和预算分配，确保在用户预算范围内
            5. **路线优化**: 优化旅行路线，减少不必要的往返和时间浪费
            6. **方案完善**: 提供备选方案、应急计划和个性化建议

            ## 规划原则：
            - **用户为中心**: 严格按照用户的偏好和限制条件制定方案
            - **实用性**: 确保行程安排合理可行，时间分配恰当
            - **经济性**: 在预算范围内提供最优价值的旅行体验
            - **灵活性**: 为可能的变化留出调整空间

            ## 输出格式：
            - 详细的日程安排（按天分解）
            - 清晰的预算分配表
            - 交通和住宿预订建议
            - 重要提醒和注意事项
            - 备选方案和应急计划

            ## 协作要求：
            - 基于信息专家提供的数据进行规划，避免重复搜索
            - 如需补充信息，明确向信息专家提出具体需求
            - 确保最终方案的完整性和可操作性
            """,
            goal="""基于收集的信息制定完美的个性化旅行方案，确保用户获得最佳的旅行体验。"""
        )
        
        # 创建智能体团队
        travel_team = Team(
            members=[research_agent, planning_agent],
            name="Travel Planning Team",
            markdown=True,
            show_tool_calls=True,
            instructions="""
            作为AI旅行规划团队的协调者，请协调制定全面的旅行计划：

            ## 团队协作核心原则：
            1. **在各个规划代理之间共享信息**，确保信息收集专家与行程规划专家之间的数据同步和一致性
            2. **考虑旅行中不同方面之间的依赖关系**（如航班时间影响住宿选择、景点开放时间影响活动安排）
            3. **优先考虑用户的偏好和约束条件**（严格遵守预算限制、时间安排、兴趣偏好、饮食限制等）
            4. **当首选方案不可用时，提供备选方案**（如备用酒店、替代景点、不同价位选择）
            5. **在计划活动与自由时间之间保持平衡**，避免行程过度紧张或过于松散
            6. **考虑当地的活动和季节性因素**（如节日庆典、天气条件、旅游高峰期、营业时间）
            7. **确保所有推荐内容符合用户预算**，进行详细的成本计算，避免超支

            ## 智能体分工协调：
            ### 🔍 信息收集专家职责：
            - 系统性收集目的地信息（景点、文化、安全、气候）
            - 搜索航班、住宿、餐饮、交通、活动等各类选项
            - 验证信息准确性和时效性
            - 提供价格范围和可用性信息
            
            ### 📋 行程规划专家职责：
            - 分析用户需求并制定个性化方案
            - 整合所有收集的信息进行综合规划
            - 优化时间安排和路线规划
            - 进行预算分配和成本控制

            ## 协作工作流程：
            1. **需求分析阶段**: 共同理解用户需求，分解具体任务
            2. **信息收集阶段**: 信息专家系统性搜索所有相关数据
            3. **数据传递阶段**: 确保搜索结果完整传递给规划专家
            4. **方案制定阶段**: 规划专家基于数据制定详细方案
            5. **协作优化阶段**: 两专家协作优化和完善方案
            6. **质量检查阶段**: 确保方案完整性和可操作性

            ## 最终输出要求：
            ### 必须包含的详细安排：
            - **预订信息**：机票预订建议（航班号、时间、价格）、酒店预订信息（地址、价格、特色）、景点门票信息
            - **路线规划**：详细的交通方式与时间安排、从机场到酒店的路线、各景点间的交通方案
            - **天气预报**：旅行期间的天气情况和穿衣建议
            - **每日活动计划**：按天分解的详细行程，包括时间、地点、活动内容、预计费用
            - **预算分配表**：详细的费用breakdown（交通、住宿、餐饮、活动、其他）
            - **实用信息**：紧急联系方式、重要提醒、当地习俗、支付方式等
            - **备选方案**：每个主要环节的备用选择

            ## 质量控制标准：
            - 信息准确性：所有信息都经过验证
            - 预算合规性：总费用不超过用户预算
            - 时间合理性：行程安排时间充裕且高效
            - 个性化程度：充分体现用户的偏好和需求
            - 可操作性：提供具体可执行的预订和行动指导
            """
        )
        
        # 运行团队协作
        result = await travel_team.arun(message)
        
        # 获取响应内容
        if hasattr(result, 'content'):
            return result.content
        elif hasattr(result, 'messages') and result.messages:
            return result.messages[-1].content if hasattr(result.messages[-1], 'content') else str(result.messages[-1])
        else:
            return str(result)  
    
# -------------------- Streamlit 应用 --------------------
    
# 为 API 密钥添加侧边栏
with st.sidebar:
    st.header("🔑 API 密钥配置")
    st.markdown("请输入您的 API 密钥以使用旅行规划助手。")
    
    # 模型提供商选择
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = "OpenAI"
    
    st.session_state.model_provider = st.selectbox(
        "🤖 选择AI模型提供商",
        ["OpenAI", "Gemini"],
        index=["OpenAI", "Gemini"].index(st.session_state.model_provider),
        help="选择您喜欢的AI模型提供商"
    )
    
    # 如果会话状态中不存在 API 密钥，则初始化（使用环境变量作为默认值）
    if 'searchapi_key' not in st.session_state:
        st.session_state.searchapi_key = os.environ.get("SEARCHAPI_API_KEY", "")
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = os.environ.get("OPENAI_API_KEY", "")
    if 'gemini_key' not in st.session_state:
        st.session_state.gemini_key = ""

    # API 密钥输入字段
    st.session_state.searchapi_key = st.text_input(
        "SearchAPI 密钥",
        value=st.session_state.searchapi_key,
        type="password",
        help="用于访问Google搜索、地图、酒店、航班等所有搜索功能"
    )
    
    # 根据选择的模型提供商显示相应的API密钥输入
    if st.session_state.model_provider == "OpenAI":
        st.session_state.openai_key = st.text_input(
            "OpenAI API 密钥",
            value=st.session_state.openai_key,
            type="password",
            help="用于GPT模型的API访问"
        )
    elif st.session_state.model_provider == "Gemini":
        st.session_state.gemini_key = st.text_input(
            "Gemini API 密钥",
            value=st.session_state.gemini_key,
            type="password",
            help="用于Google Gemini模型的API访问"
        )
    
    # 检查是否填写了所有必需的 API 密钥
    required_keys = [
        st.session_state.searchapi_key
    ]
    
    # 根据选择的模型添加相应的API密钥检查
    if st.session_state.model_provider == "OpenAI":
        required_keys.append(st.session_state.openai_key)
    elif st.session_state.model_provider == "Gemini":
        required_keys.append(st.session_state.gemini_key)
    
    all_keys_filled = all(required_keys)

    if not all_keys_filled:
        st.warning("⚠️ 请填写所有必需的 API 密钥以使用旅行规划助手。")
    else:
        st.success(f"✅ 所有 API 密钥已配置完成！当前使用：{st.session_state.model_provider}")
    
    # 显示当前选择的模型信息
    if st.session_state.model_provider == "OpenAI":
        st.info("🤖 双API配置")
        st.caption("🔍 信息收集专家：gpt-4o-mini (OpenAI代理)")
        st.caption("📋 行程规划专家：gpt-3.5-turbo (Xi-AI)")
        st.caption("✨ 特点：双API冗余、专业分工、高可用性")
    elif st.session_state.model_provider == "Gemini":
        st.info("🌟 当前使用 Gemini 2.0 Flash 模型")
        st.caption("✨ 特点：最新AI技术、多模态支持、创新性旅行建议")
    
    # 添加帮助链接
    with st.expander("📋 如何获取 API 密钥？"):
        st.markdown("""
        **SearchAPI 密钥获取步骤：**
        1. 访问 [SearchAPI.io](https://www.searchapi.io/)
        2. 注册账户并登录
        3. 在控制台中获取您的API密钥
        4. 复制并保存密钥
        
        **SearchAPI提供的功能：**
        - ✅ Google 搜索结果
        - ✅ Google 地图搜索
        - ✅ Google 酒店搜索
        - ✅ Google 航班搜索
        - ✅ 地点评论和评级
        - ✅ 视频搜索
        """)
        
        if st.session_state.model_provider == "OpenAI":
            st.markdown("""
            **OpenAI API 密钥获取步骤：**
            1. 访问 [OpenAI API Keys](https://platform.openai.com/api-keys)
            2. 登录或注册账户
            3. 点击 "Create new secret key"
            4. 复制并保存密钥
            
            **双API配置说明：**
            - 🔍 信息收集专家使用OpenAI代理API
            - 📋 行程规划专家使用Xi-AI API
            - ✨ 优势：API冗余备份，提高服务可用性
            """)
        elif st.session_state.model_provider == "Gemini":
            st.markdown("""
            **Google Gemini API 密钥获取步骤：**
            1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
            2. 登录 Google 账户
            3. 点击 "Create API Key"
            4. 复制并保存密钥
            """)
    
    with st.expander("📦 PDF功能说明"):
        st.markdown("""
        **PDF下载功能：**
        - 自动生成完整的旅行计划PDF
        - 包含所有详细信息和推荐
        - 方便保存和分享
        
        **如果PDF功能不可用：**
        ```bash
        pip install fpdf2
        ```
        """)

# 标题和描述
st.title("✈️ AI 双智能体旅行规划助手")
st.markdown("""
这个 AI 驱动的旅行规划助手采用**双智能体协作架构**，使用多种AI模型（OpenAI GPT 和 Google Gemini），通过SearchAPI.io提供全面的旅行服务：

### 🤖 双智能体团队架构
- **🔍 信息收集专家**: 专门负责搜索、收集和验证旅行相关数据
- **📋 行程规划专家**: 专门负责整合信息、制定计划和优化行程

### ✨ 核心功能特色
- 🤖 双API架构：OpenAI代理 + Xi-AI，提高服务稳定性
- ⚡ 并行处理：两个智能体同时工作，提高效率
- 🗺️ 地图搜索和地点发现（通过SearchAPI的Google Maps功能）
- 🏨 酒店和住宿搜索
- ✈️ 航班信息和价格比较
- 📍 地点评论和评级
- 🔍 综合旅行信息搜索
- ⏰ 智能时间管理和行程规划
- 🎯 个性化推荐系统
- 🤝 智能体协作优化
""")

# 创建两列用于输入
col1, col2 = st.columns(2)

with col1:
    # 出发地和目的地
    source = st.text_input("出发地", placeholder="输入您的出发城市")
    destination = st.text_input("目的地", placeholder="输入您的目的地城市")
    
    # 旅行日期
    travel_dates = st.date_input(
        "旅行日期",
        [date.today(), date.today()],
        min_value=date.today(),
        help="选择您的旅行日期"
    )

with col2:
    # 预算
    budget = st.number_input(
        "预算（美元）",
        min_value=0,
        max_value=10000,
        step=100,
        help="输入您的旅行总预算"
    )
    
    # 旅行偏好
    travel_preferences = st.multiselect(
        "旅行偏好",
        ["冒险", "休闲", "观光", "文化体验", 
         "海滩", "山区", "豪华", "经济实惠", "美食",
         "购物", "夜生活", "家庭友好"],
        help="选择您的旅行偏好"
    )

# 其他偏好设置
st.subheader("其他偏好设置")
col3, col4 = st.columns(2)

with col3:
    accommodation_type = st.selectbox(
        "首选住宿类型",
        ["任何", "酒店", "青年旅社", "公寓", "度假村"],
        help="选择您首选的住宿类型"
    )
    
    transportation_mode = st.multiselect(
        "首选交通方式",
        ["火车", "巴士", "飞机", "租车"],
        help="选择您首选的交通方式"
    )

with col4:
    dietary_restrictions = st.multiselect(
        "饮食限制",
        ["无", "素食", "纯素", "无麸质", "清真", "犹太洁食"],
        help="选择任何饮食限制"
    )

# 提交按钮
if st.button("🚀 启动双智能体规划", type="primary", disabled=not all_keys_filled):
    if not source or not destination:
        st.error("请输入出发地和目的地城市。")
    elif not travel_preferences:
        st.warning("建议选择一些旅行偏好以获得更好的推荐。")
    else:
        # 显示智能体状态
        display_agent_status()
        
        # 创建进度跟踪
        st.markdown("### 🔄 团队协作进度")
        progress_tracker = create_progress_tracker()
        
        # 开始处理
        with st.spinner("🤖 双智能体团队正在协作为您规划完美的旅行..."):
            try:
                # 更新进度
                progress_tracker(1, 4, "正在初始化智能体团队...")
                
                # 为智能体团队构建详细消息
                message = f"""
                旅行规划任务分工：
                
                【信息收集专家任务】:
                1. 搜索 {destination} 的主要景点、文化特色和气候信息
                2. 查找从 {source} 到 {destination} 的航班选项（日期：{travel_dates[0]} 到 {travel_dates[1]}）
                3. 搜索 {destination} 的住宿选项（类型偏好：{accommodation_type}）
                4. 收集当地餐厅和美食推荐（饮食限制：{', '.join(dietary_restrictions)}）
                5. 获取当地交通和路线信息
                6. 搜索符合以下偏好的活动：{', '.join(travel_preferences)}
                
                【行程规划专家任务】:
                1. 分析用户需求：预算${budget}，偏好{', '.join(travel_preferences)}
                2. 整合信息收集专家的数据
                3. 制定{len(travel_dates)}天的详细行程安排
                4. 进行预算分配和成本控制
                5. 优化路线和时间安排
                6. 提供个性化建议和备选方案
                
                请两位专家协作完成完整的旅行规划。
                """
                
                # 更新进度
                progress_tracker(2, 4, "信息收集专家正在搜索数据...")
                
                # 运行智能体团队
                response = asyncio.run(run_agents_team(message))
                
                # 更新进度
                progress_tracker(3, 4, "行程规划专家正在整合方案...")
                
                # 更新进度
                progress_tracker(4, 4, "团队协作完成！正在生成最终方案...")
                
                # 显示响应 - 限制显示长度
                st.success("✅ 双智能体团队协作完成！您的旅行计划已准备好！")
                
                # 添加团队协作说明
                st.info("🤝 **团队协作成果**: 信息收集专家负责数据搜索，行程规划专家负责方案制定")
                
                # 显示简化版本
                if len(response) > 2000:
                    st.markdown("### 旅行计划预览")
                    st.markdown(response[:2000] + "...")
                    st.info("📄 完整的旅行计划请下载PDF查看")
                else:
                    st.markdown(response)
                
                # 生成PDF下载链接
                try:
                    pdf_bytes = create_travel_plan_pdf(
                        response, 
                        source, 
                        destination, 
                        travel_dates, 
                        budget
                    )
                    
                    st.markdown("---")
                    st.markdown("### 📥 下载选项")
                    
                    if pdf_bytes:
                        filename = f"travel_plan_{source}_{destination}_{travel_dates[0]}.pdf"
                        download_link = create_download_link(pdf_bytes, filename)
                        if download_link:
                            st.markdown(download_link, unsafe_allow_html=True)
                            st.caption("点击上方链接下载PDF旅行计划")
                    
                    # 提供文本版本下载作为备用
                    text_filename = f"travel_plan_{source}_{destination}_{travel_dates[0]}.txt"
                    text_download_link = create_text_download_link(response, text_filename)
                    if text_download_link:
                        st.markdown(text_download_link, unsafe_allow_html=True)
                        st.caption("或下载文本版本（支持中文）")
                        
                except Exception as e:
                    st.warning(f"PDF生成遇到问题: {str(e)}")
                    # 至少提供文本下载
                    try:
                        st.markdown("---")
                        st.markdown("### 📥 下载选项")
                        text_filename = f"travel_plan_{source}_{destination}_{travel_dates[0]}.txt"
                        text_download_link = create_text_download_link(response, text_filename)
                        if text_download_link:
                            st.markdown(text_download_link, unsafe_allow_html=True)
                            st.caption("下载文本版旅行计划")
                    except:
                        st.info("您可以复制上方的文本内容保存")
                
            except Exception as e:
                st.error(f"规划旅行时发生错误：{str(e)}")
                st.info("请重试，如果问题持续存在，请联系技术支持。")


