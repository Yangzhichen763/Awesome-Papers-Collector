from core.awesome import awesome_search


if __name__ == '__main__':
    keyword = 'Relighting'

    # 搜索关键词匹配的论文并生成 markdown 文件
    awesome_search.search(keyword)

    # 筛除关键词匹配的论文并生成 markdown 文件
    filter_keywords = ['NeRF', 'Gaussian Splatting', 'Neural Radiance Fields', 'Neural', 'Gaussian',
                       'Geometry', 'Geometric', 'Material', 'Render', 'Radiance Field', '3D']
    awesome_search.filter_title(filter_keywords, keyword)
