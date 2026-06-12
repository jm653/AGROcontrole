import urllib.request
import json

try:
    req = urllib.request.Request(
        'https://query1.finance.yahoo.com/v8/finance/chart/KC=F?interval=1d&range=7d',
        headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        print('SUCESSO - Arabica ICE:', price)
except Exception as e:
    print('ERRO:', e)
