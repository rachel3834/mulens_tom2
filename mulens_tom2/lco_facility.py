from django.core.cache import cache
from django.conf import settings
from tom_observations.facilities.lco import make_request

PORTAL_URL = 'https://observe.lco.global'
LCO_SETTINGS = settings.FACILITIES['LCO']

class LCOInstruments():

    def __init__(self):
        self.imagers = {
                    'coj.clma.2m0.fs01': 'Australia Clamshell A 2m, FS01',
                    'coj.doma.1m0.fa12': 'Australia Dome A 1m, FA12',
                    'coj.domb.1m0.fa11': 'Australia Dome B 1m, FA11',
                    'coj.clma.0m4.kb97': 'Australia Clamshell A 0m4 A, KB97',
                    'coj.clma.0m4.kb56': 'Australia Clamshell A 0m4 B, KB56',

                    'cpt.doma.1m0.fa16': 'South Africa Dome A, FA16',
                    'cpt.domb.1m0.fa14': 'South Africa Dome B, FA14',
                    'cpt.domc.1m0.fa06': 'South Africa Dome C, FA06',
                    'cpt.aqwa.0m4.kb84': 'South Africa Aqawan A 0m4 A, KB84',

                    'tfn.aqwa.0m4.kb81': 'Tenerife Aqawan A 0m4 A, KB81',
                    'tfn.aqwb.0m4.kb98': 'Tenerife Aqawan A 0m4 B, KB98',

                    'lsc.doma.1m0.fa15': 'Chile Dome A 1m, FA15',
                    'lsc.domb.1m0.fa04': 'Chile Dome B 1m, FA04',
                    'lsc.domc.1m0.fa03': 'Chile Dome C 1m, FA03',
                    'lsc.aqwa.0m4.kb96': 'Chile Aqawan A 0m4 A, KB96',
                    'lsc.aqwb.0m4.kb26': 'Chile Aqawan B 0m4 B, KB26',

                    'elp.doma.1m0.fa05': 'Texas Dome A 1m, FA05',
                    'elp.domb.1m0.fa07': 'Texas Dome B 1m, FA07',
                    'elp.aqwa.0m4.kb88': 'Texas Aqawan A 0m4, KB88',

                    'ogg.clma.2m0.fs02': 'Hawaii Clamshell A 2m, FS02',
                    'ogg.aqwb.0m4.kb27': 'Hawaii Aqawan B 0m4, KB27',
                    'ogg.aqwc.0m4.kb82': 'Hawaii Aqawan C 0m4, KB82',

                    }

        self.spectrographs = {
                    'coj.clma.2m0.en12': 'Australia Clamshell A 2m, FLOYDS',

                    'tlv.doma.1m0.fa18': 'Israel Dome A 1m, NRES',

                    'cpt.domb.1m0.fa13': 'South Africa Dome B, NRES',

                    'lsc.domb.1m0.fa09': 'Chile Dome B 1m, NRES',

                    'elp.domb.1m0.fa17': 'Texas Dome B 1m, NRES',

                    'ogg.clma.2m0.en06': 'Hawaii Clamshell A 2m, FLOYDS',

                    }

    def get_imagers_tuple(self):

        imagers = []
        for idcode, name in self.imagers.items():
            imagers.append( (idcode, name) )

        return tuple(imagers)

    def get_instrument_class_data(self):
        cached_instruments = cache.get('lco_instruments')

        if not cached_instruments:
            response = make_request(
                'GET',
                PORTAL_URL + '/api/instruments/',
                headers={'Authorization': 'Token {0}'.format(LCO_SETTINGS['api_key'])}
            )
            cached_instruments = {k: v for k, v in response.json().items() if 'SOAR' not in k}
            cache.set('lco_instruments', cached_instruments)

        return cached_instruments

    def get_filter_choices(self):
        return set([
            (f['code'], f['name']) for ins in self.get_instrument_class_data().values() for f in
            ins['optical_elements'].get('filters', []) + ins['optical_elements'].get('slits', [])
            ])
