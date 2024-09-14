import requests
from time import sleep


# User_Agent 可以按照自己浏览器中的表头修改，开发者模式（F12）-> 网络（Network） -> 任意点击一个请求 -> 查看标头（Headers）
# Cookie 很重要，相当于个人喜好，大数据（一个经常看论文的人更容易搜到论文）
request_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}


def get_page_content(url: str, headers: dict = None):
    """
    获取网页的 html 内容
    """
    if headers is None:
        headers = request_headers

    while True:
        try:
            response = requests.get(url=url, headers=headers)   # 通过 url 获取网页相应
            response.raise_for_status()                         # 检查相应状态码
            content = response.text                             # 获取网页内容
            return content
        except requests.exceptions.RequestException as e:
            print(f"获取网页内容失败：{e}，\n重试中...")
            sleep(0.1)                                          # 重试间隔
