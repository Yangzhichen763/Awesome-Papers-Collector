import re

from bs4 import BeautifulSoup

from core.html_requester import get_page_content
from core.paper import Overview, Figure
from core.paper_soup import FigureSoup


def parse_arxiv_html(url: str):
    """
    解析 arXiv 网页内容，返回一个 Overview

    Args:
        url: 网页地址

    Returns:
        论文的 Overview
    """
    # == 摘要内容 ==
    print("\r正在寻找并请求 arXiv 的 abstract 版内容...", end="")
    html_content = get_page_content(url)
    soup = BeautifulSoup(html_content, "html.parser")

    print("\r正在提取 arXiv 的 abstract 版内容...", end="")
    # 标题
    title_with_tag = soup.find("h1", class_="title mathjax").text.strip()
    title = title_with_tag.replace("Title:", "")
    # 分区
    subjects = soup.find("td", class_="tablecell subjects").text.strip()
    # 作者
    authors_with_tag = soup.find("div", class_="authors").text.strip()
    authors = authors_with_tag.replace("Authors:", "").split(", ")
    # 所有版本的发布日期
    date = soup.find("div", class_="submission-history").text.strip()
    dates = re.findall(r"\S+, \d+ \S+ \d{4} \d{2}:\d{2}:\d{2}", date)
    first_date = dates[0][5:-9]  # 第一次发布的日期
    # 摘要
    abstract_with_tag = soup.find("blockquote", class_="abstract mathjax").text.strip()
    abstract = abstract_with_tag.replace("Abstract:", "")
    # 项目链接（源代码）
    project_url_html = soup.find("a", class_="link-external link-https")

    md_classes = []
    # == html 内容 ==
    print("\r正在寻找并请求 arXiv 的 HTML 版内容...", end="")
    html_url = url.replace("abs", "html")   # 将 arXiv 的摘要链接转换为 HTML 链接
    html_content = get_page_content(html_url)
    if html_content is not None:
        print("\r将 HTML 内容转换为 BeautifulSoup 对象...", end="")
        html_soup = BeautifulSoup(html_content, "html.parser")

        # 项目链接（源代码）（如果 abstract 版没有提供的话）
        if project_url_html is None:
            print("\r正在寻找项目链接...", end="")
            project_url_html = html_soup.find("a", class_="ltx_ref ltx_url ltx_font_typewriter")

        # 图片
        print("\r正在提取图片链接和标题...", end="")
        figures = []
        figure_url_htmls: list[BeautifulSoup] = html_soup.findAll("figure", class_="ltx_figure")
        for figure_url_html in figure_url_htmls:
            # 避免重复处理子 html
            for figure_child_url_html in figure_url_html.findAll("figure", class_="ltx_figure"):
                figure_url_htmls.remove(figure_child_url_html)

            for image_html in figure_url_html.findAll("img"):
                image_url = f"{html_url}/{image_html['src']}"
                image_html["src"] = image_url
            figure_html = FigureSoup(figure_url_html)
            figures.append(figure_html)

        md_classes += figures

    print("\r完成 arXiv 网页内容的提取！")
    return Overview(
        arxiv_url=url,
        html_url=html_url if html_content is not None else None,
        project_url=project_url_html["href"] if project_url_html is not None else None,
        title=title,
        subjects=subjects,
        authors=authors,
        first_date=first_date,
        abstract=abstract,
        md_classes=md_classes,
    )


if __name__ == "__main__":
    _url = "https://arxiv.org/abs/1706.03762"
    overview = parse_arxiv_html(_url)
    overview.make()

