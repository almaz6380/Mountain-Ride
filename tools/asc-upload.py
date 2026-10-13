# Uploads Mountain Ride to App Store Connect with the App Store Connect API.
#   ASC_KEY_ID=… ASC_ISSUER_ID=… ASC_KEY_P8=<base64 of the .p8> python3 tools/asc-upload.py <steps>
# steps (comma separated): meta (category, age rating, free price, URLs), listing (texts + iPhone 6.9" screenshots
# in 10 languages), products (the in-app purchases from store/products.md).
# The app record itself must already exist (Apple only lets a person click „Neue App“).
# App privacy („App-Datenschutz“) has no public API: enter it by hand from store/privacy-answers.md.
import base64, glob, hashlib, json, os, sys, time
import jwt, requests

BUNDLE = 'com.almaz6380.mountainride'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = {'en': 'en-US', 'de': 'de-DE', 'es': 'es-ES', 'pt': 'pt-BR', 'fr': 'fr-FR', 'it': 'it', 'ru': 'ru',
         'zh': 'zh-Hans', 'ja': 'ja', 'ar': 'ar-SA'}
SITE = 'https://almaz6380.github.io/Mountain-Ride/'
PRIVACY = SITE + 'privacy.html'
steps = sys.argv[1].split(',') if len(sys.argv) > 1 else ['listing']
KEY = base64.b64decode(os.environ['ASC_KEY_P8']).decode()


def token():
    now = int(time.time())
    return jwt.encode({'iss': os.environ['ASC_ISSUER_ID'], 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'},
                      KEY, algorithm='ES256', headers={'kid': os.environ['ASC_KEY_ID'], 'typ': 'JWT'})


def call(method, path, body=None, params=None, ok=()):
    url = path if path.startswith('http') else 'https://api.appstoreconnect.apple.com' + path
    r = requests.request(method, url, json=body, params=params, timeout=120,
                         headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    if r.status_code >= 400:
        if r.status_code in ok:
            return None
        raise SystemExit(f'{method} {path} -> {r.status_code}\n{r.text[:2000]}')
    return r.json() if r.text else {}


def rel(kind, id_):
    return {'data': {'type': kind, 'id': id_}}


def keywords(s, limit=100):
    out = []
    for k in s.split(','):
        if len(','.join(out + [k])) > limit:
            break
        out.append(k)
    return ','.join(out)


def upload_asset(reservation, path):
    data = open(path, 'rb').read()
    for op in reservation['data']['attributes']['uploadOperations']:
        chunk = data[op['offset']:op['offset'] + op['length']]
        requests.request(op['method'], op['url'], data=chunk, timeout=300,
                         headers={h['name']: h['value'] for h in op.get('requestHeaders', [])}).raise_for_status()
    return hashlib.md5(data).hexdigest()


apps = call('GET', '/v1/apps', params={'filter[bundleId]': BUNDLE})['data']
if not apps:
    raise SystemExit('App not found in App Store Connect yet – create it there first („Neue App“).')
APP = apps[0]['id']
listing = {l: json.load(open(os.path.join(ROOT, 'store', 'listing', l + '.json'), encoding='utf8')) for l in LANGS}
version = next(v for v in call('GET', f'/v1/apps/{APP}/appStoreVersions', params={'filter[platform]': 'IOS'})['data']
               if v['attributes']['appStoreState'] in ('PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED',
                                                        'METADATA_REJECTED', 'INVALID_BINARY'))
VER = version['id']
info = next(i for i in call('GET', f'/v1/apps/{APP}/appInfos')['data']
            if i['attributes'].get('appStoreState', i['attributes'].get('state')) not in ('READY_FOR_SALE', 'READY_FOR_DISTRIBUTION'))
INFO = info['id']
print('app', APP, 'version', VER, version['attributes']['versionString'], 'info', INFO)

if 'meta' in steps:
    call('PATCH', f'/v1/appInfos/{INFO}', {'data': {'type': 'appInfos', 'id': INFO, 'relationships': {
        'primaryCategory': rel('appCategories', 'GAMES'), 'primarySubcategoryOne': rel('appCategories', 'GAMES_ACTION'),
        'primarySubcategoryTwo': rel('appCategories', 'GAMES_SPORTS'), 'secondaryCategory': rel('appCategories', 'SPORTS')}}})
    call('PATCH', f'/v1/apps/{APP}', {'data': {'type': 'apps', 'id': APP, 'attributes': {
        'contentRightsDeclaration': 'DOES_NOT_USE_THIRD_PARTY_CONTENT'}}})
    # age rating: everything „none“, except user-generated names (leaderboards, live duel without chat) and ads
    age = call('GET', f'/v1/appInfos/{INFO}/ageRatingDeclaration')['data']
    attrs = {'alcoholTobaccoOrDrugUseOrReferences': 'NONE', 'contests': 'NONE', 'gamblingSimulated': 'NONE',
             'horrorOrFearThemes': 'NONE', 'matureOrSuggestiveThemes': 'NONE', 'medicalOrTreatmentInformation': 'NONE',
             'profanityOrCrudeHumor': 'NONE', 'sexualContentGraphicAndNudity': 'NONE', 'sexualContentOrNudity': 'NONE',
             'violenceCartoonOrFantasy': 'NONE', 'violenceRealistic': 'NONE', 'violenceRealisticProlongedGraphicOrSadistic': 'NONE',
             'gambling': False, 'unrestrictedWebAccess': False, 'kidsAgeBand': None,
             'gunsOrOtherWeapons': 'NONE', 'messagingAndChat': False, 'userGeneratedContent': True, 'advertising': True,
             'lootBox': False, 'healthOrWellnessTopics': False, 'parentalControls': False, 'ageAssurance': False}
    # Apple adds new questions now and then; drop any the API does not know (yet)
    for _ in range(len(attrs)):
        r = requests.patch(f'https://api.appstoreconnect.apple.com/v1/ageRatingDeclarations/{age["id"]}', timeout=60,
                           headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'},
                           json={'data': {'type': 'ageRatingDeclarations', 'id': age['id'], 'attributes': attrs}})
        if r.ok:
            break
        bad = [e.get('source', {}).get('pointer', '').rsplit('/', 1)[-1] for e in r.json().get('errors', [])]
        bad = [b for b in bad if b in attrs]
        if not bad:
            raise SystemExit('age rating ' + r.text[:1500])
        for b in bad:
            attrs.pop(b)
    print('age rating ok')
    # free in every territory
    call('POST', '/v1/appPriceSchedules', {'data': {'type': 'appPriceSchedules', 'relationships': {
        'app': rel('apps', APP), 'baseTerritory': rel('territories', 'USA'),
        'manualPrices': {'data': [{'type': 'appPrices', 'id': '${free}'}]}}},
        'included': [{'type': 'appPrices', 'id': '${free}', 'attributes': {'startDate': None}, 'relationships': {
            'appPricePoint': rel('appPricePoints', next(p['id'] for p in call('GET', f'/v1/apps/{APP}/appPricePoints', params={
                'filter[territory]': 'USA', 'limit': 200})['data'] if float(p['attributes']['customerPrice']) == 0))}}]})
    print('price free')
    call('PATCH', f'/v1/appStoreVersions/{VER}', {'data': {'type': 'appStoreVersions', 'id': VER, 'attributes': {
        'copyright': '2026 Josef Gallab', 'releaseType': 'MANUAL'}}})
    print('meta ok')

if 'listing' in steps:
    have_info = {x['attributes']['locale']: x['id'] for x in call('GET', f'/v1/appInfos/{INFO}/appInfoLocalizations')['data']}
    have_ver = {x['attributes']['locale']: x['id'] for x in call('GET', f'/v1/appStoreVersions/{VER}/appStoreVersionLocalizations')['data']}
    for l, loc in LANGS.items():
        d = listing[l]
        a = {'name': d['name'][:30], 'subtitle': d['subtitle'][:30], 'privacyPolicyUrl': PRIVACY}
        if loc in have_info:
            call('PATCH', f'/v1/appInfoLocalizations/{have_info[loc]}', {'data': {'type': 'appInfoLocalizations', 'id': have_info[loc], 'attributes': a}})
        else:
            call('POST', '/v1/appInfoLocalizations', {'data': {'type': 'appInfoLocalizations', 'attributes': dict(a, locale=loc),
                                                              'relationships': {'appInfo': rel('appInfos', INFO)}}})
        v = {'description': d['description'][:4000], 'keywords': keywords(d['keywords']), 'promotionalText': d['promotionalText'][:170],
             'supportUrl': SITE, 'marketingUrl': SITE}
        if loc in have_ver:
            vid = have_ver[loc]
            call('PATCH', f'/v1/appStoreVersionLocalizations/{vid}', {'data': {'type': 'appStoreVersionLocalizations', 'id': vid, 'attributes': v}})
        else:
            vid = call('POST', '/v1/appStoreVersionLocalizations', {'data': {'type': 'appStoreVersionLocalizations', 'attributes': dict(v, locale=loc),
                       'relationships': {'appStoreVersion': rel('appStoreVersions', VER)}}})['data']['id']
        # screenshots: 1290 × 2796 goes into the 6.9" slot (APP_IPHONE_67)
        sets = call('GET', f'/v1/appStoreVersionLocalizations/{vid}/appScreenshotSets')['data']
        sset = next((s['id'] for s in sets if s['attributes']['screenshotDisplayType'] == 'APP_IPHONE_67'), None)
        if sset:
            for s in call('GET', f'/v1/appScreenshotSets/{sset}/appScreenshots')['data']:
                call('DELETE', f'/v1/appScreenshots/{s["id"]}')
        else:
            sset = call('POST', '/v1/appScreenshotSets', {'data': {'type': 'appScreenshotSets', 'attributes': {'screenshotDisplayType': 'APP_IPHONE_67'},
                        'relationships': {'appStoreVersionLocalization': rel('appStoreVersionLocalizations', vid)}}})['data']['id']
        for f in sorted(glob.glob(os.path.join(ROOT, 'store', 'screenshots', l, 'ios-*.jpg'))):
            res = call('POST', '/v1/appScreenshots', {'data': {'type': 'appScreenshots', 'attributes': {
                'fileName': os.path.basename(f), 'fileSize': os.path.getsize(f)}, 'relationships': {'appScreenshotSet': rel('appScreenshotSets', sset)}}})
            md5 = upload_asset(res, f)
            call('PATCH', f'/v1/appScreenshots/{res["data"]["id"]}', {'data': {'type': 'appScreenshots', 'id': res['data']['id'],
                 'attributes': {'uploaded': True, 'sourceFileChecksum': md5}}})
        print('listing', loc, 'ok')

if 'products' in steps:
    # names and descriptions come from the game's own texts (same as tools/play-upload.py)
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read()
    i = src.index('const I18N_DE = ') + len('const I18N_DE = ')
    texts = {'de': json.JSONDecoder().raw_decode(src[i:])[0]}
    js = open(os.path.join(ROOT, 'assets', 'lib', 'i18n.js'), encoding='utf8').read()
    texts.update(json.loads(js[js.index('{'):js.rindex('}') + 1]))
    fmt = lambda s, n: s.replace('{n}', f'{n:,}'.replace(',', '.'))
    PRODUCTS = [  # id, type, price in EUR, title key, description key / coins
        ('starter_pack', 'NON_CONSUMABLE', 4.99, 'iap.starter', ('iap.starter.desc', 3000)),
        ('coin_doubler', 'NON_CONSUMABLE', 2.99, 'iap.doubler', ('iap.doubler.desc', 0)),
        ('no_ads', 'NON_CONSUMABLE', 2.99, 'iap.noAds', ('iap.noAds.desc', 0)),
        ('coins_small', 'CONSUMABLE', 0.99, 'iap.coinsS', ('iap.coins', 1000)),
        ('coins_medium', 'CONSUMABLE', 4.99, 'iap.coinsM', ('iap.coins', 5500)),
        ('coins_large', 'CONSUMABLE', 9.99, 'iap.coinsL', ('iap.coins', 12000)),
    ]
    shot = os.path.join(ROOT, 'store', 'iap-review.jpg')
    have = {p['attributes']['productId']: p['id'] for p in call('GET', f'/v1/apps/{APP}/inAppPurchasesV2', params={'limit': 200})['data']}
    territories = [t['id'] for t in call('GET', '/v1/territories', params={'limit': 200})['data']]
    for sku, kind, eur, tkey, (dkey, n) in PRODUCTS:
        if sku in have:
            pid = have[sku]
        else:
            pid = call('POST', '/v2/inAppPurchases', {'data': {'type': 'inAppPurchases', 'attributes': {
                'name': texts['de'][tkey][:30] if sku != 'coins_small' else 'Münzen 1000', 'productId': sku,
                'inAppPurchaseType': kind, 'reviewNote': 'Shop → Münzen. ' + fmt(texts['en'][dkey], n), 'familySharable': False},
                'relationships': {'app': rel('apps', APP)}}})['data']['id']
        have_loc = {x['attributes']['locale']: x['id'] for x in call('GET', f'/v2/inAppPurchases/{pid}/inAppPurchaseLocalizations')['data']}
        for l, loc in LANGS.items():
            a = {'name': texts[l][tkey][:30], 'description': fmt(texts[l][dkey], n)[:45]}
            if loc in have_loc:
                call('PATCH', f'/v1/inAppPurchaseLocalizations/{have_loc[loc]}', {'data': {'type': 'inAppPurchaseLocalizations', 'id': have_loc[loc], 'attributes': a}})
            else:
                call('POST', '/v1/inAppPurchaseLocalizations', {'data': {'type': 'inAppPurchaseLocalizations', 'attributes': dict(a, locale=loc),
                     'relationships': {'inAppPurchaseV2': rel('inAppPurchases', pid)}}})
        # price: the euro tier in Germany, Apple converts it for every other country
        points = call('GET', f'/v2/inAppPurchases/{pid}/pricePoints', params={'filter[territory]': 'DEU', 'limit': 8000})['data']
        pp = next(p['id'] for p in points if abs(float(p['attributes']['customerPrice']) - eur) < 0.005)
        call('POST', '/v1/inAppPurchasePriceSchedules', {'data': {'type': 'inAppPurchasePriceSchedules', 'relationships': {
            'inAppPurchase': rel('inAppPurchases', pid), 'baseTerritory': rel('territories', 'DEU'),
            'manualPrices': {'data': [{'type': 'inAppPurchasePrices', 'id': '${p}'}]}}},
            'included': [{'type': 'inAppPurchasePrices', 'id': '${p}', 'attributes': {'startDate': None},
                          'relationships': {'inAppPurchasePricePoint': rel('inAppPurchasePricePoints', pp)}}]})
        call('POST', '/v1/inAppPurchaseAvailabilities', {'data': {'type': 'inAppPurchaseAvailabilities',
             'attributes': {'availableInNewTerritories': True}, 'relationships': {
                 'inAppPurchase': rel('inAppPurchases', pid), 'availableTerritories': {'data': [{'type': 'territories', 'id': t} for t in territories]}}}}, ok=(409,))
        # Apple wants one screenshot of the purchase for the review: the shop's coin tab
        old = call('GET', f'/v2/inAppPurchases/{pid}/appStoreReviewScreenshot', ok=(404,)) or {}
        if os.path.exists(shot) and not old.get('data'):
            res = call('POST', '/v1/inAppPurchaseAppStoreReviewScreenshots', {'data': {'type': 'inAppPurchaseAppStoreReviewScreenshots',
                       'attributes': {'fileName': 'iap-review.jpg', 'fileSize': os.path.getsize(shot)},
                       'relationships': {'inAppPurchaseV2': rel('inAppPurchases', pid)}}})
            md5 = upload_asset(res, shot)
            call('PATCH', f'/v1/inAppPurchaseAppStoreReviewScreenshots/{res["data"]["id"]}', {'data': {
                'type': 'inAppPurchaseAppStoreReviewScreenshots', 'id': res['data']['id'], 'attributes': {'uploaded': True, 'sourceFileChecksum': md5}}})
        print('product', sku, 'ok', eur, '€')
