# gaiaviz
Tools for visualizing data from Gaia DR3.

Created as part of Code/Astro 2022 to learn about Python package development!

## Installation
To install gaiaviz, simply run the following command in the Python environment you wish the package to be installed in:

<pre><code>pip install gaiaviz</pre></code>

Currently, the package contains a single class called SkyPatch that implements all of the visualization functionality. You can import the SkyPatch part of the package in any Python code as follows:

<pre><code>from gaiaviz.SkyPatch import SkyPatch</pre></code>

From there, we recommend reading our docs to get a sense of what gaiaviz can do in its current version!

## Example
Create a SkyPatch centered on a certain RA and DEC, with a certain radius (make sure it's in the range \[1,90], per the docs!)

<pre><code>ra = 50
dec = 30
radius = 5
sp = SkyPatch(ra, dec, radius)
</pre></code>

Plot the positions of the sources in the SkyPatch in 2D:

<pre><code>sp.plot_2D_star_positions()</pre></code>

Animate the orbits of the sources in the SkyPatch in 2D:

<pre><code>sp.animate_2D_star_positions()</pre></code>

If you're curious about how these functions work or what other arguments you can specify, please read the docs included in our repo!

[![codeastro](https://img.shields.io/badge/Made%20at-Code/Astro-blueviolet.svg)](https://semaphorep.github.io/codeastro/)
