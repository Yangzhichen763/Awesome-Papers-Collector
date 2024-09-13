from core import reference_do


if __name__ == '__main__':
    title = "Attention is all you need"  # 文章标题，或者能在搜索引擎中搜索到的关键词

    reference_do.search_authors_by_title(title)  # 检索文章作者
    # 可以通过更改 reference_do.search_engine 来切换搜索引擎
    # 可以通过修改 reference_do.num_pages 来调整搜索结果数
