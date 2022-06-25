import numpy as np
import pandas as pd

import plotly.graph_objects as go

from astropy import units as u
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord

from galpy.orbit import Orbit
from galpy.potential import LogarithmicHaloPotential

class SkyPatch():
    """
    Class to store a patch of sky from Gaia and make different visualizations from it.

    Args:
        ra (float) (default=5.): The RA of the center of the patch of sky to visualize.
        dec (float): The DEC of the center of the patch of sky to visualize.
        radius (integer): The radius of the circular patch of sky to visualize. Must be in range [1,90].
        num_sources (None or int) (default=None): If None, all sources found in the specified area will 
            be pulled from Gaia. If an integer, that number of sources will be pulled.
    """
    def __init__(self, ra, dec, radius=5., num_sources=None):
        assert 1 < radius < 100, 'radius cannot be greater than 90 or less than 1'
        self.ra = ra
        self.dec = dec
        self.radius = radius
        self.num_sources = num_sources
        #Constructing the Gaia query
        query = f"""source_id, ra, dec, pmra, pmdec, parallax, radial_velocity, phot_g_mean_mag, phot_variable_flag
        FROM gaiadr3.gaia_source
        WHERE 1=CONTAINS(POINT(ra,dec), CIRCLE({ra},{dec},{radius}))
        AND radial_velocity IS NOT NULL AND ra IS NOT NULL AND dec IS NOT NULL AND parallax >= 0
        AND phot_g_mean_mag < 10
        ORDER BY phot_g_mean_mag"""
        if num_sources is not None:
            query = f"""TOP {num_sources} """ + query
        query = """SELECT """ + query
        #Querying Gaia
        gaia_job = Gaia.launch_job(query)
        self.data = gaia_job.get_results()
        self.pandas_data = self.data.to_pandas()
        self.pandas_data['distance'] = self.pandas_data['parallax']*u.marcsec.to(u.kpc, equivalencies=u.parallax())

    def plot_2D_star_positions(self):
        """
        Plots the current RA and DEC positions of stars in the desired patch of sky.
        """
        fig = go.Figure()
        fig.add_trace(go.Scatter(x = self.pandas_data['ra'], 
                                    y = self.pandas_data['dec'], 
                                    mode = 'markers',
                                    marker = {'size' : (10-self.pandas_data['phot_g_mean_mag'])*2,
                                    'colorscale' : 'gray_r',
                                    'color' : (self.pandas_data['phot_g_mean_mag']),
                                    'opacity' : 0.6
                                    }))
        fig.update_xaxes(title = 'RA', showgrid=False)
        fig.update_yaxes(title = 'Dec', scaleanchor = 'x', scaleratio=1, showgrid=False)
        fig.update_layout(template='plotly_dark', width = 800, height=800)
        fig.show()

    def animate_2D_star_positions(self, filename=None):
        """
        Animates the motion of stars forward in time using orbit integration (through galpy).
        Note that the animation produced will be an HTML file.
        
        Args:
            filename (string) (default=None): Path to save the final HTML animation to. If None, the animation will not be saved.
        
        """
        #Sets up the orbit integration with Galpy
        skycoords = SkyCoord(ra=self.pandas_data['ra']*u.deg, 
                    dec=self.pandas_data['dec']*u.deg, 
                    distance=self.pandas_data['distance']*u.kpc,
                    pm_ra_cosdec = self.pandas_data['pmra']*u.mas/u.yr,
                    pm_dec=self.pandas_data['pmdec']*u.mas/u.yr,
                    radial_velocity=self.pandas_data['radial_velocity']*u.km/u.s,
                    frame='icrs')
        lp = LogarithmicHaloPotential(normalize=1.)
        o = Orbit(skycoords)
        n_timesteps = 6
        max_t = 1 #in My
        ts = [0, 0.2, 0.4, 0.6, 0.8, 1]*u.Myr #must not be linspace bc might get floating-point error
        n_timesteps = len(ts)
        o.integrate(ts, lp)
        o.animate(d1=['ra', 'x'],d2=['dec', 'y'])
        os = o(ts)
        #Make DataFrame with timestep information
        df = pd.DataFrame(columns = ['source_id', 'timestep', 'ra', 'dec', 'pmra', 'pmdec', 'vlos', 'phot_g_mean_mag'])
        source_ids = pd.Series([], dtype=object)
        timesteps = pd.Series([], dtype=object)
        ras = pd.Series([], dtype=object)
        decs = pd.Series([], dtype=object)
        pmras = pd.Series([], dtype=object)
        pmdecs = pd.Series([], dtype=object)
        vloss = pd.Series([], dtype=object)
        phot_g_mean_mags = pd.Series([], dtype=object)
        for i in range(n_timesteps):
            source_ids = pd.concat([source_ids, self.pandas_data['source_id']], ignore_index=True)
            timesteps = pd.concat([timesteps, pd.Series([ts[i].value]*os.ra().shape[0])], ignore_index=True)
            ras = pd.concat([ras, pd.Series([source[i] for source in os.ra()])], ignore_index=True)
            decs = pd.concat([decs, pd.Series([source[i] for source in os.dec()])], ignore_index=True)
            pmras = pd.concat([pmras, pd.Series([source[i] for source in os.pmra()])], ignore_index=True)
            pmdecs = pd.concat([pmdecs, pd.Series([source[i] for source in os.pmdec()])], ignore_index=True)
            vloss = pd.concat([vloss, pd.Series([source[i] for source in os.vlos()])], ignore_index=True)
            phot_g_mean_mags = pd.concat([phot_g_mean_mags, self.pandas_data['phot_g_mean_mag']], ignore_index=True)
        df['source_id'] = source_ids
        df['timestep'] = timesteps
        df['ra'] = ras
        df['dec'] = decs
        df['pmra'] = pmras
        df['pmdec'] = pmdecs
        df['vlos'] = vloss
        df['phot_g_mean_mag'] = phot_g_mean_mags
        #Animate!
        fig_dict = {
            'data' : [], 
            'layout' : {},
            'frames' : []
        }
        sliders_dict = {
            'active': 0,
            'yanchor': 'top',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 20},
                'suffix': ' Myr from now',
                'visible': True,
                'xanchor': 'right'
            },
            'transition': {'duration': 100, 'easing': 'linear'},
            'pad': {'b': 10, 't': 50},
            'len': 0.9,
            'x': 0.1,
            'y': 0,
            'steps': []
        }
        #add data for zeroth frame
        fig_dict['data'].append(dict(
                            x = df[df.timestep == 0]['ra'],
                            y = df[df.timestep == 0]['dec'],
                            mode = 'markers',
                            marker = dict(
                                size=(10-self.pandas_data['phot_g_mean_mag'])*2,
                                colorscale='gray_r', #try 'thermal_r'
                                color=(self.pandas_data['phot_g_mean_mag']),
                                showscale=True,
                                opacity=1,
                                colorbar = dict(
                                    orientation='h',
                                    title='g-mag',
                                    thickness=10,
                                    thicknessmode='pixels'
                                ),
                                line=dict(width=0)
                            )
                            )
        )
        #add data for the rest of the frames
        ts_frames = np.insert(ts.value, 0, ts.value[0])
        for t in ts.value:
            frame = {'data' : [], 'name' : t}
            data_dict = dict(
                            x = df[df.timestep == t]['ra'],
                            y = df[df.timestep == t]['dec'],
                            mode = 'markers',
                            marker = dict(
                                #size=(10-self.pandas_data['phot_g_mean_mag'])*2,
                                colorscale='gray_r', #try 'thermal_r'
                                color=(self.pandas_data['phot_g_mean_mag']),
                                showscale=True,
                                opacity=1,
                                colorbar = dict(
                                    orientation='h',
                                    title='g-mag',
                                    thickness=6,
                                    thicknessmode='pixels'
                                ),
                                line=dict(width=0)
                            )
            )
            slider_step = {'args': [
                [t],
                {'frame': {'duration': 1000, 'redraw': False},
                'mode': 'immediate',
                'transition': {'duration': 1000}}
            ],
                'label': t,
                'method': 'animate'
            }
            sliders_dict['steps'].append(slider_step)
            frame['data'].append(data_dict)
            fig_dict['frames'].append(frame)
        fig_dict['layout']['xaxis'] = {'title': 'RA', 'showgrid' : False}
        fig_dict['layout']['yaxis'] = {'title': 'Dec', 'scaleanchor' : 'x', 'scaleratio' : 1, 'showgrid': False}
        #fig_dict['layout']['coloraxis'] = {'showscale' : True, 'reversed' : True}
        fig_dict['layout']['hovermode'] = 'closest'
        fig_dict['layout'] = {
            'hovermode' : 'closest',
            'template' : 'plotly_dark',
            'width' : 800,
            'height' : 800,
            'autosize' : True
        }
        fig_dict['layout']['updatemenus'] = [
            {
                'buttons': [
                    {
                        'args': [None, {'frame': {'duration': 1000, 'redraw': False},
                                        'fromcurrent': True, 'transition': {'duration': 1000,
                                                                            'easing': 'linear'}}],
                        'label': 'Replay',
                        'method': 'animate'
                    }
                ],
                'direction': 'left',
                'pad': {'r': 10, 't': 87},
                'showactive': False,
                'type': 'buttons',
                'x': 0.1,
                'xanchor': 'right',
                'y': 0,
                'yanchor': 'top'
            }
        ]
        fig_dict['layout']['sliders'] = [sliders_dict]
        fig = go.Figure(fig_dict)
        if filename: fig.write_html(filename, auto_play=False, full_html=True)
        fig.show()