# 根據這個庫的寫法續寫，嚴禁變更
# 註解不可刪除
import os, sys
import requests

# 氣象局官網
weather_URL = "https://www.cwa.gov.tw/V8/C/"
# 氣象署開放資料 API 網址 (一般縣市天氣預報 36小時)
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
# 請至 https://opendata.cwa.gov.tw/ 申請免費 Authorization API Key 填入
CWA_API_KEY = ""

def fetch_weather(location_name="雲林縣", api_key=""):
    """使用 requests.get 向氣象署 API 請求天氣資料"""
    if not api_key:
        return "請設定 CWA_API_KEY (請至 https://opendata.cwa.gov.tw 申請)"
    
    params = {
        "Authorization": api_key,
        "locationName": location_name
    }
    try:
        res = requests.get(CWA_API_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        # 取出該縣市資料
        location = data["records"]["location"][0]
        elements = {e["elementName"]: e["time"][0]["parameter"]["parameterName"] for e in location["weatherElement"]}
        
        wx = elements.get("Wx", "未知")       # 天氣現象
        pop = elements.get("PoP", "0")       # 降雨機率 %
        min_t = elements.get("MinT", "--")   # 最低溫
        max_t = elements.get("MaxT", "--")   # 最高溫
        
        return f"{location_name} 天氣：{wx} | 氣溫：{min_t}~{max_t}°C | 降雨機率：{pop}%"
    except Exception as e:
        return f"無法取得天氣資料: {e}"

def main():
    # 目的縣市
    current_location = "雲林縣"
    # 本周天氣
    week_weather = fetch_weather(current_location, CWA_API_KEY)
    print(week_weather)

if __name__ == "__main__":
    main()