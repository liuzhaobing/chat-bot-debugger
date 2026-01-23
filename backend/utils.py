# -*- coding:utf-8 -*-
# Filename: utils
# Description: 
# Author: zhaobing.liu@outlook.com
# Created: 2026/1/23
# Last Modified: 2026/1/23
import re
import json


def extract_output_json(content: str) -> dict:
    def try_load_json(string: str) -> dict:
        try:
            return json.loads(string)
        except json.JSONDecodeError:
            return {}

    def try_json_warp(string: str) -> dict:
        # 使用正则表达式提取 ```json 与 ``` 之间的部分
        match = re.search(r'```json\s*(.*?)\s*```', string, re.DOTALL)
        if match:
            return try_load_json(match.group(1))
        return {}

    def try_char_warp(string: str) -> dict:
        # 找到JSON部分
        json_start_index = string.find('{')
        json_end_index = string.rfind('}') + 1
        if json_start_index == -1 or json_end_index == 0:
            return {}
        return try_load_json(string[json_start_index:json_end_index])

    # 尝试正则表达式提取，如果失败则尝试字符提取
    return try_json_warp(content) or try_char_warp(content)
