import math

from bs4 import BeautifulSoup

from core.md import MDClass


class FigureSoup(MDClass):
    single_image_width = dict(min=0.4, max=0.9)  # 单张图片的宽度占比最小最大值

    def __init__(self, html_soup: BeautifulSoup):
        super().__init__()
        self.html_soup = html_soup

    @staticmethod
    def ratio_to_width(width_height_ratio: float):
        """
        根据宽高比计算图片在 md 文档中占的总的宽度
        Args:
            width_height_ratio: 图片宽高比
        """
        _min = FigureSoup.single_image_width['min']
        _max = FigureSoup.single_image_width['max']
        return _min + (_max - _min) * (1 - 2 / math.pi * math.atan(1 / width_height_ratio))

    @staticmethod
    def adjust_image(html_soup: BeautifulSoup):
        images_html = html_soup.findAll("img")
        num_images = len(images_html)
        if num_images == 0:
            return False

        total_width = FigureSoup.ratio_to_width(float(images_html[0].get("width")) / float(images_html[0].get("height")))
        for image_html in images_html:
            image_html.attrs["width"] = f"{total_width * 100:.2f}%"
            if "height" in image_html.attrs:
                del image_html.attrs["height"]
            image_html["style"] = f"border-radius: 0.3125em; box-shadow: 0 2px 10px 0 {MDClass.shadow_color}"

        return True

    @staticmethod
    def adjust_caption(html_soup: BeautifulSoup):
        captions_html = html_soup.findAll("figcaption")
        for caption_html in captions_html:
            caption_html["style"] = "color: #999; padding: 2px; font-size: 0.8em;"

        return True

    def get_md(self):
        success = True
        success &= FigureSoup.adjust_image(self.html_soup)
        success &= FigureSoup.adjust_caption(self.html_soup)
        return f'''
<center>
{self.html_soup}
</center>
''' if success else ""
