from core.awesome.general import *

import re
from bs4 import BeautifulSoup


def ecva_paper_search(
        keywords: [str, list[str]],
        years: [int, list[int]],
        mode: Mode = Mode.AND
):
    if isinstance(keywords, str):
        keywords = [keywords]
    if isinstance(years, int):
        years = [years]

    url_after_2018 = "https://www.ecva.net/papers.php"
    print_(f"正在访问链接: {url_after_2018}...", end="")
    response = get_html(url_after_2018)
    soup = BeautifulSoup(response.text, "html.parser")
    print_(f"\r正在寻找匹配关键词为 {keywords} 的论文: {url_after_2018}...")

    papers = []
    button_htmls = soup.find_all("button", class_="accordion")
    for button_html in button_htmls:
        year_str = button_html.text.strip()
        year = re.findall(r"\d{4}", year_str)[0]
        if int(year) not in years:
            continue

        content_html = button_html.find_next_sibling("div", class_="accordion-content")
        paper_html = content_html.find("dl")
        while True:
            paper_html = paper_html.find_next("dt", class_="ptitle")
            if paper_html is None:
                break

            paper = {}

            title_html = paper_html.find("a")
            title = title_html.text.strip()
            paper["title"] = remove_quotes(title)
            html_link = title_html.get("href")
            paper["html_link"] = f"https://www.ecva.net/{normalize_link(html_link)}"

            authors_html = paper_html.find_next_sibling("dd")
            authors = [author.strip() for author in authors_html.text.split(",")]
            paper["authors"] = authors

            links_html = paper_html.find_next_sibling("dd")
            pdf_link_html = links_html.find("a", string="pdf")
            if pdf_link_html:
                pdf_link = pdf_link_html.get("href")
                paper["pdf_link"] = f"https://www.ecva.net/{normalize_link(pdf_link)}"

            while True:
                next_link_html = links_html.find_next_sibling("a")
                if next_link_html is None:
                    break

                if "Supplementary Material".lower() == next_link_html.text.lower():
                    supp_link = next_link_html.get("href")
                    paper["supp_link"] = f"https://www.ecva.net/{normalize_link(supp_link)}"
                if "DOI".lower() == next_link_html.text.lower():
                    doi_link = next_link_html.get("href")
                    paper["doi_link"] = doi_link

            papers.append(paper)

    def get_paper_info(paper: dict):
        response = get_html(paper["html_link"])
        soup = BeautifulSoup(response.text, "html.parser")

        abstract_html = soup.find("div", id="abstract")
        if abstract_html:
            abstract = abstract_html.text.strip()
            paper["abstract"] = abstract

        if match_paper(keywords, paper, mode):
            return paper
        else:
            return None

    pbar = tqdm(total=len(papers))
    pbar.set_postfix_str(f"正在访问链接，寻找匹配关键词为 {keywords} 的论文: {url_after_2018}...")

    # 更新 tqdm 进度条
    def update_tqdm(x=1):
        pbar.update(x)
        pbar.refresh()

    filtered_papers = []
    with ThreadPoolExecutor(max_workers=128) as pool:
        futures = {}
        for paper in papers:
            future = pool.submit(get_paper_info, paper)
            futures[future] = paper

        for future in as_completed(futures):
            paper = future.result()
            update_tqdm()
            if paper:
                filtered_papers.append(paper)

    return filtered_papers


# TODO: 支持搜索 ECCV 2018 年以前的论文
if __name__ == '__main__':
    _keyword = "Relighting"
    years = range(2019, 2024 + 1)


    # AAAI 会议中的论文搜索
    all_papers = ecva_paper_search(_keyword, years)


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)
