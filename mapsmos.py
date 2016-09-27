#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import json
import os

from dateutil import parser as dateparser
from matplotlib.colors import Normalize
from mpl_toolkits.basemap import Basemap
import netCDF4

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np


DPI = 100.

def fromto(fname):
    deb = dateparser.parse(fname.split("_")[4])
    fin = dateparser.parse(fname.split("_")[5])
    fmt = '%Y/%m/%d %H:%M'
    return deb.strftime(fmt) + ' to ' + fin.strftime(fmt)


def guess_product_type(product_name):
    ll = product_name.split('_')
    return '_'.join(ll[2:4])


def read_product_conf(ptype, path=None):
    if not path:
        path = os.path.dirname(__file__) + '/mapsmos.json'
    with open(path) as f:
        conf = json.load(f)
    meta = conf['META'][ptype]
    mode = conf['MODES'][meta['mode']]
    return meta, mode


def mapsmos(smos_file, output=None, conf=None, cut=None):
    """ SMOS products map generator.
      
        Use mapsmos.json to configure each product types
        
        see http://matplotlib.org/basemap/api/basemap_api.html#mpl_toolkits.basemap.Basemap
        for cartographic projection settings (i.e. --mapargs-- property in mapsmos.json)
        
    """
    fig_file = os.path.basename(smos_file).split('.')[0] + '.png'

    if output:
        fig_file = output + '/' + os.path.basename(fig_file)
    ptype = guess_product_type(os.path.basename(smos_file))
    meta, mode = read_product_conf(ptype, conf)
    # lecture du fichier
    ncsmos = netCDF4.Dataset(smos_file)
    latsmos = ncsmos.variables['lat'][:]
    lonsmos = ncsmos.variables['lon'][:]
    param = ncsmos.variables[meta['param_id']]
    if meta['inc'] is not None:
        ndparam = param[meta['inc'], :, :]
    else:
        ndparam = param[:, :]
    if cut is not None:
        meta['vmin'], meta['vmax'] = np.nanpercentile(ndparam.filled(np.nan), [cut, 100-cut])
    title = meta['title'] + ', ' + fromto(os.path.basename(smos_file))
    lonsmos = np.fmod(lonsmos+180.+3600.0, 360.) - 180.
    index = np.argsort(lonsmos)
    lonsmos = lonsmos[index].flatten()
    latsmos = latsmos.flatten()
    ndparam = ndparam[:, index]
    # visualisation graphique
    width, height = meta["size"]
    fig = plt.figure(figsize=(width/DPI, height/DPI), dpi=DPI)
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    #ax.set_title(title, fontdict={'fontsize': 20.0,  'verticalalignment': 'baseline', })
    m = Basemap(**mode['mapargs'])
    m.drawcoastlines(linewidth=0.01, antialiased=False)
    m.drawmapboundary(fill_color='white', linewidth=0.01)
    m.drawmeridians(np.arange(-180, 181, 60),
        labels=[0, 0, 0, 0],
        #linewidth=0.8,
        labelstyle=None, )
    m.drawparallels(np.arange(-90, 91, 30),
        labels=[1, 0, 0, 0],
        #linewidth=0.8,
        labelstyle=None, )
    if mode['fill_continents']:
        m.fillcontinents(color='grey')
    ticks = np.linspace(meta['vmin'], meta['vmax'] , meta['nbColors']/2+1)
    lonsmosout, z = m.shiftdata(lonsmos, ndparam, lon_0=mode['lon_0'])
    lon, lat = np.meshgrid(lonsmosout, latsmos)
    x, y = m(lon, lat)
    cmap = cm.get_cmap(mode['colormap'], meta['nbColors'])
    cmap.set_bad('1.0')
    #cmap.set_over((0.0, 0.0, 1.0, 1.0))
    #cmap.set_under((0.0, 1.0, 0.0, 1.0))
    pc = m.pcolormesh(x, y, z, norm=Normalize(meta['vmin'], meta['vmax']), cmap=cmap)
    cb = plt.colorbar(pc,
                shrink=0.8,
                orientation='horizontal',
                fraction=0.04,
                extend='both',
                ticks=ticks,
                pad=0.08)
    cb.set_label(param.long_name + ' (%s)' % (param.units))
    plt.title(title, fontdict={'fontsize': 18.0,  'verticalalignment': 'baseline', })
    plt.text(1.0, -0.03, meta['copyright'], 
                horizontalalignment='right',
                verticalalignment='center',
                transform=ax.transAxes)
    plt.savefig(fig_file)
    plt.close()
    ncsmos.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", type=str, help="SMOS Product full path")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    parser.add_argument("-c", "--conf", default=None, help="Mapsmos configuration file path")
    args = parser.parse_args()
    mapsmos(args.filepath, output=args.output, conf=args.conf)