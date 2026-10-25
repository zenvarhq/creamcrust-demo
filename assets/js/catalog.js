/* Shared catalogue boundary for the local demonstration. No server writes. */
(() => {
  'use strict';
  const siteRoot = new URL('../../', document.currentScript.src);
  const asset = path => new URL(path.replace(/^\//, ''), siteRoot).href;
  const KEY = 'cc_catalog_override_v1';
  const clone = value => JSON.parse(JSON.stringify(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const valid = data => {
    if (!data || !Array.isArray(data.items) || !Array.isArray(data.categories) || !data.items.length || !data.categories.length || data.items.length > 2000) return false;
    const categories = new Set(data.categories.map(c => c.id));
    if(categories.size!==data.categories.length)return false;
    const ids = new Set();
    return data.categories.every(c => typeof c.id === 'string' && typeof c.label === 'string') && data.items.every(i => {
      if (!i || typeof i.id !== 'string' || ids.has(i.id) || typeof i.name !== 'string' || !categories.has(i.category)) return false;
      ids.add(i.id);
      return i.price === null || (typeof i.price === 'number' && Number.isFinite(i.price) && i.price >= 0 && i.price <= 1000000);
    });
  };
  const read = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const write = (key, value) => { try { localStorage.setItem(key, value); return true; } catch { return false; } };
  const sanitize = value => {
    const data=clone(value);data.approved_for_live_use=false;
    data.items.forEach(i=>i.verified_by_owner=false);
    return data;
  };
  const load = () => {
    try { const data = JSON.parse(read(KEY)); if (valid(data)) return sanitize(data); } catch { /* Use source catalogue. */ }
    return sanitize(window.CREAMCRUST_CATALOG);
  };
  const price = value => value == null ? 'Price pending' : '₹' + Number(value).toLocaleString('en-IN');
  const photoNames = {'fried-chicken':'nc-chicken','chicken-snacks':'nc-chicken',waffles:'nc-waffle',sundaes:'nc-icecream','ice-cream':'nc-icecream',sandwiches:'nc-burger'};
  const categoryArt = category => asset('assets/art/category-'+(['waffles','sundaes','ice-cream'].includes(category)?'sweet':['shakes','falooda','beverages'].includes(category)?'sip':'crisp')+'.svg');
  const picture = item => {
    return photoNames[item.category]?asset('assets/images/'+photoNames[item.category]+'.webp'):categoryArt(item.category);
  };
  window.CC = {KEY, clone, esc, valid, read, write, load, price, picture,categoryArt,sanitize,business:window.CREAMCRUST_BUSINESS};
})();
