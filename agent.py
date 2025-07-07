import os
import requests
from datetime import date
from typing import List, Dict, Optional, Tuple
import uuid
from pydantic import SecretStr
# --- 新增导入 ---
from concurrent.futures import ThreadPoolExecutor

from langchain.agents import initialize_agent, AgentType
from langchain.schema import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI

# 添加Redis连接配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ------- 高德地图工具模块 -------
def gaode_geocode(address: str) -> dict:
    """调用高德地图 API，将地址转为经纬度"""
    key = os.getenv("GAODE_API_KEY")
    if not key:
        return {"error": "高德地图API密钥未配置"}
    
    resp = requests.get(
        "https://restapi.amap.com/v3/geocode/geo",
        params={"address": address, "key": key},
    ).json()
    return resp

def gaode_search_poi(location: str, keywords: str = "", poi_type: Optional[str] = None) -> dict:
    """根据经纬度和关键字搜索兴趣点：酒店、景点等"""
    key = os.getenv("GAODE_API_KEY")
    if not key:
        return {"error": "高德地图API密钥未配置"}
    
    params = {"location": location, "keywords": keywords, "key": key}
    if poi_type:
        params["types"] = poi_type
    resp = requests.get("https://restapi.amap.com/v3/place/around", params=params).json()
    return resp

def gaode_route(origin: str, destination: str, strategy: str = "0") -> dict:
    """路径规划：驾车（0）、公交（1）、步行（3）等"""
    key = os.getenv("GAODE_API_KEY")
    if not key:
        return {"error": "高德地图API密钥未配置"}
    
    resp = requests.get(
        "https://restapi.amap.com/v3/direction/driving",
        params={"origin": origin, "destination": destination, "strategy": strategy, "key": key},
    ).json()
    return resp

def gaode_weather(city: str) -> dict:
    """根据城市名称查询未来的天气预报"""
    key = os.getenv("GAODE_API_KEY")
    if not key:
        return {"error": "高德地图API密钥未配置"}
    
    geocode_resp = gaode_geocode(city)
    if geocode_resp.get("status") != "1" or not geocode_resp.get("geocodes"):
        return {"error": f"无法解析城市 '{city}' 的地理编码"}
    
    adcode = geocode_resp["geocodes"][0].get("adcode")
    if not adcode:
        return {"error": f"无法从地理编码响应中找到城市 '{city}' 的 adcode"}

    resp = requests.get(
        "https://restapi.amap.com/v3/weather/weatherInfo",
        params={"city": adcode, "key": key, "extensions": "all"},
    ).json()
    return resp

# ------- 将功能打包成 LangChain Tool -------
gaode_tools = [
    Tool(name="geocode", func=gaode_geocode, description="将地址转经纬度"),
    Tool(name="search_poi", func=gaode_search_poi, description="搜索酒店或景点信息"),
    Tool(name="route_planning", func=gaode_route, description="规划行程路径"),
]

weather_tools = [
    Tool(name="get_weather_forecast", func=gaode_weather, description="根据城市名称查询未来几天的天气预报")
]

def search_hotel(location: str, keywords: Optional[str] = "") -> dict:
    """搜索附近酒店"""
    safe_keywords = keywords if keywords is not None else ""
    return gaode_search_poi(location, safe_keywords, poi_type="酒店")

hotel_tools = [
    Tool(name="search_hotel", func=search_hotel, description="根据位置查询酒店")
]

def recommend_attractions(location: str, keywords: Optional[str] = "") -> dict:
    """搜索附近旅游景点"""
    safe_keywords = keywords if keywords is not None else ""
    return gaode_search_poi(location, safe_keywords, poi_type="旅游景点")

recommend_tools = [
    Tool(name="recommend_attractions", func=recommend_attractions, description="根据位置推荐景点")
]

def plan_itinerary(location: str, days: str = "") -> str:
    """制定行程安排"""
    if not location or not days:
        return "请提供位置和天数信息"
    return f"为位置 {location} 和 {days} 天行程，生成示例安排"

planner_tools = [
    Tool(name="plan_itinerary", func=plan_itinerary, description="制定行程安排")
]

# ------- 智能体定义 -------
def create_llm() -> ChatOpenAI:
    """创建LLM实例"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OpenAI API密钥未配置")
    openai_api_key=SecretStr(openai_api_key)
    return ChatOpenAI(
        temperature=0.7,
        api_key=openai_api_key,
        model="",
        base_url="https://api.openai-proxy.org/v1",
    )

def create_agent(agent_type: str, tools: List[Tool], email: str, conv_id: str) -> dict:
    """创建特定类型的智能体，使用Redis存储记忆"""
    llm = create_llm()
    
    agent_config = {
        "maps": {
            "name": "地图代理",
            "goal": "作为地图代理，您的职责是处理地理位置、路线规划和兴趣点搜索。请准确解析中文地址并提供基于位置的建议。"
        },
        "weather": {
            "name": "天气代理",
            "goal": "作为天气代理，您的职责是提供详细的天气预报，并根据天气状况给出旅行建议。"
        },
        "booking": {
            "name": "预订代理",
            "goal": "作为预订代理，您的职责是在预算范围内寻找并推荐合适的住宿，同时考虑位置、价格和评价。"
        },
        "itinerary": {
            "name": "行程代理",
            "goal": "作为行程代理，您的职责是综合所有信息，创建一份详细、合理、逻辑清晰的旅行计划。"
        }
    }
    
    if agent_type not in agent_config:
        raise ValueError(f"未知的智能体类型: {agent_type}")
    
    config = agent_config[agent_type]
    
    redis_session_id = f"{email}-{conv_id}-{agent_type}"
    message_history = RedisChatMessageHistory(
        session_id=redis_session_id,
        url=REDIS_URL
    )
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=ConversationBufferMemory(
            memory_key="chat_history",
            chat_memory=message_history,
            return_messages=True
        ),
        verbose=True,
        handle_parsing_errors=True,
    )
    
    return {
        "agent": agent,
        "name": config["name"],
        "goal": config["goal"]
    }

# ------- 多智能体协作系统 -------
class MultiAgentTravelPlanner:
    def __init__(self, email: str, conv_id: str):
        self.email = email
        self.conv_id = conv_id
        self.agents = {
            "maps": create_agent("maps", gaode_tools + recommend_tools, email, conv_id),
            "weather": create_agent("weather", weather_tools, email, conv_id),
            "booking": create_agent("booking", hotel_tools, email, conv_id),
            "itinerary": create_agent("itinerary", planner_tools, email, conv_id)
        }
        
    def get_agent_response(self, agent_type: str, message: str) -> str:
        """获取特定智能体的响应"""
        if agent_type not in self.agents:
            return f"错误: 未知的智能体类型 '{agent_type}'"
        
        agent_info = self.agents[agent_type]
        agent = agent_info["agent"]
        prompt = f"你的身份是 {agent_info['name']}。\n你的目标是：\n{agent_info['goal']}\n\n请根据以下信息作出回应：\n{message}"

        try:
            return agent.run(prompt)
        except Exception as e:
            return f"智能体错误: {str(e)}"
        
    def coordinate_agents(self, user_request: str) -> str:
        """协调多个智能体共同处理用户请求"""
        # 步骤1: 地图代理处理位置信息（串行，因为后续步骤依赖它）
        maps_response = self.get_agent_response(
            "maps", 
            f"用户请求: {user_request}\n请提供位置分析和路线建议。"
        )
        
        weather_response = ""
        booking_response = ""

        # --- 修改部分：并发执行步骤2和步骤3 ---
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 准备天气代理和预订代理的任务
            weather_prompt = f"基于地图代理的分析: {maps_response}\n请提供目的地的天气预报。"
            booking_prompt = f"用户请求: {user_request}\n地图代理分析: {maps_response}\n请推荐合适的住宿。"
            
            # 提交任务到线程池
            future_weather = executor.submit(self.get_agent_response, "weather", weather_prompt)
            future_booking = executor.submit(self.get_agent_response, "booking", booking_prompt)
            
            # 获取两个任务的结果
            # .result() 方法会阻塞直到该任务完成
            try:
                weather_response = future_weather.result()
            except Exception as e:
                weather_response = f"天气代理执行出错: {e}"

            try:
                booking_response = future_booking.result()
            except Exception as e:
                booking_response = f"预订代理执行出错: {e}"

        # 步骤4: 行程代理制定详细计划（串行，等待前面所有结果）
        itinerary_response = self.get_agent_response(
            "itinerary", 
            f"用户请求: {user_request}\n地图代理分析: {maps_response}\n天气代理分析: {weather_response}\n预订代理分析: {booking_response}\n请制定详细的旅行行程。"
        )
        
        # 综合所有代理的结果
        return f"""
                        ## 综合旅行计划

                        ### 地点和路线
                        {maps_response}

                        ### 天气预报
                        {weather_response}

                        ### 住宿推荐
                        {booking_response}

                        ### 详细行程
                        {itinerary_response}
                        """

# ------- 全局缓存和入口点 -------
planner_cache = {}

def get_agent_response(user_message: str, email: str, conv_id: str) -> str:
    """处理用户消息并返回AI响应（入口函数）"""
    cache_key = f"{email}-{conv_id}"
    if cache_key not in planner_cache:
        planner_cache[cache_key] = MultiAgentTravelPlanner(email, conv_id)
    
    planner = planner_cache[cache_key]
    return planner.coordinate_agents(user_message)