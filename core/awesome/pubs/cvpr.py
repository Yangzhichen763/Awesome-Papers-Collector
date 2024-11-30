from core.awesome.general import *

import requests
from bs4 import BeautifulSoup


def cvpr_search(
        year: int,
        keywords: [str, list[str]],
        mode: Mode = Mode.OR
) -> list[dict[str, str]]:
    """
    通过给定的网页检索地址，提取检索结果中与论文网站相关的链接
    Args:
        year: 年份
        keywords: 要搜索的关键词
        mode: 匹配模式，默认为 OR

    Returns:
        list[str]: 与论文网站相关的链接
    """
    url = f"https://cvpr.thecvf.com/Conferences/{year}/AcceptedPapers"
    if isinstance(keywords, str):
        keywords = [keywords]

    # 发送请求并获取页面内容
    response = get_html(url)
    if response is None:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')

    # 获取论文名、作者、链接
    def get_result(title_tag, paper):
        title = title_tag.text.strip()              # 论文名
        project_page = title_tag['href']            # 论文项目链接
        authors = paper.find('i').text.strip()      # 作者

        return {
            'title': title,
            'authors': authors,
            'project_page': project_page,
            'link': f"https://cvpr.thecvf.com{project_page}"
        }

    # 查找所有论文条目
    papers = soup.find_all('tr')

    # 存储结果
    results: list[dict[str, str]] = []

    # 遍历每个论文条目
    for paper in papers:
        # 获取论文名
        title_tag = paper.find('a')
        if title_tag:
            any_match = match_text(keywords, title_tag.text, mode)
            if any_match:
                results.append(get_result(title_tag, paper))

    # 如果 results 中有重复的论文，则根据论文名去重
    seen = set()
    results = [x for x in results if not (x['title'], tuple(x['authors'])) in seen and not seen.add((x['title'], tuple(x['authors'])))]
    return results


if __name__ == '__main__':
    year = 2024
    keyword = "Relighting"

    # 调用 quick_search 函数
    results = cvpr_search(year, keyword)

    # 输出结果
    for result in results:
        print_(f"论文名: {result['title']}")
        print_(f"所有作者: {', '.join(result['authors'])}")
        print_(f"论文链接: {result['link']}")
        print_("-" * 40)
