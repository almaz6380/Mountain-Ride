"""Build the standalone web app (GitHub Pages) into dist/, or with --app the store app's www/ (Capacitor).

index.html is written as an Artifact page (no doctype/head of its own), so this
adds the document head a normal website needs. The web build also gets the PWA
manifest and service worker; the app build has neither (the app ships its files).
"""
import pathlib, shutil, sys

APP = '--app' in sys.argv
root = pathlib.Path(__file__).resolve().parent.parent
dist = root / ('www' if APP else 'dist')
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
"""
if not APP:
    head += '<link rel="manifest" href="manifest.webmanifest">\n'
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
(dist / 'index.html').write_text(head + page + ('' if APP else sw) + "</html>\n", encoding='utf-8')
for f in ([] if APP else ['manifest.webmanifest', 'sw.js']) + [f.name for f in root.glob('*.html') if f.name != 'index.html']:
    shutil.copy(root / f, dist / f)   # privacy.html / imprint.html and friends
shutil.copytree(root / 'assets', dist / 'assets', ignore=shutil.ignore_patterns('key-art.jpg'))
if not APP:
    (dist / '.nojekyll').write_text('')
print('built', sorted(p.name for p in dist.iterdir()))
