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
    for l, loc in LANGS.items():
        d = listing[l]
        a = {'name': d['name'][:30], 'subtitle': d['subtitle'][:30], 'privacyPolicyUrl': PRIVACY}
        if loc in have_info:
            call('PATCH', f'/v1/appInfoLocalizations/{have_info[loc]}', {'data': {'type': 'appInfoLocalizations', 'id': have_info[loc], 'attributes': a}})
        else:
            call('POST', '/v1/appInfoLocalizations', {'data': {'type': 'appInfoLocalizations', 'attributes': dict(a, locale=loc),
                                                              'relationships': {'appInfo': rel('appInfos', INFO)}}})
        # Apple creates the version's localization together with the app info's one, so look it up only now
        have_ver = {x['attributes']['locale']: x['id'] for x in call('GET', f'/v1/appStoreVersions/{VER}/appStoreVersionLocalizations')['data']}
        desc = d['description']
        if d.get('gameCenter'):   # iOS only: the Game Center line goes right under the achievements line
            lines = desc.split('\n'); k = next(i for i, x in enumerate(lines) if x.startswith('•') and '15' in x)
            desc = '\n'.join(lines[:k + 1] + [d['gameCenter']] + lines[k + 1:])
        v = {'description': desc[:4000], 'keywords': keywords(d['keywords']), 'promotionalText': d['promotionalText'][:170],
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
    # no_ads and the coin packs are already used by other apps of the account: on iOS they carry the prefix mr_
    PRODUCTS = [  # id, type, price in EUR, title key, description key / coins
        ('starter_pack', 'NON_CONSUMABLE', 4.99, 'iap.starter', ('iap.starter.desc', 3000)),
        ('coin_doubler', 'NON_CONSUMABLE', 2.99, 'iap.doubler', ('iap.doubler.desc', 0)),
        ('mr_no_ads', 'NON_CONSUMABLE', 2.99, 'iap.noAds', ('iap.noAds.desc', 0)),
        ('mr_coins_small', 'CONSUMABLE', 0.99, 'iap.coinsS', ('iap.coins', 1000)),
        ('mr_coins_medium', 'CONSUMABLE', 4.99, 'iap.coinsM', ('iap.coins', 5500)),
        ('mr_coins_large', 'CONSUMABLE', 9.99, 'iap.coinsL', ('iap.coins', 12000)),
    ]
    shot = os.path.join(ROOT, 'store', 'iap-review.jpg')
    have = {p['attributes']['productId']: p['id'] for p in call('GET', f'/v1/apps/{APP}/inAppPurchasesV2', params={'limit': 200})['data']}
    territories = [t['id'] for t in call('GET', '/v1/territories', params={'limit': 200})['data']]
    for sku, kind, eur, tkey, (dkey, n) in PRODUCTS:
        if sku in have:
            pid = have[sku]
        else:
            pid = call('POST', '/v2/inAppPurchases', {'data': {'type': 'inAppPurchases', 'attributes': {
                'name': texts['de'][tkey][:30], 'productId': sku,
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

if 'gamecenter' in steps:
    # Game Center: leaderboards (distance, points, slalom time) and every medal of the game's achievements (ACH in
    # index.html) as mr_<id>_<tier>, texts from the game's translations, images from tools/gc-medals.js
    def game_texts():
        html = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read().split('\n')
        de = json.loads(next(l for l in html if l.startswith('  const I18N_DE = '))[len('  const I18N_DE = '):].rstrip(';'))
        js = open(os.path.join(ROOT, 'assets', 'lib', 'i18n.js'), encoding='utf8').read().split('\n')
        other = json.loads(next(l for l in js if l.startswith('window.I18N = '))[len('window.I18N = '):].rstrip(';'))
        ach = []
        for m in __import__('re').finditer(r"\{ id: '(\w+)', stat: '\w+', tiers: \[(\d+), (\d+), (\d+)\] \}", '\n'.join(html)):
            ach.append((m.group(1), [int(m.group(i)) for i in (2, 3, 4)]))
        return dict(other, de=de), ach
    TX, ACHS = game_texts()
    SEP = {'de': '.', 'en': ',', 'es': '.', 'pt': '.', 'fr': ' ', 'it': '.', 'ru': ' ', 'zh': ',', 'ja': ',', 'ar': ','}
    num = lambda n, l: f'{n:,}'.replace(',', SEP[l])
    BOARDS = [
        ('mr_distance', 'Longest run', 'INTEGER', 'DESC', ' m', {
            'de': 'Weiteste Fahrt', 'en': 'Longest Run', 'es': 'Bajada más larga', 'pt': 'Descida mais longa', 'fr': 'Plus longue descente',
            'it': 'Discesa più lunga', 'ru': 'Самый длинный заезд', 'zh': '最远距离', 'ja': '最長距離', 'ar': 'أطول مسافة'}),
        ('mr_score', 'High score', 'INTEGER', 'DESC', None, {
            'de': 'Höchste Punktzahl', 'en': 'High Score', 'es': 'Mejor puntuación', 'pt': 'Maior pontuação', 'fr': 'Meilleur score',
            'it': 'Punteggio migliore', 'ru': 'Рекорд очков', 'zh': '最高分', 'ja': 'ハイスコア', 'ar': 'أعلى نتيجة'}),
        ('mr_slalom', 'Slalom best time', 'ELAPSED_TIME_CENTISECOND', 'ASC', None, {
            'de': 'Slalom-Bestzeit', 'en': 'Slalom Best Time', 'es': 'Mejor tiempo de slalom', 'pt': 'Melhor tempo no slalom', 'fr': 'Meilleur temps en slalom',
            'it': 'Miglior tempo slalom', 'ru': 'Лучшее время в слаломе', 'zh': '回转赛最佳时间', 'ja': 'スラロームベストタイム', 'ar': 'أفضل وقت في السلالوم'}),
    ]
    detail = call('GET', f'/v1/apps/{APP}/gameCenterDetail')['data']
    if not detail:
        detail = call('POST', '/v1/gameCenterDetails', {'data': {'type': 'gameCenterDetails', 'relationships': {'app': rel('apps', APP)}}})['data']
    GCD = detail['id']
    have = {b['attributes']['vendorIdentifier']: b['id'] for b in call('GET', f'/v1/gameCenterDetails/{GCD}/gameCenterLeaderboards', params={'limit': 200})['data']}
    for vid, ref, form, sort, suffix, names in BOARDS:
        bid = have.get(vid) or call('POST', '/v1/gameCenterLeaderboards', {'data': {'type': 'gameCenterLeaderboards', 'attributes': {
            'referenceName': ref, 'vendorIdentifier': vid, 'defaultFormatter': form, 'submissionType': 'BEST_SCORE', 'scoreSortType': sort},
            'relationships': {'gameCenterDetail': rel('gameCenterDetails', GCD)}}})['data']['id']
        locs = {x['attributes']['locale'] for x in call('GET', f'/v1/gameCenterLeaderboards/{bid}/localizations', params={'limit': 50})['data']}
        for l, loc in LANGS.items():
            if loc in locs:
                continue
            attrs = {'locale': loc, 'name': names[l]}
            if suffix:
                attrs.update(formatterSuffix=suffix, formatterSuffixSingular=suffix)
            call('POST', '/v1/gameCenterLeaderboardLocalizations', {'data': {'type': 'gameCenterLeaderboardLocalizations', 'attributes': attrs,
                 'relationships': {'gameCenterLeaderboard': rel('gameCenterLeaderboards', bid)}}})
        print('leaderboard', vid, 'ok')
    have = {a['attributes']['vendorIdentifier']: a['id'] for a in call('GET', f'/v1/gameCenterDetails/{GCD}/gameCenterAchievements', params={'limit': 200})['data']}
    # achievement names (max. 30 characters): a short title per medal set, the tier as I / II / III
    NAMES = {
        'dist': ['Pistenkilometer', 'Kilometers', 'Kilómetros', 'Quilômetros', 'Kilomètres', 'Chilometri', 'Километры', '滑行里程', '滑走距離', 'الكيلومترات'],
        'far': ['Langstrecke', 'Long Haul', 'Larga distancia', 'Longa distância', 'Longue distance', 'Lunga distanza', 'Дальний заезд', '长途滑行', 'ロングラン', 'مسافة طويلة'],
        'score': ['Punktejäger', 'High Scorer', 'Cazapuntos', 'Caçador de pontos', 'Chasseur de points', 'Cacciatore di punti', 'Охотник за очками', '得分高手', 'スコアハンター', 'صياد النقاط'],
        'coins': ['Münzsammler', 'Coin Collector', 'Coleccionista', 'Colecionador', 'Collectionneur', 'Collezionista', 'Коллекционер', '金币收藏家', 'コインコレクター', 'جامع العملات'],
        'runs': ['Dauerfahrer', 'Regular', 'Habitual', 'Frequentador', 'Habitué', 'Habitué', 'Завсегдатай', '常客', '常連', 'متزلج دائم'],
        'spins': ['Drehwurm', 'Spin Master', 'Rey del giro', 'Rei dos giros', 'Roi des rotations', 'Re delle rotazioni', 'Мастер вращений', '旋转大师', 'スピンマスター', 'سيد الدوران'],
        'flips': ['Saltokönig', 'Flip King', 'Rey del mortal', 'Rei do mortal', 'Roi du salto', 'Re del salto', 'Король сальто', '空翻之王', 'フリップキング', 'ملك الشقلبة'],
        'combo': ['Kombokünstler', 'Combo Artist', 'Artista del combo', 'Artista do combo', 'Artiste du combo', 'Artista della combo', 'Мастер комбо', '连击艺术家', 'コンボアーティスト', 'فنان الكومبو'],
        'powers': ['Power-up-Fan', 'Power-up Fan', 'Fan de potenciadores', 'Fã de power-ups', 'Fan de bonus', 'Fan dei power-up', 'Любитель бонусов', '道具达人', 'パワーアップ好き', 'محب التعزيزات'],
        'gates': ['Abtaucher', 'Ducker', 'Agachado', 'Abaixado', 'Plongeur', 'Schivatore', 'Пригнись', '低头高手', 'くぐり名人', 'المنحني'],
        'crevasses': ['Spaltenspringer', 'Crevasse Jumper', 'Saltagrietas', 'Saltador de fendas', 'Sauteur de crevasses', 'Salta crepacci', 'Прыгун через трещины', '冰缝飞跃者', 'クレバスジャンパー', 'قافز الشقوق'],
        'cats': ['Überholer', 'Overtaker', 'Adelantador', 'Ultrapassador', 'Dépasseur', 'Sorpassatore', 'Обгоняющий', '超车高手', '追い越し名人', 'المتجاوز'],
        'avalanche': ['Lawinenflüchter', 'Avalanche Escape', 'Huida de alud', 'Fuga da avalanche', 'Échappée avalanche', 'Fuga dalla valanga', 'Побег от лавины', '逃离雪崩', '雪崩エスケープ', 'الهروب من الانهيار'],
        'places': ['Weltenbummler', 'Globetrotter', 'Trotamundos', 'Viajante', 'Globe-trotteur', 'Giramondo', 'Путешественник', '环球旅行者', '旅人', 'رحالة'],
        'slalom': ['Slalomprofi', 'Slalom Pro', 'Pro del slalom', 'Pro do slalom', 'Pro du slalom', 'Pro dello slalom', 'Профи слалома', '回转赛高手', 'スラロームプロ', 'محترف السلالوم'],
    }
    NAME_LANGS = ['de', 'en', 'es', 'pt', 'fr', 'it', 'ru', 'zh', 'ja', 'ar']
    POINTS = [10, 20, 35]
    for aid, tiers in ACHS:
        for t, n in enumerate(tiers):
            vid = f'mr_{aid}_{t + 1}'
            gid = have.get(vid) or call('POST', '/v1/gameCenterAchievements', {'data': {'type': 'gameCenterAchievements', 'attributes': {
                'referenceName': f'{aid} {t + 1}', 'vendorIdentifier': vid, 'points': POINTS[t], 'showBeforeEarned': True, 'repeatable': False},
                'relationships': {'gameCenterDetail': rel('gameCenterDetails', GCD)}}})['data']['id']
            locs = {x['attributes']['locale']: x['id'] for x in call('GET', f'/v1/gameCenterAchievements/{gid}/localizations', params={'limit': 50})['data']}
            for l, loc in LANGS.items():
                lid = locs.get(loc)
                if not lid:
                    text = TX[l]['ach.' + aid].replace('{n}', num(n, l)).replace('\u2066', '').replace('\u2069', '')   # Apple rejects bidi marks
                    lid = call('POST', '/v1/gameCenterAchievementLocalizations', {'data': {'type': 'gameCenterAchievementLocalizations', 'attributes': {
                        'locale': loc, 'name': NAMES[aid][NAME_LANGS.index(l)] + ' ' + 'I' * (t + 1), 'beforeEarnedDescription': text, 'afterEarnedDescription': text},
                        'relationships': {'gameCenterAchievement': rel('gameCenterAchievements', gid)}}})['data']['id']
                img = call('GET', f'/v1/gameCenterAchievementLocalizations/{lid}/gameCenterAchievementImage')['data']
                if img:
                    continue
                path = os.path.join(ROOT, 'store', 'gamecenter', vid + '.png')
                res = call('POST', '/v1/gameCenterAchievementImages', {'data': {'type': 'gameCenterAchievementImages', 'attributes': {
                    'fileName': vid + '.png', 'fileSize': os.path.getsize(path)},
                    'relationships': {'gameCenterAchievementLocalization': rel('gameCenterAchievementLocalizations', lid)}}})
                upload_asset(res, path)
                call('PATCH', f'/v1/gameCenterAchievementImages/{res["data"]["id"]}', {'data': {
                    'type': 'gameCenterAchievementImages', 'id': res['data']['id'], 'attributes': {'uploaded': True}}})
            print('achievement', vid, 'ok')
