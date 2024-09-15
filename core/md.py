from abc import ABC, abstractmethod


class MDClass(ABC):
    """
    生成 MD 文本的抽象类
    """
    def __init__(self):
        pass

    @abstractmethod
    def get_md(self):
        pass

