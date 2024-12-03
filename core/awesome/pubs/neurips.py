from core.awesome.general import *

from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor, as_completed


# noinspection PyTypeChecker
def neurips_paper_search(
        keywords: [str, list[str]],
        year: int,
        mode: Mode = Mode.AND
) -> list[dict]:
    """
    通过给定的网页检索地址，提取检索结果中与 CVF 相关的链接，
    CVF 中只包含 CVPR、ICCV、WACV 等会议的论文

    Args:
        conference: 会议名称，如 CVPR、ICCV、ECCV 等
        year: 年份
        keywords: 要搜索的关键词
        mode: 匹配模式，默认为 OR

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

    url = f"https://proceedings.neurips.cc/paper/{year}"
    print_(f"正在寻找会议链接，访问链接: {url}...", end='')
    response = get_html(url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    paper_list_elem = soup.find('ul', class_='paper-list')

    # 通过论文列表链接获取论文信息
    papers: list[dict] = []

    # 假设论文信息在某个特定的 HTML 结构中
    paper_elems = paper_list_elem.find_all('li')
    number_paper = len(paper_elems)
    if number_paper == 0:
        colored_print(f"不存在该会议或者该年份的会议未接受任何论文", color='red')
        return papers

    pbar = tqdm(total=number_paper)
    pbar.set_postfix_str(f"正在访问链接，寻找匹配关键词为 {keywords} 的论文: {url}...")
    # 更新 tqdm 进度条
    def update_tqdm(x=1):
        pbar.update(x)
        pbar.refresh()
        # if 'title' in paper:
        #     pbar.set_postfix_str(f"正在匹配论文 {paper['title']}...")
        #     # print_(f"({i})正在匹配论文 {title}...", end='')

    # 通过论文的 html 主页获取论文其他信息
    def set_paper_file_info(paper: dict, paper_file_link: str):
        response = get_html(paper_file_link)
        if response is None:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        container_elem = soup.find('div', class_='container-fluid')
        if container_elem:
            pdf_link_elem = container_elem.find('a', string='Paper')
            if pdf_link_elem:
                pdf_link = normalize_link(pdf_link_elem['href'])
                paper['pdf_link'] = f"https://proceedings.neurips.cc/{pdf_link}"

            review_and_comment_link_elem = container_elem.find('a', string='Reviews And Public Comment')
            if review_and_comment_link_elem:
                review_and_comment_link = normalize_link(review_and_comment_link_elem['href'])
                paper['review_and_comment_link'] = f"https://proceedings.neurips.cc/{review_and_comment_link}"

            supplementary_link_elem = container_elem.find('a', string='Supplemental')
            if supplementary_link_elem:
                supplementary_link = normalize_link(supplementary_link_elem['href'])
                paper['supplementary_link'] = f"https://proceedings.neurips.cc/{supplementary_link}"

            abstract_elem = container_elem.find_next('h4', string='Abstract')
            if abstract_elem:
                abstract = abstract_elem.find_next('p').find_next('p').text.strip()
                paper['abstract'] = abstract

            update_paper_with_code_and_project_page(paper)

    # 通过 html 获取论文信息
    def get_paper_info(paper_elem):
        paper = {}

        # 标题
        title_elem = paper_elem.find('a', title='paper title')
        paper['title'] = remove_quotes(title_elem.text)
        html_link = normalize_link(title_elem['href'])
        paper['html'] = f"https://proceedings.neurips.cc/{html_link}"

        # 作者
        author_elem = paper_elem.find('i')
        if author_elem:
            authors = author_elem.text.strip().split(', ')
            paper['authors'] = authors

        # 论文链接，包括 PDF、Supplementary、等链接
        if 'html' in paper:
            set_paper_file_info(paper, paper['html'])

        # 关键词匹配
        return match_paper(keywords, paper, mode)

    # 多线程加速
    with ThreadPoolExecutor(max_workers=128) as pool:
        futures = {}
        for paper_elem in paper_elems:
            future = pool.submit(get_paper_info, paper_elem)
            futures[future] = paper_elem

        for future in as_completed(futures):
            paper = future.result()
            update_tqdm()
            if paper:
                papers.append(paper)

    # 结尾判断和日志输出
    if len(papers) > 0:
        pbar.set_postfix_str(f"匹配完成，共找到 {len(papers)} 篇论文，于链接 {url}")
        # print_(f"\r({i})匹配完成，共找到 {len(papers)} 篇论文")
    else:
        pbar.set_postfix_str(f"匹配完成，未找到论文，于链接 {url}")
        # print_(f"\r({i})匹配完成，未找到论文")
    pbar.refresh()
    pbar.close()

    # 如果 papers 中有重复的论文，则根据论文名去重
    seen = set()
    papers = [x for x in papers if not (x['title']) in seen and not seen.add(x['title'])]
    return papers


# noinspection SpellCheckingInspection
def neurips_search(
        keywords: [str, list[str]],
        years: [int, list[int]],
        mode: Mode = Mode.AND):
    """
    综合搜索 CVF 会议论文，包括 CVPR、ICCV、WACV 等

    Args:
        keywords: 要搜索的关键词
        years: 年份列表
        mode: 匹配模式，默认为 OR

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
    for year in years:
        cvf_papers = neurips_paper_search(keywords, year, mode)
        for cvf_paper in cvf_papers:
            paper = {
                'conference': "NeurIPS",
                'publication_year': str(year),
            }
            paper.update(cvf_paper)

            all_papers.append(paper)

    return all_papers


if __name__ == '__main__':
    _keyword = "Relighting"
    years = range(2019, 2024 + 1)


    # NeurIPS 会议中的论文搜索
    all_papers = neurips_search(_keyword, years)


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)