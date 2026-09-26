"""Rebuild checked-in search data from the extracted HTML pages (standard library only)."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = None
        self.has_article = False
        self.ignored = 0
        self.parts = {'title': [], 'time': [], 'article': []}

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignored += 1
        if tag == 'article':
            self.has_article = True
        if tag in self.parts:
            self.active = tag
        if tag in ('p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'blockquote') and self.active == 'article':
            self.parts['article'].append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored = max(0, self.ignored - 1)
        if tag == self.active:
            self.active = None
        elif tag in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'blockquote') and self.active == 'article':
            self.parts['article'].append('\n')

    def handle_data(self, data):
        if self.active and not self.ignored:
            self.parts[self.active].append(data)

    def text(self, field):
        return re.sub(r'\s+', ' ', ''.join(self.parts[field])).strip()


def collect(root=ROOT):
    documents = []
    for kind in ('answer', 'article'):
        for path in sorted((root / kind).glob('*/index.html')):
            if not path.parent.name.isdecimal():
                continue
            parser = ArticleText()
            parser.feed(path.read_text(encoding='utf-8'))
            doc = dict(title=parser.text('title'), body=parser.text('article'), date=parser.text('time'),
                       type=kind, url=path.relative_to(root).as_posix())
            if not parser.has_article or not doc['title'] or not doc['date']:
                raise ValueError(f'Missing title, article container or date: {path}')
            documents.append(doc)
    if not documents:
        raise ValueError('No article pages found')
    return documents


def build(root=ROOT):
    documents = collect(root)
    (root / 'archive-search/data.js').write_text('window.ARCHIVE_DOCS=' + json.dumps(documents, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    homepage = root / 'index.html'
    counts = {kind: sum(doc['type'] == kind for doc in documents) for kind in ('answer', 'article')}
    stats = f'<p id="archive-stats">{counts["answer"]:,} 个回答 · {counts["article"]:,} 篇文章<br>使用真实归档正文搜索</p>'
    updated, replacements = re.subn(r'<p id="archive-stats">.*?</p>', lambda _: stats, homepage.read_text(encoding='utf-8'), flags=re.S)
    if replacements != 1:
        raise ValueError('Homepage must have exactly one archive-stats element')
    homepage.write_text(updated, encoding='utf-8')
    print(f'Indexed {len(documents)} complete articles')


if __name__ == '__main__':
    build()
