from core.html_requester import get_page_content
import pypinyin


# pypinyin 教程参考文章：https://blog.csdn.net/qq_64192931/article/details/139239535
def search_by_pinyin(url, query):
    html = get_page_content(url)

    # pypinyin.slug(query): 福建233 -> fu-jian-233
    # pypinyin.pinyin(query): 福建233 -> [['fú'], ['jiàn'], ['233']]
    # pypinyin.lazy_pinyin(query): 福建233 -> ['fu', 'jian', '233']
    # heteronym=True: 启用多音字模式
    html_pinyin = pypinyin.slug(html)


def name_to_pinyin(names: [str, list[str]]):
    if isinstance(names, str):
        names = [names]

    pinyin_list = []
    for name in names:
        pinyin = pypinyin.slug(name)
        pinyin_list.append(pinyin)

    return pinyin_list


if __name__ == '__main__':
    name = "张三"
    pinyin = name_to_pinyin(name)
    print(pinyin)

