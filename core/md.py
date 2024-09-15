from abc import ABC, abstractmethod


class MDClass(ABC):
    shadow_color = "#5554"

    """
    生成 MD 文本的抽象类
    """
    def __init__(self):
        pass

    @abstractmethod
    def get_md(self):
        pass

    @property
    def md(self):
        return self.get_md()

