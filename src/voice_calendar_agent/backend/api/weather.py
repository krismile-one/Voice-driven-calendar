"""
天气信息 API 接口

通过 wttr.in 免费 API 获取实时天气，用于前端动态背景切换。
参考：https://github.com/chubin/wttr.in
"""

import logging
import time
from datetime import datetime, time as dt_time
from typing import Optional

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── WWO 天气码 → 简化分类（供前端 CSS 选择器使用） ──
# https://www.worldweatheronline.com/weather-api/api/docs/weather-icons.aspx
WWO_CATEGORY: dict[str, str] = {
    "113": "sunny",
    "116": "partly_cloudy",
    "119": "cloudy",
    "122": "overcast",
    "143": "fog",
    "176": "light_rain",
    "179": "snow",
    "182": "sleet",
    "185": "freezing_drizzle",
    "200": "thunder",
    "227": "snow",
    "230": "snow",
    "248": "fog",
    "260": "fog",
    "263": "light_rain",
    "266": "light_rain",
    "281": "freezing_drizzle",
    "284": "freezing_drizzle",
    "293": "light_rain",
    "296": "light_rain",
    "299": "moderate_rain",
    "302": "heavy_rain",
    "305": "heavy_rain",
    "308": "heavy_rain",
    "311": "freezing_rain",
    "314": "freezing_rain",
    "317": "sleet",
    "320": "sleet",
    "323": "snow",
    "326": "snow",
    "329": "snow",
    "332": "snow",
    "335": "snow",
    "338": "snow",
    "350": "sleet",
    "353": "light_rain",
    "356": "moderate_rain",
    "359": "heavy_rain",
    "362": "sleet",
    "365": "sleet",
    "368": "snow",
    "371": "snow",
    "374": "sleet",
    "377": "sleet",
    "386": "thunder",
    "389": "thunder",
    "392": "thunder",
    "395": "snow",
}

# WWO 码 → 中文描述
WWO_DESC: dict[str, str] = {
    "113": "晴",
    "116": "晴间多云",
    "119": "多云",
    "122": "阴",
    "143": "雾",
    "176": "小雨",
    "179": "雪",
    "182": "雨夹雪",
    "185": "冻毛毛雨",
    "200": "雷暴",
    "227": "阵雪",
    "230": "暴雪",
    "248": "雾",
    "260": "霾",
    "263": "小阵雨",
    "266": "小阵雨",
    "281": "冻毛毛雨",
    "284": "冻毛毛雨",
    "293": "小雨",
    "296": "小雨",
    "299": "中雨",
    "302": "大雨",
    "305": "大雨",
    "308": "暴雨",
    "311": "冻雨",
    "314": "冻雨",
    "317": "雨夹雪",
    "320": "雨夹雪",
    "323": "小雪",
    "326": "小雪",
    "329": "中雪",
    "332": "中雪",
    "335": "大雪",
    "338": "大雪",
    "350": "雨夹雪",
    "353": "阵雨",
    "356": "中雨",
    "359": "暴雨",
    "362": "雨夹雪",
    "365": "雨夹雪",
    "368": "雪",
    "371": "雪",
    "374": "雨夹雪",
    "377": "雨夹雪",
    "386": "雷阵雨",
    "389": "雷暴",
    "392": "雷阵雨",
    "395": "大雪",
}

# ── 简单内存缓存 ──
_cache: dict = {"raw": None, "data": None, "ts": 0, "coord_key": ""}
CACHE_TTL = 30 * 60  # 30 分钟

# ── WWO 天气码 → Emoji（供前端日期格右上角使用） ──
WWO_EMOJI: dict[str, str] = {
    "113": "☀️",   # 晴 ☀️
    "116": "⛅",          # 晴间多云 ⛅
    "119": "☁️",   # 多云 ☁️
    "122": "☁️",   # 阴 ☁️
    "143": "🌫️️",  # 雾 🌫️
    "176": "🌧️️",  # 小雨 🌧️
    "179": "\U0001f328️",  # 雪 🌨️
    "182": "\U0001f328️",  # 雨夹雪 🌨️
    "185": "\U0001f327️",  # 冻毛毛雨 🌧️
    "200": "⛈️",   # 雷暴 ⛈️
    "227": "\U0001f328️",  # 阵雪 🌨️
    "230": "\U0001f328️",  # 暴雪 🌨️
    "248": "\U0001f32b️",  # 雾 🌫️
    "260": "\U0001f32b️",  # 霾 🌫️
    "263": "🌧️️",  # 小阵雨 🌧️
    "266": "\U0001f327️",  # 小阵雨 🌧️
    "281": "\U0001f327️",  # 冻毛毛雨 🌧️
    "284": "\U0001f327️",  # 冻毛毛雨 🌧️
    "293": "🌧️️",  # 小雨 🌧️
    "296": "🌧️",  # 小雨 🌧️
    "299": "🌧️️",  # 中雨 🌧️
    "302": "🌧️️",  # 大雨 🌧️
    "305": "🌧️️",  # 大雨 🌧️
    "308": "🌧️️",  # 暴雨 🌧️
    "311": "\U0001f327️",  # 冻雨 🌧️
    "314": "\U0001f327️",  # 冻雨 🌧️
    "317": "\U0001f328️",  # 雨夹雪 🌨️
    "320": "\U0001f328️",  # 雨夹雪 🌨️
    "323": "\U0001f328️",  # 小雪 🌨️
    "326": "\U0001f328️",  # 小雪 🌨️
    "329": "\U0001f328️",  # 中雪 🌨️
    "332": "\U0001f328️",  # 中雪 🌨️
    "335": "\U0001f328️",  # 大雪 🌨️
    "338": "\U0001f328️",  # 大雪 🌨️
    "350": "\U0001f328️",  # 雨夹雪 🌨️
    "353": "\U0001f327️",  # 阵雨 🌧️
    "356": "\U0001f327️",  # 中雨 🌧️
    "359": "\U0001f327️",  # 暴雨 🌧️
    "362": "\U0001f328️",  # 雨夹雪 🌨️
    "365": "\U0001f328️",  # 雨夹雪 🌨️
    "368": "\U0001f328️",  # 雪 🌨️
    "371": "\U0001f328️",  # 雪 🌨️
    "374": "\U0001f328️",  # 雨夹雪 🌨️
    "377": "\U0001f328️",  # 雨夹雪 🌨️
    "386": "⛈️",   # 雷阵雨 ⛈️
    "389": "⛈️",   # 雷暴 ⛈️
    "392": "⛈️",   # 雷阵雨 ⛈️
    "395": "\U0001f328️",  # 大雪 🌨️
}


class WeatherResponse(BaseModel):
    """天气信息响应"""

    weather_code: str = Field(..., description="WWO 天气码，如 '113'=晴")
    weather_desc: str = Field(..., description="中文天气描述")
    weather_category: str = Field(
        ...,
        description="简化分类: sunny/partly_cloudy/cloudy/overcast/fog/"
        "light_rain/moderate_rain/heavy_rain/snow/sleet/"
        "freezing_drizzle/freezing_rain/thunder",
    )
    is_day: bool = Field(..., description="是否白天（基于日出日落时间）")
    temperature: Optional[int] = Field(None, description="当前温度（摄氏度）")
    city: Optional[str] = Field(None, description="城市名称")
    source: str = Field(default="wttr.in", description="数据来源")


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    lat: Optional[float] = Query(None, ge=-90, le=90, description="纬度"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="经度"),
):
    """
    获取当前天气信息。

    通过 wttr.in 免费 API 获取实时天气与天文数据（日出日落），
    返回简化的天气分类和昼夜判断，供前端切换动态背景。

    不传坐标时默认使用北京（39.9, 116.4）。
    带 30 分钟内存缓存（按坐标区分），避免频繁请求外部 API。
    """
    _lat = lat if lat is not None else 39.9
    _lon = lon if lon is not None else 116.4
    coord_key = f"{_lat:.2f},{_lon:.2f}"

    # ── 命中缓存 ──
    now_ts = time.time()
    if (
        _cache["data"]
        and _cache["coord_key"] == coord_key
        and (now_ts - _cache["ts"]) < CACHE_TTL
    ):
        return _cache["data"]

    try:
        raw = await _fetch_wttr(_lat, _lon)

        # ── 解析当前天气 ──
        current = raw.get("current_condition", [{}])[0]
        weather_code = str(current.get("weatherCode", "113"))
        temp_c = current.get("temp_C")
        temperature = int(float(temp_c)) if temp_c is not None else None

        # ── 解析天文（日出日落） ──
        weather_arr = raw.get("weather", [{}])
        astronomy = weather_arr[0].get("astronomy", [{}])[0] if weather_arr else {}
        sunrise_str = astronomy.get("sunrise", "06:00 AM")
        sunset_str = astronomy.get("sunset", "06:00 PM")
        is_day = _is_daytime(sunrise_str, sunset_str)

        # ── 城市名 ──
        nearest = raw.get("nearest_area", [{}])[0]
        city = None
        for name_obj in nearest.get("areaName", []):
            if name_obj.get("value"):
                city = name_obj["value"]
                break
        if not city:
            for name_obj in nearest.get("region", []):
                if name_obj.get("value"):
                    city = name_obj["value"]
                    break

        category = WWO_CATEGORY.get(weather_code, "cloudy")
        desc = WWO_DESC.get(weather_code, "多云")

        result = WeatherResponse(
            weather_code=weather_code,
            weather_desc=desc,
            weather_category=category,
            is_day=is_day,
            temperature=temperature,
            city=city,
        )

        # 更新缓存
        _cache["data"] = result
        _cache["ts"] = now_ts
        _cache["coord_key"] = coord_key

        logger.info(
            "天气: %s %s°C, 白天=%s, 城市=%s",
            desc, temperature, is_day, city,
        )
        return result

    except Exception as e:
        logger.warning("获取天气失败: %s", e)
        # 如果有旧缓存（任意坐标），降级返回
        if _cache["data"]:
            return _cache["data"]
        # 完全无缓存时返回默认（北京晴天）
        return WeatherResponse(
            weather_code="113",
            weather_desc="晴",
            weather_category="sunny",
            is_day=True,
        )


class ForecastDay(BaseModel):
    """单日天气预报"""

    date: str = Field(..., description="日期，格式 YYYY-MM-DD")
    weather_code: str = Field(..., description="WWO 天气码")
    weather_desc: str = Field(..., description="中文天气描述")
    weather_category: str = Field(..., description="简化天气分类")
    emoji: str = Field(..., description="天气 emoji")


class ForecastResponse(BaseModel):
    """三日天气预报响应"""

    forecast: list[ForecastDay] = Field(..., description="未来 3 天预报")
    city: Optional[str] = Field(None, description="城市名称")


async def _fetch_wttr(lat: float, lon: float) -> dict:
    """获取 wttr.in 原始数据（带缓存）"""
    coord_key = f"{lat:.2f},{lon:.2f}"
    now_ts = time.time()

    if (
        _cache["raw"]
        and _cache["coord_key"] == coord_key
        and (now_ts - _cache["ts"]) < CACHE_TTL
    ):
        return _cache["raw"]

    url = f"https://wttr.in/{lat},{lon}?format=j1&lang=zh"
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.json()

    _cache["raw"] = raw
    _cache["ts"] = now_ts
    _cache["coord_key"] = coord_key
    return raw


@router.get("/weather/forecast", response_model=ForecastResponse)
async def get_forecast(
    lat: Optional[float] = Query(None, ge=-90, le=90, description="纬度"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="经度"),
):
    """
    获取未来 3 天天气预报。

    用于前端日期格右上角显示天气 emoji。
    不传坐标时默认使用北京。
    """
    _lat = lat if lat is not None else 39.9
    _lon = lon if lon is not None else 116.4

    try:
        raw = await _fetch_wttr(_lat, _lon)

        # ── 城市名 ──
        nearest = raw.get("nearest_area", [{}])[0]
        city = None
        for name_obj in nearest.get("areaName", []):
            if name_obj.get("value"):
                city = name_obj["value"]
                break

        # ── 解析未来 3 天预报 ──
        weather_arr = raw.get("weather", [])
        forecast: list[ForecastDay] = []

        for day_data in weather_arr[:3]:
            date_str = day_data.get("date", "")
            # 取中午时段的天气码（index 4 ≈ 12:00，index 5 ≈ 15:00）
            hourly = day_data.get("hourly", [])
            midday = hourly[4] if len(hourly) > 4 else (hourly[0] if hourly else {})
            code = str(midday.get("weatherCode", "113"))
            desc = WWO_DESC.get(code, "多云")
            category = WWO_CATEGORY.get(code, "cloudy")
            emoji = WWO_EMOJI.get(code, "☁️")

            forecast.append(ForecastDay(
                date=date_str,
                weather_code=code,
                weather_desc=desc,
                weather_category=category,
                emoji=emoji,
            ))

        return ForecastResponse(forecast=forecast, city=city)

    except Exception as e:
        logger.warning("获取天气预报失败: %s", e)
        # 降级：返回空预报，前端不显示 emoji
        return ForecastResponse(forecast=[])


def _is_daytime(sunrise_str: str, sunset_str: str) -> bool:
    """根据日出日落时间判断当前是否白天"""
    try:
        now = datetime.now().time()
        sunrise = _parse_ampm_time(sunrise_str)
        sunset = _parse_ampm_time(sunset_str)
        if sunrise and sunset:
            return sunrise <= now <= sunset
    except Exception:
        pass
    # fallback: 6:00-18:00 为白天
    h = datetime.now().hour
    return 6 <= h < 18


def _parse_ampm_time(s: str) -> Optional[dt_time]:
    """解析 '06:00 AM' / '06:52 PM' 格式的时间字符串"""
    try:
        return datetime.strptime(s.strip(), "%I:%M %p").time()
    except (ValueError, AttributeError):
        return None
