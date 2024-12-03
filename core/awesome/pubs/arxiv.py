from core.awesome.general import *

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re

import lxml

from concurrent.futures import ThreadPoolExecutor, as_completed


def arxiv_paper_search(
        keyword: str
) -> list[dict]:
    """
    搜索 arXiv 论文，返回包含关键词的论文信息。

    Args:
        keyword: 关键词

    Returns:
        list[dict[str, str]]: 论文信息
        包括以下几个字段：
            title: 论文标题
            authors: 作者列表
            abstract: 论文摘要
            updated_date: 论文更新日期
            published_date: 论文发布日期
            arxiv_link: arXiv 链接
            pdf_link: PDF 链接
            primary_category: 主要分类
            categories: 所有分类
            doi: 论文 DOI（如果有）
    """

    url_base = 'http://export.arxiv.org/api/query'
    url = f'{url_base}?search_query=all:{keyword}&start=0&max_results=1'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'xml')
    total_results_html = soup.find('opensearch:totalResults')
    if not total_results_html:
        print_(f'无法搜索到关键词 "{keyword}"，获取到的信息为 {soup.prettify()}')
        return []
    number_results = int(total_results_html.text)

    all_papers = []
    def get_papers_info(_start):
        _url = f'{url_base}?search_query=all:{keyword}&start={_start}&max_results=100'
        _response = requests.get(_url)
        _soup = BeautifulSoup(_response.text, 'xml')
        _paper_elems = _soup.find_all('entry')

        _papers = []
        for paper_elem in _paper_elems:
            _paper = {}

            _paper['title'] = paper_elem.find('title').text.replace('\n ', '')
            _paper['authors'] = [author.text.strip().split("\n")[0] for author in paper_elem.find_all('author')]
            _paper['abstract'] = paper_elem.find('summary').text.replace('\n', ' ')
            _paper['updated_date'] = paper_elem.find('updated').text
            _paper['published_date'] = paper_elem.find('published').text
            _paper['arxiv_link'] = paper_elem.find('id').text
            _paper['pdf_link'] = paper_elem.find('link', title='pdf')['href']
            _paper['primary_category'] = paper_elem.find('arxiv:primary_category')['term']
            _paper['categories'] = [category['term'] for category in paper_elem.find_all('category')]

            code_links: list = re.findall(r'https?://(?:www\.)?github\.com/[^/]+/[^., ]*', _paper['abstract'])
            if code_links and len(code_links) > 1:
                _paper['code_link'] = code_links[0]

            project_links: list = re.findall(r'https?://(?:www\.)?[^/]+\.github\.io/[^., ]*', _paper['abstract'])
            if project_links and len(project_links) > 1:
                _paper['project_page_link'] = project_links[0]

            doi_link_elem = paper_elem.find('link', title='doi')
            if doi_link_elem:
                _paper['doi'] = doi_link_elem.get('href')

            journal_ref_elem = paper_elem.find('arxiv:journal_ref')
            if journal_ref_elem:
                _paper['journal_ref'] = paper_elem.find('arxiv:journal_ref').text.replace('\n ', '')

            _papers.append(_paper)
            update_tqdm()
            pbar.refresh()

        return _papers

    pbar = tqdm(total=number_results)
    def update_tqdm(x=1):
        pbar.update(x)

    # 单线程
    # for start in range(0, number_results, 100):
    #     papers = get_papers_info(start)
    #     all_papers.extend(papers)

    # 多线程
    with ThreadPoolExecutor() as pool:
        futures = {}
        for start in range(0, number_results, 100):
            future = pool.submit(get_papers_info, start)
            futures[future] = min(100, number_results - start)

        for future in as_completed(futures):
            papers = future.result()
            all_papers.extend(papers)

    pbar.close()

    return all_papers


if __name__ == '__main__':
    keyword = "relighting"


    # arXiv 中的论文搜索
    all_papers = arxiv_paper_search(keyword)


    print(f'Found {len(all_papers)} papers containing keyword "{keyword}"')
    print(all_papers)
