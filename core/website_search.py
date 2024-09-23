from abc import ABC, abstractmethod

import re
from bs4 import BeautifulSoup

from core.console import colored_print
from core.html_requester import get_page_content
from core.reference import Reference


search_engine = "cn.bing.com"
action = "search"
search_param_name = "q"

start_page = 5
max_num_pages = 20


def assert_kw(key, **kwargs):
    value = kwargs.get(key)
    if value is None:
        raise ValueError(f"{key} is not in kwargs")
    return value


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
    global start_page
    _start_page = start_page
    url_search = search_engine_url

    # 获取网页的检索内容 html，并提取检索结果中与论文网站相关的链接
    urls_result = []
    while True:
        page_content = get_page_content(url_search)

        urls_result += re.findall(search_url_regex, page_content)  # 正则表达式匹配 ieee 链接
        if _start_page >= max_num_pages:
            break
        else:
            print(f"\r正在寻找有关 {search_method} 的链接，当前页码 {_start_page}~{_start_page+9}...", end="")
            url_search = search_engine_url + f"&first={_start_page}"  # 翻页
            _start_page += 10

    # 判断是否有搜索结果
    urls_result = list(set(urls_result))  # 去重
    if len(urls_result) > 0:
        print(f"\r以关键词 {query} 搜索出的结果如下：\n{urls_result}")
    else:
        print(f"\r以关键词 {query} 搜索，超过 {max_num_pages} 页未找到 {search_method} 链接，退出...")

    return urls_result


class WebsiteSearch(ABC):
    def __init__(self, search_engine_url: str, query: str, **kwargs):
        self.search_engine_url = search_engine_url
        self.query = query
        self.kwargs = kwargs

        self.search_type = None     # 论文网站类型
        self.url_regex = None       # 网站链接的正则表达式匹配 regex

    def search_urls(self):
        urls = search_url(
            self.search_engine_url, self.query,
            search_url_regex=self.url_regex,
            search_method=self.search_type
        )
        return urls

    @staticmethod
    def filter_urls(urls, titles, query):
        """
        筛选 query 和标题一致的 url，由于 query 时标题的匹配对象，故不需再返回 url 对应的标题
        """
        filtered_urls = []
        for url, title in zip(urls, titles):
            if query.lower() == title.lower():
                filtered_urls.append(url)

        if len(filtered_urls) == 0:
            colored_print(f"从 {len(urls)} 个链接中未找到与关键词 {query} 完全匹配的链接", "red")
        return filtered_urls

    @staticmethod
    @abstractmethod
    def search_title(**kwargs) -> str:
        pass

    def search_and_filter_urls_by_query(self):
        urls = self.search_urls()
        titles = [
            self.search_title(url=url)
            for url in urls
        ]
        filtered_urls = self.filter_urls(urls, titles, self.query)
        return filtered_urls

    @staticmethod
    @abstractmethod
    def search_reference(url) -> Reference:
        pass


class ArxivSearch(WebsiteSearch):
    def __init__(self, search_engine_url: str, query: str, **kwargs):
        super().__init__(search_engine_url, query, **kwargs)
        self.search_type = "arXiv"
        self.url_regex = r"\"(https://arxiv\.org/abs/\d+?\.\d+?)\""

    @staticmethod
    def search_title(**kwargs):
        """
        提取页面中文章的标题
        """
        url = kwargs.get("url")
        if url is not None:
            html_content = get_page_content(url)
            soup = BeautifulSoup(html_content, "html.parser")
        else:
            soup = assert_kw("soup", **kwargs)

        title_html = soup.find("title").text.strip()
        title = re.findall(r"\[\d+?\.\d+?] (.*)", title_html)[0]

        return title

    @staticmethod
    def search_authors(**kwargs):
        """
        提取页面中文章的作者信息
        """
        soup = assert_kw("soup", **kwargs)

        authors_html = soup.find("div", class_="authors")
        authors = authors_html.findAll("a")
        authors = [author.text.strip() for author in authors]

        return authors

    @staticmethod
    def search_reference(url):
        # 获取网页 html 内容
        html_content = get_page_content(url)
        soup = BeautifulSoup(html_content, "html.parser")

        title = ArxivSearch.search_title(soup=soup)
        authors = ArxivSearch.search_authors(soup=soup)

        return Reference(
            title=title,
            authors=authors,
        )


class IEEESearch(WebsiteSearch):
    def __init__(self, search_engine_url: str, query: str, **kwargs):
        super().__init__(search_engine_url, query, **kwargs)
        self.search_type = "IEEE"
        self.url_regex = r"\"(https://ieeexplore\.ieee\.org/document/\d*)\""

    @staticmethod
    def search_title(**kwargs):
        """
        提取页面中文章的标题
        """
        url = kwargs.get("url")
        html_content = get_page_content(url) if url is not None else assert_kw("html_content", **kwargs)

        # 提取页面中文章的标题
        title = re.findall(r"<title>(.*?)(?: [|].*?)?</title>", html_content)[0]

        return title

    @staticmethod
    def search_authors(**kwargs):
        """
        提取页面中文章的作者信息
        """
        html_content = assert_kw("html_content", **kwargs)

        # 提取页面中整个作者信息
        authors_html = re.findall(r"\"authors\":\[\{.*?}]", html_content)[0]
        # 提取每个作者名称
        authors = re.findall(r"\"name\":\"(.*?)\"", authors_html)

        return authors

    @staticmethod
    def search_reference(url):
        # 获取网页 html 内容
        html_content = get_page_content(url)

        title = IEEESearch.search_title(html_content=html_content)
        authors = IEEESearch.search_authors(html_content=html_content)

        return Reference(
            title=title,
            authors=authors,
        )


class ACMSearch(WebsiteSearch):
    def __init__(self, search_engine_url: str, query: str, **kwargs):
        super().__init__(search_engine_url, query, **kwargs)
        self.search_type = "ACM"
        self.url_regex = r"\"(https://dl\.acm\.org/doi/\d+\.\d+/\d+\.\d+)\""

    @staticmethod
    def search_title(**kwargs):
        """
        提取页面中文章的标题
        """
        url = kwargs.get("url")
        html_content = get_page_content(url) if url is not None else assert_kw("html_content", **kwargs)

        # 提取页面中文章的标题
        title = re.findall(r"<title>(.*?)(?: [|].*?)?</title>", html_content)[0]

        return title

    @staticmethod
    def search_authors(**kwargs):
        """
        提取页面中文章的作者信息
        """
        soup = assert_kw("soup", **kwargs)

        authors_html = soup.find("span", class_="authors")
        authors_family_name = authors_html.findAll("span", property="familyName")
        authors_given_name = authors_html.findAll("span", property="givenName")
        authors = [
            f"{author_family_name.text} {author_given_name.text}"
            for author_family_name, author_given_name in zip(authors_family_name, authors_given_name)
        ]
        authors = list(set(authors))    # 去重

        return authors

    @staticmethod
    def search_reference(url):
        # 获取网页 html 内容
        html_content = get_page_content(url)
        soup = BeautifulSoup(html_content, "html.parser")

        title = ACMSearch.search_title(html_content=html_content)
        authors = ACMSearch.search_authors(soup=soup)

        return Reference(
            title=title,
            authors=authors,
        )


class SemanticsScholarSearch(WebsiteSearch):
    def __init__(self, search_engine_url: str, query: str, **kwargs):
        super().__init__(search_engine_url, query, **kwargs)
        self.search_type = "Semantics Scholar"
        self.url_regex = r"\"(https://www\.semanticscholar\.org/paper/.+?)\""

    @staticmethod
    def search_title(**kwargs):
        """
        提取页面中文章的标题
        """
        if "soup" not in kwargs:
            raise ValueError("soup is not in kwargs")
        soup = kwargs["soup"]

        # 提取页面中文章的标题
        title_html = soup.find("title").text.strip()
        title = re.findall(r"(?:\[[^]]*?] )?(.*?)(?: [|].*?)?", title_html)[0]

        return title

    @staticmethod
    def search_authors(**kwargs):
        """
        提取页面中文章的作者信息
        """
        if "soup" not in kwargs:
            raise ValueError("soup is not in kwargs")
        soup = kwargs["soup"]

        authors_html = soup.findAll("meta", name="citation author")
        authors = [author.get("content") for author in authors_html]
        authors = list(set(authors))    # 去重

        return authors

    @staticmethod
    def search_reference(url):
        # 获取网页 html 内容
        html_content = get_page_content(url)
        soup = BeautifulSoup(html_content, "html.parser")

        title = SemanticsScholarSearch.search_title(soup=soup)
        authors = SemanticsScholarSearch.search_authors(soup=soup)

        return Reference(
            title=title,
            authors=authors,
        )


search_method_map = {
    "arXiv": ArxivSearch,
    "IEEE": IEEESearch,
    "ACM": ACMSearch,
    "Semantics Scholar": SemanticsScholarSearch,
}


def search_urls_by_title(
        titles: [str, list[str]],
        search_types: (tuple, list,) = ("arXiv", "IEEE", "ACM")
):
    """
    通过论文标题（或关键词）搜索论文网站链接
    Args:
        titles: 论文标题（或关键词）列表
        search_types: 搜索方式，可以选择 arXiv, IEEE, ACM 等

    Returns:
        dict: 搜索结果字典，键为搜索方式，值为搜索结果列表
    """
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
            search_method: WebsiteSearch = search_method_map[search_type](search_engine_url, title)
            method_urls_map[search_type] = search_method.search_urls()

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
        search_types: 搜索方式，可以选择 arXiv, IEEE, ACM 等
        is_abbreviate_name: 是否缩写作者姓名
    """
    if not isinstance(search_types, tuple) and not isinstance(search_types, list):
        search_types = (search_types,)
    search_types = list(search_types)
    if isinstance(titles, str):
        titles = [titles]

    # 查询论文作者信息，并缩写
    for title in titles:
        # 关键词网址 url
        cur_query = title.replace(" ", "+")
        search_engine_url = f"https://{search_engine}/{action}?{search_param_name}={cur_query}"   # 翻页 &first=6&FORM=PERE
        print(f"\n查询网页链接：{search_engine_url}")

        # 在 arxiv 中找到作者信息
        any_complete_match_result = False
        for search_type in search_types:
            search_method: WebsiteSearch = search_method_map[search_type](search_engine_url, title)
            urls = search_method.search_and_filter_urls_by_query()
            if len(urls) == 0:
                continue

            reference = search_method.search_reference(urls[0])
            if is_abbreviate_name:
                reference.abbreviate_authors()

            if reference.authors is not None:
                break

        if not any_complete_match_result:
            colored_print("无法找到完全匹配关键词的文章作者信息！", "red")


def search_reference(
        titles: [str, list[str]],
        search_types: (tuple, list,) = ("arXiv", "IEEE", "ACM"),
):
    """
    通过论文标题（或关键词）搜索论文引用信息
    Args:
        titles: 论文标题（或关键词）列表
        search_types: 搜索方式，可以选择 arXiv, IEEE, ACM 等
    """
    if not isinstance(search_types, tuple) and not isinstance(search_types, list):
        search_types = (search_types,)
    search_types = list(search_types)
    if isinstance(titles, str):
        titles = [titles]

    # 查询论文作者信息，并缩写
    for title in titles:
        # 关键词网址 url
        cur_query = title.replace(" ", "+")
        search_engine_url = f"https://{search_engine}/{action}?{search_param_name}={cur_query}"   # 翻页 &first=6&FORM=PERE
        print(f"\n查询网页链接：{search_engine_url}")

        # 在 arxiv 中找到作者信息
        references = []
        for search_type in search_types:
            search_method: WebsiteSearch = search_method_map[search_type](search_engine_url, title)
            urls = search_method.search_and_filter_urls_by_query()
            reference = search_method.search_reference(urls[0])
            references.append(reference)

        return references


if __name__ == '__main__':
    max_num_pages = 20
    _query = "Attention is all you need"

    search_authors_by_title(_query, search_types=["arXiv", "IEEE"])

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
