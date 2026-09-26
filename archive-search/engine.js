(function (root) {
  'use strict';
  const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const terms = query => [...new Set(query.trim().toLowerCase().split(/\s+/).filter(Boolean))];
  function prepare(documents) {
    return documents.map(doc => ({...doc, titleLower:doc.title.toLowerCase(), bodyLower:doc.body.toLowerCase()}));
  }
  function search(documents, query, type, sort) {
    const words = terms(query);
    return documents.filter(doc => (type === 'all' || type === doc.type) && words.every(word => doc.titleLower.includes(word) || doc.bodyLower.includes(word)))
      .map(doc => ({doc, score:words.reduce((score, word) => score + (doc.titleLower.includes(word) ? 10 : 0) + (doc.bodyLower.includes(word) ? 1 : 0), 0)}))
      .sort((a,b) => (sort === 'date' ? 0 : b.score-a.score) || b.doc.date.localeCompare(a.doc.date) || a.doc.url.localeCompare(b.doc.url))
      .map(result => result.doc);
  }
  function highlight(text, query) {
    const words = terms(query).sort((a,b) => b.length-a.length);
    if (!words.length) return escape(text);
    const pattern = new RegExp(words.map(word => word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|'),'gi');
    let end = 0, html = '';
    for (const match of text.matchAll(pattern)) {
      html += escape(text.slice(end,match.index)) + '<mark>' + escape(match[0]) + '</mark>';
      end = match.index + match[0].length;
    }
    return html + escape(text.slice(end));
  }
  function snippet(doc, query) {
    const positions = terms(query).map(word => doc.bodyLower.indexOf(word)).filter(index => index >= 0);
    const start = positions.length ? Math.max(0, Math.min(...positions)-45) : 0;
    return (start ? '…' : '') + doc.body.slice(start,start+200) + (doc.body.length > start+200 ? '…' : '');
  }
  const api = {escape, terms, prepare, search, highlight, snippet};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.ArchiveSearch = api;
})(typeof window !== 'undefined' ? window : globalThis);
