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
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#2b3d63">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Mountain Ride">
<link rel="manifest" href="manifest.webmanifest">
"""
page = (root / 'index.html').read_text(encoding='utf-8')
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
