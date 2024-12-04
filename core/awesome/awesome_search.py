import re

import core.awesome.pubs.ieee
from core.awesome.general import *
from core.awesome.pubs.cvf import cvf_search
from core.awesome.pubs.ieee import ieee_search
from core.awesome.pubs.acm import acm_search
from core.awesome.pubs.open_review import openreview_search
from core.awesome.pubs.neurips import neurips_search
from core.awesome.pubs.arxiv import arxiv_paper_search
from core.awesome.pubs.aaai import aaai_search
from core.awesome.pubs.ecva import ecva_paper_search as eccv_search


# == 加载和保存 ==
def load_from_csv(csv_file_path: str):
    # 从 csv 文件中读取论文信息
    import csv
    with open(csv_file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        papers = []
        for row in reader:
            if row[0] == "conference":
                continue
            paper = {
                'conference': row[0] if row[0] != "" else None,
                'journal': row[1] if row[1] != "" else None,
                'publication_year': int(row[2]),
                'title': row[3],
                'authors': row[4].split(" · "),
                'pdf_link': row[5],
                'supplementary_link': row[6],
                'arxiv_link': row[7],
            }
            papers.append(paper)
        return papers


def save_to_csv(csv_file_path: str, all_papers: list[dict]):
    # 写入 csv 文件
    import csv
    with open(csv_file_path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["conference", "journal", "year", "title", "authors", "pdf_link", "supplementary_link", "arxiv_link"])
        for paper in all_papers:
            conference = paper.get('conference', "")
            journal = paper.get('journal', "")
            pdf_link = paper.get('pdf_link', "")
            supplementary_link = paper.get('supplementary_link', "")
            arxiv_link = paper.get('arxiv_link', "")
            writer.writerow([conference, journal, paper['publication_year'], paper['title'], " · ".join(paper['authors']),
                             pdf_link, supplementary_link, arxiv_link])


# paper 中包含的 key
# 'title': 论文标题
# 'authors': 作者列表
# 'pdf_link': PDF 链接
# 'supplementary_link': 附件链接
# 'arxiv_link': arXiv 链接
# 'code_link': 代码链接
# 'project_page_link': 项目页面链接
# 'doi': 论文 DOI
# 'publication_year': 出版年份
# 'journal': 期刊名称
# 'conference': 会议名称
"""
![Static Badge](https://img.shields.io/badge/CCF_A-crimson)
![Static Badge](https://img.shields.io/badge/CCF_B-blue)
![Static Badge](https://img.shields.io/badge/CCF_C-seagreen)

<img src='https://img.shields.io/badge/Code-Github-goldenrod' alt='Paper PDF Link'>
<img src='https://img.shields.io/badge/Paper-PDF-red' alt='Paper PDF Link'>
<img src='https://img.shields.io/badge/arXiv-1234.12345-limegreen' alt='Paper PDF Link'>
<img src='https://img.shields.io/badge/Project-Page-mediumslateblue' alt='Paper PDF Link'>
<img src='https://img.shields.io/badge/DOI-Link-deepskyblue' alt='Paper PDF Link'>
<img src='https://img.shields.io/badge/Supp-Link-lightgrey' alt='Paper PDF Link'>
"""
def save_to_md(md_file_path: str, keyword: str, all_papers: list[dict], arxiv_papers: list[dict] = None,
               title_md: str = None):
    # 按照会议或期刊名称排序
    # print_("===================")
    # print_('\n'.join([f"{(x.get('conference') or x.get('journal'), x['title'])}" for x in all_papers]))
    all_papers.sort(key=lambda x: x.get('conference') or x.get('journal'))

    # 写入 md 文件中
    with open(md_file_path, "w", encoding="utf-8") as f:
        # 按年份分组
        papers_by_year = {}
        for paper in all_papers:
            year = str(paper['publication_year'])
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append(paper)

        # 按年份排序
        years = sorted(papers_by_year.keys(), reverse=True)

        # 以表格的形式输出论文信息
        awesome_title = title_md or keyword
        f.write(f'# Awesome {awesome_title}\n'
                f'[![Awesome](https://cdn.jsdelivr.net/gh/sindresorhus/awesome/media/badge.svg)](https://github.com/sindresorhus/awesome)\n'
                f'[![Awesome {awesome_title}](https://img.shields.io/badge/Awesome-{awesome_title.replace(" ", "_")}-orchid)](https://github.com/topics/awesome)\n\n')
        for year in years:
            f.write(f"### {year}\n")
            f.write(f"{len(papers_by_year[year])} papers received.\n\n")
            f.write("| Pub. | Title | Links |\n")
            f.write("| :---: | :--- | :--- |\n")
            for paper in papers_by_year[year]:
                # Pub.
                pub_title = paper.get('conference') or paper.get('journal')
                pub_ccf_level = (conference_short_name_dict.get(pub_title) or journal_short_name_dict.get(pub_title))['CCF']
                ccf_level_colormap = {"A": "crimson", "B": "blue", "C": "seagreen"}
                level_md = f"<br><sub>![Static Badge](https://img.shields.io/badge/CCF_{pub_ccf_level}-{ccf_level_colormap[pub_ccf_level]})</sub>" \
                    if pub_ccf_level in ccf_level_colormap else ""
                pub_md = f"{pub_title}<br><sup>{paper['publication_year']}</sup>{level_md}"

                # Title
                title_md = f"{paper['title']}<br> <sup><sub>*{', '.join(paper['authors'])}*</sub></sup>"

                # Links
                links_list = []
                if paper.get('code_link'):
                    code_link = paper['code_link']
                    links_list.append(
                        f"<a href='{code_link}'><img src='https://img.shields.io/badge/Code-Github-goldenrod' alt='{code_link}'></a> ")
                if paper.get('pdf_link'):
                    pdf_link = paper['pdf_link']
                    links_list.append(f"<a href='{pdf_link}'><img src='https://img.shields.io/badge/Paper-PDF-red' alt='{pdf_link}'></a> ")
                if paper.get('arxiv_link'):
                    arxiv_link = paper['arxiv_link']
                    try:
                        arxiv_code = re.search(r".*?(\d{4}.\d{4,5}(?:v\d+)?)", arxiv_link).group(1)
                    except AttributeError:
                        print_(f"无法解析 arXiv 链接 {arxiv_link}")
                        arxiv_code = "?"
                    links_list.append(
                        f"<a href='{arxiv_link}'><img src='https://img.shields.io/badge/arXiv-{arxiv_code}-limegreen' alt='{arxiv_link}'></a> ")
                if paper.get('project_page_link'):
                    project_page_link = paper['project_page_link']
                    links_list.append(
                        f"<a href='{project_page_link}'><img src='https://img.shields.io/badge/Project-Page-mediumslateblue' alt='{project_page_link}'></a> ")
                if paper.get('doi'):
                    doi = normalize_link(paper['doi'])
                    doi_link = f"https://doi.org/{doi}"
                    links_list.append(
                        f"<a href='{doi_link}'><img src='https://img.shields.io/badge/DOI-Link-deepskyblue' alt='{doi}'></a> ")
                if paper.get('supplementary_link'):
                    # 后缀一般是四个字符内的
                    if "." not in paper['supplementary_link'][-5:]:
                        file_type = "Link"
                    else:
                        file_type = paper['supplementary_link'][-5:].split(".")[-1].upper()
                    links_list.append(f"<a href='{paper['supplementary_link']}'><img src='https://img.shields.io/badge/Supp-{file_type}-lightgrey' alt='Supplementary Materials Link'></a> ")
                links_md = "".join(links_list)
                f.write(f"| {pub_md} | {title_md} | {links_md} |\n")

        # 按年份分组
        if arxiv_papers:
            for paper in arxiv_papers:
                time = paper['updated_date']
                formated_time = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
                daytime = formated_time.strftime('%Y.%m.%d')
                year = formated_time.year

                paper['daytime'] = daytime
                paper['year'] = year

            # 按年月日排序
            arxiv_papers.sort(key=lambda x: x['daytime'], reverse=True)

            # 输出 arXiv 论文信息
            f.write(f"### arXiv\n")
            f.write(f"{len(arxiv_papers)} papers preprinted.\n\n")
            f.write("| Catergory | Title | Links |\n")
            f.write("| :---: | :--- | :--- |\n")
            for paper in arxiv_papers:
                # Category
                category = paper['primary_category']
                daytime = paper['daytime']
                category_md = f"{category}<br><sup>{daytime}</sup>"

                # Title
                title_md = f"{paper['title']}<br> <sup><sub>*{', '.join(paper['authors'])}*</sub></sup>"

                # Links
                links_list = []
                if paper.get('pdf_link'):
                    pdf_link = paper['pdf_link']
                    links_list.append(f"<a href='{pdf_link}'><img src='https://img.shields.io/badge/Paper-PDF-red' alt='Paper PDF Link'></a> ")
                if paper.get('arxiv_link'):
                    arxiv_link = paper['arxiv_link']
                    try:
                        arxiv_code = re.search(r".*?(\d{4}.\d{4,5}(?:v\d+)?)", arxiv_link).group(1)
                    except AttributeError:
                        print_(f"无法解析 arXiv 链接 {arxiv_link}")
                        arxiv_code = "?"
                    links_list.append(
                        f"<a href='{paper['arxiv_link']}'><img src='https://img.shields.io/badge/arXiv-{arxiv_code}-limegreen' alt='{arxiv_code}'></a> ")
                if paper.get('project_link'):
                    project_link = paper['project_link']
                    links_list.append(
                        f"<a href='{project_link}'><img src='https://img.shields.io/badge/Project-Page-yellow' alt='{project_link}'></a> ")
                if paper.get('doi'):
                    doi = normalize_link(paper['doi'])
                    doi_link = f"https://doi.org/{doi}"
                    links_list.append(
                        f"<a href='{doi_link}'><img src='https://img.shields.io/badge/DOI-Link-cornflowerblue' alt='{doi}'></a> ")
                links_md = "".join(links_list)
                f.write(f"| {category_md} | {title_md} | {links_md} |\n")

    print_(f"Awesome {awesome_title} 已保存到 {md_file_path}")


from source.path import root
import os
import datetime
current_year = datetime.datetime.now().year
def search(
        keyword: str,
        search_type: [str, list[str]] = "all",
        years: list[int] = range(current_year - 5, current_year + 1),
        save_file_dir: str = f"{root}/test/docs/"
):
    union_keywords = keyword.split(" ")
    start_year, end_year = years[0], years[-1]
    os.makedirs(save_file_dir, exist_ok=True)

    # 去除重复的论文并保存到 csv 文件中
    def save_csv_checkpoints(all_papers, preserve_new_paper=True, do_save=True):
        """
        保存论文到 csv 文件中，并去除重复的论文
        Args:
            all_papers: 论文列表
            preserve_new_paper: 是否保留最新论文，如果为 False，则保留旧的论文
            do_save: 是否保存到文件
        Returns:
            去除重复后的论文列表
        """
        def preserve_order(papers):
            papers = reversed(papers) if preserve_new_paper else papers
            return papers

        seen = dict()
        # 使用论文名称判断是否重复，逆序是使用新的论文覆盖旧的论文
        # 如果新的论文中没有旧的论文的一部分内容，则旧的论文中的内容会填入新的论文中的空
        tmp_all_papers = []
        for paper in preserve_order(all_papers):
            if paper['title'] in seen:
                new_paper = seen[paper['title']]
                old_paper = paper
                # 将 old_paper 中 new_paper 没有的内容填入 new_paper 中
                for key in old_paper:
                    if (key not in new_paper or new_paper[key] is None) and old_paper[key] is not None:
                        new_paper[key] = old_paper[key]
            else:
                seen[paper['title']] = paper
                tmp_all_papers.append(paper)
        tmp_all_papers = list(preserve_order(tmp_all_papers))
        if do_save:
            print_(f"将论文从 {len(all_papers)} 篇去除重复到 {len(tmp_all_papers)} 篇，保存到 {csv_file_path} 中")
            save_to_csv(csv_file_path, tmp_all_papers)
        else:
            print_(f"将论文从 {len(all_papers)} 篇去除重复到 {len(tmp_all_papers)} 篇")
        return tmp_all_papers


    # 将 new_papers 中的论文内容补充到 base_papers 中
    def append_content_to(base_papers, new_papers):
        """
        将 new_papers 中的论文（该论文是 base_papers 中存在的）的内容补充到 base_papers 中
        """
        base_papers_map = dict((x['title'], x) for x in base_papers)
        for new_paper in new_papers:
            if new_paper['title'] in base_papers_map:
                base_paper = base_papers_map[new_paper['title']]
                for key in new_paper:
                    if (key not in base_paper or base_paper[key] is None) and new_paper[key] is not None:
                        base_paper[key] = new_paper[key]
        return base_papers


    # 读取 csv 文件中的记录
    csv_file_path = os.path.join(save_file_dir, f"{keyword} papers.csv")
    md_file_path = os.path.join(save_file_dir, f"{keyword} papers.md")
    if not os.path.exists(csv_file_path):
        all_papers = []
    else:
        all_papers: list[dict] = load_from_csv(csv_file_path)
    print_(f"从已有文件 {csv_file_path} 中读入 {len(all_papers)} 篇论文")

    # == CVF 会议 == 中的论文搜索
    if "cvf" in search_type or search_type == "all":
        print_(f"正在搜索 CVF 会议中的论文...")
        cvf_papers = cvf_search(union_keywords, years)
        all_papers.extend(cvf_papers)
        print_(f"筛选后的 CVF 会议搜索结果 {len(all_papers)} 篇论文：\n{all_papers}")
        save_csv_checkpoints(all_papers)

    # == IEEE 会议和期刊 == 中的论文搜索
    if "ieee" in search_type or search_type == "all":
        print_(f"正在搜索 IEEE 会议和期刊中的论文...")
        journals = ["TIP", "TPAMI", "TOG", "TIFS", "TMM", "TCSCV", "TITS", "TOC", "TNNLS"]
        conferences = ["CVPR", "ICCV", "WACV"]
        # 将 total_journal_short_names 键值互换
        filtered_journals = {v['full_name']: k for k, v in journal_short_name_dict.items() if k in journals}
        # 从搜索出的信息格式转换为自定义的适合 md 处理的格式
        ieee_papers = ieee_search(keyword, filtered_journals, conferences, start_year, end_year)
        all_papers.extend(ieee_papers)
        print_(f"筛选后的 IEEE 会议和期刊搜索结果 {len(ieee_papers)} 篇论文：\n{ieee_papers}")
        save_csv_checkpoints(all_papers)

    # == ACM 会议和期刊 == 中的论文搜索
    if "acm" in search_type or search_type == "all":
        print_(f"正在搜索 ACM 会议和期刊中的论文...")
        journals = ["TOG", "TOMM"]
        conferences = ["MM", "SIGGRAPH"]
        # 从搜索出的信息格式转换为自定义的适合 md 处理的格式
        acm_papers = acm_search(keyword, journals, conferences, start_year, end_year)
        all_papers.extend(acm_papers)
        print_(f"筛选后的 ACM 会议和期刊搜索结果 {len(acm_papers)} 篇论文：\n{acm_papers}")
        save_csv_checkpoints(all_papers)

    # == NeurIPS == 会议中的论文搜索
    if "neurips" in search_type or search_type == "all":
        print_(f"正在搜索 NeurIPS 会议中的论文...")
        neurips_papers = neurips_search(union_keywords, years)
        all_papers.extend(neurips_papers)
        print_(f"筛选后的 NeurIPS 会议搜索结果 {len(neurips_papers)} 篇论文：\n{neurips_papers}")
        save_csv_checkpoints(all_papers)

    # == OpenReview == 会议中的论文搜索
    if "openreview" in search_type or search_type == "all":
        print_(f"正在搜索 OpenReview 会议中的论文...")
        conferences = ["NeurIPS", "ICML", "AAAI", "IJCAI", "ECCV", "ICME", "ICASSP", "BMVC", "ACCV", "ICIP", "ICPR", "ICLR"]
        # 从搜索出的信息格式转换为自定义的适合  md 处理的格式
        openreview_papers = openreview_search(keyword, conferences, years)
        all_papers.extend(openreview_papers)
        print_(f"筛选后的 OpenReview 会议搜索结果 {len(openreview_papers)} 篇论文：\n{openreview_papers}")
        save_csv_checkpoints(all_papers)

    # == AAAI == 会议中的论文搜索
    if "aaai" in search_type or search_type == "all":
        print_(f"正在搜索 AAAI 会议中的论文...")
        aaai_papers = aaai_search(union_keywords, years)
        all_papers.extend(aaai_papers)
        print_(f"筛选后的 AAAI 会议搜索结果 {len(aaai_papers)} 篇论文：\n{aaai_papers}")
        save_csv_checkpoints(all_papers)

    # == ECCV == 会议中的论文搜索
    if "eccv" in search_type or search_type == "all":
        print_(f"正在搜索 ECCV 会议中的论文...")
        eccv_papers = eccv_search(union_keywords, years)
        all_papers.extend(eccv_papers)
        print_(f"筛选后的 ECCV 会议搜索结果 {len(eccv_papers)} 篇论文：\n{eccv_papers}")
        save_csv_checkpoints(all_papers)

    # == arXiv == 中的论文搜索
    print_(f"正在搜索 arXiv 中的论文...")
    arxiv_papers = arxiv_paper_search(keyword)

    # 将 arXiv 论文内容补充到 all_papers 中（如果 all_papers 中有该论文）
    all_papers = append_content_to(all_papers, arxiv_papers)
    save_csv_checkpoints(all_papers)

    # 去除 all_papers 中已经出现的 arXiv 论文
    all_titles = [x['title'] for x in all_papers]
    arxiv_papers = [x for x in arxiv_papers if x['title'] not in all_titles]
    # 筛选 arXiv 论文中 CV 领域的论文
    filtered_arxiv_papers = []
    for arxiv_paper in arxiv_papers:
        if arxiv_paper.get('primary_category') and arxiv_paper['primary_category'] == 'cs.CV':
            filtered_arxiv_papers.append(arxiv_paper)
    print_(f"筛选后的 arXiv 搜索结果 {len(filtered_arxiv_papers)} 篇论文：\n{filtered_arxiv_papers}")

    # 将筛选和偶的记录保存到 md 进行可视化
    all_papers: list[dict] = load_from_csv(csv_file_path)
    save_to_md(md_file_path=md_file_path, keyword=keyword, all_papers=all_papers, arxiv_papers=filtered_arxiv_papers)


def filter_title(
        remove_keywords: [str, list[str]],
        keyword: str,
        load_file_dir: str = f"{root}/test/docs/",
        save_file_dir: str = None,
):
    """
    根据论文标题中是否包含关键词过滤论文

    Args:
        remove_keywords: 要移除的关键词
        load_file_dir: 加载文件目录
        save_file_dir: 保存文件目录，默认与 load_file_dir 相同
    """
    if isinstance(remove_keywords, str):
        remove_keywords = [remove_keywords]
    save_file_dir = save_file_dir or load_file_dir

    os.makedirs(save_file_dir, exist_ok=True)
    csv_file_path = os.path.join(load_file_dir, f"{keyword} papers.csv")
    md_file_path = os.path.join(save_file_dir, f"{keyword} filtered papers.md")

    # 读取 csv 文件中的记录
    if not os.path.exists(csv_file_path):
        all_papers = []
    else:
        all_papers: list[dict] = load_from_csv(csv_file_path)
    print_(f"从已有文件 {csv_file_path} 中读入 {len(all_papers)} 篇论文")

    # 在 papers 中筛选 title 中不包含关键词的论文
    filtered_papers = [x for x in all_papers if all(k.lower() not in x['title'].lower() for k in remove_keywords)]
    print_(f"筛选后的论文 {len(filtered_papers)} 篇论文：\n{filtered_papers}")

    # 将筛选和偶的记录保存到 md 进行可视化
    save_to_md(md_file_path=md_file_path, keyword=keyword, all_papers=filtered_papers)



if __name__ == '__main__':
    total_keywords = ['Anything']  # Relighting
    search_type = []  # "all"  # "cvf", "ieee", "acm", "neurips", "openreview", "aaai"
    years = range(2019, 2024 + 1)
    for keyword in total_keywords:
        search(keyword, search_type, list(years))