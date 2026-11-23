(function(){
  // Mobile menu
  var t=document.getElementById('menuToggle'),n=document.getElementById('mainNav');
  if(t&&n)t.addEventListener('click',function(){var o=n.classList.toggle('open');t.setAttribute('aria-expanded',o);document.body.style.overflow=o?'hidden':'';});

  // Header hides on scroll down, shows on scroll up
  var h=document.querySelector('header.site'),ly=window.scrollY;
  window.addEventListener('scroll',function(){var y=window.scrollY;if(h&&!(n&&n.classList.contains('open')))h.classList.toggle('hide',y>ly&&y>300);ly=y;},{passive:true});

  // Mobile call bar: on the home page it slides in once the hero buttons are scrolled past
  var mb=document.querySelector('.mbar'),hb=document.querySelector('.hero .ctas');
  if(hb){document.body.classList.add('has-hero');if(mb&&'IntersectionObserver' in window)new IntersectionObserver(function(es){mb.classList.toggle('show',!es[0].isIntersecting&&es[0].boundingClientRect.top<0)}).observe(hb);else if(mb)mb.classList.add('show');}

  // Before / after sliders
  document.querySelectorAll('.ba').forEach(function(b){var r=b.querySelector('.ba-range');
    r.addEventListener('input',function(){b.style.setProperty('--pos',r.value+'%')});
    if('IntersectionObserver' in window&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
      var o=new IntersectionObserver(function(es){if(!es[0].isIntersecting)return;o.disconnect();var t0=null;
        function f(t){if(!t0)t0=t;var p=Math.min(1,(t-t0)/1600),v=50+Math.sin(p*Math.PI*2)*28*(1-p);b.style.setProperty('--pos',v+'%');r.value=v;if(p<1)requestAnimationFrame(f);}
        requestAnimationFrame(f);},{threshold:.5});o.observe(b);}
  });

  // Reveal on scroll
  if('IntersectionObserver' in window){
    var els=document.querySelectorAll('.sec-head,.step,.why-grid>div,.post-card,.svc-card,.values>div,.split>div,.faq details,.cta-band .wrap,.mini,.gal-item');
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}})},{rootMargin:'0px 0px -8% 0px'});
    els.forEach(function(el,i){el.classList.add('rv');el.style.transitionDelay=(i%4)*70+'ms';io.observe(el);});
  }

  // Forms post to /api/form, which emails them.
  function collect(f){var out=[];[].forEach.call(f.elements,function(el){if(!el.name||el.type==='submit')return;if(el.type==='checkbox'&&!el.checked)return;out.push([el.name,el.value]);});return out;}
  document.querySelectorAll('form[data-form]').forEach(function(f){
    f.addEventListener('submit',function(e){e.preventDefault();if(!f.reportValidity())return;
      var btn=f.querySelector('[type=submit]'),ok=f.querySelector('.form-ok'),err=f.querySelector('.form-err');
      btn.disabled=true;btn.textContent='Sending...';if(err)err.style.display='none';
      fetch('/api/form',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({form:f.getAttribute('data-form'),page:location.pathname,fields:collect(f)})})
      .then(function(r){return r.json().then(function(j){if(!r.ok||!j.ok)throw new Error('failed');})})
      .then(function(){f.classList.add('sent');if(ok)ok.focus();})
      .catch(function(){btn.disabled=false;btn.textContent=btn.getAttribute('data-label')||'Send';if(err)err.style.display='block';});
    });});

  // Live Google reviews (feed served by twofourmedia.com)
  document.querySelectorAll('[data-greviews]').forEach(function(gr){
    if(!window.fetch)return;
    var site=gr.getAttribute('data-greviews'),wrap=gr.parentNode;
    var STARS=function(n,l){var o='';for(var i=1;i<=5;i++)o+=i<=Math.round(n)?'&#9733;':'<i>&#9733;</i>';return '<div class="stars"'+(l?' aria-label="'+l+'"':' aria-hidden="true"')+'>'+o+'</div>'};
    var esc=function(t){return String(t).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
    var ago=function(d){var s=(Date.now()-new Date(d))/864e5;if(!(s>=0))return '';if(s<1)return 'today';if(s<2)return 'yesterday';if(s<30)return Math.floor(s)+' days ago';
      if(s<60)return 'a month ago';if(s<365)return Math.floor(s/30)+' months ago';var y=Math.floor(s/365);return y===1?'a year ago':y+' years ago'};
    fetch('https://www.twofourmedia.com/api/reviews?site='+site).then(function(r){return r.json()}).then(function(j){
      if(!j.ok||!j.reviews||j.reviews.length<3)return;
      var pick=j.reviews.filter(function(v){return v.text.length>=100}).concat(j.reviews.filter(function(v){return v.text.length<100})).slice(0,+(gr.getAttribute('data-count')||6));
      gr.innerHTML=pick.map(function(v){
        var av=v.photo?'<img src="'+esc(v.photo)+'" alt="" width="40" height="40" loading="lazy" referrerpolicy="no-referrer">':'<span>'+esc(v.author.charAt(0))+'</span>';
        return '<figure class="review">'+STARS(v.rating,v.rating+' out of 5 stars')+
          '<blockquote class="clamp">'+esc(v.text)+'</blockquote><button type="button" class="r-more" hidden>Read more</button>'+
          '<figcaption><div class="r-who"><div class="r-av">'+av+'</div><div><b>'+esc(v.author)+'</b><span>'+ago(v.date)+' on Google</span></div></div></figcaption></figure>';
      }).join('');
      gr.classList.add('is-live');var sec=gr.closest('section');if(sec)sec.hidden=false;
      gr.querySelectorAll('.review').forEach(function(f){var q=f.querySelector('blockquote'),b=f.querySelector('.r-more');
        if(q.scrollHeight>q.clientHeight+4){b.hidden=false;b.addEventListener('click',function(){var o=q.classList.toggle('clamp');b.textContent=o?'Read more':'Show less';});}});
      if(j.rating&&j.count){var sm=document.createElement('div');sm.className='g-summary';
        sm.innerHTML='<b class="g-score">'+j.rating.toFixed(1)+'</b><div>'+STARS(j.rating,'')+'<span>'+j.rating.toFixed(1)+' out of 5 from '+j.count+' Google reviews</span></div>';
        wrap.insertBefore(sm,gr);}
      var btns=document.createElement('div');btns.className='g-btns';
      btns.innerHTML=(j.url?'<a class="btn '+'btn-red'+'" href="'+esc(j.url)+'" target="_blank" rel="noopener">Read all our reviews on Google</a>':'')+
        (j.writeUrl?'<a class="btn '+'btn-line'+'" href="'+esc(j.writeUrl)+'" target="_blank" rel="noopener">Leave us a review</a>':'');
      gr.parentNode.insertBefore(btns,gr.nextSibling);
    }).catch(function(){});
  });
})();
