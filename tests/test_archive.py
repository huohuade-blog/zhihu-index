import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_search import ArticleText, collect

class ArchiveTests(unittest.TestCase):
    def test_body_text_and_entities(self):
        parser = ArticleText()
        parser.feed('<title>A &amp; B</title><time>2020-01-01</time><article><p>芯片</p><p>大学 &lt;test&gt;</p><script>ignored()</script></article><footer>footer</footer>')
        self.assertEqual(parser.text('title'), 'A & B')
        self.assertEqual(parser.text('article'), '芯片 大学 <test>')
    def test_archive_counts_and_paths(self):
        root = Path(__file__).resolve().parents[1]
        docs = collect(root)
        self.assertEqual(len(docs), 1178)
        self.assertEqual(sum(d['type'] == 'article' for d in docs), 70)
        for doc in docs:
            self.assertTrue((root / doc['url']).is_file())
        catalog = (root / 'catalog.html').read_text(encoding='utf-8')
        self.assertEqual(catalog.count('title="原页已失效，仅保留索引"'), 8)
        self.assertEqual(catalog.count('/index.html"'),1178)

if __name__ == '__main__':
    unittest.main()
