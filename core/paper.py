import math
import os
import re
from typing import Optional

from core.md import MDClass


class Figure(MDClass):
    """
    原本的图片提取代码如下：
    figures = []
    figure_url_htmls: list[BeautifulSoup] = html_soup.findAll("figure", class_="ltx_figure")  # 如果要读取表格 class_="ltx_table"
    if len(figure_url_htmls) > 0:
        for figure_url_html in figure_url_htmls:
            # 图片链接
            image_urls = [
                f"{html_url}/{image_html['src']}"
                for image_html in figure_url_html.findAll("img")
            ]
            # 图片标题
            caption = figure_url_html.find("figcaption").text.strip()

            figure = Figure(
                urls=image_urls,
                caption=caption
            )
            figures.append(figure)
    """
    single_image_width = 0.5  # 单张图片的宽度占比

    def __init__(
            self, *,
            urls: [str, list[str]],
            caption: str,
    ):
        super().__init__()

        self.urls = urls
        self.caption = caption

    @staticmethod
    def calculate_image_width(count):
        """
        根据图片数量计算总的图片宽度占比
        """
        return (2 / math.pi * (1 - Figure.single_image_width) * math.atan(count - 1)
                + Figure.single_image_width)

    @staticmethod
    def make_figure_md(figure_url, count):
        width = f"{Figure.calculate_image_width(count) * 100:.2f}%"
        return f'''<img 
    style="border-radius: 0.3125em; box-shadow: 0 2px 10px 0 {MDClass.shadow_color}" 
    width={width} 
    src="{figure_url}" 
    alt="{figure_url}">
'''

    def get_md(self):
        figures_md = [
            self.make_figure_md(url, len(self.urls))
            for url in self.urls
        ]
        return f'''
<center>
{"".join(figures_md)}
<div style="color: #999; padding: 2px; font-size: 0.8em;">{self.caption}</div>
</center>
'''


class Overview(MDClass):
    date_sep = "-"  # 日期分隔符，比如 20xx.01.xx

    def __init__(
        self, *,
        arxiv_url: str, html_url: Optional[str] = None, project_url: Optional[str] = None,
        title: str,
        subjects: str,
        authors: list[str],
        first_date: str,
        abstract: str,
        md_classes: Optional[list[MDClass]] = None,
    ):
        super().__init__()

        self.arxiv_url = arxiv_url
        self.html_url = html_url
        self.project_url = project_url

        self.title = title
        self.subjects = subjects
        self.authors = authors
        self.first_date = first_date
        self.abstract = abstract

        self.content = self.get_md()
        self.md_class = md_classes

    @staticmethod
    def validate_title(title):
        """
        验证将标题作为文件名是否合法，并将其转换为合法的文件名
        """
        new_title = re.sub(r'[\\/:*?"<>|\r\n]+', "_", title)
        return new_title

    @staticmethod
    def make_authors_md(authors):
        # md 格式化作者
        authors_md = [
            f"[**{author}**]()"
            for author in authors
        ]
        # 每行最多三个作者
        authors_md_pairs = []
        for i in range(len(authors_md)):
            if i % 3 == 2 or i == len(authors_md) - 1:
                authors_md_pairs.append(" · ".join(authors_md[i//3*3:i+1]))
        return "<br>\n".join(authors_md_pairs)

    @staticmethod
    def make_date_md(date):
        def parse_month(_month):
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return f"{months.index(_month) + 1:02d}"  # 或者 .rjust(2, "0")

        def parse_day(_day):
            return f"{int(_day):02d}"

        # 将 xx Jan 20xx 格式化为 20xx-01-xx
        day, month, year = date.split(" ")
        month = parse_month(month)
        day = parse_day(day)
        return f"**{year}{Overview.date_sep}{month}{Overview.date_sep}{day}**"

    def make_shields_md(self):
        def make_shield_md(url, header, body, color):
            if url is None:
                md = ""
            else:
                md = (
                    f"<a href=\"{url}\">"
                    f"<img src='https://img.shields.io/badge/{header}-{body}-{color}' alt='{body}'>"
                    f"</a>"
                )
            return md

        arxiv_code = re.findall(r"/(\d+?\.\d+)", self.arxiv_url)[0]
        shields = [
            make_shield_md(self.arxiv_url, header="arXiv", body=arxiv_code, color="red"),
            make_shield_md(self.html_url, header="HTML", body="Page", color="yellow"),
            make_shield_md(self.project_url, header="Project", body="Page", color="green")
        ]
        for shield in shields:
            if shield == "":
                shields.remove(shield)
        shield_md = "\n".join(shields)
        return shield_md

    def get_md(self):
        content = f'''
<div align="center">
<h1>{self.title}</h1>

{self.make_date_md(self.first_date)}

{self.make_authors_md(self.authors)}

{self.make_shields_md()}
</div>

{self.abstract}
'''
        return content

    def append_md(self, mds: [MDClass, list[MDClass]]):
        if mds is None:
            return

        if not isinstance(mds, list):
            mds = [mds]

        for md in mds:
            self.content += f"<br>{md.get_md()}<br>"

    def make(self, rel_dir: Optional[str] = None):
        from source.path import root

        # 创建文件夹
        cur_dir: str = os.path.join(root, "test/papers")
        if rel_dir is not None:
            cur_dir = os.path.join(cur_dir, rel_dir)
        filename = f"{cur_dir}/{self.validate_title(self.title)}.md"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # 生成内容
        self.append_md(self.md_class)
        content = self.content

        # 写入文件
        with open(filename, "wb") as file:
            file.write(content.encode())

        print(f"完成文档 {os.path.relpath(filename)} 的创建")


if __name__ == "__main__":
    _abstract = " ".join(["It is very long and it is going to be very long." for i in range(10)])
    paper = Overview(
        arxiv_url="https://arxiv.org/abs/2103.12345",
        title="Title of the Paper",
        subjects="Subject1, Subject2",
        authors=["Author1", "Author2", "Author3"],
        first_date="01 Jun 2021",
        abstract="Abstract of the paper goes here. And this is a very long abstract. "
                 f"{_abstract}"
    )
    paper.make()
