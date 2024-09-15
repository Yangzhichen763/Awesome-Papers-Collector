from core.arxiv_crawler import parse_arxiv_html
from core.website_search import search_urls_by_title


if __name__ == '__main__':
    # 文章关键词
    query = 'Attention is all you need'

    # 爬取文章链接
    urls = search_urls_by_title(query, "arXiv")

    # 爬取文章摘要并生成 md 文档
    for url in urls["arXiv"]:
        overview = parse_arxiv_html(url)
        overview.make()
