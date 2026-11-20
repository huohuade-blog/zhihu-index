"""Mirror the repository's archived HTML into Supabase with psql and libpq settings."""
import argparse
import csv
import os
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

from build_search import collect

BASE_URL = 'https://huohuade-blog.github.io/zhihu-index/'
COLUMNS = ('id', 'type', 'title', 'body', 'body_html', 'published_at', 'url')
COLUMN_LIST = ', '.join(COLUMNS)


def archive_rows():
    for doc in collect(include_html=True):
        path = doc['url'].split('/')
        published_at = datetime.fromisoformat(doc['date'])
        if published_at.utcoffset() is None:
            raise ValueError(f'Missing timezone in {doc["url"]}')
        yield (
            f'{doc["type"]}:{path[1]}', doc['type'], doc['title'], doc['body'],
            doc['body_html'], published_at.isoformat(), BASE_URL + doc['url'],
        )


def copy_field(value):
    if '\0' in value:
        raise ValueError('Archive field contains a NUL character')
    return value.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')


def sync(rows):
    if not os.environ.get('PGHOST'):
        raise SystemExit('Set PGHOST and other libpq connection settings before syncing.')
    data = ''.join('\t'.join(map(copy_field, row)) + '\n' for row in rows)
    script = f"""begin;
create temp table archive_snapshot (like public.articles) on commit drop;
copy archive_snapshot ({COLUMN_LIST}) from stdin;
{data}\\.
lock table public.articles in share row exclusive mode;
insert into public.articles as old ({COLUMN_LIST})
select {COLUMN_LIST} from archive_snapshot
on conflict (id) do update
set (type, title, body, body_html, published_at, url) =
    (excluded.type, excluded.title, excluded.body, excluded.body_html, excluded.published_at, excluded.url)
where (old.type, old.title, old.body, old.body_html, old.published_at, old.url)
      is distinct from
      (excluded.type, excluded.title, excluded.body, excluded.body_html, excluded.published_at, excluded.url);
delete from public.articles as a
where not exists (select 1 from archive_snapshot as s where s.id = a.id);
select type, count(*) from public.articles group by type order by type;
commit;
"""
    subprocess.run(
        ['psql', '-X', '-w', '-v', 'ON_ERROR_STOP=1', '-f', '-'],
        input=script.encode('utf-8'),
        env={**os.environ, 'PGCLIENTENCODING': 'UTF8'},
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Validate the local corpus without connecting.')
    mode.add_argument('--csv', type=Path, help='Export a CSV for a one-time dashboard import into an empty table.')
    args = parser.parse_args()
    rows = list(archive_rows())
    if len(rows) != len({row[0] for row in rows}):
        raise ValueError('Duplicate archive IDs')
    for row in rows:
        if any('\0' in field for field in row):
            raise ValueError(f'Archive record {row[0]} contains a NUL character')
    counts = Counter(row[1] for row in rows)
    print(f'{len(rows):,} records ({dict(counts)}), {sum(not row[3] for row in rows)} without plain text', flush=True)
    if args.csv:
        with args.csv.open('x', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(COLUMNS)
            writer.writerows(rows)
    elif not args.check:
        sync(rows)


if __name__ == '__main__':
    main()
