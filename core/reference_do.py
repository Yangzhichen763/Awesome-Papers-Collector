import os.path
from time import sleep

import requests
import re

from console import colored_print


search_engine = "cn.bing.com"
action = "search"
search_param_name = "q"

num_pages = 5
max_num_pages = 20

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}   # Cookie 很重要，相当于个人喜好，大数据（一个经常看论文的人更容易搜到论文）



def get_page_content(url: str):
    """
    获取网页的 html 内容
    """
    while True:
        try:
            response = requests.get(url=url, headers=headers)   # 通过 url 获取网页相应
            response.raise_for_status()                         # 检查相应状态码
            content = response.text                             # 获取网页内容
            return content
        except requests.exceptions.RequestException as e:
            print(f"获取网页内容失败：{e}，\n重试中...")
            sleep(0.1)                                          # 重试间隔


# 缩写作者姓名
def abbreviate_name(name: str):
    """
    缩写作者姓名
    """
    name_list = name.split()
    name_list = [name_list[-1], *name_list[:-1]]
    for i in range(len(name_list))[1:]:
        name_list[i] = name_list[i][0]
    return " ".join(name_list)


# 包括一下的 search 都是检索论文作者用的，有其他用途可以自行更改
def search(url: str, query: str,
           regex_search_result: str, regex_title: str, regex_authors_html: str, regex_author: str,
           search_method: str,
           is_abbreviate_name=True):
    """

    Args:
        url: 网页的检索地址
        query: 要搜索的关键词
        regex_search_result: 对搜索结果进行匹配的正则表达式
        regex_title: 对文章标题进行匹配的正则表达式
        regex_authors_html: 对作者信息 html 进行匹配的正则表达式
        regex_author: 对作者名称进行匹配的正则表达式
        search_method: 搜索方法，可以选择 arxiv, ieee 等
    """
    global num_pages
    url_search = url

    # 获取网页的检索内容 html，并提取检索结果中与 arXiv 相关的链接
    urls_result = []
    while True:
        page_content = get_page_content(url_search)

        urls_result += re.findall(regex_search_result, page_content)  # 正则表达式匹配 ieee 链接
        if num_pages >= max_num_pages:
            break
        else:
            print(f"\r正在寻找有关 {search_method} 的链接，当前页码 {num_pages}~{num_pages+9}...", end="")
            url_search = url + f"&first={num_pages}"  # 翻页
            num_pages += 10

    urls_result = list(set(urls_result))  # 去重
    if len(urls_result) > 0:
        print(f"\r以关键词 {query} 搜索出的结果如下：\n{urls_result}")
    else:
        print(f"\r以关键词 {query} 搜索，超过 {max_num_pages} 页未找到 {search_method} 链接，退出...")

    if len(urls_result) == 0:
        return False

    # 访问 ieee 链接，提取作者信息
    for url_result in urls_result:
        # 获取网页 html 内容
        page_content = get_page_content(url_result)
        # print(page_content)

        # 提取也页面中文章的标题
        title = re.findall(regex_title, page_content)[0]

        # 提取页面中整个作者信息
        authors_html = re.findall(regex_authors_html, page_content)[0]
        # 提取每个作者名称
        authors = re.findall(regex_author, authors_html)
        print(f"在 {search_method} 链接 {url_result} 中，文章标题为：{title}，提取出的作者信息如下：\n{authors}")

        # 缩写作者姓名
        if is_abbreviate_name:
            abb_authors = [abbreviate_name(name) for name in authors]
            if abb_authors is not None:
                author_str = ""
                if len(abb_authors) == 1:
                    author_str = abb_authors[0]
                elif len(abb_authors) >= 2:
                    author_str = ", ".join(abb_authors[:-1]) + " and " + abb_authors[-1]
                print(f"缩写后的作者信息如下：\n{author_str}")

        if query.lower() in title.lower():
            colored_print(f"文章标题中包含关键词 {query}，符合搜索条件", "green")

    return True


def arxiv_search(url: str, query: str, **kwargs):
    return search(
        url, query,
        regex_search_result=r"https://arxiv\.org/abs/\d{4}\.\d{4,5}",
        regex_title=r"<title>(.*?)</title>",
        regex_authors_html=r"<div class=\"authors\">.*?</div>",
        regex_author=r"<a href=\".*?\">(.*?)</a>",
        search_method="arxiv",
        **kwargs
    )


def ieee_search(url: str, query: str, **kwargs):
    return search(
        url, query,
        regex_search_result=r"https://ieeexplore\.ieee\.org/document/\d*",
        regex_title=r"<title>(.*?)</title>",
        regex_authors_html=r"\"authors\":\[\{.*?\}\]",
        regex_author=r"\"name\":\"(.*?)\"",
        search_method="ieee",
        **kwargs
    )


# TODO: 增加其他论文检索网页的搜索功能 acm
def acm_search(url: str, query: str, **kwargs):
    return search(
        url, query,
        regex_search_result=r"https://dl.acm.org/doi/abs/\d+?.\d+?/\d+?.\d+?",
        regex_title=r"<title>(.*?)</title>",
        regex_authors_html=r"<div class=\"authors\">.*?</div>",
        regex_author=r"<a href=\".*?\">(.*?)</a>",
        search_method="acm",
        **kwargs
    )


# TODO: 增加其他论文检索网页的搜索功能 semantics_scholar
# noinspection SpellCheckingInspection
def semanticsscholar_search(url: str, query: str, **kwargs):
    return search(
        url, query,
        regex_search_result=r"\"(https://www.semanticscholar.org/paper/.+?)\"",
        regex_title=r"<title>(.*?)</title>",
        regex_authors_html=r"<div class=\"authors\">.*?</div>",
        regex_author=r"<a href=\".*?\">(.*?)</a>",
        search_method="semantics scholar",
        **kwargs
    )


def search_authors_by_title(
    titles: [str, list[str]],
    search_methods: (tuple[str], list[str]) = (arxiv_search, ieee_search),
    is_abbreviate_name=True
):
    global num_pages
    search_methods = list(search_methods)
    if isinstance(titles, str):
        titles = [titles]

    # 读取 Cookies.txt 文件，设置 headers
    if os.path.exists("Cookies.txt"):
        with open("Cookies.txt", "r") as f:
            cookies = f.read()
            headers["Cookie"] = cookies

    # 查询论文作者信息，并缩写
    for title in titles:
        # 关键词网址 url
        cur_query = title.replace(" ", "+")
        url_origin = f"https://{search_engine}/{action}?{search_param_name}={cur_query}"   # 翻页 &first=6&FORM=PERE
        print(f"\n查询网页链接：{url_origin}")

        # 在 arxiv 中找到作者信息
        any_result = False
        for search_method in search_methods:
            num_pages = 5

            any_result |= search_method(url_origin, title, is_abbreviate_name=is_abbreviate_name)

        if not any_result:
            colored_print("无法找到作者信息！", "red")


if __name__ == '__main__':
    # 所有要搜索的关键词
    titles = [
        "Improving single-image defocus deblurring: How dual-pixel images help through multi-task learning",
        "Defocus deblurring using dual-pixel data",
        "End-to-end object detection with transformers",
        "Transformer tracking",
        "Rethinking coarse-to-fine approach in single image deblurring",
        "Focal network for image restoration",
        "Deep defocus map estimation using domain adaptation",
        "Iterative filter adaptive network for single image defocus deblurring",
        "Neumann network with recursive kernels for single image defocus deblurring",
        "Learning to deblur using light field generated and real defocus images",
        "Discriminative blur detection features",
        "Just noticeable defocus blur detection and estimation",
        "Single image defocus deblurring using kernel-sharing parallel atrous convolutions",
        "Segmenter: Transformer for semantic segmentation",
        "Pyramid vision transformer: A versatile backbone for dense prediction without convolutions",
        "Restormer: Efficient Transformer for high-resolution image restoration",
        "Efficient fusion of depth information for defocus deblurring",
        "Learnable blur kernel for single-image defocus deblurring in the wild",
        "An image is worth 16x16 words: Transformers for image recognition at scale",
        "Non-parametric blur map regression for depth of field extension",
        "Blind deconvolution by means of the Richardson–Lucy algorithm",
        "Recurrent relational memory network for unsupervised image captioning",
        "Edge-based defocus blur estimation with adaptive scale selection",
        "Fast image deconvolution using hyper-Laplacian priors",
        "Image deblurring by exploring in-depth properties of Transformer",
        "A motion deblur method based on multi-scale high frequency residual image learning",
        "Defocus image deblurring network with defocus map estimation as auxiliary task",
        "Gaussian kernel mixture network for single image defocus deblurring",
        "Revisiting image deblurring with an efficient ConvNet",
        "AIFNet: All-in-focus image restoration network using a light field-based dataset",
        "DDABNet: A dense Do-conv residual network with multisupervision and mixed attention for image deblurring",
        "Attention is all you need"
    ]

    search_authors_by_title(
        titles,
        search_methods=[arxiv_search, ieee_search],
        is_abbreviate_name=True
    )
