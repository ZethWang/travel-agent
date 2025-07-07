"""
AI旅行规划智能体模块
专门负责旅行规划的智能体逻辑和配置
"""

import asyncio
import os
from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini

# 导入提示词模块
from travel_prompts import (
    TRAVEL_AGENT_SYSTEM_PROMPT,
    TRAVEL_AGENT_GOAL,
    TRAVEL_AGENT_NAME,
    TRAVEL_MESSAGE_TEMPLATE,
    CONTEXT_MESSAGE_TEMPLATE
)


class TravelPlanningAgent:
    """AI旅行规划智能体类"""
    
    def __init__(self, model_provider="OpenAI", openai_key=None, gemini_key=None, searchapi_key=None):
        """
        初始化旅行规划智能体
        
        Args:
            model_provider: 模型提供商 ("OpenAI" 或 "Gemini")
            openai_key: OpenAI API密钥
            gemini_key: Gemini API密钥  
            searchapi_key: SearchAPI密钥
        """
        self.model_provider = model_provider
        self.openai_key = openai_key
        self.gemini_key = gemini_key
        self.searchapi_key = searchapi_key
        
    def _validate_keys(self):
        """验证API密钥是否完整"""
        if not self.searchapi_key:
            raise ValueError("🚨 缺少 SearchAPI API 密钥")
        elif self.model_provider == 'OpenAI' and not self.openai_key:
            raise ValueError("🚨 缺少 OpenAI API 密钥")
        elif self.model_provider == 'Gemini' and not self.gemini_key:
            raise ValueError("🚨 缺少 Gemini API 密钥")
    
    def _get_model(self):
        """根据提供商获取相应的模型实例"""
        if self.model_provider == 'OpenAI':
            return OpenAIChat(
                id="gpt-4.1",  # 使用xi-ai支持的模型
                api_key=self.openai_key,
                base_url="https://api.xi-ai.cn/v1",
            )
        elif self.model_provider == 'Gemini':
            return Gemini(id="gemini-2.0-flash-exp", api_key=self.gemini_key)
        else:
            raise ValueError(f"不支持的模型提供商: {self.model_provider}")
    
    def _get_environment(self):
        """获取环境变量配置"""
        env = {
            **os.environ,
            "SEARCHAPI_API_KEY": self.searchapi_key
        }
        
        if self.model_provider == 'OpenAI':
            env["OPENAI_API_KEY"] = self.openai_key
        elif self.model_provider == 'Gemini':
            env["GOOGLE_API_KEY"] = self.gemini_key
            
        return env
    
    def _get_agent_instructions(self):
        """获取智能体指令"""
        return TRAVEL_AGENT_SYSTEM_PROMPT
    
    async def plan_travel(self, message: str, progress_callback=None):
        """
        执行旅行规划任务
        
        Args:
            message: 用户的旅行规划请求消息
            progress_callback: 可选的进度回调函数
            
        Returns:
            str: 旅行规划结果
        """
        # 验证API密钥
        self._validate_keys()
        
        # 获取环境变量和模型
        env = self._get_environment()
        travel_model = self._get_model()
        
        if progress_callback:
            progress_callback(1, 4, "正在初始化AI旅行规划专家...")
        
        async with MultiMCPTools(
            ["python /mnt/public/code/zzy/wzh/doremi/searchAPI-mcp/mcp_server.py"],
            env=env,
        ) as mcp_tools:
            
            if progress_callback:
                progress_callback(2, 4, "正在搜索旅行信息...")
            
            # 创建旅行规划智能体
            travel_agent = Agent(
                tools=[mcp_tools],
                model=travel_model,
                name=TRAVEL_AGENT_NAME,
                instructions=self._get_agent_instructions(),
                goal=TRAVEL_AGENT_GOAL
            )
            
            if progress_callback:
                progress_callback(3, 4, "正在制定行程方案...")
            
            # 运行智能体
            result = await travel_agent.arun(message)
            
            if progress_callback:
                progress_callback(4, 4, "AI规划完成！正在生成最终方案...")
            
            # 获取响应内容
            if hasattr(result, 'content'):
                return result.content
            elif hasattr(result, 'messages') and result.messages:
                return result.messages[-1].content if hasattr(result.messages[-1], 'content') else str(result.messages[-1])
            else:
                return str(result)


def build_travel_message(source, destination, travel_dates, budget, travel_preferences, 
                        accommodation_type, transportation_mode, dietary_restrictions):
    """
    构建旅行规划消息
    
    Args:
        source: 出发地
        destination: 目的地
        travel_dates: 旅行日期 [开始日期, 结束日期]
        budget: 预算
        travel_preferences: 旅行偏好列表
        accommodation_type: 住宿类型
        transportation_mode: 交通方式列表
        dietary_restrictions: 饮食限制列表
        
    Returns:
        str: 格式化的旅行规划请求消息
    """
    return TRAVEL_MESSAGE_TEMPLATE.format(
        source=source,
        destination=destination,
        start_date=travel_dates[0],
        end_date=travel_dates[1],
        budget=budget,
        preferences=', '.join(travel_preferences),
        accommodation_type=accommodation_type,
        transportation_mode=', '.join(transportation_mode),
        dietary_restrictions=', '.join(dietary_restrictions)
    )


def build_context_message(travel_plan, travel_context, user_question):
    """
    构建包含旅行计划上下文的对话消息
    
    Args:
        travel_plan: 当前的旅行计划内容
        travel_context: 旅行基本信息字典
        user_question: 用户的追问
        
    Returns:
        str: 包含上下文的完整消息
    """
    # 处理旅行日期
    travel_dates = travel_context.get('travel_dates', ['未设定', '未设定'])
    start_date = travel_dates[0] if isinstance(travel_dates, list) and len(travel_dates) > 0 else '未设定'
    end_date = travel_dates[1] if isinstance(travel_dates, list) and len(travel_dates) > 1 else '未设定'
    
    return CONTEXT_MESSAGE_TEMPLATE.format(
        travel_plan=travel_plan,
        source=travel_context.get('source', '未设定'),
        destination=travel_context.get('destination', '未设定'),
        start_date=start_date,
        end_date=end_date,
        budget=travel_context.get('budget', 0),
        preferences=', '.join(travel_context.get('preferences', [])),
        user_question=user_question
    )


# 异步运行智能体的便捷函数
async def run_travel_agent(message: str, model_provider="OpenAI", 
                          openai_key=None, gemini_key=None, searchapi_key=None, progress_callback=None):
    """
    运行旅行规划智能体的便捷函数
    
    Args:
        message: 旅行规划请求消息
        model_provider: 模型提供商
        openai_key: OpenAI API密钥
        gemini_key: Gemini API密钥
        searchapi_key: SearchAPI密钥
        progress_callback: 进度回调函数
        
    Returns:
        str: 旅行规划结果
    """
    agent = TravelPlanningAgent(
        model_provider=model_provider,
        openai_key=openai_key,
        gemini_key=gemini_key,
        searchapi_key=searchapi_key
    )
    
    return await agent.plan_travel(message, progress_callback)
