# Uploads Mountain Ride to Google Play with the Play Developer API (androidpublisher v3).
#   PLAY_SERVICE_ACCOUNT_JSON='{...}' PYTHONPATH=<dir with google-api-python-client> python3 tools/play-upload.py <steps> [aab]
# steps (comma separated): listing (texts + images in 10 languages), bundle (upload the .aab as a draft production
# release with release notes), products (the one-time products from store/products.md).
# The key comes only from the environment variable; nothing secret is written anywhere.
import json, os, sys, glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PKG = 'com.almaz6380.mountainride'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = {'en': 'en-US', 'de': 'de-DE', 'es': 'es-ES', 'pt': 'pt-BR', 'fr': 'fr-FR', 'it': 'it-IT', 'ru': 'ru-RU',
         'zh': 'zh-CN', 'ja': 'ja-JP', 'ar': 'ar'}
steps = sys.argv[1].split(',') if len(sys.argv) > 1 else ['listing']
aab = sys.argv[2] if len(sys.argv) > 2 else None

creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ['PLAY_SERVICE_ACCOUNT_JSON']), scopes=['https://www.googleapis.com/auth/androidpublisher'])
api = build('androidpublisher', 'v3', credentials=creds, cache_discovery=False)
listing = {l: json.load(open(os.path.join(ROOT, 'store', 'listing', l + '.json'))) for l in LANGS}

if 'listing' in steps or 'bundle' in steps:
    E = api.edits(); eid = E.insert(packageName=PKG, body={}).execute()['id']
    if 'listing' in steps:
        E.details().update(packageName=PKG, editId=eid, body={'defaultLanguage': 'en-US',
            'contactEmail': 'kontakt@wellbooked.at', 'contactWebsite': 'https://almaz6380.github.io/'}).execute()
        for l, code in LANGS.items():
            d = listing[l]
            E.listings().update(packageName=PKG, editId=eid, language=code, body={'language': code, 'title': d['name'],
                'shortDescription': d['shortDescription'], 'fullDescription': d['description']}).execute()
            for kind, files in (('phoneScreenshots', sorted(glob.glob(os.path.join(ROOT, 'store', 'screenshots', l, 'android-*.jpg')))),
                                ('featureGraphic', [os.path.join(ROOT, 'store', 'feature-graphic.png')]),
                                ('icon', [os.path.join(ROOT, 'assets', 'icon-512.png')])):
                E.images().deleteall(packageName=PKG, editId=eid, language=code, imageType=kind).execute()
                for f in files:
                    E.images().upload(packageName=PKG, editId=eid, language=code, imageType=kind,
                                      media_body=MediaFileUpload(f, mimetype='image/jpeg' if f.endswith('.jpg') else 'image/png')).execute()
            print('listing', code, 'ok')
    if 'bundle' in steps:
        b = E.bundles().upload(packageName=PKG, editId=eid,
                               media_body=MediaFileUpload(aab, mimetype='application/octet-stream', resumable=True)).execute()
        vc = b['versionCode']; print('bundle versionCode', vc)
        notes = [{'language': code, 'text': listing[l]['whatsNew'][:500]} for l, code in LANGS.items()]
        E.tracks().update(packageName=PKG, editId=eid, track='production', body={'track': 'production', 'releases': [
            {'name': '1.0', 'versionCodes': [str(vc)], 'status': 'draft', 'releaseNotes': notes}]}).execute()
    print('validate', E.validate(packageName=PKG, editId=eid).execute().get('id'))
    E.commit(packageName=PKG, editId=eid).execute(); print('committed')

if 'products' in steps:
    # names and descriptions come from the game's own texts
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read()
    i = src.index('const I18N_DE = ') + len('const I18N_DE = ')
    texts = {'de': json.JSONDecoder().raw_decode(src[i:])[0]}
    js = open(os.path.join(ROOT, 'assets', 'lib', 'i18n.js'), encoding='utf8').read()
    texts.update(json.loads(js[js.index('{'):js.rindex('}') + 1]))
    fmt = lambda s, n: s.replace('{n}', f'{n:,}'.replace(',', '.'))
    PRODUCTS = [  # id, price in EUR, title key, description key / coins
        ('starter_pack', 4.99, 'iap.starter', ('iap.starter.desc', 3000)),
        ('coin_doubler', 2.99, 'iap.doubler', ('iap.doubler.desc', 0)),
        ('no_ads', 2.99, 'iap.noAds', ('iap.noAds.desc', 0)),
        ('coins_small', 0.99, 'iap.coinsS', ('iap.coins', 1000)),
        ('coins_medium', 4.99, 'iap.coinsM', ('iap.coins', 5500)),
        ('coins_large', 9.99, 'iap.coinsL', ('iap.coins', 12000)),
    ]
    om = api.monetization()
    for sku, eur, tkey, (dkey, n) in PRODUCTS:
        # new one-time product API: one "buy" option, prices for every region converted from the euro price
        units, cents = int(eur), round((eur - int(eur)) * 100)
        conv = om.convertRegionPrices(packageName=PKG, body={'price': {'currencyCode': 'EUR', 'units': str(units), 'nanos': cents * 10_000_000}}).execute()
        regions = [{'regionCode': r, 'price': v['price'], 'availability': 'AVAILABLE'} for r, v in conv['convertedRegionPrices'].items()]
        body = {'packageName': PKG, 'productId': sku,
                'listings': [{'languageCode': code, 'title': texts[l][tkey][:55], 'description': fmt(texts[l][dkey], n)[:200]} for l, code in LANGS.items()],
                'purchaseOptions': [{'purchaseOptionId': 'buy', 'buyOption': {'legacyCompatible': True, 'multiQuantityEnabled': False},
                                     'regionalPricingAndAvailabilityConfigs': regions}]}
        try:
            om.onetimeproducts().patch(packageName=PKG, productId=sku, allowMissing=True, updateMask='listings,purchaseOptions',
                                       regionsVersion_version=conv.get('regionVersion', {}).get('version', '2022/02'), body=body).execute()
            om.onetimeproducts().purchaseOptions().batchUpdateStates(packageName=PKG, productId=sku, body={'requests': [
                {'activatePurchaseOptionRequest': {'packageName': PKG, 'productId': sku, 'purchaseOptionId': 'buy'}}]}).execute()
            print('product', sku, 'ok', len(regions), 'regions')
        except Exception as e:
            print('product', sku, 'FAILED', str(e)[:400])
