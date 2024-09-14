from core.arxiv_crawler import parse_arxiv_html
from core.html_requester import get_page_content


if __name__ == '__main__':
    # 要生成的文章 arXiv 链接
    url = "https://arxiv.org/abs/1706.03762"

    # 爬取文章摘要并生成 md 文档
    html_content = get_page_content(url)
    overview = parse_arxiv_html(html_content, url)
    overview.make()
