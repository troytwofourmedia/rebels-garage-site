"""Site images.

media/  holds one web-sized master of every photo (WebP, longest side 1600px).
img/    holds the cropped sizes the pages ask for, named <master>-<w>x<h>.webp.

Pages call variant(master, w, h) to get a cropped size. When the build runs on a
machine with Pillow installed (pip install pillow), any missing crops are made
from the masters and saved into img/ so they can be committed. Vercel does not
have Pillow, so it uses the committed crops and the build stops with a clear
message if one is missing.

To add a photo: save it into media/ as <name>.webp (or any format, then run
the build locally to make crops), reference it as /media/<name>.webp in a post,
or add it to IM in build.py.
"""
import os, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MEDIA = os.path.join(ROOT, 'media')
IMG = os.path.join(ROOT, 'img')
NEEDED = set()
FOCUS = {}  # master -> (x, y) crop anchor, 0 = left/top


def size_of(master):
    """Width and height of a master, read from the WebP header (no Pillow needed)."""
    with open(os.path.join(MEDIA, master + '.webp'), 'rb') as f:
        d = f.read(40)
    chunk = d[12:16]
    if chunk == b'VP8X':
        return 1 + int.from_bytes(d[24:27], 'little'), 1 + int.from_bytes(d[27:30], 'little')
    if chunk == b'VP8 ':
        return int.from_bytes(d[26:28], 'little') & 0x3fff, int.from_bytes(d[28:30], 'little') & 0x3fff
    if chunk == b'VP8L':
        b = int.from_bytes(d[21:25], 'little')
        return (b & 0x3fff) + 1, ((b >> 14) & 0x3fff) + 1
    return 0, 0


def variant(master, w, h):
    """A cropped size of a master. Pass h=0 to keep the photo's shape at width w."""
    NEEDED.add((master, int(w), int(h)))
    return f'/img/{master}-{int(w)}x{int(h)}.webp'


def _make(master, w, h, dest):
    from PIL import Image, ImageOps
    im = Image.open(os.path.join(MEDIA, master + '.webp'))
    im = im.convert('RGBA' if im.mode in ('RGBA', 'LA') else 'RGB')
    if h == 0:  # keep the photo's shape, just limit the width
        im.thumbnail((w, 10000), Image.LANCZOS)
    else:
        im = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=FOCUS.get(master, (0.5, 0.5)))
    im.save(dest, 'WEBP', quality=78, method=6)


def write_variants(out):
    os.makedirs(IMG, exist_ok=True)
    missing = [(m, w, h) for m, w, h in sorted(NEEDED) if not os.path.exists(os.path.join(IMG, f'{m}-{w}x{h}.webp'))]
    if missing:
        try:
            import PIL  # noqa: F401
        except ImportError:
            raise SystemExit('Missing image crops (run the build locally with Pillow and commit img/): '
                             + ', '.join(f'{m}-{w}x{h}' for m, w, h in missing[:10]))
        for m, w, h in missing:
            if not os.path.exists(os.path.join(MEDIA, m + '.webp')):
                raise SystemExit(f'No master photo media/{m}.webp')
            _make(m, w, h, os.path.join(IMG, f'{m}-{w}x{h}.webp'))
        print('made', len(missing), 'image crops')
    shutil.copytree(MEDIA, os.path.join(out, 'media'))
    shutil.copytree(IMG, os.path.join(out, 'img'))
