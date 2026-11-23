#!/usr/bin/env python3
"""Builds The Rebels Garage site into ../dist. Run: python3 src/build.py

Content lives in:
  content/posts/*.html  blog posts (details at the top as JSON, body below).
                        A post dated in the future stays hidden until a build runs on or after its date.
  media/                photos (WebP masters); img/ holds the cropped sizes (see images.py)
To swap a photo, change the name in PHOTO below.
"""
import os, sys, json, re, html, shutil
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from images import variant, write_variants, FOCUS

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(SRC, '..')
OUT = os.path.join(ROOT, 'dist')
SITE = 'https://www.therebelsgarage.com'
NAME = 'The Rebels Garage'
PHONE, PHONE_T = '(702) 935-4200', '+17029354200'
EMAIL = 'info@rebelsauto.us'
STREET, UNIT, CITY = '2695 S Decatur Blvd', 'Suite 400', 'Las Vegas, NV 89102'
MAPS = 'https://www.google.com/maps/search/?api=1&query=The+Rebels+Garage+2695+S+Decatur+Blvd+Suite+400+Las+Vegas+NV'
HOURS = [('Monday to Friday', '8:00 am to 5:30 pm'), ('Saturday', '9:00 am to 1:00 pm'), ('Sunday', 'Closed')]
esc = html.escape
LOGO, LOGO_SM = '/media/logo.webp', '/media/logo-sm.webp'

# Which photo goes where. Every slot points at a file in media/ (name without .webp).
# When the shop photos from Drive are added, change these names.
PHOTO = {
    'hero': 'storefront-dusk',
    'collision': 'lexus-front-damage', 'dent': 'panel-sanding', 'paint': 'liftgate-paint-stand', 'frame': 'trans-am-frame-rack',
    'offroad': 'utv-honda-talon', 'rv': 'silverado-on-lift', 'about': 'storefront-wide', 'about_side': 'team-duo',
    'band': 'shop-floor', 'services': 'shop-floor', 'gallery': 'corvette-rear', 'contact': 'storefront-wide', 'blog': 'painter-mixing',
    'notfound': 'corvette-black-shop', 'gallery_top': 'c8-shop-front',
}
FOCUS.update({'utv-honda-talon': (0.5, 0.6), 'trans-am-frame-rack': (0.5, 0.55), 'storefront-door': (0.5, 0.35), 'corvette-black-shop': (0.5, 0.6), 'lexus-front-damage': (0.72, 0.5), 'team-duo': (0.5, 0.3), 'owner-storefront': (0.5, 0.35), 'tech-panel-fit': (0.6, 0.3), 'red-suv-front-damage': (0.5, 0.55), 'panel-sanding': (0.5, 0.45), 'car-on-lift': (0.5, 0.35),
              'lifted-truck-rear': (0.5, 0.6), 'silverado-on-lift': (0.5, 0.4), 'team-inspection': (0.5, 0.4),
              'painter-mixing': (0.5, 0.35), 'storefront-wide': (0.5, 0.45), 'owner-storefront': (0.5, 0.55), 'front-counter': (0.5, 0.5)})

# Gallery grid: (master, title, caption)
GALLERY = [
    ('c8-shop-front', 'C8 Corvette Z06', 'In the shop for body work'),
    ('tech-panel-fit', 'Panel fit check', 'Checking gaps and alignment'),
    ('corvette-black-shop', 'C7 Corvette', 'Body and paint'),
    ('red-suv-front-damage', 'Front end collision', 'Collision repair in progress'),
    ('lexus-front-damage', 'Lexus front end', 'Collision teardown'),
    ('black-suv-before-after', 'Black SUV', 'Side damage, repaired'),
    ('door-panels-repair', 'Door panels', 'Panel repair and refinish'),
    ('liftgate-paint-stand', 'Liftgate refinish', 'Paint prep'),
    ('truck-door-primer', 'Truck door', 'Primed and ready for paint'),
    ('truck-front-teardown', 'Truck front end', 'Frame and front end repair'),
    ('car-on-lift', 'Underbody work', 'Suspension and frame check'),
    ('silverado-on-lift', 'Chevy Tahoe', 'Front end collision repair'),
    ('lifted-truck-rear', 'GMC Denali', 'Collision repair'),
    ('motorcycle-fairing-repair', 'Motorcycle fairing', 'Fairing repair and paint'),
    ('harley-custom', 'Harley custom', 'Custom finish'),
    ('bmw-m3-green', 'BMW M3', 'Collision repair and color change'),
    ('honda-fit-finished', 'Honda Fit', 'Repair in progress'),
    ('painter-mixing', 'Color matching', 'Mixing paint in house'),
]
FOCUS['bmw-after'] = (0.45, 0.6)

ICON = {
    'car': '<path d="M5 15l1.5-5h11L19 15M4 15h16v3H4z"/><circle cx="7.5" cy="18" r="1.3"/><circle cx="16.5" cy="18" r="1.3"/>',
    'dent': '<path d="M3 15c3 0 3-4 6-4s3 4 6 4 3-4 6-4"/><path d="M3 19h18"/>',
    'spray': '<path d="M9 8h6v13H9zM10 8V5h4v3M14 5l4-2M15 6l4 0M14 7l4 2"/>',
    'frame': '<path d="M4 6h16M4 18h16M7 6v12M17 6v12M7 12h10"/>',
    'atv': '<circle cx="6" cy="17" r="3"/><circle cx="18" cy="17" r="3"/><path d="M6 14l3-6h6l3 6M9 8l1-3h4"/>',
    'truck': '<path d="M3 7h11v9H3zM14 10h4l3 3v3h-7z"/><circle cx="7" cy="17.5" r="1.6"/><circle cx="17" cy="17.5" r="1.6"/>',
    'phone': '<path d="M6 3h4l2 5-2.5 1.5a11 11 0 005 5L16 12l5 2v4a2 2 0 01-2 2A16 16 0 014 5a2 2 0 012-2z"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'check': '<path d="M5 12l5 5 9-10"/>',
    'arrow': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'pin': '<path d="M12 21s-7-6.5-7-12a7 7 0 0114 0c0 5.5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    'mail': '<path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/>',
    'shield': '<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    'camera': '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    'doc': '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
    'key': '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/>',
}


def ic(name, cls='ic'):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>'


# ---------- services ----------
# slug, icon, photo slot, short name, page title, one-liner, intro, what's included, signs/when to call
SERVICES = [
    ('collision-repair', 'car', 'collision', 'Collision Repair', 'Collision Repair in Las Vegas',
     'Complete collision repair that puts your vehicle back to pre-accident condition.',
     'From fender benders to major hits, we handle the full repair under one roof: teardown, damage assessment, structural and panel work, refinishing and final inspection. You get a clear estimate before work starts and updates while your vehicle is with us.',
     ['Free written estimates', 'Panel repair and replacement', 'Bumper repair and replacement', 'Structural and frame work', 'Factory color matched refinishing', 'Final quality inspection'],
     ['Visible damage after an accident, even a minor one', 'Doors, hood or trunk that no longer line up', 'Gaps between panels that were not there before', 'New noises, pulling or warning lights after a hit']),
    ('dent-repair', 'dent', 'dent', 'Dent Removal', 'Dent Removal &amp; Repair in Las Vegas',
     'Door dings, hail and creases removed without hurting your paint.',
     'Not every dent needs a body shop bill. Where the paint is intact we use paintless techniques to massage the panel back into shape. Where it is not, we repair the panel and blend the finish so you cannot tell where the damage was.',
     ['Door dings and parking lot damage', 'Hail damage', 'Body line creases', 'Bumper dents', 'Paintless dent repair where possible', 'Panel repair and blending where needed'],
     ['A ding you notice every time you walk up to the car', 'Hail damage after a storm', 'A crease along a body line', 'Before trading in or selling your vehicle']),
    ('custom-paint', 'spray', 'paint', 'Custom Paint', 'Custom Paint &amp; Auto Painting in Las Vegas',
     'Factory color matching, full color changes and custom finishes.',
     'Whether you need one panel matched to factory paint or a complete color change, our paint work is done with careful prep, precise color matching and a clean, even finish. See the BMW X6 we took from factory white to a custom green metallic.',
     ['Factory color matching', 'Complete color changes', 'Custom and metallic finishes', 'Spot and panel refinishing', 'Clear coat repair', 'Bumper and trim painting'],
     ['Faded, peeling or oxidized paint', 'A mismatched panel from an old repair', 'You want a whole new look', 'Scratches through the clear coat']),
    ('frame-straightening', 'frame', 'frame', 'Frame Straightening', 'Frame Straightening in Las Vegas',
     'Precision frame and unibody straightening for structural integrity.',
     'After a serious collision, the frame or unibody can shift even when the damage looks cosmetic. We measure, pull and straighten the structure back to spec so your vehicle drives straight, wears tires evenly and protects you the way it was designed to.',
     ['Frame and unibody measuring', 'Frame straightening', 'Structural repair after collisions', 'Alignment of panels and doors', 'Post-repair inspection'],
     ['The vehicle pulls or does not track straight', 'Uneven tire wear after an accident', 'Doors or hood that will not close right', 'Any collision with significant impact']),
    ('utv-off-road-repair', 'atv', 'offroad', 'UTV &amp; Off-Road', 'UTV, Can-Am &amp; RZR Repair in Las Vegas',
     'Body and collision repair for UTVs, Can-Ams, RZRs and side-by-sides.',
     'Desert trails are hard on off-road machines. We repair cracked and broken body panels, bent cages and bumpers, and damaged plastics on side-by-sides and UTVs, and we can refinish them in factory colors or something custom.',
     ['Can-Am, Polaris RZR and other side-by-sides', 'Body panel and plastics repair', 'Cage, bumper and guard repair', 'Rollover damage', 'Custom paint and finishes'],
     ['Cracked or missing panels after a ride', 'A rollover, even if it still runs', 'Bent bumpers, guards or cage', 'Getting ready to sell or trade your machine']),
    ('rv-box-truck-repair', 'truck', 'rv', 'RV &amp; Box Truck', 'RV &amp; Box Truck Body Repair in Las Vegas',
     'Body repair for RVs, motorhomes, trailers and commercial box trucks.',
     'Big vehicles need a shop with room and experience to work on them. We repair body and collision damage on RVs, motorhomes, travel trailers and commercial box trucks, so you can get back on the road or back to work.',
     ['RV and motorhome body repair', 'Travel trailer damage', 'Box truck and work truck body repair', 'Collision and impact damage', 'Paint and refinishing'],
     ['Damage from a low branch, pole or tight turn', 'Collision damage on a work truck', 'Dented or torn exterior panels', 'Getting a fleet vehicle back in service']),
]
SLUGS = {s[0] for s in SERVICES}

NAV = [('', 'Home'), ('services', 'Services'), ('gallery', 'Our Work'), ('about', 'About'), ('blog', 'Blog'), ('contact', 'Contact')]


def head(title, desc, path, image='', og_type='website', extra='', noindex=False):
    canon = f'{SITE}/{path}'.rstrip('/') if path else SITE
    img = SITE + (image or variant(PHOTO['hero'], 1200, 630))
    robots = '<meta name="robots" content="noindex">' if noindex else ''
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canon}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="{og_type}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{img}">{robots}
<meta name="theme-color" content="#070707"><link rel="icon" href="/media/favicon.png"><link rel="apple-touch-icon" href="/media/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">{extra}</head><body>'''


def top(active):
    def item(p, t):
        cur = ' aria-current="page"' if p == active or (p == 'services' and active in SLUGS) or (p == 'blog' and active.startswith('blog/')) else ''
        if p == 'services':
            sub = ''.join(f'<a href="/{s[0]}">{s[3]}</a>' for s in SERVICES)
            return f'<div class="dd"><a href="/services"{cur}>Services</a><div class="dd-menu">{sub}</div></div>'
        return f'<a href="/{p}"{cur}>{t}</a>'
    links = ''.join(item(p, t) for p, t in NAV)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap bar"><a class="logo" href="/" aria-label="{NAME} home"><img src="{LOGO_SM}" alt="{NAME}" width="62" height="55"></a>
<nav class="main" id="mainNav" aria-label="Main">{links}<div class="nav-cta"><a class="tel" href="tel:{PHONE_T}">{ic("phone")}{PHONE}</a><a class="btn btn-red btn-sm" href="/contact#quote">Free Estimate</a></div></nav>
<button class="menu-toggle" id="menuToggle" aria-expanded="false" aria-controls="mainNav"><span></span><span></span><span class="sr">Menu</span></button></div></header><main id="main">'''


HP = '<label class="hp" aria-hidden="true">Leave this empty<input name="company_site" tabindex="-1" autocomplete="off"></label>'


def field(label, name=None, kind='text', req=False, auto='', area=False, opts=None):
    name = name or label
    fid = 'f-' + re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')
    star = ' <i>*</i>' if req else ''
    r = ' required' if req else ''
    if area:
        return f'<label for="{fid}"><span>{esc(label)}{star}</span><textarea id="{fid}" name="{esc(name)}"{r}></textarea></label>'
    if opts:
        o = ''.join(f'<option>{esc(x)}</option>' for x in opts)
        return f'<label for="{fid}"><span>{esc(label)}{star}</span><select id="{fid}" name="{esc(name)}"{r}>{o}</select></label>'
    a = f' autocomplete="{auto}"' if auto else ''
    return f'<label for="{fid}"><span>{esc(label)}{star}</span><input id="{fid}" name="{esc(name)}" type="{kind}"{r}{a}></label>'


def quote_form():
    inner = ('<div class="row2">' + field('Name', req=True, auto='name') + field('Phone', kind='tel', req=True, auto='tel') + '</div>'
             + '<div class="row2">' + field('Email', kind='email', auto='email') + field('Vehicle (year, make, model)', name='Vehicle') + '</div>'
             + field('What do you need?', name='Service', opts=['Collision repair', 'Dent removal', 'Custom paint', 'Frame straightening', 'UTV / Can-Am / RZR repair', 'RV or box truck repair', 'Not sure yet'])
             + field('Tell us about the damage', name='Details', area=True))
    return (f'<form class="form" data-form="quote" novalidate>{inner}{HP}'
            '<p class="form-note">Have photos of the damage? Mention it and we\'ll reply with where to send them.</p>'
            '<button class="btn btn-red btn-block" type="submit" data-label="Get My Free Estimate">Get My Free Estimate</button>'
            '<p class="form-ok" role="status" tabindex="-1">Got it. We\'ll reach out shortly to talk about your estimate.</p>'
            f'<p class="form-err" role="alert">That didn\'t send. Please call <a href="tel:{PHONE_T}">{PHONE}</a> or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p></form>')


def hours_list():
    return '<ul class="hours">' + ''.join(f'<li><span>{d}</span><span>{h}</span></li>' for d, h in HOURS) + '</ul>'


def foot():
    svc = ''.join(f'<li><a href="/{s[0]}">{s[3]}</a></li>' for s in SERVICES)
    return f'''</main>
<footer class="site-foot"><div class="skyline" aria-hidden="true"></div><div class="wrap foot-grid">
<div class="foot-brand"><img src="{LOGO}" alt="{NAME}" width="220" height="196" loading="lazy"><p>Collision repair, dent removal, custom paint and frame straightening for cars, trucks, UTVs, RVs and box trucks in Las Vegas.</p></div>
<div><h4>Services</h4><ul>{svc}</ul></div>
<div><h4>Shop</h4><ul><li><a href="/gallery">Our Work</a></li><li><a href="/about">About</a></li><li><a href="/blog">Blog</a></li><li><a href="/contact">Contact</a></li></ul></div>
<div><h4>Visit</h4><ul class="contact-list"><li>{ic("pin")}<a href="{MAPS}" rel="noopener">{STREET}, {UNIT}<br>{CITY}</a></li><li>{ic("phone")}<a href="tel:{PHONE_T}">{PHONE}</a></li><li>{ic("mail")}<a href="mailto:{EMAIL}">{EMAIL}</a></li></ul>{hours_list()}</div>
</div><div class="wrap legal"><span>&copy; 2026 {NAME}. Las Vegas, Nevada.</span><span>Site by <a href="https://www.twofourmedia.com" rel="noopener">Two Four Media</a></span></div></footer>
<div class="mbar"><a href="tel:{PHONE_T}">{ic("phone")}Call</a><a class="mbar-red" href="/contact#quote">Free Estimate</a></div>
<script src="/site.js"></script></body></html>'''


def phero(crumb, eyebrow, title, lede, slot='hero', ctas=True):
    c = (f'<div class="ctas"><a class="btn btn-red" href="/contact#quote">Get a Free Estimate</a><a class="btn btn-ghost" href="tel:{PHONE_T}">{ic("phone")}{PHONE}</a></div>') if ctas else ''
    return (f'<section class="phero"><div class="phero-bg" style="background-image:url({variant(PHOTO[slot], 1920, 900)})"></div><div class="wrap">'
            f'<p class="crumbs"><a href="/">Home</a><span>/</span>{crumb}</p><p class="eyebrow">{eyebrow}</p><h1>{title}</h1><p class="lede">{lede}</p>{c}</div></section>')


def sec_head(kicker, title, lede='', link=''):
    l = f'<p class="lede">{lede}</p>' if lede else ''
    return f'<div class="sec-head"><div><p class="eyebrow">{kicker}</p><h2>{title}</h2>{l}</div>{link}</div>'


def ticks(items):
    return '<ul class="ticks">' + ''.join(f'<li>{ic("check")}<span>{x}</span></li>' for x in items) + '</ul>'


def cta_band(title='Wrecked, dented or ready for a new look?', lede='Send us a few details or give the shop a call. Estimates are free.'):
    return (f'<section class="cta-band"><div class="wrap"><p class="eyebrow">Free estimates</p><h2>{title}</h2><p class="lede">{lede}</p>'
            f'<div class="ctas"><a class="btn btn-red" href="/contact#quote">Get a Free Estimate</a><a class="btn btn-ghost" href="tel:{PHONE_T}">{ic("phone")}{PHONE}</a></div></div></section>')


def choice_sec():
    return (f'''<section class="choice"><div class="wrap split choice-in"><div class="choice-photo"><img class="rounded" src="{variant('lexus-front-damage', 900, 1050)}" alt="A Lexus SUV with front end collision damage in the shop at The Rebels Garage" loading="lazy" width="900" height="1050"></div>
<div><p class="eyebrow">Your car, your choice</p><h2>Do I have to use my insurance company's shop?</h2>
<p class="lede">No. In Nevada, you can have your vehicle repaired at any licensed body shop you choose. Your insurance company can suggest one of its preferred shops, but state law says it cannot require you to use one, and it has to tell you about that right when you first report the claim.</p>
{ticks(["Tell your insurance company you want your repair done at The Rebels Garage", "We inspect the damage and write up the repair estimate", "We work with your adjuster directly, from photos to paperwork", "If hidden damage shows up once the car is apart, we document it and send it to your insurer"])}
<p class="fine">Nevada Revised Statutes 690B.016. Your insurer still pays based on the reasonable cost of the repair under your policy.</p>
<div class="ctas"><a class="btn btn-red" href="/contact#quote">Start my estimate</a><a class="btn btn-ghost" href="tel:{PHONE_T}">{ic("phone")}{PHONE}</a></div></div></div></section>''')


def family_sec():
    return (f'''<section class="family"><div class="wrap split family-in"><div><p class="eyebrow">Family owned</p><h2>Family owned and operated by Daniel Hernandez.</h2>
<p class="lede">When you bring your vehicle to The Rebels Garage, you deal directly with the people doing the work. Daniel and his crew treat every customer like family and every repair like it is their own car.</p>
<blockquote class="fam-quote">&ldquo;The staff made me feel like family the moment I walked in.&rdquo;<cite>Gerardo R., Google review</cite></blockquote>
<div class="ctas"><a class="btn btn-red" href="/contact#quote">Get a Free Estimate</a><a class="btn btn-ghost" href="/about">About the shop</a></div></div>
<div class="family-photo"><img class="rounded" src="{variant('owner-storefront', 900, 1050)}" alt="Daniel Hernandez, owner of The Rebels Garage, outside the shop on S Decatur Blvd" loading="lazy" width="900" height="1050"></div></div></section>''')


def insurance_band():
    return (f'''<section class="ins-band"><div class="ins-bg" style="background-image:url({variant('storefront-door', 1920, 900)})"></div><div class="wrap ins-in">
<p class="eyebrow">Insurance claims</p><h2>We work with all insurance companies.</h2>
<p class="lede">Whoever your coverage is with, bring it to us. We handle the back and forth with your adjuster so you are not stuck in the middle, and we keep you updated until your vehicle is ready.</p>
<div class="ins-points"><div><b>Any insurer</b><span>All carriers welcome</span></div><div><b>Your choice</b><span>Your car, your shop</span></div><div><b>Free estimates</b><span>With or without a claim</span></div><div><b>Free towing</b><span>With your repair</span></div><div><b>NV licensed</b><span>State licensed shop</span></div></div>
</div></section>''')


def ba(before, after, label, w=1200, h=800):
    return (f'<figure class="ba" style="--pos:50%"><img src="{variant(after, w, h)}" alt="{esc(label)}, after" width="{w}" height="{h}" loading="lazy">'
            f'<div class="ba-before"><img src="{variant(before, w, h)}" alt="{esc(label)}, before" width="{w}" height="{h}" loading="lazy"></div>'
            '<span class="ba-tag ba-tag-b">Before</span><span class="ba-tag ba-tag-a">After</span><span class="ba-line" aria-hidden="true"><i></i></span>'
            '<input class="ba-range" type="range" min="0" max="100" value="50" aria-label="Drag to compare before and after"></figure>')


MARQUEE = ['Collision Repair', 'Dent Removal', 'Custom Paint', 'Frame Straightening', 'Color Matching', 'Can-Am &amp; RZR', 'RV Body Repair', 'Box Trucks', 'Bumper Repair', 'Free Estimates']


def marquee():
    items = ''.join(f'<span>{x}</span>' for x in MARQUEE)
    return f'<div class="marquee" aria-hidden="true"><div class="mq-track">{items}{items}</div></div>'


def svc_cards():
    return '<div class="svc-grid">' + ''.join(
        f'<a class="svc-card" href="/{s[0]}"><span class="svc-n">0{i + 1}</span><span class="svc-ic">{ic(s[1])}</span><h3>{s[3]}</h3><p>{s[5]}</p><span class="link">Learn more {ic("arrow")}</span></a>'
        for i, s in enumerate(SERVICES)) + '</div>'


def steps():
    s = [('phone', 'Call or send details', 'Tell us what happened. Photos help us give you a head start.'),
         ('doc', 'Free written estimate', 'We inspect the damage and explain the repair and cost before any work begins.'),
         ('spray', 'Repair and refinish', 'Body work, structural repair and paint, done with care and attention to detail.'),
         ('key', 'Inspect and hand back', 'We check the fit, finish and function, then hand you the keys.')]
    return '<ol class="steps">' + ''.join(f'<li class="step"><span class="step-ic">{ic(i)}</span><span class="step-n">0{n + 1}</span><h3>{t}</h3><p>{d}</p></li>' for n, (i, t, d) in enumerate(s)) + '</ol>'


FAQ = [
    ('Do I have to use the shop my insurance company recommends?', 'No. Nevada law lets you take your vehicle to any licensed body shop you choose, and your insurer cannot require you to use a particular shop. Just tell them you want the repair done at The Rebels Garage.'),
    ('Do you work with my insurance company?', 'Yes. We work with all insurance companies and deal with your adjuster directly.'),
    ('Do you offer towing?', 'Yes. Towing is free when we do the repair. Call the shop at (702) 935-4200 and we will set it up.'),
    ('Are estimates free?', 'Yes. Call the shop, stop by, or send your details through the estimate form and we will set up a free estimate.'),
    ('What kinds of vehicles do you repair?', 'Cars, trucks and SUVs, plus UTVs, Can-Ams, RZRs and other side-by-sides, RVs, motorhomes, travel trailers and commercial box trucks.'),
    ('Can you match my factory paint?', 'Yes. We match factory colors for panel and spot repairs, and we also do complete color changes and custom finishes.'),
    ('Do I need to fix a small dent?', 'Not always right away, but a dent with cracked or chipped paint can let moisture in and lead to rust. Many small dents can be fixed without repainting, which keeps the cost down.'),
    ('How long will my repair take?', 'It depends on the damage and parts. Minor dent work can be quick, while collision and frame repairs take longer. We give you a time estimate along with your written estimate.'),
    ('Where are you located?', f'{STREET}, {UNIT}, {CITY}. We are open Monday to Friday 8:00 am to 5:30 pm and Saturday 9:00 am to 1:00 pm.'),
]


def faq(cls=''):
    items = ''.join(f'<details{" open" if i == 0 else ""}><summary>{q}</summary><p>{a}</p></details>' for i, (q, a) in enumerate(FAQ))
    ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': html.unescape(q), 'acceptedAnswer': {'@type': 'Answer', 'text': html.unescape(a)}} for q, a in FAQ]}
    return (f'<section id="faq" class="{cls}"><div class="wrap faq-grid"><div><p class="eyebrow">FAQ</p><h2>Good questions.</h2>'
            f'<p class="lede">The short answers. Anything else, call the shop.</p></div>'
            f'<div><div class="faq">{items}</div><a class="btn btn-ghost faq-cta" href="tel:{PHONE_T}">{ic("phone")}Ask a question</a></div></div></section>'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def reviews():
    # Fills from the live Google reviews feed when the shop's profile is connected; stays hidden until then.
    return ('<section class="reviews-sec" hidden><div class="wrap">' + sec_head('Reviews', 'What drivers say.')
            + '<div class="grid3 reviews" data-greviews="rebels" data-count="3"></div></div></section>')


ORG = {'@context': 'https://schema.org', '@type': 'AutoBodyShop', '@id': SITE + '/#business', 'name': NAME, 'url': SITE, 'telephone': PHONE_T, 'email': EMAIL,
       'image': SITE + LOGO, 'logo': SITE + LOGO,
       'address': {'@type': 'PostalAddress', 'streetAddress': f'{STREET} {UNIT}', 'addressLocality': 'Las Vegas', 'addressRegion': 'NV', 'postalCode': '89102', 'addressCountry': 'US'},
       'openingHoursSpecification': [
           {'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'opens': '08:00', 'closes': '17:30'},
           {'@type': 'OpeningHoursSpecification', 'dayOfWeek': 'Saturday', 'opens': '09:00', 'closes': '13:00'}],
       'areaServed': [{'@type': 'City', 'name': c} for c in ('Las Vegas', 'Henderson', 'North Las Vegas', 'Spring Valley', 'Paradise', 'Summerlin')],
       'makesOffer': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': html.unescape(s[3])}} for s in SERVICES]}


# ---------- blog ----------
def is_live(iso):
    d = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone(timedelta(hours=-8)))
    return d <= datetime.now(timezone.utc)


def load_posts():
    posts = []
    folder = os.path.join(ROOT, 'content', 'posts')
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith('.html'):
            continue
        s = open(os.path.join(folder, fn), encoding='utf-8').read()
        m = re.match(r'<!--\s*(\{.*?\})\s*-->\s*(.*)', s, re.S)
        meta = json.loads(m.group(1))
        meta['slug'], meta['body'] = fn[:-5], m.group(2).strip()
        if meta.get('draft') or not is_live(meta['date']):
            continue
        meta['minutes'] = max(1, round(len(re.sub(r'<[^>]+>', ' ', meta['body']).split()) / 230))
        posts.append(meta)
    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts


def nice(iso):
    return datetime.fromisoformat(iso.replace('Z', '+00:00')).strftime('%B %-d, %Y')


def post_img(p, w, h):
    return variant(p.get('photo') or PHOTO['hero'], w, h)


def post_card(p):
    return (f'<a class="post-card" href="/blog/{p["slug"]}"><span class="pc-img"><img src="{post_img(p, 720, 405)}" alt="" loading="lazy" width="720" height="405"></span>'
            f'<span class="pc-b"><span class="meta">{nice(p["date"])} &middot; {p["minutes"]} min read</span><h3>{esc(p["title"])}</h3><span class="link">Read more {ic("arrow")}</span></span></a>')


def post_page(p, posts):
    img = post_img(p, 1600, 900)
    ld = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': p['title'], 'description': p['description'], 'image': SITE + img,
          'datePublished': p['date'], 'dateModified': p.get('updated') or p['date'], 'author': {'@type': 'Organization', 'name': NAME},
          'publisher': {'@type': 'Organization', 'name': NAME, 'logo': {'@type': 'ImageObject', 'url': SITE + LOGO}}, 'mainEntityOfPage': f'{SITE}/blog/{p["slug"]}'}
    others = [q for q in posts if q['slug'] != p['slug']][:3]
    more = (f'<section class="alt"><div class="wrap">{sec_head("Keep reading", "More from the shop", link="<a class=link href=/blog>All posts " + ic("arrow") + "</a>")}<div class="grid3">{"".join(post_card(q) for q in others)}</div></div></section>') if others else ''
    body = (f'<article class="post"><section class="post-head"><div class="wrap narrow"><p class="crumbs"><a href="/">Home</a><span>/</span><a href="/blog">Blog</a></p>'
            f'<h1>{esc(p["title"])}</h1><p class="meta">{nice(p["date"])} &middot; {p["minutes"]} min read</p></div></section>'
            f'<section class="tight"><div class="wrap narrow"><img class="post-img" src="{img}" alt="" width="1600" height="900"><div class="prose">{p["body"]}</div>'
            f'<div class="post-cta"><div><h3>Need body work or paint?</h3><p>Get a free estimate from The Rebels Garage.</p></div><div class="ctas"><a class="btn btn-red" href="/contact#quote">Free Estimate</a><a class="btn btn-ghost" href="tel:{PHONE_T}">{PHONE}</a></div></div></div></section></article>'
            + more)
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return head(p['seo_title'], p['description'], f'blog/{p["slug"]}', img, 'article', extra) + top('blog/' + p['slug']) + body + foot()


# ---------- pages ----------
def service_page(i, s):
    slug, icn, slot, short, title, one, intro, incl, signs = s
    others = [x for x in SERVICES if x[0] != slug]
    other_links = ''.join(f'<a class="mini" href="/{x[0]}">{ic(x[1])}<span>{x[3]}</span>{ic("arrow", "chev")}</a>' for x in others)
    paint_ba = (f'<section class="alt"><div class="wrap">{sec_head("Before &amp; after", "BMW X6: factory white to custom green.", "Drag the slider to see the full color change.")}{ba("bmw-before", "bmw-after", "BMW X6 custom paint")}</div></section>') if slug == 'custom-paint' else ''
    body = (phero(f'<a href="/services">Services</a><span>/</span>{short}', f'0{i + 1} &middot; {short}', title, one, slot)
            + f'''<section><div class="wrap split"><div><p class="eyebrow">How we handle it</p><h2>{short} done right.</h2><p class="lede">{intro}</p>{ticks(incl)}
<div class="ctas"><a class="btn btn-red" href="/contact#quote">Get a Free Estimate</a></div></div>
<div><img class="rounded" src="{variant(PHOTO[slot], 900, 700)}" alt="{esc(html.unescape(short))} at The Rebels Garage in Las Vegas" loading="lazy" width="900" height="700"></div></div></section>'''
            + paint_ba
            + f'''<section class="dark"><div class="wrap split"><div><p class="eyebrow">When to bring it in</p><h2>Signs it's time to call.</h2></div>
<div><ol class="num-list">{"".join(f"<li><span>0{n + 1}</span>{x}</li>" for n, x in enumerate(signs))}</ol></div></div></section>
<section><div class="wrap">{sec_head("The process", "From first call to keys in hand.")}{steps()}</div></section>
<section class="alt"><div class="wrap">{sec_head("More services", "Everything else we fix.")}<div class="mini-grid">{other_links}</div></div></section>'''
            + cta_band())
    svc_ld = {'@context': 'https://schema.org', '@type': 'Service', 'name': html.unescape(title), 'serviceType': html.unescape(short), 'description': html.unescape(intro),
              'provider': {'@id': SITE + '/#business'}, 'areaServed': {'@type': 'City', 'name': 'Las Vegas'}}
    desc = html.unescape(f'{one} The Rebels Garage, {STREET}, Las Vegas. Free estimates: {PHONE}.')
    return (html.unescape(title) + ' | The Rebels Garage', desc, body, {'extra': f'<script type="application/ld+json">{json.dumps(svc_ld, ensure_ascii=False)}</script>'})


def pages(posts):
    P = {}
    latest = ''.join(post_card(p) for p in posts[:3])
    blog_sec = (f'<section><div class="wrap">{sec_head("From the shop", "Body shop tips for Las Vegas drivers.", link="<a class=link href=/blog>All posts " + ic("arrow") + "</a>")}<div class="grid3">{latest}</div></div></section>') if posts else ''
    P[''] = ('Collision Repair & Auto Body Shop Las Vegas | The Rebels Garage',
             'The Rebels Garage is a Las Vegas collision repair and auto body shop: dent removal, custom paint, frame straightening, and body repair for UTVs, RVs and box trucks. Free estimates.',
             f'''<section class="hero"><div class="hero-bg"><img src="{variant(PHOTO["hero"], 1920, 1100)}" alt="" width="1920" height="1100" fetchpriority="high"></div><div class="neon-glow" aria-hidden="true"></div>
<div class="wrap hero-in"><img class="hero-logo" src="{LOGO}" alt="The Rebels Garage, Auto Collision Repair, Las Vegas NV" width="585" height="522">
<div class="hero-copy"><p class="eyebrow">The Rebels Garage</p><h1>Collision repair &amp; custom paint, <em>done right.</em></h1>
<p class="lede">From dents to full collision repairs, we get your car, truck, UTV or RV looking and driving like new.</p>
<div class="ctas"><a class="btn btn-red" href="/contact#quote">Get a Free Estimate</a><a class="btn btn-ghost" href="tel:{PHONE_T}">{ic("phone")}{PHONE}</a></div></div></div></section>
{marquee()}
<section><div class="wrap">{sec_head("What we fix", "Six ways we bring vehicles back.", "Comprehensive body work and repairs for a wide range of vehicles, all under one roof on Decatur.", '<a class="link" href="/services">All services ' + ic("arrow") + '</a>')}{svc_cards()}</div></section>
<section class="alt"><div class="wrap split ba-split"><div><p class="eyebrow">Custom paint</p><h2>Factory white to custom green.</h2>
<p class="lede">A complete color change on a BMW X6, with precise prep and a flawless metallic finish. Drag to compare.</p><a class="btn btn-ghost" href="/gallery">See more of our work</a></div>
<div>{ba("bmw-before", "bmw-after", "BMW X6 color change")}</div></div></section>
<section class="dark"><div class="wrap split why"><div><p class="eyebrow">Why The Rebels Garage</p><h2>Built for Vegas drivers.<br>Every kind of vehicle.</h2>
<p class="lede">Cars to RVs, UTVs to box trucks. We repair them all with the same attention to detail.</p></div>
<div class="why-grid">
<div>{ic("shield")}<h3>Experienced techs</h3><p>A team with years of collision and body repair experience.</p></div>
<div>{ic("spray")}<h3>Quality materials</h3><p>High quality parts and paint materials on every repair.</p></div>
<div>{ic("check")}<h3>Satisfaction guaranteed</h3><p>We stand behind our work on every service.</p></div>
<div>{ic("truck")}<h3>Big or small</h3><p>The room and know-how for side-by-sides, motorhomes and work trucks.</p></div></div></div></section>
{choice_sec()}
{insurance_band()}
<section><div class="wrap">{sec_head("How it works", "From first call to keys in hand.")}{steps()}</div></section>
{family_sec()}
{reviews()}
{blog_sec}
{faq('alt')}
<section id="contact"><div class="wrap split contact"><div><p class="eyebrow">Free estimates</p><h2>Tell us what happened.</h2>
<p class="lede">Send a few details and we'll get back to you, or call the shop at {PHONE}.</p>{visit_box()}</div><div id="quote">{quote_form()}</div></div></section>''',
             {'extra': f'<script type="application/ld+json">{json.dumps(ORG, ensure_ascii=False)}</script>'})

    P['services'] = ('Auto Body & Collision Services in Las Vegas | The Rebels Garage',
                     'Collision repair, dent removal, custom paint, frame straightening, UTV and side-by-side repair, and RV and box truck body repair in Las Vegas.',
                     phero('Services', 'What we do', 'Auto body &amp; collision services.', 'Comprehensive body work and repairs for cars, trucks, UTVs, RVs and box trucks in Las Vegas.', 'services')
                     + marquee() + f'<section><div class="wrap">{svc_cards()}</div></section>'
                     + f'<section class="alt"><div class="wrap">{sec_head("The process", "From first call to keys in hand.")}{steps()}</div></section>' + cta_band())

    for i, s in enumerate(SERVICES):
        P[s[0]] = service_page(i, s)

    P['gallery'] = ('Our Work | Before & After Auto Body Repair Las Vegas | The Rebels Garage',
                    'Before and after photos of collision repair, custom paint and body work from The Rebels Garage in Las Vegas.',
                    phero('Our Work', 'Before &amp; after', 'Our work.', 'Real vehicles from our Las Vegas shop. Drag the slider to compare before and after.', 'gallery', ctas=False)
                    + f'''<section><div class="wrap"><div class="gal">
<figure class="gal-item gal-wide">{ba("bmw-before", "bmw-after", "BMW X6 color change")}<figcaption><b>BMW X6 complete color change</b><span>Custom paint &middot; Factory white to custom green metallic</span></figcaption></figure>
</div><div class="gal-grid">''' + ''.join(f'<figure><img src="{variant(m, 640, 800)}" alt="{esc(t)}: {esc(c)} at The Rebels Garage in Las Vegas" loading="lazy" width="640" height="800"><figcaption><b>{esc(t)}</b><span>{esc(c)}</span></figcaption></figure>' for m, t, c in GALLERY) + '''</div></div></section>''' + cta_band())

    P['about'] = ('About The Rebels Garage | Las Vegas Auto Body Shop',
                  'The Rebels Garage is a Las Vegas auto body and collision shop on S Decatur Blvd, repairing cars, trucks, UTVs, RVs and box trucks.',
                  phero('About', 'About the shop', 'Las Vegas built.<br>Rebel made.', 'A collision center on Decatur that treats every vehicle like it matters, because it does.', 'about', ctas=False)
                  + f'''<section><div class="wrap split"><div><img class="rounded" src="{variant(PHOTO["about_side"], 900, 760)}" alt="Two of The Rebels Garage crew in the shop" loading="lazy" width="900" height="760"></div>
<div class="prose"><p class="eyebrow">Our story</p><h2>A reputation built panel by panel.</h2>
<p>With years of experience in the automotive repair industry, The Rebels Garage has built a reputation for excellence in body work and collision repair.</p>
<p>We repair the vehicles other shops turn away: side-by-sides after a hard day on the trails, motorhomes with a tangle of branch damage, box trucks that need to get back to work. And we give a daily driver with a door ding the same care.</p>
<p>Every job starts with a clear estimate and ends with an inspection of the fit, finish and function before you get your keys back.</p></div></div></section>
<section class="dark"><div class="wrap">{sec_head("What we stand for", "Four promises on every job.")}<div class="values">
<div><span>01</span><h3>Expert technicians</h3><p>Experienced professionals who know body and collision work.</p></div>
<div><span>02</span><h3>Quality materials</h3><p>High quality parts and materials on every repair.</p></div>
<div><span>03</span><h3>Satisfaction guaranteed</h3><p>We stand behind our work on all services.</p></div>
<div><span>04</span><h3>Versatile expertise</h3><p>From cars to RVs and UTVs to box trucks, the same attention to detail.</p></div></div></div></section>
<section><div class="wrap">{sec_head("Inside the shop", "Come see us on Decatur.", "A clean lobby, a real front counter and the crew that does the work.")}<div class="trio">
<img class="rounded" src="{variant('lobby', 800, 600)}" alt="Customer lobby at The Rebels Garage" loading="lazy" width="800" height="600">
<img class="rounded" src="{variant('front-counter', 800, 600)}" alt="Front counter at The Rebels Garage" loading="lazy" width="800" height="600">
<img class="rounded" src="{variant('owner-storefront', 800, 600)}" alt="Outside The Rebels Garage on S Decatur Blvd" loading="lazy" width="800" height="600"></div></div></section>
<section><div class="wrap split contact"><div><p class="eyebrow">Visit the shop</p><h2>Find us on Decatur.</h2>{visit_box()}</div>
<div><iframe class="map" title="Map to {NAME}" loading="lazy" src="https://www.google.com/maps?q=2695+S+Decatur+Blvd+Suite+400,+Las+Vegas,+NV&amp;output=embed"></iframe></div></div></section>''' + cta_band())

    P['contact'] = ('Contact & Free Estimates | The Rebels Garage Las Vegas',
                    f'Get a free collision repair or paint estimate from The Rebels Garage in Las Vegas. Call {PHONE} or send your details online.',
                    phero('Contact', 'Free estimates', 'Get your free estimate.', f'Send a few details about your vehicle and the damage, or call {PHONE}.', 'contact', ctas=False)
                    + f'''<section><div class="wrap split contact"><div id="quote"><h2>Request an estimate</h2>{quote_form()}</div>
<div><h2>Visit the shop</h2>{visit_box()}<iframe class="map" title="Map to {NAME}" loading="lazy" src="https://www.google.com/maps?q=2695+S+Decatur+Blvd+Suite+400,+Las+Vegas,+NV&amp;output=embed"></iframe></div></div></section>''' + faq('alt'))

    P['blog'] = ('Auto Body & Collision Repair Blog | The Rebels Garage Las Vegas',
                 'Collision repair, paint and dent tips for Las Vegas drivers from The Rebels Garage.',
                 phero('Blog', 'From the shop', 'Body shop tips &amp; news.', 'Straight answers about collision repair, paint, dents and keeping your vehicle looking right in the desert.', 'blog', ctas=False)
                 + '<section><div class="wrap grid3">' + ''.join(post_card(p) for p in posts) + '</div></section>' + cta_band())

    P['404'] = ('Page not found | The Rebels Garage', 'This page could not be found.',
                phero('Not found', '404', 'Took a wrong turn.', 'That page does not exist. Head home or give the shop a call.'), {'noindex': True})
    return P


def visit_box():
    return (f'<div class="visit"><p><a href="{MAPS}" rel="noopener">{ic("pin")}{STREET}, {UNIT}<br>{CITY}</a></p>'
            f'<p><a href="tel:{PHONE_T}">{ic("phone")}{PHONE}</a></p><p><a href="mailto:{EMAIL}">{ic("mail")}{EMAIL}</a></p>'
            f'<h3>{ic("clock")}Hours</h3>{hours_list()}</div>')


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'blog'))
    posts = load_posts()
    urls = []
    for path, v in pages(posts).items():
        title, desc, body = v[:3]
        opts = v[3] if len(v) > 3 else {}
        doc = head(title, desc, path, extra=opts.get('extra', ''), noindex=opts.get('noindex', False)) + top(path) + body + foot()
        open(os.path.join(OUT, (path or 'index') + '.html'), 'w', encoding='utf-8').write(doc)
        if not opts.get('noindex'):
            urls.append((path, None))
    for p in posts:
        open(os.path.join(OUT, 'blog', p['slug'] + '.html'), 'w', encoding='utf-8').write(post_page(p, posts))
        urls.append(('blog/' + p['slug'], (p.get('updated') or p['date'])[:10]))
    sm = ''.join(f'<url><loc>{SITE}/{u}</loc>' + (f'<lastmod>{d}</lastmod>' if d else '') + '</url>' for u, d in urls)
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    write_variants(OUT)
    for f in ('styles.css', 'site.js'):
        shutil.copy(os.path.join(SRC, f), OUT)
    print('built', len(urls), 'pages:', len(posts), 'posts')


build()
