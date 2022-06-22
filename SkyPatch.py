import numpy as np
import pandas as pd
from astropy import units as u
import matplotlib.pyplot as plt
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord

from galpy.orbit import Orbit
from galpy.potential import LogarithmicHaloPotential

class SkyPatch():

    def __init__(self, ra, dec, radius=1, num_sources=None):
        self.ra = ra
        self.dec = dec
        self.radius = radius
        self.num_sources = num_sources
        #Constructing the Gaia query
        query = f"""source_id, ra, dec, pmra, pmdec, parallax, radial_velocity, phot_g_mean_mag
        FROM gaiadr3.gaia_source
        WHERE 1=CONTAINS(POINT(ra,dec), CIRCLE({ra},{dec},{radius}))
        AND radial_velocity IS NOT NULL AND ra IS NOT NULL AND dec IS NOT NULL AND parallax >= 0"""
        if num_sources is not None:
            query = f"""TOP {num_sources} """ + query
        query = """SELECT """ + query
        #Querying Gaia
        gaia_job = Gaia.launch_job(query)
        self.data = gaia_job.get_results()
        self.pandas_data = self.data.to_pandas()
        self.pandas_data['distance'] = self.pandas_data['parallax']*u.marcsec.to(u.kpc, equivalencies=u.parallax())

    def plot_2D_star_positions(self):
        plt.figure(figsize=(14,12))
        plt.scatter(self.pandas_data['ra'], self.pandas_data['dec'], marker='*', s=10, c=self.pandas_data['distance'])
        plt.xlabel('ra', fontsize=14)
        plt.ylabel('dec', fontsize=14)
        cbar = plt.colorbar(pad=0.07)
        cbar.set_label('distance (kpc)', fontsize=14)
        cbar.ax.yaxis.set_label_position('left')
        plt.show()

    def animate_2D_star_positions(self):
        '''
        Note that HTML animations will be shown automatically in Jupyter notebooks, but not in regular iPython.
        '''
        skycoords = SkyCoord(ra=self.pandas_data['ra']*u.deg, 
                    dec=self.pandas_data['dec']*u.deg, 
                    distance=self.pandas_data['distance']*u.kpc,
                    pm_ra_cosdec = self.pandas_data['pmra']*u.mas/u.yr,
                    pm_dec=self.pandas_data['pmdec']*u.mas/u.yr,
                    radial_velocity=self.pandas_data['radial_velocity']*u.km/u.s,
                    frame='icrs')
        lp = LogarithmicHaloPotential(normalize=1.)
        o = Orbit(skycoords)
        ts = np.linspace(0., 10, 100)
        o.integrate(ts, lp)
        o.plot3d(d1='ra', d2='dec', d3='vlos')
        html_animation = o.animate(d1=['ra', 'x'],d2=['dec', 'y'])
        return html_animation