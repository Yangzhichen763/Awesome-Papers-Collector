def abbreviate_authors(authors):
    """
    缩写所有作者名
    """
    # 缩写作者姓名
    def abbreviate_name(name: str):
        name_list = name.split()
        name_list = [name_list[-1], *name_list[:-1]]
        for i in range(len(name_list))[1:]:
            name_list[i] = name_list[i][0]
        return " ".join(name_list)

    abb_authors = [abbreviate_name(name) for name in authors]
    author_str = ""
    if abb_authors is not None:
        if len(abb_authors) == 1:
            author_str = abb_authors[0]
        elif len(abb_authors) >= 2:
            author_str = ", ".join(abb_authors[:-1]) + " and " + abb_authors[-1]
        print(f"缩写后的作者信息如下：\n{author_str}")

    return author_str


class Reference:
    def __init__(self, **kwargs):
        self.authors = kwargs.get("authors")                       # 全体作者
        self.publication_year = kwargs.get("publication_year")     # 出版年
        self.title = kwargs.get("title")                           # 文献标题名称
        self.journal = kwargs.get("journal")                       # 期刊名称
        self.volume = kwargs.get("volume")                         # 卷
        self.issue = kwargs.get("issue")                           # 期
        self.pages = kwargs.get("pages")                           # 页码
        self.doi = kwargs.get("doi")                               # 文献的数字对象标识符

    def abbreviate_authors(self):
        """
        缩写所有作者名
        """
        return abbreviate_authors(self.authors)

