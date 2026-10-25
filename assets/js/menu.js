/* Local menu demonstration: no checkout or owner-approved pricing. */
(() => {
  'use strict';
  const {esc,load,price,picture,imageAlt,read,write,categoryArt,business} = window.CC, data=load(), FAVE_KEY='cc_saved_items_v1';
  const $=id=>document.getElementById(id), grid=$('menu-grid'), rail=$('category-rail'), term=$('menu-search'), dialog=$('item-dialog');
  const state={category:'all',query:'',sort:'default',onlySaved:false,hidePrices:read('cc_hide_prices_v1')==='1'};
  let saved=new Set(), opener=null;
  try {const ids=JSON.parse(read(FAVE_KEY)); if(Array.isArray(ids)) saved=new Set(ids.filter(id=>data.items.some(i=>i.id===id)));} catch {}
  const categoryLabel=id=>data.categories.find(c=>c.id===id)?.label||id;
  const edited=i=>window.CREAMCRUST_CATALOG.items.find(x=>x.id===i.id)?.price!==i.price;
  function filtered(){
    const q=state.query.trim().toLocaleLowerCase();
    const list=data.items.filter(i=>(state.category==='all'||i.category===state.category)&&(!state.onlySaved||saved.has(i.id))&&(!q||[i.name,categoryLabel(i.category),i.description].some(v=>String(v||'').toLocaleLowerCase().includes(q))));
    if(state.sort==='price-asc') list.sort((a,b)=>(a.price??Infinity)-(b.price??Infinity));
    if(state.sort==='price-desc') list.sort((a,b)=>(b.price??-1)-(a.price??-1));
    if(state.sort==='name') list.sort((a,b)=>a.name.localeCompare(b.name));
    return list;
  }
  function card(i){
    const art=picture(i).endsWith('.svg');
    return `<article class="product-card"><div class="product-art"><button class="photo-open" type="button" data-open="${esc(i.id)}" aria-label="View ${esc(i.name)} details"><img src="${picture(i).replace('.webp','-small.webp')}" data-fallback="${categoryArt(i.category)}" alt="${esc(imageAlt(i))}" width="320" height="320" loading="lazy"><span class="photo-label">${art?'Category art':'Illustrative'}</span></button><button type="button" class="heart" data-heart="${esc(i.id)}" aria-label="${saved.has(i.id)?'Unsave':'Save'} ${esc(i.name)}" aria-pressed="${saved.has(i.id)}">${saved.has(i.id)?'♥':'♡'}</button></div><div class="product-body"><p class="product-cat">${esc(categoryLabel(i.category))}</p><h3 class="product-title">${esc(i.name)}</h3>${i.available===false?'<p class="availability">Unavailable in local preview</p>':''}<div class="product-footer"><span class="product-price ${state.hidePrices?'is-hidden':''}">${state.hidePrices?'Price pending approval':price(i.price)}<small>${state.hidePrices?'Price hidden for this preview':edited(i)?'Local demo price*':'Unverified public price*'}</small></span><button class="details-button" type="button" data-open="${esc(i.id)}" aria-label="Details for ${esc(i.name)}">Details ↗</button></div></div></article>`;
  }
  function render(){
    const list=filtered(); grid.innerHTML=list.map(card).join(''); grid.hidden=!list.length; $('empty-state').hidden=!!list.length;
    $('result-title').textContent=state.onlySaved?'Your saved selection':state.category==='all'?'The menu edit':categoryLabel(state.category);
    $('result-count').textContent=list.length+(list.length===1?' item':' items'); $('fave-count').textContent=saved.size;
    $('faves-toggle').classList.toggle('active',state.onlySaved); $('faves-toggle').setAttribute('aria-pressed',String(state.onlySaved)); $('clear-search').hidden=!state.query;
    $('price-toggle').textContent=state.hidePrices?'Show prices':'Hide prices';$('price-toggle').setAttribute('aria-pressed',String(state.hidePrices));
    rail.querySelectorAll('[data-cat]').forEach(b=>{const active=b.dataset.cat===state.category;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
  }
  function updateURL(push=false){
    const url=new URL(location.href);url.searchParams.delete('item');
    for(const [key,value] of [['q',state.query],['sort',state.sort==='default'?'':state.sort],['saved',state.onlySaved?'1':'']]) value?url.searchParams.set(key,value):url.searchParams.delete(key);
    state.hidePrices?url.searchParams.set('prices','hidden'):url.searchParams.delete('prices');
    url.hash=state.category==='all'?'':'category-'+state.category;history[push?'pushState':'replaceState']({},'',url);
  }
  function readURL(){
    const url=new URL(location.href);let hash='';try{hash=decodeURIComponent(url.hash.slice(1));}catch{}
    const id=hash.startsWith('category-')?hash.slice(9):'';state.category=data.categories.some(c=>c.id===id)?id:'all';
    state.query=url.searchParams.get('q')||'';state.sort=['price-asc','price-desc','name'].includes(url.searchParams.get('sort'))?url.searchParams.get('sort'):'default';state.onlySaved=url.searchParams.get('saved')==='1';
    state.hidePrices=url.searchParams.has('prices')?url.searchParams.get('prices')==='hidden':read('cc_hide_prices_v1')==='1';
    term.value=state.query;$('menu-sort').value=state.sort;render();
    requestAnimationFrame(()=>revealCategory(state.category));
  }
  function revealCategory(id){
    const chip=rail.querySelector(`[data-cat="${CSS.escape(id)}"]`);if(!chip)return;
    // Scroll only the rail; scrollIntoView can unexpectedly move the whole page.
    const start=chip.offsetLeft-rail.offsetLeft,end=start+chip.offsetWidth;
    if(start<rail.scrollLeft+6)rail.scrollLeft=Math.max(0,start-6);
    else if(end>rail.scrollLeft+rail.clientWidth-6)rail.scrollLeft=end-rail.clientWidth+6;
    updateRail();
  }
  function updateRail(){
    const max=Math.max(0,rail.scrollWidth-rail.clientWidth);
    $('category-prev').disabled=rail.scrollLeft<2;
    $('category-next').disabled=rail.scrollLeft>=max-2;
  }
  function showItem(id,trigger){
    const i=data.items.find(x=>x.id===id);if(!i)return;opener=trigger||grid.querySelector(`[data-open="${CSS.escape(id)}"]`);
    $('item-dialog-content').innerHTML=`<div class="modal-layout"><div class="modal-photo"><img class="${picture(i).endsWith('.svg')?'category-art':''}" src="${picture(i).replace('.webp','-medium.webp')}" data-fallback="${categoryArt(i.category)}" alt="${esc(imageAlt(i))}" width="550" height="650"></div><div class="modal-copy"><p class="modal-overline">${esc(categoryLabel(i.category))} · Menu preview</p><h2 id="item-title">${esc(i.name)}</h2><div class="modal-price ${state.hidePrices?'is-hidden':''}">${state.hidePrices?'Price pending approval':price(i.price)+'*'}</div><p class="modal-clarity">${esc(i.description||'A public-listing observation. Ingredients, variations, allergens and current availability remain unverified.')}</p><p class="availability">${i.available===false?'Unavailable in this local demonstration.':'Availability has not been confirmed by the café.'}</p><hr class="modal-divider"><div class="modal-actions"><a href="${esc(business.links.swiggy)}" target="_blank" rel="noopener noreferrer">View public Swiggy listing <span>↗</span></a><a href="${esc(business.links.maps)}" target="_blank" rel="noopener noreferrer">View Maps search <span>↗</span></a></div><p class="modal-small">${edited(i)?'Locally edited demonstration price.':esc(business.menu.priceContext)+'. Snapshot: '+esc(business.menu.sourceDate)+'.'} Dine-in prices unverified. Category image is illustrative. This demo accepts no orders.</p></div></div>`;
    document.body.style.overflow='hidden';dialog.showModal();$('item-close').focus();
  }
  if(read(window.CC.KEY))$('storage-status').textContent='Local demonstration catalogue active in this browser. These edits are not published or owner approved.';
  $('all-count').textContent=data.items.length;
  rail.insertAdjacentHTML('beforeend',data.categories.map(c=>`<button type="button" class="cat-chip" data-cat="${esc(c.id)}" aria-pressed="false">${esc(c.label)} <span>${data.items.filter(i=>i.category===c.id).length}</span></button>`).join(''));
  rail.addEventListener('click',e=>{const b=e.target.closest('[data-cat]');if(!b)return;state.category=b.dataset.cat;state.onlySaved=false;updateURL(true);render();revealCategory(state.category);});
  rail.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)||!e.target.matches('[data-cat]'))return;
    e.preventDefault();const chips=[...rail.querySelectorAll('[data-cat]')],index=chips.indexOf(e.target);
    const next=e.key==='Home'?0:e.key==='End'?chips.length-1:Math.max(0,Math.min(chips.length-1,index+(e.key==='ArrowRight'?1:-1)));
    revealCategory(chips[next].dataset.cat);chips[next].focus({preventScroll:true});
  });
  term.addEventListener('input',()=>{state.query=term.value;updateURL();render();});
  $('clear-search').addEventListener('click',()=>{state.query='';term.value='';updateURL();render();term.focus();});
  $('menu-sort').addEventListener('change',e=>{state.sort=e.target.value;updateURL();render();});
  $('faves-toggle').addEventListener('click',()=>{state.onlySaved=!state.onlySaved;updateURL();render();});
  $('price-toggle').addEventListener('click',()=>{state.hidePrices=!state.hidePrices;write('cc_hide_prices_v1',state.hidePrices?'1':'0');updateURL();render();});
  $('category-next').addEventListener('click',()=>rail.scrollBy({left:Math.max(160,rail.clientWidth*.7),behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'}));
  $('category-prev').addEventListener('click',()=>rail.scrollBy({left:-Math.max(160,rail.clientWidth*.7),behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'}));
  rail.addEventListener('scroll',updateRail,{passive:true});
  const controls=$('menu-controls');
  const resizeControls=()=>{document.documentElement.style.setProperty('--menu-controls-height',controls.offsetHeight+'px');updateRail();};
  document.documentElement.classList.add('menu-document');
  new ResizeObserver(resizeControls).observe(controls);
  // Font swaps and viewport changes can move the selected chip after initial load.
  const resizeCategories=new ResizeObserver(()=>revealCategory(state.category));
  resizeCategories.observe(rail);
  rail.querySelectorAll('[data-cat]').forEach(chip=>resizeCategories.observe(chip));
  $('reset-filters').addEventListener('click',()=>{Object.assign(state,{category:'all',query:'',sort:'default',onlySaved:false});term.value='';$('menu-sort').value='default';updateURL();render();term.focus();});
  grid.addEventListener('click',e=>{
    const heart=e.target.closest('[data-heart]');if(heart){const id=heart.dataset.heart;saved.has(id)?saved.delete(id):saved.add(id);if(!write(FAVE_KEY,JSON.stringify([...saved])))$('storage-status').textContent='Browser storage is unavailable. Saved items last for this visit only.';render();(grid.querySelector(`[data-heart="${CSS.escape(id)}"]`)||$('faves-toggle')).focus();return;}
    const trigger=e.target.closest('[data-open]');if(trigger)showItem(trigger.dataset.open,trigger);
  });
  $('item-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
  dialog.addEventListener('close',()=>{
    if(dialog.open)return;
    document.body.style.overflow='';
    const active=document.activeElement;
    // Native focus restoration may finish before this queued event. Do not
    // steal focus from a subsequent action such as saving a menu item.
    if(active===document.body||dialog.contains(active)||!active?.isConnected){
      if(opener?.isConnected)opener.focus();else term.focus();
    }
    if(new URL(location.href).searchParams.has('item'))updateURL();
  });
  window.addEventListener('popstate',readURL);window.addEventListener('hashchange',readURL);readURL();
  document.fonts.ready.then(()=>revealCategory(state.category));
  const item=new URL(location.href).searchParams.get('item');if(item)showItem(item);
})();
