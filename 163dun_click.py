import requests
import re
import json
import execjs
import base64
import random



def get_params():
    params_dict = requests.get("http://127.0.0.1:5000/get_api_params").json()
    return {
        "fp": params_dict["fp"],
        "cb": params_dict["cb"],
    }

def click_verify(front):
    url = "http://api.jfbym.com/api/YmServer/customApi"
    with open('click.png', 'rb') as f:
        img = f.read()
    data = {
        "token": "_DrOYPrOmEQ11FuwuMjcOPPBa_nx2cXrlEuFpzslZBY",
        "type": "30100",
        "image": base64.b64encode(img).decode(),
        "extra": (",").join(front)
    }
    _headers = {
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=_headers, data=json.dumps(data))
    return resp.json()['data']['data']

def render_coordinates(coordinates):
    rendered_coordinates = []

    for coord in coordinates:
        x, y = map(int, coord.split(','))
        rendered_coordinates.append((round(x / 3 * 2)-2, round(y / 3 * 2) + 1))  

    return rendered_coordinates

def ease_in_out_quad(t):
    """ 二次缓动函数：ease in and out """
    if t < 0.5:
        return 2 * t * t
    else:
        return -1 + (4 - 2 * t) * t
def generate_movement_coordinates(rendered_coordinates, begin_time):
    result = []
    timestamp = begin_time
    
    start_x, start_y = rendered_coordinates[0]
    result.append((start_x, start_y, timestamp))  

    for i in range(1, len(rendered_coordinates)):
        target_x, target_y = rendered_coordinates[i]
        length = random.randint(135, 160)  
        
        
        for j in range(length):
            t = j / (length - 1)  
            eased_x = ease_in_out_quad(t) * (target_x - start_x) + start_x 
            
            
            y = int(start_y + (target_y - start_y) * t) + random.randint(-5, 5)  # ±5波动
            
            result.append((int(eased_x), y, timestamp))  
            
            timestamp += random.randint(5, 15)  

        
        result.append((target_x, target_y, timestamp))  
        start_x, start_y = target_x, target_y  

    return result


def encode_coord(token, x, y, ts, begin_time):
    params = {
    'token': token,
    'x': x,
    'y': y,
    'beginTime': begin_time,
    'ts': ts
    }
    res = requests.get("http://127.0.0.1:5000/encode_coord", params=params).json()
    return res.get("context")["encoded"]

def main():
    # 获取cb, fp
    params1 = get_params()
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,fr;q=0.8,en;q=0.7,zh-TW;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://dun.163.com/",
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\""
    }

    # 获取图片链接，文字信息和token 
    url = "https://c.dun.163.com/api/v3/get"
    params = {
        "referer": "https://dun.163.com/trial/picture-click",
        "zoneId": "CN31",
        "dt": "UhBvgHrZhB9FVkQFQRfDEpLtJqDziR0s",
        "irToken": "oU3OvVk+pjFAdxVBRROSDcP3OdjC6qm1",
        "id": "07e2387ab53a4d6f930b8d9a9be71bdf",
        "fp": params1['fp'],
        "https": "true",
        "type": "3",
        "version": "2.28.0",
        "dpr": "2",
        "dev": "1",
        "cb": params1['cb'],
        "ipv6": "false",
        "runEnv": "10",
        "group": "",
        "scene": "",
        "lang": "zh-CN",
        "sdkVersion": "",
        "loadVersion": "2.5.0",
        "iv": "4",
        "user": "",
        "width": "320",
        "audio": "false",
        "sizeType": "10",
        "smsVersion": "v3",
        "callback": "__JSONP_9rmrg1h_18"
    }

    jsonp_response = requests.get(url, headers=headers, params=params).text
    match = re.search(r'^\w+\((.*)\);$', jsonp_response)

    if match:
        json_string = match.group(1)  
        data_object = json.loads(json_string)
        img_res = data_object['data']

        bg_url = img_res["bg"][0]
        front = img_res["front"]
        # print((",").join(front))
        token = img_res["token"]

        bg_res = requests.get(bg_url)
        with open('click.png', 'wb') as f:
            f.write(bg_res.content)

    # 计算文字坐标并处理
    coords_str = click_verify(front)
    coord_list = coords_str.split("|")

    begin_time = execjs.eval("new Date().getTime()")

    # 调整渲染后坐标 480*240 -> 320*160
    rendered_coords = render_coordinates(coord_list)

    # 生成鼠标移动轨迹
    movement_coordinates = generate_movement_coordinates(rendered_coords, begin_time)

    # 在轨迹中截取文字坐标对应元素
    unique_specific_points = {}
    for x, y, ts in movement_coordinates:
        if (x, y) in rendered_coords and (x, y) not in unique_specific_points:
            unique_specific_points[(x, y)] = ts  # 只记录首次出现的时间戳

    # 轨迹算法
    trace_data = []
    for x, y, ts in movement_coordinates:
        trace_data.append(encode_coord(token, x, y, ts, begin_time))
    # print(trace_data)

    # 文字坐标算法
    points_stack = []
    for (x_, y_), ts_ in unique_specific_points.items():  
        points_stack.append(encode_coord(token, x_, y_, ts_ + random.randint(1234, 5678), begin_time))
        # random.randint(1234, 5678): 前端加密pointsStack的时间比加密traceData时间晚
    # print(points_stack)

    # 利用html补环境进行check接口参数处理
    params = {
        "trace_data": json.dumps(trace_data), 
        "points_stack": json.dumps(points_stack),
        'token': token,
    }
    resp = requests.get("http://127.0.0.1:5000/check_api_params", params=params).text
    # print(resp)

    url3 = "https://c.dun.163.com/api/v3/check"

    params3 = {
        "referer": "https://dun.163.com/trial/picture-click",
        "zoneId": "CN31",
        "dt": "UhBvgHrZhB9FVkQFQRfDEpLtJqDziR0s",
        "id": "07e2387ab53a4d6f930b8d9a9be71bdf",
        "token": token,
        "data": resp,
        "width": "320",
        "type": "3",
        "version": "2.28.0",
        "cb": get_params()["cb"],
        "user": "",
        "extraData": "",
        "bf": "0",
        "runEnv": "10",
        "sdkVersion": "",
        "loadVersion": "2.5.0",
        "iv": "4",
        "callback": "__JSONP_2eq1ihp_19"
    }
    response = requests.get(url3, headers=headers, params=params3)
    # print("Sending parameters:", params3)

    print(response.text)
    print(response)

if __name__ == "__main__":
    main()