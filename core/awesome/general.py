
from requests import Response
from concurrent.futures import ThreadPoolExecutor, as_completed

import enum
from enum import Enum
from typing import Optional

from tqdm import tqdm

from core.console import colored_print
from core.html_requester import get_page_content, post_page_content


# 标头
get_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
}
post_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
}


def get_html(url: str, params: dict = None, headers: dict = None, max_retry_times=3) -> Optional[Response]:
    """
    获取网页内容
    对 IEEE 无效，IEEE 使用的是 ajax 慢加载方式防止爬虫爬取页面，直接访问链接不能直接得到所有想要的内容
    Args:
        url: 网页地址
        params: GET 请求参数，会显示在 URL 后面
        headers: 请求头

    Returns:
        str: 网页内容, 若请求失败则返回 None
    """
    if headers is None:
        headers = get_headers
    return get_page_content(url, params=params, headers=headers, max_retry_times=max_retry_times, return_type='default')


def post_html(url: str, data: dict, headers: dict=None, max_retry_times=0) -> Optional[Response]:
    """
    发送 POST 请求获取网页内容
    Args:
        url: 网页地址
        data: POST 请求参数
        headers: 请求头

    Returns:
        str: 网页内容, 若请求失败则返回 None
    """
    if headers is None:
        headers = post_headers
    return post_page_content(url, data=data, headers=headers, max_retry_times=max_retry_times, return_type='default')


# 期刊会议简称全称对应表
# noinspection SpellCheckingInspection
conference_short_name_dict = {
    "ICCV"      : {'CCF': "A", 'full_name': "International Conference on Computer Vision"},
    "CVPR"      : {'CCF': "A", 'full_name': "IEEE Conference on Computer Vision and Pattern Recognition"},
    "NeurIPS"   : {'CCF': "A", 'full_name': "Advances in Neural Information Processing Systems"},
    "ICML"      : {'CCF': "A", 'full_name': "International Conference on Machine Learning"},
    "MM"        : {'CCF': "A", 'full_name': "ACM Multimedia Conference"},
    "AAAI"      : {'CCF': "A", 'full_name': "AAAI Conference on Artificial Intelligence"},
    "IJCAI"     : {'CCF': "A", 'full_name': "International Joint Conference on Artificial Intelligence"},
    "VR"        : {'CCF': "A", 'full_name': "Virtual Reality"},

    "ECCV"      : {'CCF': "B", 'full_name': "European Conference on Computer Vision"},
    "ICME"      : {'CCF': "B", 'full_name': "International Conference on Multimedia & Expo"},
    "ICASSP"    : {'CCF': "B", 'full_name': "International Conference on Acoustics, Speech and Signal Processing"},

    "BMVC"      : {'CCF': "C", 'full_name': "British Machine Vision Conference"},
    "ACCV"      : {'CCF': "C", 'full_name': "Asian Conference on Computer Vision"},
    "ICIP"      : {'CCF': "C", 'full_name': "International Conference on Image Processing"},
    "ICPR"      : {'CCF': "C", 'full_name': "International Conference on Pattern Recognition"},

    "WACV"      : {'CCF': "?", 'full_name': "Winter Conference on Applications of Computer Vision"},
    "ICLR"      : {'CCF': "?", 'full_name': "International Conference on Learning Representations"},
    "SIGGRAPH"  : {'CCF': "?", 'full_name': "ACM SIGGRAPH"},
    "SA"        : {'CCF': "?", 'full_name': "ACM SIGGRAPH Asia"},
}

# noinspection SpellCheckingInspection
journal_short_name_dict = {
    "TIP"   : {'CCF': "A", 'full_name': "IEEE Transactions on Image Processing"},
    "TPAMI" : {'CCF': "A", 'full_name': "IEEE Transactions on Pattern Analysis and Machine Intelligence"},
    "IJCV"  : {'CCF': "A", 'full_name': "International Journal of Computer Vision"},
    "TOG"   : {'CCF': "A", 'full_name': "ACM Transactions on Graphics"},
    "TIFS"  : {'CCF': "A", 'full_name': "IEEE Transactions on Information Forensics and Security"},

    "TMM"   : {'CCF': "B", 'full_name': "IEEE Transactions on Multimedia"},
    "TCSVT" : {'CCF': "B", 'full_name': "IEEE Transactions on Circuits and Systems for Video Technology"},
    "TGRS"  : {'CCF': "B", 'full_name': "IEEE Transactions on Geoscience and Remote Sensing"},
    "PR"    : {'CCF': "B", 'full_name': "Pattern Recognition"},
    "TITS"  : {'CCF': "B", 'full_name': "IEEE Transactions on Intelligent Transportation Systems"},
    "TOC"   : {'CCF': "B", 'full_name': "IEEE Transactions on Computers"},
    "TNNLS" : {'CCF': "B", 'full_name': "IEEE Transactions on Neural Networks and Learning Systems"},
    "TOMM"  : {'CCF': "B", 'full_name': "ACM Transactions on Multimedia Computing, Communications, and Applications"},
    "CVIU"  : {'CCF': "B", 'full_name': "Computer Vision and Image Understanding"},
}


class Mode(Enum):
    AND = enum.auto()
    OR = enum.auto()


def print_(*args, **kwargs):
    try:
        tqdm.write(*args, **kwargs)
    except Exception as e:
        print(*args, **kwargs)


def normalize_link(link: str) -> str:
    """
    将链接规范化，去除前缀 '/'
    比如：/1905.12596.pdf -> 1905.12596.pdf
    Args:
        link: 链接

    Returns:
        str: 规范化后的链接
    """
    if link.startswith('/'):
        link = link[1:]
    return link


def remove_quotes(text: str) -> str:
    """
    移除文本中开头和结尾的引号
    Args:
        text: 文本

    Returns:
        str: 移除引号后的文本
    """
    text = text.strip()
    any_start_quote = text.startswith('"') or text.startswith("'")
    any_end_quote = text.endswith('"') or text.endswith("'")
    if any_start_quote and any_end_quote:
        text = text[1:-1]
    elif any_start_quote:
        text = text[1:]
    elif any_end_quote:
        text = text[:-1]
    return text


def match_paper(keywords: list[str], paper: dict, mode: Mode = Mode.OR):
    """
    根据关键词匹配论文

    Args:
        keywords: 关键词列表
        paper: 论文信息字典
        mode: 匹配模式，OR 或 AND

    Returns:
        dict: 匹配到的论文信息字典，若没有匹配到则返回 None
    """
    if mode == Mode.OR:
        for keyword in keywords:
            if 'title' in paper and (keyword.lower() in paper['title'].lower()):
                return paper
            if 'abstract' in paper and (keyword.lower() in paper['abstract'].lower()):
                return paper
    elif mode == Mode.AND:
        for keyword in keywords:
            if 'title' in paper and (keyword.lower() not in paper['title'].lower()):
                return None
            if 'abstract' in paper and (keyword.lower() not in paper['abstract'].lower()):
                return None
        return paper

    return None


def match_text(keywords: list[str], text: str, mode: Mode = Mode.OR):
    """
    根据关键词匹配论文

    Args:
        keywords: 关键词列表
        paper: 论文信息字典
        mode: 匹配模式，OR 或 AND

    Returns:
        dict: 匹配到的论文信息字典，若没有匹配到则返回 None
    """
    if mode == Mode.OR:
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return True
    elif mode == Mode.AND:
        for keyword in keywords:
            if keyword.lower() not in text.lower():
                return False
        return True

    return False