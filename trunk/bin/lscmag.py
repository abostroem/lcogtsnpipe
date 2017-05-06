#!/usr/bin/env python
description = ">> make final magnitude"
usage = "%prog image [options] "

import string
import re
import sys
from optparse import OptionParser
import time, math
import lsc
from lsc.sites import filterst1
import numpy as np


def makecatalogue(imglist):
    from astropy.io import fits
    dicti = {}
    for img in imglist:
        t = fits.open(img)
        hdr1 = t[0].header
        _filter = lsc.util.readkey3(hdr1, 'filter')
        if _filter not in dicti: dicti[_filter] = {}
        if img not in dicti[_filter]: dicti[_filter][img] = {}
        for jj in hdr1:
            if jj[0:2] == 'ZP':
                dicti[_filter][img][jj] = lsc.util.readkey3(hdr1, jj)
        if 'mjd' in hdr1:
            print 'cazzo'
            dicti[_filter][img]['mjd'] = lsc.util.readkey3(hdr1, 'mjd')
        elif 'MJD-OBS' in hdr1:
            dicti[_filter][img]['mjd'] = lsc.util.readkey3(hdr1, 'MJD-OBS')
        dicti[_filter][img]['exptime'] = lsc.util.readkey3(hdr1, 'exptime')
        dicti[_filter][img]['airmass'] = lsc.util.readkey3(hdr1, 'airmass')
        dicti[_filter][img]['telescope'] = lsc.util.readkey3(hdr1, 'telescop')
        dicti[_filter][img]['siteid'] = hdr1['SITEID']
        try:
            dicti[_filter][img]['PSFMAG1'] = float(lsc.util.readkey3(hdr1, 'PSFMAG1'))
            dicti[_filter][img]['PSFDMAG1'] = float(lsc.util.readkey3(hdr1, 'PSFDMAG1'))
            dicti[_filter][img]['APMAG1'] = float(lsc.util.readkey3(hdr1, 'APMAG1'))
        except:
            dicti[_filter][img]['PSFMAG1'] = 9999.
            dicti[_filter][img]['APMAG1'] = 9999.
            dicti[_filter][img]['PSFDMAG1'] = 0.0
    return dicti


if __name__ == "__main__":
    start_time = time.time()
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-i", "--interactive", action="store_true", dest='interactive', default=False,
                      help='Interactive \t\t\t [%default]')
    parser.add_option("-e", "--exzp", dest="exzp", default='',
                      type='str', help='external zero point from different field \t\t %default')
    parser.add_option("-t", "--typemag", dest="typemag", default='fit',
                      type='str', help='type of magnitude fit,ph \t\t %default')
    parser.add_option("--datatable", dest="datatable", default='photlco',
                      type='str', help='mysql table where stroe reduction info \t\t %default')
    parser.add_option("--calib", dest="calibration", default='sloan',
                      type='str', help='calibration to  (sloan,sloanprime,natural,apass) \t\t %default')

    option, args = parser.parse_args()
    if len(args) < 1: sys.argv.append('--help')
    _typemag = option.typemag
    if _typemag not in ['fit', 'ph']: sys.argv.append('--help')
    option, args = parser.parse_args()
    imglist = args[0]
    lista = lsc.util.readlist(imglist)
    hdr = lsc.util.readhdr(lista[0])
    tel = lsc.util.readkey3(hdr, 'telescop')
    _datatable = option.datatable
    _exzp = option.exzp
    _calib = option.calibration
    _interactive = option.interactive
    typemag = 'PSFMAG1'
    typemagerr = 'PSFDMAG1'
    namemag = {'fit': ['PSFMAG1', 'PSFDMAG1'], 'ph': ['APMAG1', 'PSFDMAG1']}
    dicti0 = makecatalogue(lista)
    dicti = {}
    for _filter in dicti0:
        for img in dicti0[_filter]:
            if dicti0[_filter][img][namemag[_typemag][0]] != 9999:
                if _filter not in dicti: dicti[_filter] = {}
                if img not in dicti[_filter]: dicti[_filter][img] = {}
                for key in dicti0[_filter][img].keys(): dicti[_filter][img][key] = dicti0[_filter][img][key]

    if len(dicti) > 0:
        allfilters = ''
        for fil in dicti:     allfilters = allfilters + filterst1[fil]
        if _interactive:  print allfilters
        queste0 = lsc.myloopdef.chosecolor(allfilters, False)
        queste1 = lsc.myloopdef.chosecolor(allfilters, True)
        if _exzp:
            lista2 = lsc.util.readlist(_exzp)
            dicti2 = makecatalogue(lista2)
            for _filter2 in dicti2:
                img2 = dicti2[_filter2].keys()[0]
                for jj in dicti2[_filter2][img2].keys():
                    if 'ZP' in jj:
                        if _filter2 in dicti:
                            for img in dicti[_filter2].keys():
                                dicti[_filter2][img][jj] = dicti2[_filter2][img2][jj]
                                lsc.util.updateheader(img, 0, {jj: [dicti2[_filter2][img2][jj], 'a b sa sb in y=a+bx']})
                                lsc.util.updateheader(img, 0, {'CATALOG': [str(img2), 'catalogue source']})
                                print jj, dicti2[_filter2][img2][jj]

        for _filter in dicti:
            for img in dicti[_filter]:
                if _interactive: print '\#### ', img
                # if dicti[_filter][img][namemag[_typemag][0]]!=9999:
                # start calibrating image 1
                secondimage = []
                mjdvec = []
                filtvec = []
                colore = []
                for ii in dicti[_filter][img].keys():
                    if 'ZP' in ii:  # for each zero point available
                        cc = ii[-2:]  # color used
                        for filt2 in dicti.keys():
                            if filt2 != _filter:
                                for jj in dicti[filt2].keys():
                                    for ll in dicti[filt2][jj].keys():
                                        if 'ZP' in ll and ll[-2:] == cc:
                                            secondimage.append(jj)
                                            mjdvec.append(dicti[filt2][jj]['mjd'] - dicti[_filter][img]['mjd'])
                                            filtvec.append(filt2)
                                            colore.append(cc)
                if len(secondimage) > 0:
                    colorescelto = ''
                    vv = queste1[filterst1[_filter]]
                    if len(vv) > 0:
                        if vv[0].upper() in colore:  colorescelto = vv[0].upper()
                    else:
                        vv = queste0[filterst1[_filter]]
                        if len(vv) > 0:
                            if vv[0].upper() in colore:  colorescelto = vv[0].upper()
                    if colorescelto:
                        print 'use ' + _filter + ' with color ' + colorescelto
                        filtvec = np.compress(np.array(colore) == colorescelto, filtvec)
                        mjdvec = np.compress(np.array(colore) == colorescelto, mjdvec)
                        secondimage = np.compress(np.array(colore) == colorescelto, secondimage)
                        colore = np.compress(np.array(colore) == colorescelto, colore)

                    dicti[_filter][img]['secondimg'] = secondimage[np.argmin(mjdvec)]
                    dicti[_filter][img]['secondfilt'] = filtvec[np.argmin(mjdvec)]
                    _filter2 = dicti[_filter][img]['secondfilt']
                    img2 = dicti[_filter][img]['secondimg']
                    col = colore[np.argmin(mjdvec)]

                    siteid = dicti[_filter][img]['siteid']
                    if siteid in lsc.sites.extinction:
                        kk = lsc.sites.extinction[siteid]
                    else:
                        print _filter, img, dicti[_filter][img]
                        sys.exit('siteid not in lsc.sites.extinction')

                    if _interactive:
                        print dicti[_filter][img]['airmass']
                        print kk[filterst1[_filter]]
                        print 2.5 * math.log10(dicti[_filter][img]['exptime'])
                        print dicti[_filter][img][namemag[_typemag][0]]
                    # instrumental mag corrected for exp time and airmass
                    mag0 = dicti[_filter][img][namemag[_typemag][0]] - kk[filterst1[_filter]] * dicti[_filter][img][
                        'airmass']
                    dmag0 = dicti[_filter][img][namemag[_typemag][1]]

                    siteid = dicti[_filter2][img2]['siteid']
                    if siteid in lsc.sites.extinction:
                        kk = lsc.sites.extinction[siteid]
                    else:
                        print dicti[_filter2][img2]
                        sys.exit('siteid not in lsc.sites.extinction')
                    # instrumental mag corrected for exp time and airmass
                    mag1 = dicti[_filter2][img2][namemag[_typemag][0]] - kk[filterst1[_filter2]] * dicti[_filter2][img2][
                        'airmass']
                    dmag1 = dicti[_filter2][img2][namemag[_typemag][1]]

                    if filterst1[_filter].upper() == col[0]:
                        Z1 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[1])
                        C1 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[2])
                        DZ1 = float(
                            string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[3])
                        Z2 = float(
                            string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[1])
                        C2 = float(
                            string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[2])
                        DZ2 = float(
                            string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[3])

                        M1, M2 = lsc.lscabsphotdef.finalmag(Z1, Z2, C1, C2, mag0, mag1)

                        #                        DZ1 = 0.0
                        #                        DZ2 = 0.0
                        dc1, dc2, dz1, dz2, dm1, dm2 = lsc.lscabsphotdef.erroremag(Z1, Z2, mag0, mag1, C1, C2, 0)
                        DM11 = np.sqrt((dm1 * dmag0) ** 2 + (dz1 * DZ1) ** 2 + (dm2 * dmag1) ** 2 + (dz2 * DZ2) ** 2)

                        if _interactive:
                            print '\n####  example computation '
                            print 'Z1  Z1  C1   C2   mag1    mag 2'
                            print 'M1   M2 '
                            print img, img2
                            print _filter, _filter2
                            print Z1, Z2, C1, C2, mag0, mag1
                            print M1, M2
                            print DZ1, DZ2
                        try:
                            if np.isfinite(M1) and M1 < 999:
                                lsc.mysqldef.updatevalue(_datatable, 'mag', M1, re.sub('sn2.fits', 'fits',
                                                                                       string.split(img, '/')[-1]))
                                if _typemag == 'fit':
                                    lsc.mysqldef.updatevalue(_datatable, 'magtype', 2, re.sub('sn2.fits', 'fits',
                                                                                              string.split(img, '/')[
                                                                                                  -1]))
                                elif _typemag == 'ph':
                                    lsc.mysqldef.updatevalue(_datatable, 'magtype', 3, re.sub('sn2.fits', 'fits',
                                                                                              string.split(img, '/')[
                                                                                                  -1]))
                                lsc.util.updateheader(img, 0, {'mag': [M1, 'calibrated mag']})
                            else:
                                lsc.mysqldef.updatevalue(_datatable, 'mag', 9999, re.sub('sn2.fits', 'fits',
                                                                                         string.split(img, '/')[-1]))
                                lsc.util.updateheader(img, 0, {'mag': [9999, 'calibrated mag']})
                            if np.isfinite(DM11):
                                lsc.mysqldef.updatevalue(_datatable, 'dmag', DM11, re.sub('sn2.fits', 'fits',
                                                                                          string.split(img, '/')[-1]))
                                lsc.util.updateheader(img, 0, {'dmag': [DM11, 'calibrated mag error']})
                            else:
                                lsc.mysqldef.updatevalue(_datatable, 'dmag', 9999, re.sub('sn2.fits', 'fits',
                                                                                          string.split(img, '/')[-1]))
                                lsc.util.updateheader(img, 0, {'dmag': [9999, 'calibrated mag error']})
                        except:
                            print 'module mysqldef not found'
                    else:
                        Z2 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[1])
                        C2 = float(string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[2])
                        DZ2 = float(
                            string.split(dicti[_filter][img]['ZP' + filterst1[_filter].upper() + col.upper()])[3])
                        Z1 = float(
                            string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[1])
                        C1 = float(
                            string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[2])
                        DZ1 = float(
                            string.split(dicti[_filter2][img2]['ZP' + filterst1[_filter2].upper() + col.upper()])[3])

                        M1, M2 = lsc.lscabsphotdef.finalmag(Z1, Z2, C1, C2, mag1, mag0)

                        #DZ1 = 0.0
                        #DZ2 = 0.0
                        dc1, dc2, dz1, dz2, dm1, dm2 = lsc.lscabsphotdef.erroremag(Z1, Z2, mag0, mag1, C1, C2, 1)
                        DM22 = np.sqrt((dm1 * dmag0) ** 2 + (dz1 * DZ1) ** 2 + (dm2 * dmag1) ** 2 + (dz2 * DZ2) ** 2)

                        if _interactive:
                            print '\n####  example computation '
                            print 'Z1  Z1  C1   C2   mag1    mag 2'
                            print 'M1   M2 '
                            print Z1, Z2, C1, C2, mag1, mag0
                            print M1, M2
                            print DZ1, DZ2
                        try:
                            if np.isfinite(M2) and M2 < 999:
                                lsc.mysqldef.updatevalue(_datatable, 'mag', M2, re.sub('sn2.fits', 'fits',
                                                                                       string.split(img, '/')[-1]))
                                if _typemag == 'fit':
                                    lsc.mysqldef.updatevalue(_datatable, 'magtype', 2, re.sub('sn2.fits', 'fits',
                                                                                              string.split(img, '/')[
                                                                                                  -1]))
                                elif _typemag == 'ph':
                                    lsc.mysqldef.updatevalue(_datatable, 'magtype', 3, re.sub('sn2.fits', 'fits',
                                                                                              string.split(img, '/')[
                                                                                                  -1]))
                                lsc.util.updateheader(img, 0, {'mag': [M2, 'calibrated mag']})
                            else:
                                lsc.mysqldef.updatevalue(_datatable, 'mag', 9999, re.sub('sn2.fits', 'fits',
                                                                                         string.split(img, '/')[-1]))
                                lsc.util.updateheader(img, 0, {'mag': [9999, 'calibrated mag']})
                            if np.isfinite(DM22):
                                lsc.mysqldef.updatevalue(_datatable, 'dmag', DM22, re.sub('sn2.fits', 'fits',
                                                                                          string.split(img, '/')[-1]))
                                lsc.util.updateheader(img, 0, {'dmag': [DM22, 'calibrated mag error']})
                            else:
                                lsc.mysqldef.updatevalue(_datatable, 'dmag', 9999, re.sub('sn2.fits', 'fits',
                                                                                          string.split(img, '/')[-1]))
                                lsc.util.updateheader(img, 0, {'dmag': [9999, 'calibrated mag error']})
                        except:
                            print 'module mysqldef not found'
                    print _filter, col
                else:
                    siteid = dicti[_filter][img]['siteid']
                    if siteid in lsc.sites.extinction:
                        kk = lsc.sites.extinction[siteid]
                    else:
                        print _filter, img, dicti[_filter][img]
                        sys.exit('siteid not in lsc.sites.extinction')

                    filename = img.split('/')[-1].replace('.sn2.fits', '.fits')
                    mag0 = dicti[_filter][img][namemag[_typemag][0]] - kk[filterst1[_filter]] * dicti[_filter][img]['airmass']
                    dmag0 = dicti[_filter][img][namemag[_typemag][1]]
                    Z1 = ''
                    if mag0 < 99:
                        best_color = lsc.chosecolor('uUBgVrRiIz', usegood=True)[filterst1[_filter]][0]
                        hdr_kwd = 'ZP' + filterst1[_filter].upper() + best_color.upper()
                        if hdr_kwd in dicti[_filter][img] and float(dicti[_filter][img][hdr_kwd].split()[1]) < 99:
                            print 'using', hdr_kwd
                            Z1 = float(dicti[_filter][img][hdr_kwd].split()[1])
                            DZ1 = float(dicti[_filter][img][hdr_kwd].split()[3])
                        else:
                            for ww in dicti[_filter][img].keys():
                                if ww[:3] == 'ZP' + filterst1[_filter].upper() and float(dicti[_filter][img][ww].split()[1]) < 99:
                                    print 'using', ww
                                    Z1 = float(string.split(dicti[_filter][img][ww])[1])
                                    DZ1 = float(string.split(dicti[_filter][img][ww])[3])
                                    break

                    if Z1:
                        M1 = mag0 + Z1
                        DM1 = (DZ1**2 + dmag0**2)**0.5
                        print 'final mag = {:.2f} +/- {:.2f}'.format(M1, DM1)
                        lsc.mysqldef.updatevalue(_datatable, 'mag', M1, filename)
                        lsc.mysqldef.updatevalue(_datatable, 'dmag', DM1,  filename)
                        if _typemag == 'fit':
                            lsc.mysqldef.updatevalue(_datatable, 'magtype', 2, filename)
                        elif _typemag == 'ph':
                            lsc.mysqldef.updatevalue(_datatable, 'magtype', 3, filename)
                        lsc.util.updateheader(img, 0, {'mag': [M1, 'calibrated mag']})
                    else:
                        print 'no other filters with calibration in ' + _filter + ' band'
                        print '(or zcat did not put the color terms in the header)'
                        print img, _filter, mag0, dmag0
                        lsc.mysqldef.updatevalue(_datatable, 'mag', 9999, filename)
                        lsc.util.updateheader(img, 0, {'mag': [9999, 'calibrated mag']})
    else:
        print '\n### warning: no measurement in sn2 files'
