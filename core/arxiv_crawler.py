import re

from bs4 import BeautifulSoup

from core.html_requester import get_page_content
from paper import Overview


def remove_tags(content: str):
    """
    移除标签，例如将 Title: Attention Is All You Need 转换为 Attention Is All You Need
    """
    _content = re.sub(r"(.+):", "", content)
    return _content


def parse_arxiv_html(url: str, html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # 标题
    title_with_tag = soup.find("h1", class_="title mathjax").text.strip()
    title = remove_tags(title_with_tag)

    # 分类
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

    return Overview(
        url=url,
        title=title,
        subjects=subjects,
        authors=authors,
        first_date=first_date,
        abstract=abstract
    )


if __name__ == "__main__":
    _url = "https://arxiv.org/abs/1706.03762"
    html_content = get_page_content(_url)
    overview = parse_arxiv_html(_url, html_content)
    overview.make()

