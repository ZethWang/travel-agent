from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type
from pydantic import BaseModel, Field
import os
import requests
import json
import itertools

# 加载 .env 文件
load_dotenv(override=True)

# 获取 API keys
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_url = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")

print("✅ Google Maps API key:", google_maps_api_key[:20] + "..." if google_maps_api_key else "未设置")
print("✅ OpenAI API key:", openai_api_key[:20] + "..." if openai_api_key else "未设置")
print("✅ OpenAI API URL:", openai_api_url)

if not google_maps_api_key:
    raise ValueError("❌ GOOGLE_MAPS_API_KEY 未在 .env 中设置！")
if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY 未在 .env 中设置！")

# 定义工具输入参数的结构
class RouteInput(BaseModel):
    origin: str = Field(description="起始地点")
    destination: str = Field(description="目的地")
    travel_mode: str = Field(default="DRIVE", description="出行方式：DRIVE（驾车）, TRANSIT（公共交通）, WALK（步行）")

class GoogleMapsRouteTool(BaseTool):
    name: str = "google_maps_route"
    description: str = "获取两地之间的路线信息，包括时间、距离和费用估算"
    args_schema: Type[BaseModel] = RouteInput
    
    def _run(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "DRIVE",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """调用Google Maps API获取路线数据"""
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_maps_api_key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.travelAdvisory.tollInfo"
        }
        
        request_body = {
            "origin": {"address": origin},
            "destination": {"address": destination},
            "travelMode": travel_mode,
            "languageCode": "zh-TW",
            "units": "METRIC"
        }
        
        try:
            response = requests.post(url, headers=headers, json=request_body, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if 'routes' in data and data['routes']:
                    route = data['routes'][0]
                    
                    # 提取时间信息
                    duration_raw = route.get('duration', {})
                    if isinstance(duration_raw, str) and duration_raw.endswith('s'):
                        seconds = int(duration_raw[:-1])
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        duration_text = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"
                        duration_minutes = hours * 60 + minutes
                    elif isinstance(duration_raw, dict) and 'seconds' in duration_raw:
                        seconds = int(duration_raw['seconds'])
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        duration_text = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"
                        duration_minutes = hours * 60 + minutes
                    else:
                        duration_text = str(duration_raw)
                        duration_minutes = 0
                    
                    # 提取距离信息
                    distance_meters = route.get('distanceMeters', 0)
                    distance_km = distance_meters / 1000
                    
                    # 费用估算
                    fuel_cost = int(distance_km * 8 / 100 * 35) if travel_mode == "DRIVE" else 0
                    toll_cost = int(distance_km * 2) if travel_mode == "DRIVE" else 0
                    total_cost = fuel_cost + toll_cost
                    
                    return f"从{origin}到{destination}的路线信息：\n时间：{duration_text}\n距离：{distance_km:.1f}km\n费用：{total_cost}元（油费{fuel_cost}元+过路费{toll_cost}元）"
                else:
                    return f"未找到从{origin}到{destination}的路线"
            else:
                return f"API调用失败：HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"查询路线时发生错误：{str(e)}"

# 定义城市间P2P路线查询工具
class CityRouteInput(BaseModel):
    cities: list[str] = Field(description="要查询的城市列表")
    travel_mode: str = Field(default="DRIVE", description="出行方式")

class GoogleMapsCityRouteTool(BaseTool):
    name: str = "google_maps_city_route"
    description: str = "获取指定城市间的P2P路线信息矩阵，用于路线规划"
    args_schema: Type[BaseModel] = CityRouteInput
    
    def _run(
        self,
        cities: list[str],
        travel_mode: str = "DRIVE",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """查询城市间的P2P路线"""
        results = []
        single_tool = GoogleMapsRouteTool()
        
        # 生成所有城市对的组合
        for origin, destination in itertools.permutations(cities, 2):
            result = single_tool._run(origin, destination, travel_mode)
            results.append(result)
        
        return "\n\n".join(results)

# 定义景点推荐工具
class AttractionInput(BaseModel):
    cities: list[str] = Field(description="要推荐景点的城市列表")

class AttractionRecommendationTool(BaseTool):
    name: str = "attraction_recommendation"
    description: str = "为指定城市推荐热门景点"
    args_schema: Type[BaseModel] = AttractionInput
    
    def _run(
        self,
        cities: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """使用LLM推荐景点"""
        try:
            # 创建LLM实例
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_base=openai_api_url,
                openai_api_key=openai_api_key,
                temperature=0.3
            )
            
            cities_str = "、".join(cities)
            prompt = f"""请为以下城市推荐3-5个最热门的旅游景点：{cities_str}

请按以下格式回答：
城市名：
1. 景点名称 - 简短描述
2. 景点名称 - 简短描述
...

要求：
- 只推荐真实存在的知名景点
- 景点名称要准确，便于地图搜索
- 每个城市推荐3-5个景点
- 描述简洁明了"""
            
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            return f"景点推荐失败：{str(e)}"

# 定义景点翻译工具
class AttractionTranslationInput(BaseModel):
    attractions: list[str] = Field(description="需要翻译的景点列表")

class AttractionTranslationTool(BaseTool):
    name: str = "attraction_translation"
    description: str = "将中文景点名称翻译为英文，用于Places API查询"
    args_schema: Type[BaseModel] = AttractionTranslationInput
    
    def _run(
        self,
        attractions: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict:
        """使用LLM将中文景点名称翻译为英文"""
        try:
            # 创建LLM实例
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_base=openai_api_url,
                openai_api_key=openai_api_key,
                temperature=0.1
            )
            
            attractions_str = "、".join(attractions)
            prompt = f"""请将以下中文景点名称翻译为英文，用于Google Places API查询：

景点列表：{attractions_str}

要求：
1. 翻译要准确，使用景点的官方英文名称
2. 以JSON格式返回，格式如：{{"中文名": "English Name"}}
3. 确保英文名称适合在Google Maps中搜索
4. 如果是知名景点，使用其通用英文名称

请只返回JSON格式的翻译结果，不要其他内容。"""
            
            response = llm.invoke([HumanMessage(content=prompt)])
            
            # 尝试解析JSON响应
            import json
            try:
                translation_dict = json.loads(response.content)
                if isinstance(translation_dict, dict):
                    return translation_dict
            except:
                # 如果JSON解析失败，返回原始名称
                return {name: name for name in attractions}
            
            return {name: name for name in attractions}
            
        except Exception as e:
            print(f"景点翻译失败: {e}")
            return {name: name for name in attractions}

# 定义景点营业时间查询工具
class AttractionHoursInput(BaseModel):
    attractions: list[str] = Field(description="景点列表")

class AttractionHoursTool(BaseTool):
    name: str = "attraction_hours"
    description: str = "获取景点的营业时间信息，用于行程规划"
    args_schema: Type[BaseModel] = AttractionHoursInput
    
    def _run(
        self,
        attractions: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """使用Google Places API (New) 查询景点营业时间"""
        results = []
        
        # 先翻译景点名称
        translation_tool = AttractionTranslationTool()
        translation_dict = translation_tool._run(attractions)
        print(f"景点翻译结果: {translation_dict}")
        
        for attraction in attractions:
            try:
                # 使用英文名称查询
                english_name = translation_dict.get(attraction, attraction)
                print(f"正在查询景点: {attraction} -> {english_name}")
                
                # 使用新版Places API搜索景点
                search_url = "https://places.googleapis.com/v1/places:searchText"
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": google_maps_api_key,
                    "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.businessStatus,places.currentOpeningHours,places.regularOpeningHours"
                }
                
                # 第一次尝试：使用tourist_attraction类型
                request_body = {
                    "textQuery": english_name,
                    "languageCode": "en",
                    "regionCode": "TW",
                    "includedType": "tourist_attraction"
                }
                
                print(f"请求URL: {search_url}")
                print(f"请求体: {request_body}")
                
                search_response = requests.post(search_url, headers=headers, json=request_body, timeout=15)
                print(f"响应状态码: {search_response.status_code}")
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    
                    # 如果没有找到结果，尝试不限制类型的搜索
                    if not search_data.get("places"):
                        print(f"未找到{attraction}，尝试不限制类型搜索...")
                        request_body_fallback = {
                            "textQuery": f"{english_name} Taiwan",
                            "languageCode": "en",
                            "regionCode": "TW"
                        }
                        
                        search_response = requests.post(search_url, headers=headers, json=request_body_fallback, timeout=15)
                        if search_response.status_code == 200:
                            search_data = search_response.json()
                    
                    if "places" in search_data and len(search_data["places"]) > 0:
                        place = search_data["places"][0]
                        
                        # 提取信息
                        name = place.get("displayName", {}).get("text", attraction)
                        address = place.get("formattedAddress", "地址未知")
                        rating = place.get("rating", "无评分")
                        rating_count = place.get("userRatingCount", 0)
                        business_status = place.get("businessStatus", "未知")
                        
                        print(f"找到景点: {name}")
                        
                        # 提取营业时间
                        current_hours = place.get("currentOpeningHours", {})
                        regular_hours = place.get("regularOpeningHours", {})
                        
                        # 优先使用当前营业时间，如果没有则使用常规营业时间
                        hours_info = current_hours or regular_hours
                        
                        if hours_info and "weekdayDescriptions" in hours_info:
                            hours_text = "\n".join(hours_info["weekdayDescriptions"])
                            current_status = "营业中" if hours_info.get("openNow", False) else "未营业"
                        else:
                            hours_text = "营业时间未知 (可能为24小时开放的户外景点)"
                            current_status = "状态未知"
                        
                        result = f"""景点：{attraction} ({english_name})
找到的景点：{name}
地址：{address}
评分：{rating} ({rating_count} reviews)
营业状态：{business_status}
当前状态：{current_status}
营业时间：
{hours_text}"""
                        
                        results.append(result)
                    else:
                        results.append(f"景点：{attraction} ({english_name})\n搜索返回空结果")
                else:
                    error_text = search_response.text
                    results.append(f"景点：{attraction} ({english_name})\n搜索API调用失败 (HTTP {search_response.status_code}): {error_text}")
                    
            except Exception as e:
                results.append(f"景点：{attraction}\n查询错误：{str(e)}")
        
        return "\n\n" + "="*50 + "\n\n".join(results)

def extract_attractions_from_recommendations(recommendations: str) -> list[str]:
    """从景点推荐结果中提取景点名称"""
    attractions = []
    
    # 按行分割推荐结果
    lines = recommendations.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 查找编号开头的行 (如 "1. 台北101 - 描述")
        if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
            # 提取景点名称
            parts = line.split(' - ')
            if len(parts) >= 2:
                # 去掉编号，提取景点名称
                attraction_name = parts[0].split('. ', 1)[-1].strip()
                attractions.append(attraction_name)
            else:
                # 如果没有 " - " 分隔符，尝试其他方式
                # 去掉编号和可能的其他符号
                cleaned = line.split('. ', 1)[-1].strip()
                if cleaned:
                    # 取第一个中文词汇或完整名称
                    first_word = cleaned.split()[0] if cleaned.split() else cleaned
                    attractions.append(first_word)
    
    # 去重并返回
    return list(set(attractions))

def extract_cities_from_prompt(prompt: str) -> list[str]:
    """从用户提示中提取城市名称"""
    try:
        # 使用LLM来提取城市名称
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_base=openai_api_url,
            openai_api_key=openai_api_key,
            temperature=0.1
        )
        
        extraction_prompt = f"""请从以下用户提示中提取所有城市名称：

用户提示："{prompt}"

要求：
1. 只提取城市名称，不要其他信息
2. 以JSON格式返回，例如：["城市1", "城市2"]
3. 如果没有找到城市，返回空数组[]
4. 确保城市名称准确无误"""

        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        
        # 尝试解析JSON响应
        import json
        try:
            cities = json.loads(response.content)
            if isinstance(cities, list):
                return cities
        except:
            # 如果JSON解析失败，尝试简单的文本解析
            pass
        
        return []
        
    except Exception as e:
        print(f"城市提取失败: {e}")
        return []

# 初始化 OpenAI 客户端
try:
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_base=openai_api_url,
        openai_api_key=openai_api_key,
        temperature=0.7
    )
    print("✅ OpenAI 客户端初始化成功")
except Exception as e:
    print(f"❌ OpenAI 客户端初始化失败: {e}")
    exit(1)

# 创建工具实例
google_maps_tool = GoogleMapsRouteTool()
city_route_tool = GoogleMapsCityRouteTool()
attraction_tool = AttractionRecommendationTool()
attraction_translation_tool = AttractionTranslationTool()
attraction_hours_tool = AttractionHoursTool()

# 将工具绑定到LLM
tools = [google_maps_tool, city_route_tool, attraction_tool, attraction_translation_tool, attraction_hours_tool]
llm_with_tools = llm.bind_tools(tools)

def run_intelligent_travel_planning(user_prompt: str):
    """执行智能旅行规划"""
    print(f"🎯 用户需求: {user_prompt}")
    
    # 提取城市信息
    cities = extract_cities_from_prompt(user_prompt)
    if not cities:
        print("❌ 未能从提示中识别出城市，请明确指定城市名称")
        return
    
    print(f"🏙️ 识别到的城市: {cities}")
    
    # 构建系统消息
    system_message = SystemMessage(content="""你是一个专业的智能旅行规划助手。你有以下工具可以使用：

1. attraction_recommendation: 为城市推荐热门景点
2. google_maps_city_route: 获取城市间的P2P路线信息
3. attraction_hours: 获取景点的营业时间和详细信息
4. google_maps_route: 获取两地间的具体路线

请按以下步骤进行规划：
1. 首先为用户指定的城市推荐景点
2. 获取城市间的路线信息
3. 获取推荐景点的营业时间信息
4. 综合分析城市路线和景点营业时间，给出最优的旅行规划建议

规划要求：
- 基于交通时间和费用制定最佳城市游览顺序
- 根据景点营业时间安排具体的每日行程
- 每个城市安排1-2天紧凑而充实的行程
- 不要添加"自由活动"或"根据兴趣安排"等模糊内容
- 提供具体的时间安排和景点游览顺序
- 考虑景点的营业时间，避免冲突
- 给出详细的交通建议和预算估算

请用中文回答，并给出详细、具体、可执行的旅行建议。""")

    # 构建用户消息
    human_message = HumanMessage(content=f"请为我规划{cities}的旅行路线。我希望了解：1) 每个城市的热门景点推荐 2) 城市间的最佳路线 3) 景点的营业时间和详细信息 4) 基于营业时间的详细每日行程安排，不要安排自由活动时间")

    print("\n🤖 开始智能规划...")
    
    try:
        # 第一步：获取景点推荐
        print("📍 第一步：获取景点推荐...")
        attraction_recommendations = attraction_tool._run(cities)
        print(f"景点推荐结果:\n{attraction_recommendations}")
        
        # 第二步：获取城市间路线
        print("\n🛣️ 第二步：获取城市间路线...")
        city_routes = city_route_tool._run(cities)
        print(f"城市间路线:\n{city_routes}")
        
        # 第三步：提取推荐景点并查询营业时间
        print("\n🕐 第三步：提取景点并查询营业时间...")
        
        # 从景点推荐结果中提取景点名称
        extracted_attractions = extract_attractions_from_recommendations(attraction_recommendations)
        print(f"提取到的景点: {extracted_attractions}")
        
        # 查询景点营业时间
        if extracted_attractions:
            attraction_hours = attraction_hours_tool._run(extracted_attractions)
            print(f"景点营业时间:\n{attraction_hours}")
        else:
            attraction_hours = "未能提取到有效景点信息"
            print("⚠️ 未能从推荐结果中提取景点信息")
        
        # 第四步：综合分析
        print("\n📊 第四步：综合分析...")
        analysis_prompt = f"""基于以下信息，请制定详细的旅行规划：

城市列表：{cities}

景点推荐：
{attraction_recommendations}

城市间路线信息：
{city_routes}

景点营业时间信息：
{attraction_hours}

请提供：
1. 最佳的城市游览顺序（基于交通时间和费用）
2. 每个城市的具体景点安排和游览时间
3. 详细的每日行程规划（具体到小时）
4. 基于营业时间的游览建议，避免时间冲突
5. 交通方式和预算估算

要求：
- 制定紧凑而充实的行程，每个城市1-2天
- 不要安排"自由活动"时间，所有时间都要有具体安排
- 根据景点营业时间合理安排游览顺序
- 考虑交通时间，确保行程可行
- 提供具体的时间点和游览建议
- 如果发现营业时间冲突，请调整顺序或提供替代景点

请给出具体可执行的详细行程安排。"""

        final_response = llm.invoke([
            SystemMessage(content="你是专业的旅行规划师，请基于提供的景点营业时间和城市路线数据给出详细的可行性旅行建议。"),
            HumanMessage(content=analysis_prompt)
        ])
        
        print("\n🎉 最终规划建议:")
        print("=" * 50)
        print(final_response.content)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 规划过程中发生错误: {e}")

def test_api_connection():
    """测试API连接"""
    try:
        test_response = llm.invoke([HumanMessage(content="Hello, can you help me?")])
        print("✅ OpenAI API 连接成功")
        return True
    except Exception as e:
        print(f"❌ OpenAI API 连接失败: {e}")
        return False

if __name__ == "__main__":
    # 测试API连接
    if test_api_connection():
        # 示例用户提示
        user_prompts = [
            "我想去台北、高雄、花蓮、屏东旅游，请帮我规划最佳路线",
            "计划台中和台南的两日游，推荐景点和路线",
            "台北到花蓮的自驾游规划"
        ]
        
        # 选择一个提示进行测试
        selected_prompt = user_prompts[0]
        run_intelligent_travel_planning(selected_prompt)
    else:
        print("由于API连接失败，跳过自动规划")