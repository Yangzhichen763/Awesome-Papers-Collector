from core.awesome.general import *

import re


tqdm_position = 0


# noinspection SpellCheckingInspection
def ieee_paper_search(
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
):
    """
    通过给定的关键词搜索 IEEE 论文，返回包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表。

    Args:
        keyword: 要搜索的关键词
        start_year: 开始年份，默认为 None
        end_year: 结束年份，默认为 None

    Returns:
        list[dict]: 包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表
        包括以下几个字段：（下列带 "*" 的是较为重要的）
            abstract (str): 文章摘要
            accessType: 访问类型，格式为 {'type': "类型", 'message': '消息’}
            * articleContentType (str): 文章类型，比如 "Journals" 或其他的
            articleNumber (str): 文章号
            * articleTitle (str): 文章标题
            * authors: 作者列表，格式为 [dict]，其中的 dict 格式为
                {
                    'preferredName': "姓名",
                    'normalizedName': "姓名缩写",
                    'firstName': "名",
                    'lastName': "姓",
                    'searchablePreferedName': "可搜索的姓名",
                    'id' (int): 作者编号
                }
            citationCount (int): 引用次数
            citationsLink (str): 引用链接，比如 "/document/9854398/citations?tabFilter=papers"
            contentType (str): 内容类型，比如 "IEEE Journals"
            course (bool): 是否是课程
            displayContentType (str): 显示内容类型，比如 "Journal Article" 或其他的
            displayPublicationTitle (str): 发表刊物名称
            docIdentifier (str): 文档标识符
            documentLinks (str): 文档链接，比如 "/document/9854398/"
            * doi (str): DOI 链接，比如 "10.1109/TIP.2022.3195366"
            downloadCount (int): 下载次数
            endPage (str): 终止页码
            ephemera (bool): 附录
            graphicalAbstract (str): 图形学摘要
            handleProduct (bool): 是否有产品
            highlightedTitle (str): 标题（高亮）
            htmlLink (str): HTML 链接，比如 "/document/9854398"
            isBook (bool): 是否是书
            isBookWithoutChapters (bool): 是否是书，但没有章节
            isConference (bool): 是否是会议论文
            isEarlyAccess (bool): 是否是早期访问论文
            isImmersiveArticle (bool):
            isJournal (bool): 是否是期刊
            isJournalAndMagazine (bool): 是否是期刊和杂志
            isMagazine (bool): 是否是杂志
            isNumber(str):
            isOnlineOnly (bool):
            isStandard (bool):
            multiMediaLinks (str): 多媒体链接，比如 "/document/9854398/media"
            patentCitationCount (int): 专利引用次数
            * pdfLink (str): PDF 下载链接，比如 "/stamp/stamp.jsp?tp=&arnumber=9854398"
            pdfSize (str): PDF 文件大小
            publicationDate (str): 发布日期
            publicationLink (str): 发表刊物链接，比如 "/xpl/RecentIssue.jsp?punumber=83"
            publicationNumber (str): 发布号
            publicationTitle (str): 发表刊物名称
            * publicationYear (str): 发布年份
            publisher (str): 出版商，比如 "IEEE"
            redline (bool):
            rightsLink (str): 版权链接
            rightslinkFlag (bool):
            showAlgorithm (bool): 是否显示算法
            showCheckbox (bool):
            showDataset (bool): 是否显示数据集
            showHtml (bool): 是否显示 HTML
            showVideo (bool): 是否显示视频
            startPage (str): 起始页码
            vj (bool):
            volume (str): 卷号
    """
    import json

    url = f"https://ieeexplore.ieee.org/rest/search"
    page_size = 100
    data = {
        'newsearch': "true",
        'queryText': keyword,
        'rowsPerPage': page_size,
        'ranges': [f"{start_year or ''}_{end_year or ''}_Year"],
    }
    headers = post_headers
    headers.update({
        'Referer': f"https://ieeexplore.ieee.org/search/searchresult.jsp",   # 使用 jsp 才能访问到其中的内容
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Content-Type': "application/json",
    })

    # 遍历所有的页码（将所有的论文都获取到）
    page_number = 1
    pbar = None
    papers = []
    total_records = 0
    total_pages = 0
    while True:
        # 发送请求
        data['pageNumber'] = page_number
        response = post_html(url, data, headers)
        if response is not None:
            json_response = json.loads(response.text)
            papers.extend(json_response['records'])

            total_pages = json_response['totalPages']
            total_records = json_response['totalRecords']

            # 显示进度条
            if pbar is None:
                pbar = tqdm(total=total_records, position=tqdm_position)
                pbar.set_description(f"正在搜索论文，关键词: {keyword}")

        # 更新进度条
        if pbar is not None:
            pbar.update(min(page_size, total_records - (page_number - 1) * page_size))
            pbar.refresh()

        # 所有论文都获取到，退出循环
        page_number += 1
        if pbar is not None and page_number > total_pages:
            pbar.close()
            break

    print_(f'在链接 {url} 中搜索关键词 {keyword}，共找到 {len(papers)} 篇论文')
    return papers


def ieee_search(
        keyword: str,
        journals_filter: dict,
        conferences_filter: list[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
):
    """
    通过给定的关键词，配合期刊列表限制范围，搜索 IEEE 论文，返回包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表。

    Args:
        keyword: 要搜索的关键词列表
        journals_filter: 期刊列表，只搜索这些期刊的论文（必须是全称，比如 "IEEE Transactions on Image Processing" 而不是 "TIP"）
        conferences_filter: 会议列表，只搜索这些会议的论文（缩写即可）
        start_year: 开始年份，默认为 None
        end_year: 结束年份，默认为 None

    Returns:
        list[dict]: 包含标题、作者、发表时间、发表刊物、卷、期、页码、DOI、PDF 链接、附件链接等信息的字典列表
        包括以下几个字段：
            title (str): 文章标题
            authors (list[str]): 作者列表
            pdf_link (str): PDF 下载链接
            doi (str): DOI 链接
            publication_year (str): 发布年份
            journal (str): 发表刊物名称
            conference (str): 所在会议名称
    """
    all_papers = []
    ieee_papers = ieee_paper_search(keyword, start_year, end_year)
    for ieee_paper in ieee_papers:
        # 更新论文的代码和项目链接
        update_paper_with_code_and_project_page(ieee_paper)

        # 跳过没有出版社的论文
        if ieee_paper.get('publicationTitle') is None:
            continue

        pub_title = ieee_paper['publicationTitle']
        # print_(pub_title)

        # 期刊和会议不同处理
        is_journal = ieee_paper['isJournalAndMagazine'] or ieee_paper['isJournal']
        is_conference = ieee_paper['isConference']
        if is_journal:
            # 期刊的格式："期刊全称"
            pub_title = pub_title
        if is_conference:
            # 会议的格式："会议全称 (会议缩写)"
            pub_title = re.findall(r'\((.*?)\)', pub_title)
            if len(pub_title) > 0:
                pub_title = pub_title[0]
            else:
                pub_title = None

        # 跳过不在筛选期刊或会议列表中的论文
        if (pub_title in journals_filter) or (pub_title in conferences_filter):
            journal = journals_filter[pub_title] if is_journal else None
            conference = pub_title if is_conference else None

            paper = {
                'title': ieee_paper['articleTitle'],
                'authors': [author['preferredName'] for author in ieee_paper['authors']],
                'pdf_link': f"https://ieeexplore.ieee.org/{normalize_link(ieee_paper['pdfLink'])}",
                'doi': ieee_paper['doi'],
                'publication_year': str(ieee_paper['publicationYear']),
                'journal': journal,
                'conference': conference,
            }

            if journal is not None or conference is not None:
                all_papers.append(paper)

    return all_papers


if __name__ == '__main__':
    _keyword = "Camouflage"
    years = range(2019, 2024 + 1)
    _start_year, _end_year = years[0], years[-1]


    """
    使用关键词搜索，检索的部分为标题、摘要等
    """
    # IEEE 会议和期刊中的论文搜索
    journals = ["TIP", "TPAMI", "TOG", "TIFS", "TMM", "TCSCV", "TITS", "TOC", "TNNLS"]
    conferences = ["CVPR", "ICCV", "WACV"]
    # 将 total_journal_short_names 键值互换
    filtered_journals = {v['full_name']: k for k, v in journal_short_name_dict.items() if k in journals}
    # 从搜索出的信息格式转换为自定义的适合 md 处理的格式
    all_papers = ieee_search(_keyword, filtered_journals, conferences, _start_year, _end_year)


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)