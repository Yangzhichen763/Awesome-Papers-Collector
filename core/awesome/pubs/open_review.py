from openreview import OpenReviewException

from core.awesome.general import *

import openreview
import re

from datetime import datetime


tqdm_position = 0


'''
以下 get_submissions、contains_text、search_submissions、extract_submission_info 代码均修改自：https://www.wzhecnu.cn/2024/10/15/gpt/openreview-api-usage/
代码学习参考官方 API：https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-submissions
'''

def get_submissions(client, venue_id, status='accepted'):
    """
    获取指定会议的提交列表
    """
    # 检索指定会议的提交列表
    venue_group = client.get_group(id=venue_id)

    # 定义所有论文评审状态
    try:
        venue_content = venue_group.content
        venue_id = venue_group.id
        status_mapping = {
            "all": venue_content['submission_name']['value'],
            "accepted": venue_id,
            "under_review": venue_content['submission_venue_id']['value'],
            "withdrawn": venue_content['withdrawn_venue_id']['value'],
            "desk_rejected": venue_content['desk_rejected_venue_id']['value']
        }
    except Exception as e:
        # notes = client.get_all_notes(invitation=f'{venue_id}/-/Blind_Submission',
        #                              details='replyCount,invitation,original,directReplies')
        # print_(notes)
        # print_(f"获取到的 venue_group：{venue_group}\n{venue_group.web}\n出现错误：{e}")
        return client.get_all_notes(content={'venueid': venue_id})

    # 根据论文状态筛选论文
    if status in status_mapping:
        if status == "all":
            # 返回所有提交的论文
            return client.get_all_notes(invitation=f'{venue_id}/-/{status_mapping[status]}')

        # 对于其他论文状态的论文，使用 'venueid' 筛选
        return client.get_all_notes(content={'venueid': status_mapping[status]})

    raise ValueError(f"要检索的论文的状态不合法: {status}. 合法状态如下: {list(status_mapping.keys())}")


def contains_text(
        submission: dict,
        target_text: str,
        fields: [str, list[str]] = None,
        is_regex: bool = False
) -> bool:
    """
    检索论文的指定字段是否包含目标文本。

    Args:
        submission: 论文的字典表示
        target_text: 要搜索的目标文本
        fields: 要搜索的字段，默认为 ['title', 'abstract']
        is_regex: 是否使用正则表达式搜索，默认为 False

    Returns:
        布尔值，表示是否找到目标文本
    """
    if fields is None:
        fields = ['title', 'abstract']
    # 如果 fields 的值是 'all'，则检索所有字段
    if fields == 'all':
        fields = ['title', 'abstract', 'keywords', 'primary_area', 'TLDR']

    if isinstance(fields, str):
        fields = [fields]

    # 检索所有字段
    for field in fields:
        content = submission.get(field, "")

        # 将 list 形式的字段内容转换为字符串 (e.g., keywords)
        if isinstance(content, list):
            content = " ".join(content)

        # 是否使用正则表达式检索
        if is_regex:
            if re.search(target_text, content):
                return True
        else:
            if target_text in content:
                return True

    return False


def search_submissions(
        submissions: list[dict],
        target_text: str,
        fields: [str, list[str]] = None,
        is_regex: bool = False
) -> list[dict]:
    """
    搜索论文列表，返回包含目标文本的论文列表。

    Args:
        submissions: 论文列表
        target_text: 要搜索的目标文本
        fields: 要搜索的字段，默认为 ['title', 'abstract']
        is_regex: 是否使用正则表达式搜索，默认为 False

    Returns:
        包含目标文本的论文列表
    """
    if fields is None:
        fields = ['title', 'abstract']
    matching_submissions = []

    for submission in submissions:
        if contains_text(submission, target_text, fields, is_regex):
            matching_submissions.append(submission)

    return matching_submissions


def extract_submission_info(submission) -> dict:
    """
    提取论文信息

    Args:
        submission: 论文的字典表示

    Returns:
        list[dict]: 信息的字典列表
        包括以下几个字段：
        {'cdate': 1727365346374,
         'content': {'_bibtex': {'value': '@inproceedings{\n'
                                          'anonymous2024do,\n'
                                          'title={Do We Really Need '
                                          'Parameter-Isolation to Protect Task '
                                          'Knowledge?},\n'
                                          'author={Anonymous},\n'
                                          'booktitle={Submitted to The Thirteenth '
                                          'International Conference on Learning '
                                          'Representations},\n'
                                          'year={2024},\n'
                                          'url={https://openreview.net/forum?id=tVNZj27pb3},\n'
                                          'note={under review}\n'
                                          '}'},
                     'abstract': {'value': 'Due to the dynamic nature of tasks, how '
                                           'deep networks can transition from a static '
                                           'structure, trained on previous tasks, to a '
                                           'dynamic structure that adapts to '
                                           'continuously changing data inputs has '
                                           'garnered significant attention. This '
                                           'involves learning new task knowledge while '
                                           'avoiding catastrophic forgetting of '
                                           'previously acquired knowledge. Continual '
                                           'learning is a learning approach aimed at '
                                           'addressing the problem of catastrophic '
                                           'forgetting, primarily by constraining or '
                                           'isolating parameter changes to protect the '
                                           'knowledge of prior tasks. However, while '
                                           'existing methods offer good protection for '
                                           'old task knowledge, they often diminish '
                                           'the ability to learn new task knowledge. '
                                           'Given the sparsity of activation channels '
                                           'in a deep network, we introduce a novel '
                                           'misaligned fusion method within the '
                                           'context of continual learning. This '
                                           'approach allows for the adaptive '
                                           'allocation of available pathways to '
                                           'protect crucial knowledge from previous '
                                           'tasks, replacing traditional isolation '
                                           'techniques. Furthermore, when new tasks '
                                           'are introduced, the network can undergo '
                                           'full parameter training, enabling a more '
                                           'comprehensive learning of new tasks. This '
                                           'work conducts comparative tests of our '
                                           'method against other approaches using deep '
                                           'network architectures of various sizes and '
                                           'popular benchmark datasets. The '
                                           'performance demonstrates the effectiveness '
                                           'and superiority of our method.'},
                     'anonymous_url': {'value': 'I certify that there is no URL (e.g., '
                                                'github page) that could be used to '
                                                'find authors’ identity.'},
                     'code_of_ethics': {'value': 'I acknowledge that I and all '
                                                 'co-authors of this work have read '
                                                 'and commit to adhering to the ICLR '
                                                 'Code of Ethics.'},
                     'keywords': {'value': ['continual learning']},
                     'no_acknowledgement_section': {'value': 'I certify that there is '
                                                             'no acknowledgement '
                                                             'section in this '
                                                             'submission for double '
                                                             'blind review.'},
                     'pdf': {'value': '/pdf/732c23523a944ddf229055ddcc37f83fb40c7fd9.pdf'},
                     'primary_area': {'value': 'transfer learning, meta learning, and '
                                               'lifelong learning'},
                     'reciprocal_reviewing': {'value': 'I understand the reciprocal '
                                                       'reviewing requirement as '
                                                       'described on '
                                                       'https://iclr.cc/Conferences/2025/CallForPapers. '
                                                       'If none of the authors are '
                                                       'registered as a reviewer, it '
                                                       'may result in a desk rejection '
                                                       'at the discretion of the '
                                                       'program chairs. To request an '
                                                       'exception, please complete '
                                                       'this form at '
                                                       'https://forms.gle/Huojr6VjkFxiQsUp6.'},
                     'submission_guidelines': {'value': 'I certify that this '
                                                        'submission complies with the '
                                                        'submission instructions as '
                                                        'described on '
                                                        'https://iclr.cc/Conferences/2025/AuthorGuide.'},
                     'title': {'value': 'Do We Really Need Parameter-Isolation to '
                                        'Protect Task Knowledge?'},
                     'venue': {'value': 'ICLR 2025 Conference Submission'},
                     'venueid': {'value': 'ICLR.cc/2025/Conference/Submission'}},
         'ddate': None,
         'details': None,
         'domain': 'ICLR.cc/2025/Conference',
         'forum': 'tVNZj27pb3',
         'id': 'tVNZj27pb3',
         'invitations': ['ICLR.cc/2025/Conference/-/Submission',
                         'ICLR.cc/2025/Conference/-/Post_Submission',
                         'ICLR.cc/2025/Conference/Submission7383/-/Full_Submission'],
         'license': 'CC BY 4.0',
         'mdate': 1728790234440,
         'nonreaders': None,
         'number': 7383,
         'odate': 1728008565725,
         'pdate': None,
         'readers': ['everyone'],
         'replyto': None,
         'signatures': ['ICLR.cc/2025/Conference/Submission7383/Authors'],
         'tcdate': 1727365346374,
         'tmdate': 1728790234440,
         'writers': ['ICLR.cc/2025/Conference',
                     'ICLR.cc/2025/Conference/Submission7383/Authors']}
    """
    # 将时间戳转换为日期格式
    def convert_timestamp_to_year(timestamp):
        return datetime.fromtimestamp(timestamp / 1000).strftime('%Y') if timestamp else None

    # print_(submission)
    # 提取信息
    if isinstance(submission, dict):
        try:
            if 'authors' not in submission['content']:
                return {}

            content = submission['content']
            submission_info = {
                'title': content['title']['value'],
                'authors': content['authors']['value'],
                'pdf_link': f"https://openreview.net/pdf?id={submission.id}",
                'publication_year': convert_timestamp_to_year(submission.pdate),
                'conference': submission['domain'].split('.')[0],   # domain 格式：'会议名.cc/年份/Conference'
            }
        except Exception as e:
            print_(f"提取论文信息失败，获取到的信息：{submission}\n错误信息：{e}")
            submission_info = None
    else:
        try:
            if 'authors' not in submission.content:
                return {}

            content = submission.content
            submission_info = {
                'title': content['title']['value'],
                'authors': content['authors']['value'],
                'pdf_link': f"https://openreview.net/pdf?id={submission.id}",
                'publication_year': convert_timestamp_to_year(submission.pdate),
                'conference': submission.domain.split('.')[0],  # domain 格式：'会议名.cc/年份/Conference'
            }
        except Exception as e:
            print_(f"提取论文信息失败，获取到的信息：{submission}\n错误信息：{e}")
            submission_info = None

    # 更新论文的代码和项目链接
    update_paper_with_code_and_project_page(submission_info)
    return submission_info


def openreview_search(
        keyword: str,
        conferences: [str, list[str]],
        years: [int, list[int]],
):
    """
    使用 OpenReview 进行论文检索

    Args:
        keyword: 要搜索的关键词
        conferences: 会议列表，只搜索这些会议的论文（缩写即可）
        year: 要搜索的年份

    Returns:
        包含目标文本的论文列表
    """
    if isinstance(conferences, str):
        conferences = [conferences]
    if isinstance(years, int):
        years = [years]

    # 初始化客户端
    # noinspection PyUnresolvedReferences
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net',
    )

    # 获取 openreview 中的所有会议列表
    venues = client.get_group(id='venues').members
    # print_(venue_ids)

    venue_ids = []
    for venue in venues:
        venue_id_parts = venue.split("/")
        for conference in conferences:
            # 获取会议的前缀，比如 ICLR 的前缀为 'ICLR.cc'，AAAI 的前缀为 'AAAI.org'
            if venue.lower().startswith(conference.lower()):
                if venue_id_parts[1].isdigit() and int(venue_id_parts[1]) in years:
                    # '会议名称.?/年份/Conference'
                    if venue_id_parts[2].lower() == "Conference".lower():
                        venue_ids.append(venue)

                    # '会议名称.org/年份/Workshop'
                    if venue_id_parts[2].lower() == "Workshop".lower():
                        venue_ids.append(venue)

            # 对于一些特殊的会议，比如 AAAI，IJCAI，ICML 等，其 venueid 格式为 '出版社.org/会议名称/年份/Workshop'
            pub_parts = venue_id_parts[0].split(".")
            if len(pub_parts) <= 1:
                continue

            if pub_parts[-1].lower() == "org":
                if venue_id_parts[1].lower() == conference.lower() \
                    and venue_id_parts[2].isdigit() and int(venue_id_parts[2]) in years \
                    and venue_id_parts[3].lower() == "Workshop".lower():
                    venue_ids.append(venue)
    print_(f"共找到 {len(venues)} 个会议，筛选后获得 {len(venue_ids)} 个会议")

    _tqdm = tqdm(total=len(venue_ids), position=tqdm_position)
    _tqdm.set_description(f"正在搜索论文，关键词: {keyword}")
    all_submissions = []
    for venue_id in venue_ids:
        try:
            _tqdm.set_postfix_str(f"正在获取 {venue_id} 的论文列表...")
            # 获取论文列表
            submissions = get_submissions(client, venue_id, 'accepted')

            # 提取论文数据
            submission_infos = [extract_submission_info(sub) for sub in submissions]

            # 检索关键词
            matching_submissions = search_submissions(submission_infos, keyword, is_regex=True, fields='all')
            all_submissions.extend(matching_submissions)
            _tqdm.set_postfix_str(f"在 {venue_id} 中找到 {len(matching_submissions)} 篇论文")
        except OpenReviewException as e:
            print_(f"获取 {venue_id} 的论文列表失败，错误信息：{e}")

        _tqdm.update(1)
    _tqdm.close()

    print_(f'在链接 https://www.openreview.net 中搜索关键词 {keyword}，共找到 {len(all_submissions)} 篇论文')
    return all_submissions


def easy_openreview_search(
        keyword: str,
        conferences: [str, list[str]],
        years: [int, list[int]],
):
    if isinstance(conferences, str):
        conferences = [conferences]
    if isinstance(years, int):
        years = [years]

    # 初始化客户端
    # noinspection PyUnresolvedReferences
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net',
    )

    # 获取 openreview 中的所有会议列表
    venue_ids = client.get_group(id='venues').members
    # print_(venue_ids)

    # 过滤出符合条件的会议
    filtered_venue_ids = []
    for venue_id in venue_ids:
        venue_id_parts = venue_id.split("/")
        for conference in conferences:
            # 比较会议的前缀，比如 ICLR 的前缀为 'ICLR.cc'，AAAI 的前缀为 'AAAI.org'
            if venue_id.lower().startswith(conference.lower()):
                if venue_id_parts[1].isdigit() and int(venue_id_parts[1]) in years:
                    # '会议名称.?/年份/Conference'
                    if venue_id_parts[2].lower() == "Conference".lower():
                        filtered_venue_ids.append(venue_id)

                    # '会议名称.org/年份/Workshop'
                    if venue_id_parts[2].lower() == "Workshop".lower():
                        filtered_venue_ids.append(venue_id)

            # 对于一些特殊的会议，比如 AAAI，IJCAI，ICML 等，其 venueid 格式为 '出版社.org/会议名称/年份/Workshop'
            pub_parts = venue_id_parts[0].split(".")
            if len(pub_parts) <= 1:
                continue

            if pub_parts[-1].lower() == "org":
                if venue_id_parts[1].lower() == conference.lower() \
                    and venue_id_parts[2].isdigit() and int(venue_id_parts[2]) in years \
                    and venue_id_parts[3].lower() == "Workshop".lower():
                    filtered_venue_ids.append(venue_id)

    papers = []
    _tqdm = tqdm(total=len(filtered_venue_ids), position=tqdm_position)
    for venue_id in filtered_venue_ids:
        group_response = get_html("https://api2.openreview.net/groups", headers={}, max_retry_times=0)
        print(group_response.json())
        data = {
            "query": keyword,
            "venueid": venue_id,
            'source': 'forum'
        }
        headers = {'Content-Type': 'application/json'}
        response = post_html(f"https://api2.openreview.net/notes/search", data=data, headers=headers, max_retry_times=0)
        datas = response.json()

        import json
        if datas['count'] > 0:
            print(json.dumps(datas, indent=4))
            for note in datas['notes']:
                submission_info = extract_submission_info(note)
                if submission_info:
                    papers.append(submission_info)
        else:
            print(datas)

        _tqdm.set_postfix_str(f"在 {venue_id} 中找到 {datas['count']} 篇论文")
        _tqdm.update(1)

    return papers


if __name__ == '__main__':
    keyword = 'Relighting'  # Relighting
    years = range(2019, 2024 + 1)

    # OpenReview 会议中的论文搜索
    # ["AAAI", "ICLR", "ICML", "NeurIPS", "IJCAI"]
    conferences = ["NeurIPS", "ICML", "AAAI", "IJCAI", "ECCV", "ICME", "ICASSP", "BMVC", "ACCV", "ICIP", "ICPR", "ICLR"]
    conferences = list(reversed(conferences))

    # # 从搜索出的信息格式转换为自定义的适合  md 处理的格式
    # all_papers = openreview_search(keyword, conferences, years)
    all_papers = openreview_search(keyword, conferences, years)

    '''
    在 openreview API 中只能获取到当年或下一年的论文
    '''


    print_(f'一共找到 {len(all_papers)} 篇论文：')
    print_(all_papers)

