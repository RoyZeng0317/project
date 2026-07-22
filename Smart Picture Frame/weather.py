# 讀取 GPS 定位、查詢中央氣象局「一週縣市天氣預報」，並用簡易機器學習模型推估降雨風險
# GPS 模組透過 UART 接在樹莓派 (或轉接在 ESP32-S3 上) 上，經由 gpsd 讀取座標
import gps
import requests
from geopy.geocoders import Nominatim
from sklearn.ensemble import RandomForestClassifier

# 中央氣象局開放資料平台 API Key，請至 https://opendata.cwa.gov.tw/ 申請後填入
API_KEY = ""
# F-C0032-005 = 一般天氣預報-1週縣市天氣預報
CWA_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-005"


def get_location():
    # 連線 gpsd，讀取目前經緯度 (gpsd 需先設定監聽 UART GPS 裝置，例如 /dev/serial0)
    session = gps.gps(mode=gps.WATCH_ENABLE)
    while True:
        try:
            report = session.next()
            if report['class'] == 'TPV':
                lat = getattr(report, 'lat', None)
                lon = getattr(report, 'lon', None)
                if lat and lon:
                    return lat, lon
        except StopIteration:
            print("GPS connection error")
            return None, None


def get_city_name(lat, lon):
    # 用經緯度反查所在縣市，當作查詢中央氣象局天氣的依據
    geolocator = Nominatim(user_agent="smart_picture_frame")
    location = geolocator.reverse((lat, lon))
    address = location.raw.get("address", {})
    return address.get("county") or address.get("city") or "雲林縣"


def rain_analysis(pop):
    # 依降雨機率 (PoP，百分比) 轉成中文提示文字
    pop = int(pop)
    if pop >= 80:
        return "大雨機率高，建議攜帶雨具"
    elif pop >= 50:
        return "可能降雨"
    elif pop >= 30:
        return "短暫雨"
    else:
        return "降雨機率低"


def get_weekly_forecast(city_name):
    # 呼叫中央氣象局「一週縣市天氣預報」API，回傳該縣市未來一週的原始 JSON
    params = {
        "Authorization": API_KEY,
        "format": "JSON",
        "locationName": city_name,
    }
    response = requests.get(CWA_URL, params=params, timeout=10)
    return response.json()


def get_weekly_pop(city_name):
    # 從一週預報 JSON 中取出「降雨機率 (PoP)」的每一筆時間資料，簡化成 [(起始時間, 機率)] 清單
    data = get_weekly_forecast(city_name)
    location = data["records"]["location"][0]
    pop_element = next(e for e in location["weatherElement"] if e["elementName"] == "PoP")
    return [(t["startTime"], t["parameter"]["parameterName"]) for t in pop_element["time"]]


# ---- 簡易機器學習：用少量示範資料訓練「是否容易下雨」分類器 ----
# 特徵：[溫度, 濕度, 氣壓, 風速]；標籤：1 = 容易下雨、0 = 不易下雨
# 注意：這裡只是示範用的極小樣本，正式使用建議改用歷史氣象資料重新訓練
_x = [
    [30, 80, 1012, 5],
    [29, 90, 1008, 8],
    [32, 60, 1015, 2],
]
_y = [1, 1, 0]

_model = RandomForestClassifier()
_model.fit(_x, _y)


def predict_rain(temperature, humidity, pressure, wind_speed):
    # 用目前氣象數值推估是否容易下雨，回傳 1 (容易) 或 0 (不易)
    return int(_model.predict([[temperature, humidity, pressure, wind_speed]])[0])


if __name__ == "__main__":
    # 直接執行本檔案時，做一次完整流程測試 (定位 -> 查天氣 -> 印出結果)
    lat, lon = get_location()
    city = get_city_name(lat, lon)
    print(city, get_weekly_pop(city))
