import math
import os
import time

import requests
import openai
import json

os.environ.setdefault('OPENAI_API_KEY', '==========')
google_maps_api_key = '================'
# 时间相关
def current_timestamp():
    return int(time.time())


def reverse_geocode(lat, lon):
    url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}'
    response = requests.get(url)
    data = response.json()
    if 'address' in data:
        return data['display_name']
    else:
        return None


# 位置相关
def get_route(start_coords, end_coords):
    """
    获取从起点到终点的导航路径
    :param start_coords: 起点坐标 (纬度, 经度)
    :param end_coords: 终点坐标 (纬度, 经度)
    :return: 路径上的坐标点列表
    """
    base_url = "http://router.project-osrm.org/route/v1/driving/"
    start = f"{start_coords[0]},{start_coords[1]}"
    end = f"{end_coords[0]},{end_coords[1]}"
    url = f"{base_url}{start};{end}?overview=full&geometries=geojson"

    response = requests.get(url)
    data = response.json()

    if data.get("routes"):
        route = data["routes"][0]["geometry"]["coordinates"]
        # 将 (经度, 纬度) 转换为 (纬度, 经度)
        route_lat_lon = [(coord[0], coord[1]) for coord in route]
        route_lat_lon.insert(0, (start_coords[0], start_coords[1]))
        route_lat_lon.append((end_coords[0], end_coords[1]))
        return route_lat_lon
    else:
        raise Exception("无法找到路径")


def haversine(coord1, coord2):
    """
    计算两个经纬度点之间的距离
    :param coord1: 第一个坐标 (纬度, 经度)
    :param coord2: 第二个坐标 (纬度, 经度)
    :return: 距离（以公里为单位）
    """
    # 将度数转换为弧度
    lat1, lon1 = map(math.radians, coord2)
    lat2, lon2 = map(math.radians, coord1)

    # Haversine 公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # 地球半径（以公里为单位）
    r = 6371.0

    # 计算距离
    distance = c * r
    return distance


def sparse_route(route, min_distance_km):
    sparse_route = [route[0]]  # 起点
    current_point = route[0]

    for point in route[1:]:
        if haversine(current_point, point) >= min_distance_km:
            sparse_route.append(point)
            current_point = point

    if current_point != route[-1]:
        sparse_route.append(route[-1])  # 确保终点包含在内

    return sparse_route


def get_image_url(image_path: str) -> str:
    # 将图片上传S3获得访问URL
    # TODO
    return 'https://baidu.com'

def get_coordinates(place_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': place_name,
        'key': google_maps_api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return [location['lng'], location['lat']]
    else:
        return None


def get_key_sights(cities):
    """
    获取城市的关键景点
    """
    prompt = f"""请你针对以下这{len(cities)}个城市，分别给出一个你认为最值得一游的景点，这些城市包括：{cities}
    请以 json 格式输出，格式如下，请确保顺序：
    {{
        "city_name_1": "sight_name_1",
        "city_name_2": "sight_name_2",
        ...
    }}
    """
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        max_tokens=4096,
        n=1,
        stop=None,
        temperature=0.5,
        messages=[{"role": "system", "content": prompt}],

    )
    gpt_resp = json.loads(response.choices[0].message.content)
    # print(gpt_resp)
    sights = []
    for i,city in enumerate(gpt_resp):
        try:
            sights.append((gpt_resp[city],get_coordinates(gpt_resp[city])))
        except:
            sights.append((city, None))
    return sights



if __name__ == '__main__':
    latitude =40.293316
    longitude = 120.00799
    print(reverse_geocode(latitude, longitude).split(',')[-3:])


