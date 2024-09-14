<div align="center">
<h1>Reference Editor</h1>

<a href="https://github.com/Yangzhichen763/ReferenceEditor"><img src='https://img.shields.io/badge/code-Reference Editor-darkgreen' alt='Project Page'></a>
</div>

这个项目目前仅实现了简单的功能，其中包括
- 爬取文章作者：通过单篇或多篇文章名，爬取文章作者（可选缩写作者名）
- 生成文章 md 文档：输入论文的 arXiv 链接，爬取文章摘要并生成 md 文档
- 敬请期待

# Preparation
克隆本仓库到本地
```bash
git clone https://github.com/Yangzhichen763/ReferenceEditor.git
cd ReferenceEditor
```
安装依赖
```bash
pip install -r requirements.txt
```
---

# Usage
## 爬取文章作者
使用方法非常简单，如下：
### 爬取单篇文章的作者
``` python
from core import reference_do

# 文章标题，或者能在搜索引擎中搜索到的关键词
title = "Attention is all you need"

# 检索文章作者
reference_do.search_authors_by_title(title)
```
贴心小卫士:
- 可以通过更改 `reference_do.search_engine` 来切换搜索引擎
- 可以通过修改 `reference_do.num_pages` 来调整搜索结果数
### 爬取多篇文章的作者
``` python
from core import reference_do

# 文章标题列表，或者能在搜索引擎中搜索到的关键词列表
titles = ["Attention is all you need", "Latent Diffusion Model"]

# 检索文章作者
reference_do.search_authors_by_titles(titles)
```

## 生成文章 md 文档
使用方法也非常简单，如下：
``` python
from core.arxiv_crawler import parse_arxiv_html
from core.html_requester import get_page_content

# 要生成的文章 arXiv 链接
url = "https://arxiv.org/abs/1706.03762"

# 爬取文章摘要并生成 md 文档
html_content = get_page_content(url)
overview = parse_arxiv_html(html_content, url)
overview.make()
```

---

# 敬请期待
更多功能正在开发中，敬请期待！