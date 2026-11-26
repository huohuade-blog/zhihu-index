# 霍华德的知乎归档

网站：https://huohuade-blog.github.io/zhihu-index/

首页使用搜索列表，支持标题与正文搜索、多关键词（空格分隔且全部匹配）、命中摘要高亮、回答/文章/想法筛选、相关度/时间排序、分页和可分享的搜索链接。搜索完全在浏览器执行。

- `answer/<编号>/index.html`、`article/<编号>/index.html`、`pin/<编号>/index.html`：2,908 条正文 HTML，直接存入仓库。
- `answer/<编号>/answer.json`：知乎账号 `rwkv-56` 的 1,008 条回答，含正文 HTML、纯文本和来源信息。
- `article/<编号>/article.json`：知乎账号 `rwkv-56` 的 38 篇文章，含正文 HTML、纯文本和来源信息。
- `pin/<编号>/pin.json`：知乎账号 `rwkv-56` 的 684 条想法，含正文 HTML、纯文本、来源和附件信息。
- `catalog.html`：2,916 条记录及其赞同数和日期。已归档记录链接到本站正文，8 条原页不存在记录保留外链。
- `archive-search/`：搜索脚本、样式与生成的全文数据。

继续使用现有 GitHub Pages 发布设置；所有站点文件直接位于仓库，无 ZIP 解压或服务器依赖，也无需新增部署 workflow。

修改正文后运行 `python tools/build_search.py` 并一并提交更新后的 `archive-search/data.js`。此命令仅依赖 Python 标准库。新增或删除归档条目时，同时更新 `catalog.html`。

验证：`python -m unittest discover -s tests`、`node tests/search.cjs`。本地预览：在仓库目录运行 `python -m http.server 8000`，打开 http://localhost:8000/。

正文中的外链图片和视频仍由原站提供，可能失效；此次归档为正文 HTML，未下载外链媒体。

部分正文仅含图片或媒体，没有可搜索文字；这些记录仍可按标题检索。

## Supabase 归档 API

GitHub 仓库里的正文 HTML 是归档源。Supabase 保存可重建的只读搜索副本。每条记录的 ID 由类型和知乎编号组成，例如 `article:2030371913365767790`。全文提供纯文本 `body` 和原始归档片段 `body_html`，后者保留段落、链接和媒体引用。

### 首次部署与同步

1. 在用于归档的 Supabase 项目启用 Data API，在 SQL Editor 执行 [归档迁移](supabase/migrations/20261120000000_archive_search.sql)。迁移创建 `public.articles`、PGroonga 全文索引和只读 RPC。
2. 安装 `psql`。从 Supabase 的 **Connect** 对话框复制 Direct connection 或 Session pooler 的连接参数（仅支持 IPv4 的网络使用 Session pooler）。在当前终端设置 `PGHOST`、`PGPORT`、`PGUSER`、`PGDATABASE` 和 `PGSSLMODE=require`，通过 libpq 密码文件提供数据库密码。密码文件放在仓库之外。
3. 从完整的仓库检出运行 `python tools/sync_supabase.py`。脚本在同一个事务里插入新增记录、更新有变更的记录并移除已离开源归档的记录。更新 GitHub 归档后重跑同一命令即可。用 `python tools/sync_supabase.py --check` 可单独检查本地数据。

首次也可以在空表上使用 Table Editor 的 CSV 导入。运行 `python tools/sync_supabase.py --csv <仓库外的新文件路径>`，然后在 `articles` 表中选择 **Insert → Import Data from CSV**。初次导入后，核对表内应有 2,908 条记录，其中 6 条的纯文本为空，但仍有 HTML。

部署文档见 [PGroonga](https://supabase.com/docs/guides/database/extensions/pgroonga)、[数据库连接](https://supabase.com/docs/guides/database/connecting-to-postgres)、[libpq 密码文件](https://www.postgresql.org/docs/current/libpq-pgpass.html)和 [CSV 导入](https://supabase.com/docs/guides/database/import-data)。

### Agent 调用

当前项目的 Data API URL 为 `https://prriepunpvlpgrhhgcte.supabase.co`。用它设置 `SUPABASE_URL`，用项目的 publishable key 设置 `SUPABASE_PUBLISHABLE_KEY`。以下示例使用 Bash。匿名调用可搜索和读取归档，写入需要数据库权限。

```bash
curl --fail-with-body "$SUPABASE_URL/rest/v1/rpc/search_articles" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"query":"人工智能","limit":10}'

curl --fail-with-body --get "$SUPABASE_URL/rest/v1/articles" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  --data-urlencode 'id=eq.article:2030371913365767790' \
  --data-urlencode 'select=id,type,title,body,body_html,published_at,url'
```

`search_articles` 返回 `id`、`type`、`title`、`published_at`、`url`、`snippet` 和 `score`。用空格分隔多个关键词时，每个词都须出现在标题或正文中。每个命中标题的词计 5 分，其他词计 1 分，同分时优先返回较新的记录。摘要最多 200 个字符，结果最多 50 条，查询最多 200 个字符。用搜索结果里的 `id` 读取全文，REST 查询返回一个数组，未找到时返回空数组。
