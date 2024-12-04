from core.awesome.general import *

import re
from bs4 import BeautifulSoup


def acm_paper_search(
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
):
    """
    通过给定的关键词搜索 ACM 论文，返回包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表。

    Args:
        keyword: 要搜索的关键词
        start_year: 开始年份，默认为 None
        end_year: 结束年份，默认为 None

    Returns:
        list[dict]: 包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表
        包括以下几个字段：
            title: 论文标题
            authors: 作者列表
            publication_title: 发表刊物名称
            publication_year: 发表年份
            volume: 卷号和 issue 号
            article_number: 文章号
            pages: 文章在期刊中的页码
            doi: DOI 链接
            pdf_link: PDF 下载链接
            supplementary_link: 附件下载链接
    """
    url = 'https://dl.acm.org/action/doSearch'
    page_size = 50
    params = {
        'AllField': keyword,
        'AfterYear': start_year,
        'BeforeYear': end_year,
        'pageSize': page_size,
    }
    headers = get_headers
    headers.update({
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "gzip, deflate, zstd",  # 不能用 br，否则会出现乱码
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Content-Encoding': "br",
        'Content-Type': "text/html;charset=UTF-8",
    })

    # 遍历所有的页码（将所有的论文都获取到）
    page_number = 0
    pbar = None
    papers = []
    number_results = 0
    total_pages = 0
    while True:
        # 发送请求
        params['startPage'] = page_number
        response = get_html(url, params, headers)
        if response is not None:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 搜索论文条目数量
            number_results = int(soup.find('span', class_='result__count').text
                                 .strip().split(' ')[0].replace(',', ''))
            total_pages = number_results // page_size + 1

            # 查找文章条目
            page_content_elem: BeautifulSoup = soup.find('div', id='pb-page-content')
            article_results_body = page_content_elem.find('ul', class_='search-result__xsl-body items-results rlist--inline')
            if article_results_body:
                papers_elem = article_results_body.find_all('li', class_='issue-item-container')

                for paper_elem in papers_elem:
                    paper = {}

                    # 发表时间
                    pub_date_elem = paper_elem.find('div', class_='bookPubDate simple-tooltip__block--b')
                    if pub_date_elem:
                        paper['publication_year'] = (pub_date_elem.text.strip()
                                    .split(' ')[-1])  # 只保留年份：July 2019 -> 2019

                    # 提取标题
                    title_elem = paper_elem.find('h5', class_='issue-item__title')
                    if title_elem:
                        paper['title'] = title_elem.text.strip()
                        paper['doi'] = title_elem.find('a')['href']

                    # 提取作者信息
                    authors_elem = paper_elem.find('ul', class_='rlist--inline')
                    if authors_elem:
                        authors = [author.text.strip() for author in authors_elem.find_all('li')]
                        paper['authors'] = authors

                    # 提取发表信息
                    pub_info: BeautifulSoup = paper_elem.find('div', class_='issue-item__detail')
                    if pub_info:
                        pub_title_elem = pub_info.find('a')
                        if pub_title_elem:
                            paper['publication_title'] = pub_title_elem['title'].strip()
                            paper['volume'] = pub_title_elem.find('span', class_='epub-section__title').text.strip()
                        other_info_elem = pub_title_elem.find_next_sibling('span')
                        if other_info_elem:
                            other_info_elem = other_info_elem.find_all('span')
                            if len(other_info_elem) > 0:
                                paper['article_number'] = other_info_elem[0].text.strip()
                            if len(other_info_elem) > 1:
                                paper['pages'] = other_info_elem[1].text.strip()

                    # 提取 DOI
                    if 'doi' not in paper:
                        doi_elem = paper_elem.find('a', class_='issue-item__doi')
                        if doi_elem:
                            paper['doi'] = doi_elem.text.strip()

                    footer_elem = paper_elem.find('div', class_='issue-item__footer clearfix')
                    if footer_elem:
                        # 提取附件信息
                        attach_holder_elem = footer_elem.find('li', class_='attach-holder')
                        if attach_holder_elem:
                            tooltip_elem = attach_holder_elem.find('div', class_='tooltip__body')
                            if tooltip_elem:
                                supplementary_elem = tooltip_elem.find_all('a')
                                if supplementary_elem:
                                    paper['supplementary_links'] = [f"https://dl.acm.org/{normalize_link(elem['href'])}" for elem in supplementary_elem]
                                    paper['supplementary_link'] = paper['supplementary_links'][0]

                        # 论文 pdf 链接
                        pdf_elem = footer_elem.find('a', class_='get-access')
                        if pdf_elem:
                            pdf_link = f"https://dl.acm.org/{normalize_link(pdf_elem['href'])}"
                            paper['pdf_link'] = pdf_link

                    papers.append(paper)

            # 显示进度条
            if pbar is None:
                pbar = tqdm(total=number_results)
                pbar.set_description(f"正在搜索论文，关键词: {keyword}")

        # 更新进度条
        pbar.update(min(page_size, number_results - page_number * page_size))
        pbar.refresh()

        # 所有论文都获取到，退出循环
        page_number += 1
        if page_number > total_pages:
            pbar.close()
            break

    print_(f'在链接 {url} 中搜索关键词 {keyword}，共找到 {len(papers)} 篇论文')
    return papers


def acm_search(
        keyword: str,
        journals_filter: list[str],
        conferences_filter: list[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
):
    """
    通过给定的关键词，配合期刊列表限制范围，搜索 ACM 论文，返回包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表。

    Args:
        keyword: 要搜索的关键词列表
        journals_filter: 期刊列表，只搜索这些期刊的论文（缩写即可）
        conferences_filter: 会议列表，只搜索这些会议的论文（缩写即可）
        start_year: 开始年份
        end_year: 结束年份

    Returns:
        list[dict]: 包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表
        包括以下几个字段：
            title: 论文标题
            authors: 作者列表
            publication_title: 发表刊物名称
            publication_year: 发表年份
            volume: 卷号和 issue 号
            article_number: 文章号
            pages: 文章在期刊中的页码
            doi: DOI 链接
            pdf_link: PDF 下载链接
            supplementary_link: 附件下载链接
            journal: 期刊名称
            conference: 会议名称
    """
    all_papers = []
    acm_papers = acm_paper_search(keyword, start_year, end_year)
    for acm_paper in acm_papers:
        # 跳过没有出版社的论文
        if acm_paper.get('publication_title') is None:
            continue

        pub_title = acm_paper['publication_title']
        # print_(pub_title)

        # 期刊和会议不同处理
        any_volume = acm_paper.get('volume')
        if any_volume:
            # 期刊的格式："期刊名称 (期刊简称)"
            pub_title = re.findall(r'\((.*?)\)', pub_title)
            if len(pub_title) > 0:
                pub_title = pub_title[0]
            else:
                pub_title = None
        else:
            # 会议的格式："会议缩写 '举办年份: 会议全称"
            pub_title = pub_title.split(' ')[0]

        # 跳过不在筛选期刊或会议列表中的论文
        if pub_title in journals_filter or pub_title in conferences_filter:
            # 期刊是有卷次的，会议没有卷次
            journal = pub_title if any_volume else None
            conference = pub_title if not any_volume else None

            paper = acm_paper
            paper.update({
                'journal': journal,
                'conference': conference,
            })

            if journal is not None or conference is not None:
                all_papers.append(paper)

    return all_papers


if __name__ == '__main__':
    _keyword = "Low Light"  # "Relighting"
    years = range(2019, 2024 + 1)
    _start_year, _end_year = years[0], years[-1]


    """
    使用关键词搜索，检索的部分为标题、摘要等
    """
    # ACM 会议和期刊中的论文搜索
    journals = ["TOG", "TOMM"]
    conferences = ["MM", "SIGGRAPH", "SA"]
    # 从搜索出的信息格式转换为自定义的适合 md 处理的格式
    all_papers = acm_search(_keyword, journals, conferences, _start_year, _end_year)


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)