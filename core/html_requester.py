import json
import os

import requests
from time import sleep
from core.console import colored_print


# User_Agent 可以按照自己浏览器中的标头修改，开发者模式（F12）-> 网络（Network） -> 任意点击一个请求 -> 查看标头（Headers）
# Cookie 很重要，相当于个人喜好，大数据（一个经常看论文的人更容易搜到论文）
request_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}


def get_page_content(url: str, params: dict = None, headers: dict = None, max_retry_times: int = 3, return_type: str = "text"):
    """
    获取网页的 html 内容

    Args:
        url: 网页地址
        headers: 请求头，默认使用 request_headers
        max_retry_times: 最大重试次数，默认 3 次
        return_type: 返回类型，默认 text，或者 default（返回 requests.Response 对象）
    """
    if headers is None:
        headers = request_headers
        # 读取 Cookies.txt 文件，设置 headers
        if os.path.exists("Cookie"):
            with open("Cookie", "r") as f:
                cookie = f.read()
                headers["Cookie"] = cookie

    retry_times = 0
    while retry_times <= max_retry_times or max_retry_times == -1:
        response = None
        try:
            # 获取网页内容
            response = requests.get(url=url, params=params, headers=headers)    # 通过 url 获取网页相应内容
            response.raise_for_status()                                     # 检查相应状态码
            content = response.text                                         # 获取网页内容
            if max_retry_times > 0 and retry_times > 0:
                colored_print(f"\r经过 {retry_times} 次重试后，获取网页 {url} 内容成功！", "green")

            # 根据 return_type 返回内容
            if return_type == "default":
                return response
            elif return_type == "text":
                return content
            else:
                raise ValueError(f"不支持的 return_type: {return_type}")
        except requests.exceptions.RequestException as e:
            retry_times += 1

            # 重试次数达到上限，打印错误信息
            if max_retry_times >= 0 and retry_times > max_retry_times:
                if not response:
                    colored_print(f"\r获取网页 {url} 内容失败！未得到响应！{f'传入参数为 {params}, ' if params else ''}"
                                  f"错误信息: \n{e}",
                              "red")
                elif response.status_code == 404:
                    colored_print(f"\r获取网页 {url} 内容失败！状态码: {response.status_code},"
                                  f" 错误信息: 页面不存在！",
                                  "red")
                else:
                    colored_print(f"\r获取网页 {url} 内容失败！状态码: {response.status_code},"
                                  f" 错误信息: \n{response.text}",
                                  "red")
                break

            # 重试
            if retry_times < max_retry_times or max_retry_times == -1:
                print(f"\r({retry_times}) 获取网页内容失败：{e}，重试中...", end="")
                sleep(0.5)                                          # 重试间隔

    return None


def post_page_content(url: str, data: dict, headers: dict = None, max_retry_times: int = 3, return_type: str = "text"):
    """
    发送 POST 请求获取网页内容

    Args:
        url: 网页地址
        data: POST 请求参数
        headers: 请求头，默认使用 request_headers
        max_retry_times: 最大重试次数，默认 3 次
        return_type: 返回类型，默认 text，或者 default（返回 requests.Response 对象）
    """
    if headers is None:
        headers = request_headers
        # 读取 Cookies.txt 文件，设置 headers
        if os.path.exists("Cookie"):
            with open("Cookie", "r") as f:
                cookie = f.read()
                headers["Cookie"] = cookie

    retry_times = 0
    while retry_times <= max_retry_times or max_retry_times == -1:
        response = None
        try:
            # 获取网页内容
            data_json = json.dumps(data)
            response = requests.post(url=url, data=data_json, headers=headers)  # 通过发送 post 请求并 url 获取网页内容
            response.raise_for_status()                                         # 检查相应状态码
            content = response.text                                             # 获取网页内容
            if max_retry_times > 0 and retry_times > 0:
                colored_print(f"\r获取网页 {url} 内容成功！", "green")

            # 根据 return_type 返回内容
            if return_type == "default":
                return response
            elif return_type == "text":
                return content
            else:
                raise ValueError(f"不支持的 return_type: {return_type}")
        except requests.exceptions.RequestException as e:
            retry_times += 1

            # 重试次数达到上限，打印错误信息
            if max_retry_times >= 0 and retry_times > max_retry_times:
                if not response:
                    colored_print(f"\r获取网页 {url} 内容失败！未得到响应！传入参数为 {data}, "
                                  f"错误信息: \n{e}",
                              "red")
                elif response.status_code == 404:
                    colored_print(f"\r获取网页 {url} 内容失败！状态码: {response.status_code}, "
                                  f"错误信息: 页面不存在！",
                                  "red")
                else:
                    colored_print(f"\r获取网页 {url} 内容失败！状态码: {response.status_code}, "
                                  f"响应内容: \n{response.text}, "
                                  f"错误信息: \n{e}",
                              "red")
                break

            # 重试
            if retry_times < max_retry_times or max_retry_times == -1:
                print(f"\r({retry_times}) 获取网页内容失败：{e}，重试中...", end="")
                sleep(0.5)  # 重试间隔

    return None
