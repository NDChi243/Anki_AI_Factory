"""
Shared engines for Japanese cards.

Includes handwriting CSS/JS, word-building JS, Japanese character pools,
speed controls, and letter-gap helpers.
"""

# ═══════════════════════════════════════════════════════════
#  SHARED HANDWRITING CSS
# ═══════════════════════════════════════════════════════════
_HW_CSS = '''
.hw-wrap{padding:16px 20px 20px;}
.hw-prompt-area{text-align:center;min-height:80px;padding:12px;margin-bottom:12px;background:var(--ex-bg);border:1px solid var(--ex-border);border-radius:12px;}
.hw-prompt-audio{display:none;}
.hw-prompt-vocab{display:none;}
.hw-prompt-reading{display:none;}
.hw-prompt-audio audio{display:block;margin:8px auto;}
.hw-boxes{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:12px;}
.hw-box{position:relative;border:2px solid var(--border);border-radius:12px;padding:4px;background:var(--card-bg);transition:border-color .3s,box-shadow .3s;}
.hw-box.active{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft);}
.hw-char-guide{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:80px;font-weight:900;color:rgba(0,0,0,.06);pointer-events:none;z-index:0;opacity:.3;transition:opacity .3s;user-select:none;}
.card.nightMode .hw-char-guide{color:rgba(255,255,255,.06);}
.hw-box canvas{display:block;width:160px;height:160px;border-radius:8px;cursor:crosshair;position:relative;z-index:1;background:#fff;}
.card.nightMode .hw-box canvas{background:#1a1a22;}
.hw-nav{display:flex;gap:8px;justify-content:center;margin-bottom:12px;}
.hw-nav-btn{width:36px;height:36px;border:2px solid var(--border);border-radius:50%;background:var(--card-bg);color:var(--text);font-size:14px;font-weight:700;cursor:pointer;transition:all .2s;}
.hw-nav-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);}
.hw-btn-clear,.hw-btn-show{padding:8px 18px;border-radius:10px;font-weight:700;font-size:13px;cursor:pointer;border:none;margin:0 6px;}
.hw-btn-clear{background:var(--border);color:var(--text);}
.hw-btn-show{background:var(--accent2);color:#fff;}
.hw-actions{text-align:center;margin-top:8px;}
'''

# ═══════════════════════════════════════════════════════════
#  SHARED WORD-BUILDING JS ENGINE
# ═══════════════════════════════════════════════════════════
_WB_JS_BODY = (
    '(function(){'
    'var word=_wbWord,pool=_wbPool;'
    'var chars=Array.from(word);'
    'var extra=[];'
    'var need=Math.max(3,Math.ceil(chars.length*0.8));'
    'var p=pool.slice();'
    'for(var i=p.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=p[i];p[i]=p[j];p[j]=tmp;}'
    'for(var i=0;i<p.length&&extra.length<need;i++){'
    'if(chars.indexOf(p[i])<0&&extra.indexOf(p[i])<0)extra.push(p[i]);}'
    'var all=chars.concat(extra);'
    'for(var i=all.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=all[i];all[i]=all[j];all[j]=tmp;}'
    'var ans=document.getElementById("wb-ans"),bank=document.getElementById("wb-bank");'
    'function mk(c,idx){'
    'var t=document.createElement("div");'
    't.className="wb-tile";t.textContent=c;t.id="wbt"+idx;'
    't.setAttribute("draggable","true");'
    't.addEventListener("click",function(){if(this.parentNode===bank)ans.appendChild(this);else bank.appendChild(this);});'
    't.addEventListener("dragstart",function(e){e.dataTransfer.setData("text/plain",this.id);this.classList.add("wb-drag");window._wbEl=this;});'
    't.addEventListener("dragend",function(){this.classList.remove("wb-drag");window._wbEl=null;});'
    'return t;}'
    'all.forEach(function(c,i){bank.appendChild(mk(c,i));});'
    'function gpos(z,x){var ts=[].slice.call(z.querySelectorAll(".wb-tile:not(.wb-drag)"));for(var i=0;i<ts.length;i++){var r=ts[i].getBoundingClientRect();if(x<r.left+r.width/2)return ts[i];}return null;}'
    '[ans,bank].forEach(function(z){z.addEventListener("dragover",function(e){e.preventDefault();var d=window._wbEl;if(!d)return;var a=gpos(this,e.clientX);if(!a)this.appendChild(d);else this.insertBefore(a,d);});});'
    '})();'
    'window.wbCheck=function(){'
    'var w=_wbWord,ts=document.getElementById("wb-ans").querySelectorAll(".wb-tile"),a="";'
    '[].forEach.call(ts,function(t){a+=t.textContent;});'
    'var r=document.getElementById("wb-result");r.style.display="block";'
    'if(a===w){r.className="wb-result wb-ok";r.textContent="✅ Chính xác!";'
    '[].forEach.call(ts,function(t){t.className="wb-tile wb-ok";});}'
    'else{r.className="wb-result wb-err";r.textContent="❌ Chưa đúng! → "+w;'
    '[].forEach.call(ts,function(t){t.className="wb-tile wb-err";});}};'
    'window.wbClear=function(){'
    'var bank=document.getElementById("wb-bank"),ts=document.getElementById("wb-ans").querySelectorAll(".wb-tile");'
    '[].forEach.call(ts,function(t){t.className="wb-tile";bank.appendChild(t);});'
    'document.getElementById("wb-result").style.display="none";};'
)

# ═══════════════════════════════════════════════════════════
#  SHARED HANDWRITING JS ENGINE
# ═══════════════════════════════════════════════════════════
_HW_JS_BODY = (
    '(function(){'
    'var types=["audio","vocab","reading"];'
    'var pick=types[Math.floor(Math.random()*types.length)];'
    'var elAudio=document.getElementById("hw-p-audio");'
    'var elVocab=document.getElementById("hw-p-vocab");'
    'var elReading=document.getElementById("hw-p-reading");'
    'if(elAudio)elAudio.style.display=pick==="audio"?"block":"none";'
    'if(elVocab)elVocab.style.display=pick==="vocab"?"block":"none";'
    'if(elReading)elReading.style.display=pick==="reading"?"block":"none";'
    'if(pick==="audio"){var ae=document.getElementById("hw-audio-el");if(ae)setTimeout(function(){try{ae.play();}catch(e){}},500);}'
    'var word=_hwWord;'
    'var chars=Array.from(word);'
    'var total=chars.length;'
    'var current=0;'
    'function drawGrid(ctx,w,h){'
    'ctx.strokeStyle="#ddd";ctx.lineWidth=0.5;'
    'for(var i=0;i<=4;i++){ctx.beginPath();ctx.moveTo(i*w/4,0);ctx.lineTo(i*w/4,h);ctx.stroke();ctx.beginPath();ctx.moveTo(0,i*h/4);ctx.lineTo(w,i*h/4);ctx.stroke();}'
    'ctx.strokeStyle="#eee";ctx.lineWidth=0.3;'
    'ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(w,h);ctx.stroke();ctx.beginPath();ctx.moveTo(w,0);ctx.lineTo(0,h);ctx.stroke();}'
    'function setupCanvas(canvas,ci){'
    'var ctx=canvas.getContext("2d");var w=canvas.width,h=canvas.height;'
    'ctx.fillStyle="#fff";ctx.fillRect(0,0,w,h);drawGrid(ctx,w,h);'
    'var drawing=false,lx=0,ly=0;'
    'canvas.addEventListener("mousedown",function(e){'
    'var r=canvas.getBoundingClientRect();'
    'var sx=canvas.width/r.width,sy=canvas.height/r.height;'
    'lx=(e.clientX-r.left)*sx;ly=(e.clientY-r.top)*sy;drawing=true;});'
    'canvas.addEventListener("mousemove",function(e){'
    'if(!drawing)return;'
    'var r=canvas.getBoundingClientRect();'
    'var sx=canvas.width/r.width,sy=canvas.height/r.height;'
    'var x=(e.clientX-r.left)*sx,y=(e.clientY-r.top)*sy;'
    'ctx.beginPath();ctx.moveTo(lx,ly);ctx.lineTo(x,y);'
    'ctx.strokeStyle="#333";ctx.lineWidth=4;ctx.lineCap="round";ctx.lineJoin="round";ctx.stroke();'
    'lx=x;ly=y;});'
    'canvas.addEventListener("mouseup",function(){drawing=false;});'
    'canvas.addEventListener("mouseleave",function(){drawing=false;});}'
    'function createBoxes(){'
    'var container=document.getElementById("hw-boxes");'
    'var nav=document.getElementById("hw-nav");'
    'if(!container)return;container.innerHTML="";if(nav)nav.innerHTML="";'
    'chars.forEach(function(ch,i){'
    'var guide=document.createElement("div");guide.className="hw-char-guide";guide.textContent=ch;'
    'var canvas=document.createElement("canvas");canvas.width=240;canvas.height=240;canvas.dataset.index=i;'
    'var box=document.createElement("div");box.className="hw-box"+(i===0?" active":"");'
    'box.appendChild(guide);box.appendChild(canvas);container.appendChild(box);'
    'if(nav){var nb=document.createElement("button");nb.className="hw-nav-btn"+(i===0?" active":"");nb.textContent=i+1;'
    'nb.addEventListener("click",function(idx){return function(){switchTo(idx);};}(i));nav.appendChild(nb);}'
    'setupCanvas(canvas,i);});}'
    'function switchTo(idx){current=idx;'
    'document.querySelectorAll(".hw-box").forEach(function(b,i){b.className="hw-box"+(i===idx?" active":"");});'
    'document.querySelectorAll(".hw-nav-btn").forEach(function(b,i){b.className="hw-nav-btn"+(i===idx?" active":"");});}'
    'var clearBtn=document.getElementById("hw-clear");'
    'if(clearBtn)clearBtn.addEventListener("click",function(){'
    'var boxes=document.querySelectorAll(".hw-box");if(!boxes[current])return;'
    'var c=boxes[current].querySelector("canvas");if(!c)return;'
    'var ctx=c.getContext("2d");ctx.fillStyle="#fff";ctx.fillRect(0,0,c.width,c.height);'
    'drawGrid(ctx,c.width,c.height);});'
    'var showBtn=document.getElementById("hw-show-ref");'
    'if(showBtn)showBtn.addEventListener("click",function(){'
    'var gs=document.querySelectorAll(".hw-char-guide");'
    'var show=!gs.length||gs[0].style.opacity!=="1";'
    'gs.forEach(function(g){g.style.opacity=show?"1":"0.3";});});'
    'createBoxes();'
    '})();'
)

# ═══════════════════════════════════════════════════════════
#  CHARACTER POOLS — cho Word-Building game
# ═══════════════════════════════════════════════════════════
JA_WB_POOL = '["は","が","に","を","で","も","と","か","し","す","い","う","え","お","な","ら","み","て","つ","ね","の","ほ","ま","め","ゆ","よ","わ","ん","き","く","け","こ","さ","せ","そ","ち","ふ","へ","む","や","ず","ど","ば","じ","ぬ","れ","ろ"]'
ZH_WB_POOL = '["我","你","他","好","的","了","在","是","不","有","人","大","小","来","去","很","这","那","年","日","国","中","上","下","说","看","想","会","能","可","以","用","个","时","就","也","为","和","与","给","从","到","把","被","让","还","都","已","又","再"]'
KO_WB_POOL = '["나","는","을","가","이","하","아","어","에","서","도","의","와","과","로","으","기","를","다","고","지","면","해","수","야","네","내","그","있","것","없","때","한","못","잘","더","들","주","오","씩","마","보","무","들","따","처","부","비","새","위"]'
EN_WB_POOL = '["a","e","i","o","u","s","t","r","n","l","m","d","p","c","h","b","f","g","w","y","k","v","j","x","q","z"]'
DE_WB_POOL = '["a","e","i","o","u","s","t","r","n","l","m","d","p","c","h","b","f","g","w","y","k","v","j","x","q","z","ä","ö","ü","ß"]'

# Map pools theo ngôn ngữ
WB_POOLS = {
    "japanese": JA_WB_POOL,
    "chinese":  ZH_WB_POOL,
    "korean":   KO_WB_POOL,
}


# ═══════════════════════════════════════════════════════════
#  SHARED UI CSS — Speed Control + Letter Gap
#  (injected via LANG_CSS và reviewer hooks)
# ═══════════════════════════════════════════════════════════
_SHARED_UI_CSS = '''
.spd-bar{position:fixed;bottom:14px;right:14px;display:flex;gap:3px;z-index:9999;
    background:rgba(10,10,10,.72);border-radius:24px;padding:5px 12px;
    backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
    box-shadow:0 2px 12px rgba(0,0,0,.35);}
.spd-btn{border:none;background:transparent;color:#fff;font-size:11px;
    font-weight:700;padding:3px 8px;border-radius:14px;cursor:pointer;
    opacity:.55;transition:all .18s;}
.spd-btn:hover{opacity:.85;}
.spd-btn.spd-active{background:rgba(255,255,255,.22);opacity:1;}
.lg-wrap{text-align:center;padding:20px 24px 24px;}
.lg-diff-badge{display:inline-block;font-size:12px;font-weight:700;
    color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;
    margin-bottom:10px;padding:3px 12px;border:1px solid var(--border);
    border-radius:12px;background:var(--ex-bg);}
.lg-display{font-size:52px;font-weight:900;letter-spacing:6px;
    color:var(--text);margin:12px 0;line-height:1.4;word-break:break-all;}
.lg-blank{color:var(--accent);border-bottom:3px solid var(--accent);
    padding:0 4px;min-width:28px;display:inline-block;opacity:.9;}
.lg-shown{color:var(--text);}
.lg-hint{font-size:12px;color:var(--muted);margin-top:6px;letter-spacing:.5px;}
.lg-clue{font-size:14px;color:var(--accent);margin:10px auto 4px;
    padding:8px 16px;background:var(--accent-soft);border-radius:8px;
    max-width:340px;line-height:1.6;display:inline-block;}
'''


# ═══════════════════════════════════════════════════════════
#  SPEED CONTROL JS — inject khi hiện mặt sau thẻ
# ═══════════════════════════════════════════════════════════
_SPEED_CTRL_JS = r"""
(function(){
  if(document.getElementById('spd-bar'))return;
  var speeds=[0.5,0.75,1.0,1.25,1.5,1.75,2.0];
  var labels=['0.5x','0.75x','1x','1.25x','1.5x','1.75x','2x'];
  var defaultSpd=parseFloat(window._ankiDefaultSpeed)||1.0;
  var cur=defaultSpd;
  try{
    var ls=localStorage.getItem('anki_spd');
    if(ls!==null&&ls!==undefined)cur=parseFloat(ls);
  }catch(e){}
  var bar=document.createElement('div');
  bar.id='spd-bar';bar.className='spd-bar';
  speeds.forEach(function(s,i){
    var b=document.createElement('button');
    b.className='spd-btn'+(Math.abs(s-cur)<0.01?' spd-active':'');
    b.textContent=labels[i];
    b.onclick=function(){
      cur=s;
      try{localStorage.setItem('anki_spd',String(s));}catch(e){}
      updateBtns();
      applySpd();
    };
    bar.appendChild(b);
  });
  // Nut nhap toc do tuy chinh
  var sep=document.createElement('span');
  sep.style.cssText='color:rgba(255,255,255,.35);font-size:11px;line-height:24px;margin:0 2px;';
  sep.textContent='|';
  bar.appendChild(sep);
  var custInput=document.createElement('input');
  custInput.type='text';
  custInput.id='spd-custom';
  custInput.style.cssText='width:40px;height:22px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:10px;color:#fff;font-size:10px;text-align:center;padding:0 4px;outline:none;';
  custInput.placeholder='?x';
  custInput.title='Nhap toc do tuy y (VD: 0.8, 2.5)';
  custInput.addEventListener('keydown',function(e){
    if(e.key==='Enter'){
      var v=parseFloat(custInput.value.replace(',','.'));
      if(!isNaN(v)&&v>=0.25&&v<=4.0){
        cur=v;
        try{localStorage.setItem('anki_spd',String(v));}catch(e){}
        updateBtns();
        applySpd();
      }
    }
  });
  bar.appendChild(custInput);
  var applyBtn=document.createElement('button');
  applyBtn.className='spd-btn';
  applyBtn.textContent='OK';
  applyBtn.style.opacity='0.7';
  applyBtn.title='Ap dung toc do tuy chinh';
  applyBtn.onclick=function(){
    var v=parseFloat(custInput.value.replace(',','.'));
    if(!isNaN(v)&&v>=0.25&&v<=4.0){
      cur=v;
      try{localStorage.setItem('anki_spd',String(v));}catch(e){}
      updateBtns();
      applySpd();
    }
  };
  bar.appendChild(applyBtn);
  document.body.appendChild(bar);
  function updateBtns(){
    document.querySelectorAll('.spd-btn').forEach(function(b){
      var s=parseFloat(b.textContent);
      b.className='spd-btn'+(Math.abs(s-cur)<0.01?' spd-active':'');
    });
  }
  function applySpd(){
    document.querySelectorAll('audio').forEach(function(a){
      a.playbackRate=cur;
      if(!a._spdBound){
        a._spdBound=true;
        a.addEventListener('play',function(){this.playbackRate=cur;});
      }
    });
    // Cung ap dung cho video elements (neu co)
    document.querySelectorAll('video').forEach(function(v){
      v.playbackRate=cur;
      if(!v._spdBound){
        v._spdBound=true;
        v.addEventListener('play',function(){this.playbackRate=cur;});
      }
    });
  }
  applySpd();
  var obs=new MutationObserver(function(){applySpd();});
  obs.observe(document.body,{childList:true,subtree:true});
})();
"""


# ═══════════════════════════════════════════════════════════
#  LETTER-GAP JS — inject khi hiện mặt trước thẻ ẩn chữ
# ═══════════════════════════════════════════════════════════
_LG_JS_BODY = r"""
(function(){
  var src=document.getElementById('lg-word-src');
  if(!src)return;
  var word=src.textContent.trim();
  var chars=Array.from(word);
  var len=chars.length;
  if(!len)return;
  var seed=chars.reduce(function(s,c){return(s+c.charCodeAt(0))%97;},0);
  var diff=seed<38?0:seed<70?1:2;
  var dlbls=['⭐ Dễ','⭐⭐ Vừa','⭐⭐⭐ Khó'];
  var el=document.getElementById('lg-diff');
  if(el)el.textContent=dlbls[diff];
  var shown=chars.map(function(c,i){
    if(i===0)return true;
    if(diff===0)return(i%3!==1);
    if(diff===1)return(i%2===0);
    return false;
  });
  var hCount=shown.filter(function(v){return!v;}).length;
  var hel=document.getElementById('lg-hint');
  if(hel)hel.textContent='('+hCount+' ký tự bị ẩn)';
  var disp=document.getElementById('lg-display');
  if(disp){
    disp.innerHTML=chars.map(function(c,i){
      return shown[i]
        ?'<span class="lg-shown">'+c+'</span>'
        :'<span class="lg-blank">_</span>';
    }).join('');
  }
})();
"""


# ═══════════════════════════════════════════════════════════
#  COMBO MODE ENGINE — card gộp 5 chế độ trong 1 thẻ
#  - Đọc mode từ window._aiFactoryMode (reviewer hook) hoặc localStorage
#  - Chuyển đổi panel mode (qa/vn/wb/pron/lg) qua nút bấm
#  - Mode qa dùng type-answer chuẩn Anki; vn/pron tự kiểm tra bằng JS
# ═══════════════════════════════════════════════════════════
_COMBO_MODE_JS = r"""
(function(){
  var MODES=['qa','vn','wb','pron','lg'];
  var mode='qa';
  if(window._aiFactoryMode && MODES.indexOf(window._aiFactoryMode)>=0) mode=window._aiFactoryMode;
  try{ var ls=localStorage.getItem('ai_factory_mode'); if(ls && MODES.indexOf(ls)>=0) mode=ls; }catch(e){}
  // Dữ liệu tham chiếu (đọc từ hidden spans do Python render)
  function txt(id){ var el=document.getElementById(id); return el?el.textContent.trim():''; }
  var refFront=txt('combo-front');
  var refMeaning=txt('combo-meaning');
  var refPron=txt('combo-pron');
  // ── Hiển thị panel theo mode ──────────────────────────
  function show(m){
    MODES.forEach(function(x){
      var p=document.getElementById('mode-panel-'+x);
      if(p) p.style.display=(x===m)?'':'none';
    });
    var btns=document.querySelectorAll('.mode-btn');
    for(var i=0;i<btns.length;i++){
      var b=btns[i];
      b.classList.toggle('active', b.getAttribute('data-mode')===m);
    }
    // Type answer của Anki (type-answer) chỉ nên "sống" ở mode qa.
    // Ở mode khác: tự động điền đúng đáp án để Anki không đánh sai khi Show Answer.
    // (Không dùng disabled — một số phiên bản Anki bỏ qua input disabled khi type answer)
    var typeInput=document.querySelector('#mode-panel-qa input');
    if(typeInput){
      if(m==='qa'){ typeInput.value=''; }
      else { typeInput.value=refMeaning; }
    }
  }
  // ── Nút chuyển mode ───────────────────────────────────
  var switcher=document.querySelectorAll('.mode-btn');
  for(var j=0;j<switcher.length;j++){
    (function(btn){
      btn.addEventListener('click', function(){
        mode=btn.getAttribute('data-mode');
        try{ localStorage.setItem('ai_factory_mode', mode); }catch(e){}
        // Đồng bộ mode với Anki config qua bridge (nếu có)
        try{ if(typeof pycmd==='function') pycmd('ai_factory_set_mode:'+mode); }catch(e2){}
        show(mode);
      });
    })(switcher[j]);
  }
  // ── Self-check mode vn (Việt → Ngôn ngữ) ──────────────
  var vnBtn=document.getElementById('vn-check');
  if(vnBtn){
    vnBtn.addEventListener('click', function(){
      var inp=document.getElementById('vn-input');
      var res=document.getElementById('vn-result');
      if(!inp||!res) return;
      var a=(inp.value||'').trim();
      res.style.display='block';
      if(a===refFront){ res.className='combo-res combo-ok'; res.textContent='✅ Chính xác!'; }
      else { res.className='combo-res combo-err'; res.textContent='❌ Chưa đúng → '+refFront; }
    });
  }
  // ── Self-check mode pron (Furigana/Pinyin) ────────────
  var pronBtn=document.getElementById('pron-check');
  if(pronBtn){
    pronBtn.addEventListener('click', function(){
      var inp=document.getElementById('pron-input');
      var res=document.getElementById('pron-result');
      if(!inp||!res) return;
      var a=(inp.value||'').trim();
      res.style.display='block';
      if(a===refPron){ res.className='combo-res combo-ok'; res.textContent='✅ Chính xác!'; }
      else { res.className='combo-res combo-err'; res.textContent='❌ Chưa đúng → '+refPron; }
    });
  }
  // ── Khởi tạo ban đầu ──────────────────────────────────
  show(mode);
  // Nếu ở mode wb/lg, cần khởi động lại game sau khi panel hiện
  if(mode==='wb' && window._wbInit) window._wbInit();
  if(mode==='lg' && window._lgInit) window._lgInit();
  // Lắng nghe hook reviewer inject mode mới (nếu đổi giữa chừng)
  window.addEventListener('ai-factory-mode', function(ev){
    var m=ev.detail;
    if(MODES.indexOf(m)>=0){ mode=m; show(m); if(m==='wb'&&window._wbInit)window._wbInit(); if(m==='lg'&&window._lgInit)window._lgInit(); }
  });
})();
"""
