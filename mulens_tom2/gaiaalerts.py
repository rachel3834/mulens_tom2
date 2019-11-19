from tom_alerts.alerts import GenericQueryForm, GenericAlert, GenericBroker
from tom_alerts.models import BrokerQuery
from tom_targets.models import Target
from dateutil.parser import parse
from django import forms
from astropy.coordinates import SkyCoord
import astropy.units as u
import requests
import json
from os import path

BROKER_URL = 'http://gsaweb.ast.cam.ac.uk/alerts/alertsindex'

class GaiaAlertsQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)
    cone = forms.CharField(
        required=False,
        label='Cone Search',
        help_text='RA,Dec,radius in degrees'
    )

class GaiaAlertsBroker(GenericBroker):
    name = 'Gaia Alerts'
    form = GaiaAlertsQueryForm

    def fetch_alerts(self, parameters):
        """Must return an iterator"""
        response = requests.get(BROKER_URL)
        response.raise_for_status()

        html_data = response.text.split('\n')
        for line in html_data:
            if 'var alerts' in line:
                alerts_data = line.replace('var alerts = ', '').replace('\n','').replace(';','')

        alert_list = json.loads(alerts_data)

        if parameters['cone'] != None and len(parameters['cone']) > 0:
            cone_params = parameters['cone'].split(',')
            parameters['cone_ra'] = float(cone_params[0])
            parameters['cone_dec'] = float(cone_params[1])
            parameters['cone_radius'] = float(cone_params[2])*u.deg
            parameters['cone_centre'] = SkyCoord(float(cone_params[0]),
                                                 float(cone_params[1]),
                                                 frame="icrs", unit="deg")

        filtered_alerts = []
        for alert in alert_list:
            if parameters['target_name'] != None and len(parameters['target_name']) > 0:
                if parameters['target_name'] in alert['name']:
                    filtered_alerts.append(alert)
            else:
                filtered_alerts.append(alert)

        filtered_alerts2 = []
        for alert in filtered_alerts:
            if 'cone_radius' in parameters.keys():
                c = SkyCoord(float(alert['ra']), float(alert['dec']),
                             frame="icrs", unit="deg")
                if parameters['cone_centre'].separation(c) <= parameters['cone_radius']:
                    filtered_alerts2.append(alert)

        return iter(filtered_alerts2)

    def to_generic_alert(self, alert):
        timestamp = parse(alert['obstime'])
        url = BROKER_URL.replace('/alerts/alertsindex', alert['per_alert']['link'])

        return GenericAlert(
            timestamp=timestamp,
            url=url,
            id=alert['name'],
            name=alert['name'],
            ra=alert['ra'],
            dec=alert['dec'],
            mag=alert['alertMag'],
            score=1.0
        )
