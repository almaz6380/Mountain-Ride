"""Build the standalone web app (GitHub Pages) into dist/.

index.html is written as an Artifact page (no doctype/head of its own), so this
adds the document head a normal website needs, plus the PWA manifest and
service worker registration.
"""
import pathlib, shutil

root = pathlib.Path(__file__).resolve().parent.parent
dist = root / 'dist'
if dist.exists():
    shutil.rmtree(dist)
dist.mkdir()

head = """<!doctype html>
<html lang="de">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#2b3d63">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Mountain Ride">
<link rel="manifest" href="manifest.webmanifest">
"""
page = (root / 'index.html').read_text(encoding='utf-8')
# the web app and the store apps run without any CDN: libraries and fonts come from assets/lib
LOCAL = [
    ('<link rel="preconnect" href="https://fonts.googleapis.com">\n', ''),
    ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n', ''),
    ('https://fonts.googleapis.com/css2?family=Bowlby+One+SC&family=Barlow+Condensed:wght@500;600;800&display=swap', 'assets/lib/fonts/fonts.css'),
    ('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'assets/lib/three.min.js'),
    ('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js', 'assets/lib/GLTFLoader.js'),
    ('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.min.js', 'assets/lib/supabase.min.js'),
]
for old, new in LOCAL:
    assert old in page, 'missing in index.html: ' + old
    page = page.replace(old, new)
sw = """
<script>
if ('serviceWorker' in navigator) addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
</script>
"""
(dist / 'index.html').write_text(head + page + sw + "</html>\n", encoding='utf-8')
for f in ['manifest.webmanifest', 'sw.js']:
    shutil.copy(root / f, dist / f)
shutil.copytree(root / 'assets', dist / 'assets', ignore=shutil.ignore_patterns('key-art.jpg'))
(dist / '.nojekyll').write_text('')
print('built', sorted(p.name for p in dist.iterdir()))
