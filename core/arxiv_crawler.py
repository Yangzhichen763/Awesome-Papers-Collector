import re
from typing import Optional

from bs4 import BeautifulSoup

from core.html_requester import get_page_content
from core.paper import Overview


def remove_tags(content: str):
    """
    移除标签，例如将 Title: Attention Is All You Need 转换为 Attention Is All You Need
    """
    _content = re.sub(r"(.+):", "", content)
    return _content


def parse_arxiv_html(url: str):
    """
    解析 arXiv 网页内容，返回一个 Overview

    Args:
        url: 网页地址

    Returns:
        论文的 Overview
    """
    # == 摘要内容 ==
    print("\r正在寻找 arXiv 的 abstract 版内容...", end="")
    html_content = get_page_content(url)
    soup = BeautifulSoup(html_content, "html.parser")

    print("\r正在提取 arXiv 的 abstract 版内容...", end="")
    # 标题
    title_with_tag = soup.find("h1", class_="title mathjax").text.strip()
    title = remove_tags(title_with_tag)
    # 分区
    subjects = soup.find("td", class_="tablecell subjects").text.strip()
    # 作者
    authors_with_tag = soup.find("div", class_="authors").text.strip()
    authors = remove_tags(authors_with_tag).split(", ")
    # 所有版本的发布日期
    date = soup.find("div", class_="submission-history").text.strip()
    dates = re.findall(r"\S+, \d+ \S+ \d{4} \d{2}:\d{2}:\d{2}", date)
    first_date = dates[0][5:-9]  # 第一次发布的日期
    # 摘要
    abstract_with_tag = soup.find("blockquote", class_="abstract mathjax").text.strip()
    abstract = remove_tags(abstract_with_tag)
    # 项目链接（源代码）
    project_url_html = soup.find("a", class_="link-external link-https")
    if project_url_html is not None:
        project_url = project_url_html["href"]
    else:
        project_url = None

    # == html 内容 ==
    print("\r正在寻找 arXiv 的 HTML 版内容...", end="")
    html_url = url.replace("abs", "html")   # 将 arXiv 的摘要链接转换为 HTML 链接
    html_content = get_page_content(html_url)
    if html_content is not None:
        print("\r将 HTML 内容转换为 BeautifulSoup 对象...", end="")
        html_soup = BeautifulSoup(html_content, "html.parser")

        # 项目链接（源代码）
        if project_url is None:
            print("\r正在寻找项目链接...", end="")
            project_url = html_soup.find("a", class_="ltx_ref ltx_url ltx_font_typewriter")["href"]

    print("\r完成 arXiv 网页内容的提取！")
    return Overview(
        arxiv_url=url,
        project_url=project_url,
        title=title,
        subjects=subjects,
        authors=authors,
        first_date=first_date,
        abstract=abstract
    )


if __name__ == "__main__":
    _url = "https://arxiv.org/abs/1706.03762"
    overview = parse_arxiv_html(_url)
    overview.make()

