from django import template
from plotly import offline
import plotly.graph_objs as go
from tom_targets.models import Target, TargetExtra
from tom_dataproducts.models import DataProduct
from django.conf import settings
import numpy as np
from os import path

register = template.Library()


@register.inclusion_tag('mulens_tom2/finderchart.html')
def navigable_image(target):

    def fetch_finder(target):

        params = {}

        keylist = ['finder_naxis1', 'finder_naxis2', 'finder_pixscale']

        for key in keylist:
            qs = TargetExtra.objects.filter(target=target, key=key)
            if len(qs) > 0:
                params[key] = float(qs[0].value)

        qs = DataProduct.objects.filter(target=target)

        image_file = None
        for data in qs:
            if '_finder_' in str(data.data):
                image_file = path.join('/data', str(data.data))

        if len(params) == len(keylist):
            return params, image_file
        else:
            return {},None

    (params,image_file) = fetch_finder(target)

    if len(params) > 0:
        half_width_y = ( (params['finder_naxis1']/2.0) * params['finder_pixscale'] ) / 3600.0
        half_width_x = ( (params['finder_naxis2']/2.0) * params['finder_pixscale'] ) / 3600.0

        xdata = np.linspace(float(target.ra)-half_width_x,float(target.ra)+half_width_x,50.0)
        ydata = np.linspace(float(target.dec)-half_width_y,float(target.dec)+half_width_y,50.0)

        scale_factor = 1.75

        fig = go.Figure()

        fig.update_xaxes(
                    visible=True,

                    range=[xdata.min(), xdata.max()],
                    title=go.layout.xaxis.Title(
                        text='RA [mag]',
                        font=dict(
                            size=18,
                            color='black')),
                    linecolor='black',
                    color = 'black'
                )

        fig.update_yaxes(
                    visible=True,
                    range=[ydata.min(), ydata.max()],
                    # the scaleanchor attribute ensures that the aspect ratio stays constant
                    scaleanchor="x",
                    title=go.layout.yaxis.Title(
                        text='Dec [deg]',
                        font=dict(
                            size=18,
                            color='black')),
                    linecolor='black',
                    color = 'black'
                )

        fig.update_layout(
                    images=[go.layout.Image(
                        x=xdata.min(),
                        sizex=((xdata.max()-xdata.min())),
                        y=ydata.max(),
                        sizey=abs((ydata.max()-ydata.min())),
                        xref="x",
                        yref="y",
                        opacity=1.0,
                        layer="below",
                        sizing="stretch",
                        source=image_file)]
                )

        fig.update_layout(
                    font=dict(color="black",size=20),
                    width=(params['finder_naxis1']*scale_factor),
                    height=(params['finder_naxis2']*scale_factor),
                    #margin={"l": 0, "r": 0, "t": 0, "b": 0},
                    margin={"l": 55, "r": 15, "t": 55, "b": 55},
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                )

        return {
            'target': target,
            'plot': offline.plot(fig, output_type='div', show_link=False),
        }

    else:

        if image_file != None:
            plot = '<img src="{% data '+image_file+' %}" class="img-fluid mx-auto">'

        else:
            plot = """<!-- include Aladin Lite CSS file in the head section of your page -->
            <link rel="stylesheet" href="//aladin.u-strasbg.fr/AladinLite/api/v2/latest/aladin.min.css" />
            <!-- insert this snippet where you want Aladin Lite viewer to appear and after the loading of jQuery -->
            <div id="aladin-lite-div" style="width:600px;height:600px;"></div>
            <script type="text/javascript" src="//aladin.u-strasbg.fr/AladinLite/api/v2/latest/aladin.min.js" charset="utf-8"></script>
            <script type="text/javascript">
                var aladin = A.aladin('#aladin-lite-div', {
                  survey: "P/DSS2/color",
                  fov:5,
                  target: """+'"'+str(target.ra)+' '+str(target.dec)+'"'+""",
                  showGotoControl: false,
                });
                var target_cat = A.catalog({name: '"""+str(target.name)+"""', sourceSize: 10, color: 'red'});
                aladin.addCatalog(target_cat, {shape: 'circle'});
                target_cat.addSources([A.marker("""+str(target.ra)+', '+str(target.dec)+""",
                  {popupTitle: '"""+str(target.name)+"""'})]);
            </script>"""

        return {'target': target,
                'plot': plot}
