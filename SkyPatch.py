import pandas as pd
from astropy import units as u
from astroquery.gaia import Gaia

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
