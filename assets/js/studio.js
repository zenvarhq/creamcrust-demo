/* Local-only demonstration. Export and save never publish changes. */
(() => {
  'use strict';
  const {KEY,load,clone,esc,valid,write}=window.CC;
  let data=load(),query='',invalid=false;
  const rows=document.getElementById('rows'),status=document.getElementById('status');
  const message=text=>status.textContent=text;
  function draw(){rows.innerHTML=data.items.filter(i=>i.name.toLowerCase().includes(query)).map(i=>`<tr data-id="${esc(i.id)}"><td><strong>${esc(i.name)}</strong></td><td>${esc(data.categories.find(c=>c.id===i.category)?.label||i.category)}</td><td><input type="number" min="0" max="1000000" step="1" data-field="price" value="${i.price??''}" aria-label="Price for ${esc(i.name)}"></td><td><select data-field="available" aria-label="Availability preview for ${esc(i.name)}"><option value="unknown" ${i.available==null?'selected':''}>Unconfirmed</option><option value="yes" ${i.available===true?'selected':''}>Available (demo)</option><option value="no" ${i.available===false?'selected':''}>Unavailable (demo)</option></select></td><td><input type="checkbox" data-field="verified_by_owner" disabled aria-label="Owner approval pending for ${esc(i.name)}"></td></tr>`).join('');}
  document.getElementById('studio-search').addEventListener('input',e=>{query=e.target.value.toLowerCase();draw();});
  rows.addEventListener('change',e=>{
    const item=data.items.find(i=>i.id===e.target.closest('tr[data-id]')?.dataset.id);if(!item)return;
    const field=e.target.dataset.field;
    if(field==='price'){
      const n=e.target.value===''?null:Number(e.target.value);
      if(n!==null&&(!Number.isFinite(n)||n<0||n>1000000||!Number.isInteger(n))){invalid=true;message('Enter a whole-rupee price from 0 to 1,000,000, or leave it blank.');e.target.setAttribute('aria-invalid','true');return;}
      item.price=n;e.target.removeAttribute('aria-invalid');
    }else if(field==='available')item.available=e.target.value==='unknown'?null:e.target.value==='yes';
    else if(field==='verified_by_owner')item.verified_by_owner=e.target.checked;
    invalid=!!rows.querySelector('[aria-invalid="true"]');
    message('Unsaved local change. Save to this browser to preview. Owner approval stays pending in this build.');
  });
  document.getElementById('save').addEventListener('click',()=>{
    if(invalid||!valid(data)){message('Fix invalid prices before saving.');return;}
    message(write(KEY,JSON.stringify(window.CC.sanitize(data)))?'Saved in this browser only. Open or refresh the menu and homepage to see changes.':'Browser storage is unavailable. Export JSON to retain these edits.');
  });
  document.getElementById('reset').addEventListener('click',()=>{
    if(!confirm('Reset local preview edits to the original public listing snapshot?'))return;
    try{localStorage.removeItem(KEY);}catch{message('Browser storage is unavailable.');return;}
    data=clone(window.CREAMCRUST_CATALOG);invalid=false;draw();message('Local preview edits reset.');
  });
  document.getElementById('export').addEventListener('click',()=>{
    if(invalid||!valid(data)){message('Fix invalid prices before exporting.');return;}
    const url=URL.createObjectURL(new Blob([JSON.stringify(window.CC.sanitize(data),null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='creamcrust-menu-edited.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('JSON exported. No information has been published.');
  });
  document.getElementById('import').addEventListener('change',async e=>{
    const file=e.target.files?.[0];if(!file)return;
    try{if(file.size>2000000)throw Error('File exceeds 2 MB');const next=JSON.parse(await file.text());if(!valid(next))throw Error('Invalid catalogue fields, categories, IDs or prices');data=window.CC.sanitize(next);invalid=false;draw();message('Imported locally. Review and save to this browser to apply.');}
    catch(error){message('Import failed: '+error.message);}
    e.target.value='';
  });
  draw();
})();
