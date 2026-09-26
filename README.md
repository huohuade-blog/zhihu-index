# 霍华德的知乎归档

网站：https://huohuade-blog.github.io/zhihu-index/

首页使用搜索列表，支持标题与正文搜索、多关键词（空格分隔且全部匹配）、命中摘要高亮、回答/文章筛选、相关度/时间排序、分页和可分享的搜索链接。搜索完全在浏览器执行。

- `answer/<编号>/index.html`、`article/<编号>/index.html`：1,178 篇解压后的正文 HTML，直接存入仓库。
- `catalog.html`：保留原索引的全部 1,186 条记录、赞同数和日期。已归档记录链接到本站正文，8 条原页不存在记录保留外链。
- `archive-search/`：搜索脚本、样式与生成的全文数据。

继续使用现有 GitHub Pages 发布设置；所有站点文件直接位于仓库，无 ZIP 解压或服务器依赖，也无需新增部署 workflow。

修改正文后运行 `python tools/build_search.py` 并一并提交更新后的 `archive-search/data.js`。此命令仅依赖 Python 标准库。新增或删除文章时，同时更新 `catalog.html`。

验证：`python -m unittest discover -s tests`、`node tests/search.cjs`。本地预览：在仓库目录运行 `python -m http.server 8000`，打开 http://localhost:8000/。

正文中的外链图片和视频仍由原站提供，可能失效；此次归档为正文 HTML，未下载外链媒体。

部分正文仅含图片或媒体，没有可搜索文字；这些记录仍可按标题检索。
