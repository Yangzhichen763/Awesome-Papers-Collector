import os.path
from typing import Callable, Optional

import re
from bs4 import BeautifulSoup

from core.console import colored_print
from core.html_requester import get_page_content, request_headers as headers


search_engine = "cn.bing.com"
action = "search"
search_param_name = "q"

num_pages = 5
max_num_pages = 20


class ReferenceData:
    def __init__(self, *,
                 title: str,
                 authors: list[str],
                 abstract: Optional[str] = None,
                 url: Optional[str] = None):
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.url = url


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


def search_url(
        search_engine_url: str,
        query: str,
        search_url_regex: str,
        search_method: str,
):
    """
    通过给定的网页检索地址，提取检索结果中与论文网站相关的链接
    Args:
        search_engine_url: 网页的检索地址
        query: 要搜索的关键词
        search_url_regex: 对搜索结果进行匹配的正则表达式
        search_method: 搜索方法，可以选择 arxiv, ieee, acm 等

    Returns:
        list[str]: 与论文网站相关的链接
    """
    global num_pages
    url_search = search_engine_url

    # 获取网页的检索内容 html，并提取检索结果中与论文网站相关的链接
    urls_result = []
    while True:
        page_content = get_page_content(url_search)

        urls_result += re.findall(search_url_regex, page_content)  # 正则表达式匹配 ieee 链接
        if num_pages >= max_num_pages:
            break
        else:
            print(f"\r正在寻找有关 {search_method} 的链接，当前页码 {num_pages}~{num_pages+9}...", end="")
            url_search = search_engine_url + f"&first={num_pages}"  # 翻页
            num_pages += 10

    # 判断是否有搜索结果
    urls_result = list(set(urls_result))  # 去重
    if len(urls_result) > 0:
        print(f"\r以关键词 {query} 搜索出的结果如下：\n{urls_result}")
    else:
        print(f"\r以关键词 {query} 搜索，超过 {max_num_pages} 页未找到 {search_method} 链接，退出...")

    return urls_result


# 包括一下的 search 都是检索论文作者用的，有其他用途可以自行更改
def search_authors(
        urls: [list[str], str],
        query: str,
        html_solver: Callable[[str], ReferenceData],
        is_abbreviate_name=True
):
    """
    通过论文网站链接检索论文作者信息
    Args:
        urls: 论文网站链接列表
        query: 要搜索的关键词
        html_solver: 对搜索结果进行解析的函数
        is_abbreviate_name: 是否缩写作者姓名

    Returns:
        bool: 是否找到标题与关键词完全匹配的论文
    """
    if isinstance(urls, str):
        urls = [urls]

    # 访问论文网站链接，提取作者信息
    for url in urls:
        # 获取网页 html 内容
        page_content = get_page_content(url)

        # 提取文章信息
        reference_data = html_solver(page_content)
        reference_data.url = url
        title = reference_data.title
        authors = reference_data.authors
        print(f"在链接 {url} 中，文章标题为：{title}，提取出的作者信息如下：\n{authors}")

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

        if query.lower() == title.lower():
            colored_print(f"文章标题与关键词 {query} 完全匹配！符合搜索条件", "green")
            return True
        elif query.lower() in title.lower():
            colored_print(f"文章标题中包含关键词 {query}，符合搜索条件", "cyan")

    return False


urls_regex = {
    'arXiv': r"\"(https://arxiv\.org/abs/\d+?\.\d+?)\"",
    'IEEE': r"\"(https://ieeexplore\.ieee\.org/document/\d*)\"",
    'ACM': r"\"(https://dl\.acm\.org/doi/\d+\.\d+/\d+\.\d+)\"",  # .../doi/abs/...也可以
    'Semantics Scholar': r"\"(https://www\.semanticscholar\.org/paper/.+?)\"",
}


def arxiv_search(search_engine_url: str, query: str, **kwargs):
    def html_solver(html_content):
        # 提取页面中文章的标题
        title = re.findall(r"<title>\[\d+?\.\d+?] (.*?)</title>", html_content)[0]

        # 提取页面中整个作者信息
        authors_html = re.findall(r"<div class=\"authors\">.*?</div>", html_content)[0]
        # 提取每个作者名称
        authors = re.findall(r"<a href=\".*?\">(.*?)</a>", authors_html)

        return ReferenceData(title=title, authors=authors)

    urls = search_url(
        search_engine_url, query,
        search_url_regex=urls_regex['arXiv'],
        search_method="arXiv"
    )
    return search_authors(
        urls, query,
        html_solver=html_solver,
        **kwargs
    )


def ieee_search(search_engine_url: str, query: str, **kwargs):
    def html_solver(html_content):
        # 提取页面中文章的标题
        title = re.findall(r"<title>(.*?)(?: [|].*?)?</title>", html_content)[0]

        # 提取页面中整个作者信息
        authors_html = re.findall(r"\"authors\":\[\{.*?}]", html_content)[0]
        # 提取每个作者名称
        authors = re.findall(r"\"name\":\"(.*?)\"", authors_html)

        return ReferenceData(title=title, authors=authors)

    urls = search_url(
        search_engine_url, query,
        search_url_regex=urls_regex['IEEE'],
        search_method="IEEE"
    )
    return search_authors(
        urls, query,
        html_solver=html_solver,
        **kwargs
    )


def acm_search(search_engine_url: str, query: str, **kwargs):
    def html_solver(html_content):
        # 提取也页面中文章的标题
        soup = BeautifulSoup(html_content, "html.parser")

        # 提取页面中文章的标题
        titles = soup.findAll("title")
        print(titles[0].text)
        title = re.findall(r"(.*?)(?: [|].*)+?", titles[0].text)[0]

        # 提取页面中所有作者名字
        authors_family_name = soup.findAll("span", property="familyName")
        authors_given_name = soup.findAll("span", property="givenName")
        authors = [
            f"{author_family_name.text} {author_given_name.text}"
            for author_family_name, author_given_name in zip(authors_family_name, authors_given_name)
        ]
        authors = list(set(authors))    # 去重

        return ReferenceData(title=title, authors=authors)

    urls = search_url(
        search_engine_url, query,
        search_url_regex=urls_regex['ACM'],
        search_method="ACM",
    )
    return search_authors(
        urls, query,
        html_solver=html_solver,
        **kwargs
    )


# TODO: semantics_scholar 检索速度太慢
# noinspection SpellCheckingInspection
def semanticsscholar_search(search_engine_url: str, query: str, **kwargs):
    def html_solver(html_content):
        # 提取也页面中文章的标题
        soup = BeautifulSoup(html_content, "html.parser")

        # 提取页面中文章的标题
        titles = soup.findAll("title")
        print(titles)
        title = re.findall(r"(?:\[[^]]*?] )?(.*?)(?: [|].*?)?", titles[0].text)[0]

        # 提取页面中所有作者名字
        authors = soup.findAll("meta", name="citation author")
        print(authors)
        authors = list(set(authors))    # 去重

        return ReferenceData(title=title, authors=authors)

    urls = search_url(
        search_engine_url, query,
        search_url_regex=urls_regex['Semantics Scholar'],
        search_method="Semantics Scholar"
    )
    return search_authors(
        urls, query,
        html_solver=html_solver,
        **kwargs
    )


search_method_map = {
    "arXiv": arxiv_search,
    "IEEE": ieee_search,
    "ACM": acm_search,
    "Semantics Scholar": semanticsscholar_search,
}


def search_urls_by_title(
        titles: [str, list[str]],
        search_types: (tuple, list,) = ("arXiv", "IEEE", "ACM")
):
    """
    通过论文标题（或关键词）搜索论文网站链接
    Args:
        titles: 论文标题（或关键词）列表
        search_types: 搜索方式，可以选择 arxiv, ieee, acm 等

    Returns:
        dict: 搜索结果字典，键为搜索方式，值为搜索结果列表
    """
    global num_pages
    if not isinstance(search_types, tuple) and not isinstance(search_types, list):
        search_types = (search_types,)
    search_types = list(search_types)
    if isinstance(titles, str):
        titles = [titles]

    # 查询论文作者信息，并缩写
    method_urls_map = {}
    for title in titles:
        # 关键词网址 url
        cur_query = title.replace(" ", "+")
        search_engine_url = f"https://{search_engine}/{action}?{search_param_name}={cur_query}"   # 翻页 &first=6&FORM=PERE
        print(f"\n查询网页链接：{search_engine_url}")

        for search_type in search_types:
            num_pages = 5

            method_urls_map[search_type] = search_url(
                search_engine_url, cur_query,
                search_url_regex=urls_regex[search_type],
                search_method=search_type,
            )

    return method_urls_map


def search_authors_by_title(
        titles: [str, list[str]],
        search_types: (tuple, list,) = ("arXiv", "IEEE", "ACM"),
        is_abbreviate_name=True
):
    """
    通过论文标题（或关键词）搜索论文作者信息
    Args:
        titles: 论文标题（或关键词）列表
        search_types: 搜索方式，可以选择 arxiv_search, ieee_search, acm_search 等
        is_abbreviate_name: 是否缩写作者姓名
    """
    global num_pages
    if not isinstance(search_types, tuple) and not isinstance(search_types, list):
        search_types = (search_types,)
    search_types = list(search_types)
    if isinstance(titles, str):
        titles = [titles]

    # 查询论文作者信息，并缩写
    for title in titles:
        # 关键词网址 url
        cur_query = title.replace(" ", "+")
        url_origin = f"https://{search_engine}/{action}?{search_param_name}={cur_query}"   # 翻页 &first=6&FORM=PERE
        print(f"\n查询网页链接：{url_origin}")

        # 在 arxiv 中找到作者信息
        any_complete_match_result = False
        for search_type in search_types:
            search_method = search_method_map[search_type]
            num_pages = 5

            any_complete_match_result |= search_method(url_origin, title, is_abbreviate_name=is_abbreviate_name)
            if any_complete_match_result:
                break

        if not any_complete_match_result:
            colored_print("无法找到完全匹配关键词的文章作者信息！", "red")


if __name__ == '__main__':
    max_num_pages = 20
    _query = "Attention is all you need"

    search_authors_by_title(_query, "arXiv")

    # 所有要搜索的关键词
    # queries = [
    #     "Improving single-image defocus deblurring: How dual-pixel images help through multi-task learning",
    #     "Defocus deblurring using dual-pixel data",
    #     "End-to-end object detection with transformers",
    #     "Transformer tracking",
    #     "Rethinking coarse-to-fine approach in single image deblurring",
    #     "Focal network for image restoration",
    #     "Deep defocus map estimation using domain adaptation",
    #     "Iterative filter adaptive network for single image defocus deblurring",
    #     "Neumann network with recursive kernels for single image defocus deblurring",
    #     "Learning to deblur using light field generated and real defocus images",
    #     "Discriminative blur detection features",
    #     "Just noticeable defocus blur detection and estimation",
    #     "Single image defocus deblurring using kernel-sharing parallel atrous convolutions",
    #     "Segmenter: Transformer for semantic segmentation",
    #     "Pyramid vision transformer: A versatile backbone for dense prediction without convolutions",
    #     "Restormer: Efficient Transformer for high-resolution image restoration",
    #     "Efficient fusion of depth information for defocus deblurring",
    #     "Learnable blur kernel for single-image defocus deblurring in the wild",
    #     "An image is worth 16x16 words: Transformers for image recognition at scale",
    #     "Non-parametric blur map regression for depth of field extension",
    #     "Blind deconvolution by means of the Richardson–Lucy algorithm",
    #     "Recurrent relational memory network for unsupervised image captioning",
    #     "Edge-based defocus blur estimation with adaptive scale selection",
    #     "Fast image deconvolution using hyper-Laplacian priors",
    #     "Image deblurring by exploring in-depth properties of Transformer",
    #     "A motion deblur method based on multi-scale high frequency residual image learning",
    #     "Defocus image deblurring network with defocus map estimation as auxiliary task",
    #     "Gaussian kernel mixture network for single image defocus deblurring",
    #     "Revisiting image deblurring with an efficient ConvNet",
    #     "AIFNet: All-in-focus image restoration network using a light field-based dataset",
    #     "DDABNet: A dense Do-conv residual network with multisupervision and mixed attention for image deblurring",
    #     "Attention is all you need"
    # ]
    #
    # search_authors_by_title(
    #     queries,
    #     search_methods=[arxiv_search, ieee_search],
    #     is_abbreviate_name=True
    # )
