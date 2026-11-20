begin;

create schema if not exists extensions;
create extension if not exists pgroonga with schema extensions;
set local search_path = pg_catalog, extensions, public;

create table public.articles (
  id text primary key,
  type text not null check (type in ('answer', 'article', 'pin')),
  title text not null,
  body text not null,
  body_html text not null,
  published_at timestamptz not null,
  url text not null
);

create index articles_full_text_idx
  on public.articles using pgroonga ((array[title, body]));

alter table public.articles enable row level security;
grant usage on schema extensions to anon, authenticated;
revoke all on public.articles from public, anon, authenticated;
grant select on public.articles to anon, authenticated;
create policy archive_public_read on public.articles
  for select to anon, authenticated using (true);

create function public.search_articles("query" text, "limit" integer default 10)
returns table (
  id text,
  type text,
  title text,
  published_at timestamptz,
  url text,
  snippet text,
  score integer
)
language sql
stable
security invoker
set search_path = pg_catalog, extensions, public
as $$
  with terms as materialized (
    select distinct term
    from regexp_split_to_table(
      case when char_length($1) <= 200 then $1 end, '[[:space:]　]+'
    ) as split(term)
    where term <> ''
  ),
  ranked as (
    select a.*, relevance.score
    from public.articles as a
    cross join lateral (
      select sum(case when a.title &@ term then 5 else 1 end)::integer as score
      from terms
    ) as relevance
    where array[a.title, a.body] &@~ (
      select string_agg('"' || pgroonga_query_escape(term) || '"', ' ' order by term) from terms
    )
    order by relevance.score desc, a.published_at desc, a.id
    limit greatest(0, least(coalesce($2, 10), 50))
  )
  select r.id, r.type, r.title, r.published_at, r.url,
    case
      when r.body = '' then left(r.title, 200)
      else substring(r.body from greatest(coalesce(match.first_position, 1) - 40, 1) for 200)
    end,
    r.score
  from ranked as r
  cross join lateral (
    select min(nullif(strpos(lower(r.body), lower(term)), 0)) as first_position
    from terms
  ) as match
  order by r.score desc, r.published_at desc, r.id
$$;

revoke all on function public.search_articles(text, integer) from public, anon, authenticated;
grant execute on function public.search_articles(text, integer) to anon, authenticated;

notify pgrst, 'reload schema';
commit;
