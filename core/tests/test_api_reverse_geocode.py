from django.test import TestCase, Client, override_settings
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO
import os

@override_settings(ALLOWED_HOSTS=['testserver'])
class TestReverseGeocode(TestCase):
    def setUp(self):
        self.client = Client()

    def test_mapbox_401_fallback(self):
        os.environ['MAPBOX_ACCESS_TOKEN'] = 'bad'
        def _raise(req, timeout=8):
            raise HTTPError(req.full_url, 401, 'Unauthorized', hdrs={}, fp=None)
        with patch('core.api_views.urlopen', side_effect=_raise):
            r = self.client.get('/api/addresses/reverse-geocode', {'lat': '33.3', 'lng': '44.4'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['provider'], 'mapbox')
        self.assertEqual(r.json()['formatted'], '')
        os.environ.pop('MAPBOX_ACCESS_TOKEN', None)

    def test_nominatim_success(self):
        os.environ.pop('MAPBOX_ACCESS_TOKEN', None)
        os.environ.pop('MAPS_API_KEY', None)
        payload = {
            'address': {
                'city': 'Baghdad',
                'suburb': 'Karrada',
                'road': 'Street',
                'house_number': '10'
            },
            'display_name': 'Baghdad, Iraq'
        }
        body = BytesIO()
        body.write(str.encode(__import__('json').dumps(payload)))
        body.seek(0)
        class _Resp:
            def __init__(self, b): self._b=b
            def read(self): return self._b.read()
        with patch('core.api_views.urlopen', return_value=_Resp(body)):
            r = self.client.get('/api/addresses/reverse-geocode', {'lat': '33.3', 'lng': '44.4'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['provider'], 'nominatim')
        self.assertEqual(data['city'], 'Baghdad')
