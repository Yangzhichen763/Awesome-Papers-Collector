from core.awesome.general import *

import requests
from bs4 import BeautifulSoup


any_print = True
global_pbar: Optional[tqdm] = None

# 正在访问的链接
task_link_list: Optional[list[str]] = None
global_keywords = None

# 以下打印都是满足调试要求的打印
def print__(*args, **kwargs):
    if not any_print:
        return

    global global_pbar
    if global_pbar is not None:
        tqdm_postfix = None
        if task_link_list is not None and global_keywords is not None:
            tqdm_postfix = f'正在访问 {len(task_link_list)} 个论文列表链接，寻找匹配关键词为 {global_keywords} 的论文...'

        if tqdm_postfix is not None:
            global_pbar.set_postfix_str(tqdm_postfix)
            global_pbar.refresh()
        else:
            _args = []
            for arg in args:
                if isinstance(arg, str):
                    arg.replace('\r', '')
                    _args.append(arg)
                    continue
                _args.append(arg)
            global_pbar.set_postfix_str(*_args)
            global_pbar.refresh()
    else:
        print_(*args, **kwargs)


def colored_print_(text: str, color: str = 'green'):
    if not any_print:
        return

    global global_pbar
    if global_pbar is not None:
        colored_print(text, color=color)



# noinspection PyTypeChecker
def cvf_paper_search(
        conference: str,
        year: int,
        keywords: [str, list[str]],
        mode: Mode = Mode.AND
) -> list[dict]:
    """
    通过给定的网页检索地址，提取检索结果中与 CVF 相关的链接，
    CVF 中只包含 CVPR、ICCV、WACV 等会议的论文

    Args:
        conference: 会议名称，如 CVPR、ICCV、ECCV 等
        year: 年份
        keywords: 要搜索的关键词
        mode: 关键词匹配模式，默认 OR，即关键词之间为或关系

    Returns:
        list[dict[str, str]]: 论文信息
        包括以下几个字段：
            title: 论文标题
            authors: 作者列表
            pdf_link: PDF 下载链接
            supplementary_link: 附件下载链接
            arxiv_link: arXiv 链接
    """
    if isinstance(keywords, str):
        keywords = [keywords]
    global task_link_list

    url = f"https://openaccess.thecvf.com/{conference}{year}"
    print__(f"正在寻找会议链接，访问链接: {url}...", end='')
    response = get_html(url)
    if response is None:
        return []

    # 获取论文列表链接，比如 https://openaccess.thecvf.com/{conference}{year}?day=all 等
    soup = BeautifulSoup(response.text, 'html.parser')
    links_elem = soup.find('div', id='content')

    # 解析会议链接，获取论文列表链接，如果 url 链接中就有所有论文列表，则直接输出该链接
    # url 链接中就有所有论文列表，比如 https://openaccess.thecvf.com/CVPR2013
    if links_elem.find('dt'):
        links = [url]
    # 有 dt 的是论文列表页
    else:
        links = []
        for link_elem in links_elem.find_all('a'):
            link_suffix = normalize_link(link_elem['href'])
            if '.py' in link_suffix:
                link_suffix = link_suffix.replace('.py', '')
            link = f"https://openaccess.thecvf.com/{link_suffix}"
            links.append(link)
    print__(f"\r匹配链接 {url} 论文列表中的所有论文...")

    # 通过论文列表链接获取论文信息
    all_papers: list[dict] = []
    def search_paper(link: str):
        print__(f"正在访问链接，寻找匹配关键词为 {keywords} 的论文: {link}...", end='')
        response = get_html(link)
        if response is None:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 假设论文信息在某个特定的 HTML 结构中
        papers_elem = soup.find('div', id='content')
        number_paper = len(papers_elem.find_all('dt', class_='ptitle'))
        papers_elem = papers_elem.find_next('dt', class_='ptitle')

        if number_paper == 0:
            colored_print_(f"链接 {link} 中未找到匹配的论文", color='red')
            return None

        # pbar = tqdm(total=number_paper)
        # pbar.set_postfix_str(f"正在访问链接，寻找匹配关键词为 {keywords} 的论文: {link}...")
        papers = []
        while papers_elem:
            title = papers_elem.text.strip()

            # 通过 html 获取论文信息
            def get_paper_info():
                paper = {}

                # 标题
                paper['title'] = title

                # 作者
                author_elem = papers_elem.find_next('dd')
                if author_elem:
                    authors = [author.text.strip() for author in author_elem.find_all('a')]
                    paper['authors'] = authors

                # 论文链接，包括 PDF、Supplementary、arxiv 链接
                links_elem = author_elem.find_next('dd')
                if links_elem:
                    for link_elem in links_elem.find_all('a'):
                        link_text = link_elem.text.lower()
                        if link_text == 'pdf':
                            pdf_link = normalize_link(link_elem['href'])
                            paper['pdf_link'] = f"https://openaccess.thecvf.com/{pdf_link}"
                        elif 'supp' in link_text:
                            supplementary_link = normalize_link(link_elem['href'])
                            paper['supplementary_link'] = f"https://openaccess.thecvf.com/{supplementary_link}"
                        elif link_text == 'arxiv':
                            arxiv_link = normalize_link(link_elem['href'])
                            paper['arxiv_link'] = f"https://openaccess.thecvf.com/{arxiv_link}"

                return paper

            # 匹配论文标题
            if match_text(keywords, title, mode):
                papers.append(get_paper_info())

            # 继续查找下一个论文
            papers_elem = papers_elem.find_next('dt', class_='ptitle')

            # pbar.update(1)
            # pbar.set_postfix_str(f"正在匹配论文 {title}...")
            # # print__(f"({i})正在匹配论文 {title}...", end='')
        return papers

    # pbar = tqdm(total=len(links))
    with ThreadPoolExecutor() as pool:
        futures = {}
        for link in links:
            task_link_list.append(link)
            future = pool.submit(search_paper, link)
            futures[future] = link

        for future in as_completed(futures):
            link = futures[future]
            task_link_list.remove(link)

            # pbar.update(1)
            papers = future.result()
            if papers:
                all_papers.extend(papers)

        if papers and len(papers) > 0:
            # pbar.set_postfix_str(f"链接 {link} 论文匹配完成，共找到 {len(papers)} 篇论文")
            print__(f"\r匹配完成，共找到 {len(papers)} 篇论文，于链接 {url}")
        else:
            # pbar.set_postfix_str(f"链接 {link} 论文匹配完成，未找到论文")
            print__(f"\r匹配完成，未找到论文，于链接 {url}")
        # pbar.close()

    # 如果 papers 中有重复的论文，则根据论文名去重
    seen = set()
    all_papers = [x for x in all_papers if not (x['title']) in seen and not seen.add(x['title'])]
    return all_papers


# noinspection SpellCheckingInspection
def cvf_search(
        keywords: [str, list[str]],
        years: [int, list[int]],
        mode: Mode = Mode.AND
):
    """
    综合搜索 CVF 会议论文，包括 CVPR、ICCV、WACV 等

    Args:
        keywords: 要搜索的关键词
        years: 年份列表
        mode: 关键词匹配模式，默认 OR，即关键词之间为或关系

    Returns:
        list[dict[str, str]]: 论文信息
        包括以下几个字段：
            title: 论文标题
            authors: 作者列表
            pdf_link: PDF 下载链接
            supplementary_link: 附件下载链接
            arxiv_link: arXiv 链接
            conference: 会议名称
            publication_year: 出版年份
    """
    if isinstance(keywords, str):
        keywords = [keywords]
    if isinstance(years, int):
        years = [years]

    all_papers = []
    conferences = ["CVPR", "ICCV", "WACV"]
    global global_pbar, task_link_list, global_keywords
    global_pbar = tqdm(total=len(years) * len(conferences))
    task_link_list = []
    global_keywords = keywords

    # 单线程
    # for year in years:
    #     for conference in conferences:
    #         cvf_papers = cvf_paper_search(conference, year, keywords)
    #         for cvf_paper in cvf_papers:
    #             paper = {
    #                 'conference': conference,
    #                 'publication_year': str(year),
    #             }
    #             paper.update(cvf_paper)
    #
    #             all_papers.append(paper)

    # 多线程
    with ThreadPoolExecutor(max_workers=len(years) * len(conferences)) as pool:
        futures = {}
        for year in years:
            for conference in conferences:
                future = pool.submit(cvf_paper_search, conference, year, keywords, mode)
                futures[future] = (conference, year)

        for future in as_completed(futures):
            conference, year = futures[future]
            papers = future.result()
            global_pbar.update(1)
            for paper in papers:
                _paper = {
                    'conference': conference,
                    'publication_year': str(year),
                }
                _paper.update(paper)

                all_papers.append(_paper)

    global_pbar.close()

    global_pbar = None
    task_link_list = None
    global_keywords = None
    return all_papers


if __name__ == '__main__':
    _keyword = "Relighting"
    years = range(2019, 2024 + 1)


    """
    只对论文标题做检索
    """
    # CVF 会议中的论文搜索
    all_papers = cvf_search(_keyword, years)


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)