# -*- coding: utf-8 -*-
from selenium import webdriver
from flask import Flask, jsonify, request
import os
import json

APP = Flask(__name__)
PRO_DIR = os.path.dirname(os.path.abspath(__file__))

driver = None

def init_driver():
    global driver
    if driver is None:
        option = webdriver.ChromeOptions()
        option.add_argument('--disable-blink-features=AutomationControlled')
        option.add_argument('--headless')  
        driver = webdriver.Chrome(options=option)

def open_html_file(html_file):
    init_driver()  
    driver.get('file://' + PRO_DIR + '/' + html_file)

@APP.route('/get_api_params')
def gen_params():
    html_file = '11.模拟浏览器.html'
    open_html_file(html_file)

    return driver.execute_script('return window.params();')

@APP.route('/encode_coord')
def encode_coord():
    html_file = '11.模拟浏览器.html'
    open_html_file(html_file)

 
    params = request.query_string.decode()
    param_dict = dict(param.split('=') for param in params.split('&'))
    token = param_dict.get('token') 

    x = int(param_dict.get('x'))  
    y = int(param_dict.get('y'))  
    beginTime = int(param_dict.get('beginTime'))  
    ts = int(param_dict.get('ts'))  

    encoded = driver.execute_script('return window.encodeCoord(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4]);'
                                    , token, x, y, ts, beginTime)
    
    # debug//print(encoded)
    context = {
        "encoded": encoded
    }

    return jsonify(context=context)

@APP.route('/check_api_params')
def gen_data():
    html_file = '11.模拟浏览器.html'
    open_html_file(html_file)


    trace_data = request.args.get('trace_data')
    points_stack = request.args.get('points_stack')
    token = request.args.get('token')

    try:
        trace_data_list = json.loads(trace_data) if trace_data else []
        points_stack_list = json.loads(points_stack) if points_stack else []


        print("Token:", token)
        print("Trace Data:", trace_data_list)
        print("Points Stack:", points_stack_list)

        res = driver.execute_script('return window.getData(arguments[0], arguments[1], arguments[2]);', json.dumps({
            'trace_data': trace_data_list,
            'points_stack': points_stack_list,
            'token': token
        }))

        return res

    except json.JSONDecodeError as e:
        return jsonify({"error": "Failed to decode JSON", "details": str(e)}), 400

if __name__ == '__main__':
    APP.run()
