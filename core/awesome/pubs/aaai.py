from core.awesome.general import *

from bs4 import BeautifulSoup
from tqdm import tqdm
import enum
from enum import Enum


class Version(Enum):
    OLDER_2022 = enum.auto()
    NEWER_2022 = enum.auto()


def aaai_paper_search(
        keywords: [str, list[str]],
        years: [int, list[int]],
        mode: Mode = Mode.AND
):
    if isinstance(keywords, str):
        keywords = [keywords]
    if isinstance(years, int):
        years = [years]

    # 找到所有 Proceedings 的 Track 列表
    main_url = 'https://aaai.org/conference/aaai/'
    response = get_html(main_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    entry_elems = soup.find('div', class_='entry-content')
    proceeding_block_elems = entry_elems.find_next('h3',
                                                   string='Proceedings of the AAAI Conference on Artificial Intelligence')
    proceeding_block_elems = proceeding_block_elems.find_next('p')
    proceeding_elems = proceeding_block_elems.find_all('a')

    # 找到所有 Proceedings 的 Track 列表的链接
    proceedings_links = []
    for proceeding_elem in proceeding_elems:
        # 检查年份是否在指定的年份范围内
        any_year = False
        for year in years:
            if str(year) in proceeding_elem.text:
                any_year = True
                break
        if not any_year:
            continue

        proceedings_links.append(proceeding_elem['href'])

    # 找到所有 Proceedings 的 Track 的链接
    all_papers = []
    for proceedings_link in proceedings_links:
        response = get_html(proceedings_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        paper_list_container_old_elem = soup.find('main', id='genesis-content')
        paper_list_container_new_elem = soup.find('div', class_='page page_issue_archive')
        print(paper_list_container_new_elem)
        if paper_list_container_old_elem:
            version = Version.OLDER_2022
            paper_list_container_elem = paper_list_container_old_elem.find('ul')
        elif paper_list_container_new_elem:
            version = Version.NEWER_2022
            paper_list_container_elem = paper_list_container_new_elem.find('ul', class_='issues_archive')
        else:
            print(f'无法找到论文列表容器元素: {proceedings_link}')
            continue

        if paper_list_container_elem is None:
            continue

        paper_list_elems = paper_list_container_elem.find_all('li')

        # 找到所有 Track 的链接
        paper_list_links = []
        for paper_list_elem in paper_list_elems:
            paper_list_link = paper_list_elem.find('a')['href']
            paper_list_links.append(paper_list_link)

        # 找到所有论文
        for paper_list_link in paper_list_links:
            response = get_html(paper_list_link)
            soup = BeautifulSoup(response.content, 'html.parser')

            if version == Version.OLDER_2022:
                paper_container_elem = soup.find('div', class_='track-wrap')
            elif version == Version.NEWER_2022:
                paper_container_elem = soup.find('div', class_='obj_issue_toc')
            else:
                raise ValueError('Unknown version')

            # paper_elems 在 paper_container_elem 二级子节点下
            paper_elems = paper_container_elem.find_all('li')
            paper_elems = [elem for elem in paper_elems if elem.parent.parent == paper_container_elem]

            # 处理每个论文
            papers = []
            if version == Version.OLDER_2022:
                def get_paper_info(paper_elem):
                    paper = {}

                    title_elem = paper_elem.find('h5').find('a')
                    paper['title'] = remove_quotes(title_elem.text).strip()
                    # 比如 https://aaai.org/papers/00003-learning-unseen-emotions-from-gestures-via-semantically-conditioned-zero-shot-perception-with-adversarial-autoencoders/">Learning Unseen Emotions from Gestures via Semantically-Conditioned Zero-Shot Perception with Adversarial Autoencoders
                    paper['html_link'] = title_elem['href']

                    paper_author_page_elem = paper_elem.find('span', class_='papers-author-page')
                    authors_elem = paper_author_page_elem.find_next('p')
                    pages_elem = authors_elem.find_next('p')
                    paper['authors'] = [author.strip() for author in authors_elem.text.split(', ')]
                    paper['pages'] = pages_elem.text.strip()

                    pdf_link_elem = paper_elem.find('a', class_='wp-block-button')
                    # 比如 https://cdn.aaai.org/ojs/19873/19873-13-23886-1-2-20220628.pdf
                    paper['pdf_link'] = pdf_link_elem['href']

                    # 获取论文主页更详细的信息
                    html_link = paper['html_link']
                    paper_file_response = get_html(html_link)
                    paper_file_soup = BeautifulSoup(paper_file_response.content, 'html.parser')

                    entry_content_elem = paper_file_soup.find('div', class_='entry-content')
                    def get_section_text(section_name):
                        section_elem = entry_content_elem.find('h4', string=section_name)
                        if section_elem:
                            section_elem = section_elem.parent.find('p')
                            return section_elem.text.strip()
                        else:
                            return None

                    track = get_section_text('Track:')
                    if track:
                        paper['track'] = track

                    issue = get_section_text('Issue:')
                    if track:
                        paper['issue'] = issue

                    proceedings = get_section_text('Proceedings:')
                    if track:
                        paper['proceedings'] = proceedings

                    abstract = get_section_text('Abstract:')
                    if abstract:
                        paper['abstract'] = remove_quotes(abstract).strip()

                    doi = get_section_text('DOI:')
                    if doi:
                        paper['doi'] = doi

                    if match_paper(keywords, paper, mode):
                        return paper

                    return None
            elif version == Version.NEWER_2022:
                def get_paper_info(paper_elem):
                    paper = {}

                    title_elem = paper_elem.find('h3').find('a')
                    paper['title'] = remove_quotes(title_elem.text).strip()
                    # 比如 https://ojs.aaai.org/index.php/AAAI/article/view/27749
                    paper['html_link'] = title_elem['href']

                    paper_author_page_elem = paper_elem.find('div', class_='meta')
                    authors_elem = paper_author_page_elem.find('div', class_='authors')
                    pages_elem = authors_elem.find('div', class_='pages')
                    paper['authors'] = [author.strip() for author in authors_elem.text.split(', ')]
                    paper['pages'] = pages_elem.text.strip()

                    links_elem = paper_elem.find('ul', class_='galleys_links')
                    # 比如 https://ojs.aaai.org/index.php/AAAI/article/view/27749/27541
                    pdf_link_elem = links_elem.find('a', class_='obj_galley_link pdf')
                    if pdf_link_elem:
                        paper['pdf_link'] = pdf_link_elem['href']
                    # 比如 https://ojs.aaai.org/index.php/AAAI/article/view/27749/27542
                    file_link_elem = links_elem.find('a', class_='obj_galley_link file')
                    if file_link_elem:
                        paper['file_link'] = file_link_elem['href']

                    # 获取论文主页更详细的信息
                    html_link = paper['html_link']
                    paper_file_response = get_html(html_link)
                    paper_file_soup = BeautifulSoup(paper_file_response.content, 'html.parser')

                    entry_content_elem = paper_file_soup.find('div', class_='main_entry')
                    def get_main_section_text(section_name):
                        section_elem = entry_content_elem.find('section', class_=section_name)
                        if section_elem:
                            section_elem = section_elem.parent.find('span', class_='value')
                            return section_elem.text.strip()
                        else:
                            return None

                    doi = get_main_section_text('item doi')
                    if doi:
                        paper['doi'] = remove_quotes(doi).strip().replace('https://doi.org/', '')

                    _keywords = get_main_section_text('item keywords')
                    if _keywords:
                        paper['keywords'] = [keyword.strip() for keyword in _keywords.split(', ')]

                    abstract = get_main_section_text('item keywords')
                    if abstract:
                        paper['abstract'] = remove_quotes(abstract).strip()

                    entry_details_elem = paper_file_soup.find('div', class_='entry_details')

                    published_elem = entry_content_elem.find('div', class_='item published')
                    published_elem = published_elem.find('div', class_='value')
                    published = published_elem.text.strip()
                    paper['published_date'] = published

                    issue_elem = entry_content_elem.find('div', class_='item issue')
                    issue_elems = issue_elem.find_all('section', class_='sub_item')
                    for issue_elem in issue_elems:
                        if issue_elem.find('h2', class_='label', string='Issue'):
                            issue = issue_elem.find('div', class_='value').text.strip()
                            paper['issue'] = issue
                            paper['proceedings'] = issue
                        if issue_elem.find('h2', class_='label', string='Section'):
                            track = issue_elem.find('div', class_='value').text.strip()
                            paper['track'] = track

                    match_paper(keywords, paper, mode)
            else:
                raise ValueError('Unknown version')

            pbar = tqdm(total=len(paper_elems))
            pbar.set_postfix_str(f"正在访问链接，寻找匹配关键词为 {keywords} 的论文: {paper_list_link}...")
            # 更新 tqdm 进度条
            def update_tqdm(x=1):
                pbar.update(x)
                pbar.refresh()

            with ThreadPoolExecutor() as pool:  # max_workers=128
                futures = {}
                for paper_elem in paper_elems:
                    future = pool.submit(get_paper_info, paper_elem)
                    futures[future] = paper_elem

                for future in as_completed(futures):
                    paper = future.result()
                    update_tqdm()
                    if paper:
                        papers.append(paper)
                        print_(papers)

            if papers and len(papers) > 0:
                pbar.set_postfix_str(f"匹配完成，共找到 {len(papers)} 篇论文，于链接 {paper_list_link}")
            else:
                pbar.set_postfix_str(f"匹配完成，未找到论文，于链接 {paper_list_link}")
            pbar.refresh()

            all_papers.extend(papers)
            pbar.close()
    return all_papers


# noinspection SpellCheckingInspection
def aaai_search(
        keywords: [str, list[str]],
        years: [int, list[int]],
        mode: Mode = Mode.OR
):
    """
    综合搜索 CVF 会议论文，包括 CVPR、ICCV、WACV 等

    Args:
        keywords: 要搜索的关键词
        years: 年份列表
        mode: 关键词匹配模式，默认 OR，即关键词出现在论文标题、作者、摘要中任意一个字段中即可

    Returns:
        list[dict[str, str]]: 论文信息
        包括以下几个字段：
            title: 论文标题
            authors: 作者列表
            page: 页码
            pdf_link: PDF 下载链接
            html_link: 论文主页链接
            abstract: 论文摘要
            conference: 会议名称
            publication_year: 出版年份
    """
    if isinstance(keywords, str):
        keywords = [keywords]
    if isinstance(years, int):
        years = [years]

    all_papers = []
    for year in years:
        aaai_papers = aaai_paper_search(keywords, year, mode)
        for aaai_paper in aaai_papers:
            paper = {
                'conference': "AAAI",
                'publication_year': str(year),
            }
            paper.update(aaai_paper)

            all_papers.append(paper)

    return all_papers


if __name__ == '__main__':
    _keyword = "Relighting"
    years = range(2019, 2024 + 1)


    # AAAI 会议中的论文搜索
    all_papers = aaai_search(_keyword, years)


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)














