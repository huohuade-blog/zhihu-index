(() => {
  'use strict';
  const engine = window.ArchiveSearch;
  const input = document.querySelector('#query');
  const results = document.querySelector('#results');
  const status = document.querySelector('#status');
  const pagination = document.querySelector('#pagination');
  const retry = document.querySelector('#retry');
  const pageSize = 20;
  let documents = null;
  let loading = false;
  let state;
  function readURL() {
    const params = new URLSearchParams(location.search);
    const page = Number(params.get('page'));
    state = {query:(params.get('q') || '').slice(0,300), type:['answer','article'].includes(params.get('type')) ? params.get('type') : 'all', sort:params.get('sort') === 'date' ? 'date' : 'relevance', page:Number.isSafeInteger(page) && page > 0 ? page : 1};
    input.value = state.query;
    document.querySelector('#sort').value = state.sort;
  }
  function writeURL(replace = false) {
    const url = new URL(location.href);
    url.search = '';
    if (state.query) url.searchParams.set('q',state.query);
    if (state.type !== 'all') url.searchParams.set('type',state.type);
    if (state.sort !== 'relevance') url.searchParams.set('sort',state.sort);
    if (state.page > 1) url.searchParams.set('page',state.page);
    if (url.href !== location.href) history[replace ? 'replaceState' : 'pushState'](null,'',url);
  }
  function render() {
    document.querySelectorAll('[data-type]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.type === state.type)));
    if (!documents) return;
    const matches = engine.search(documents,state.query,state.type,state.sort);
    const pages = Math.max(1,Math.ceil(matches.length/pageSize));
    state.page = Math.min(state.page,pages);
    writeURL(true);
    status.textContent = `${state.query ? '“'+state.query+'” · ' : ''}找到 ${matches.length.toLocaleString()} 篇 · 搜索范围包含标题与完整正文`;
    const start = (state.page-1)*pageSize;
    results.innerHTML = matches.length ? matches.slice(start,start+pageSize).map(doc => `<article class="result"><div class="meta"><span class="badge">${doc.type === 'answer' ? '回答' : '文章'}</span>${engine.escape(doc.date.slice(0,10))} · ${doc.body.length.toLocaleString()} 字</div><h2><a href="${engine.escape(doc.url)}">${engine.highlight(doc.title,state.query)}</a></h2><p>${doc.body ? engine.highlight(engine.snippet(doc,state.query),state.query) : '此归档正文为图片或媒体，可打开查看。'}</p></article>`).join('') : '<p class="empty">没有找到匹配的正文。试试更短的词，或切换到“全部”。</p>';
    pagination.innerHTML = pages > 1 ? `<button data-page="${state.page-1}" ${state.page === 1 ? 'disabled' : ''}>上一页</button><span>${state.page} / ${pages}</span><button data-page="${state.page+1}" ${state.page === pages ? 'disabled' : ''}>下一页</button>` : '';
    results.setAttribute('aria-busy','false');
  }
  function load() {
    if (loading) return;
    loading = true;
    retry.hidden = true;
    status.textContent = '正在加载全文索引…';
    results.setAttribute('aria-busy','true');
    const script = document.createElement('script');
    script.src = 'archive-search/data.js';
    script.onload = () => {
      loading = false;
      try {
        const raw = window.ARCHIVE_DOCS;
        if (!Array.isArray(raw) || raw.some(doc => !['title','body','date','url','type'].every(key => typeof doc[key] === 'string') || !/^(?:\.\/)?(?:\d+\.html|(?:answer|article)\/\d+\/index\.html)$/.test(doc.url))) throw Error('Invalid search data');
        documents = engine.prepare(raw);
        delete window.ARCHIVE_DOCS;
        render();
      } catch (_) { failed(); }
      script.remove();
    };
    script.onerror = () => {loading=false;script.remove();failed();};
    document.head.appendChild(script);
  }
  function failed() {
    status.textContent = '全文索引加载失败。请重试，或通过完整索引浏览正文。';
    results.setAttribute('aria-busy','false');
    retry.hidden = false;
  }
  function update() {
    state.query = input.value.trim().slice(0,300);
    input.value = state.query;
    state.page = 1;
    writeURL();
    render();
  }
  document.querySelector('form').addEventListener('submit',event => {event.preventDefault();update();});
  document.querySelector('#sort').addEventListener('change',event => {state.sort=event.target.value;update();});
  document.querySelectorAll('[data-type]').forEach(button => button.addEventListener('click',() => {state.type=button.dataset.type;update();}));
  document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click',() => {input.value=button.dataset.query;update();input.focus();}));
  pagination.addEventListener('click',event => {
    const button = event.target.closest('[data-page]');
    if (!button || button.disabled) return;
    state.page = Number(button.dataset.page);
    writeURL();render();input.focus();window.scrollTo({top:0,behavior:'auto'});
  });
  window.addEventListener('popstate',() => {readURL();render();});
  retry.addEventListener('click',load);
  readURL();load();
})();
