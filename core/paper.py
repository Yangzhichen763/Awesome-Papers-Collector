import os


class Overview:
    def __init__(
        self, *,
        url,
        title,
        subjects,
        authors,
        first_date,
        abstract
    ):
        self.url = url
        self.title = title
        self.subjects = subjects
        self.authors = authors
        self.first_date = first_date
        self.abstract = abstract


    def make_authors_md(self):
        authors_md = [
            f"[**{author}**]()"
            for author in self.authors
        ]
        # 每行最多三个作者
        authors_md_pairs = []
        for i in range(len(authors_md)):
            if i % 3 == 2 or i == len(authors_md) - 1:
                authors_md_pairs.append(" · ".join(authors_md[i//3*3:i+1]))
        return "<br>\n".join(authors_md_pairs)

    def make(self):
        # 创建文件夹
        filename = f"../papers/{self.title}.md"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # 编辑内容
        content = rf"""
<div align="center">
<h1>{self.title}</h1>

{self.first_date}\
{self.make_authors_md()}

<a href="{self.url}"><img src='https://img.shields.io/badge/arXiv-Paper-red' alt='Paper'></a>
</div>

{self.abstract}
"""

        # 写入文件
        with open(filename, "wb") as file:
            file.write(content.encode())


if __name__ == "__main__":
    abstract = " ".join(["It is very long and it is going to be very long." for i in range(10)])
    paper = Overview(
        url="https://arxiv.org/abs/2103.12345",
        title="Title of the Paper",
        subjects=["Subject1", "Subject2"],
        authors=["Author1", "Author2", "Author3"],
        first_date="2021-03-01",
        abstract="Abstract of the paper goes here. And this is a very long abstract. "
                 f"{abstract}"
    )
    paper.make()
