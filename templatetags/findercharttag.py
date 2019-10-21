from django import template
from plotly import offline
import plotly.graph_objs as go
from tom_targets.models import Target
from tom_dataproducts.models import DataProduct

register = template.Library()


@register.inclusion_tag('mulens_tom/finderchart.html')
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
            if 'finder' in data.data:
                image_file = data.data

        if len(params) == len(keylist):
            return params, image_file
        else:
            return {},None

    (params,image_file) = fetch_finder(target)

    if len(params) > 0:
        half_width_y = ( (params['naxis1']/2.0) * params['pixscale'] ) / 3600.0
        half_width_x = ( (params['naxis2']/2.0) * params['pixscale'] ) / 3600.0

        xdata = np.arange(float(target.ra)-half_width_x,float(target.ra)+half_width_x,0.25)
        ydata = np.arange(float(target.dec)-half_width_y,float(target.dec)+half_width_y,0.25)

        scale_factor = 0.2

        fig = go.Figure()

        fig.add_trace(
                    go.Scatter(
                        x=xdata,
                        y=ydata,
                        mode="markers",
                        marker_opacity=0
                    )
                )

        fig.update_xaxes(
                    visible=True,

                    range=[xdata.min(), xdata.max()],
                    title=go.layout.xaxis.Title(
                        text='RA [mag]',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white'
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
                            color='white')),
                    linecolor='white',
                    color = 'white'
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
                    title='Reference Image',
                    font=dict(color="white",size=20),
                    width=(params['naxis1']*scale_factor),
                    height=(params['naxis2']*scale_factor),
                    #margin={"l": 0, "r": 0, "t": 0, "b": 0},
                    margin={"l": 55, "r": 15, "t": 55, "b": 55},
                    plot_bgcolor='black',
                    paper_bgcolor='black',
                )

        return {
            'target': target,
            'plot': offline.plot(fig, output_type='div', show_link=False)
        }

    else:

        plot = '<img src="{% static img/'+str(target.name)+'_colour.png %}" class="img-fluid mx-auto">'

        return {'target': target,
                'plot': plot}
