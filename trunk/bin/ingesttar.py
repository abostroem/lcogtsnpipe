#!/usr/bin/env python

import lsc
import sys
import os
import re
import string
import tarfile
from optparse import OptionParser
_dir = os.environ['LCOSNDIR']

def ingesttar(_tarfile,force=False):
    _targetid = re.sub('.tar.gz','',string.split(_tarfile,'_')[-1])
    my_tar = tarfile.open(_tarfile)
    imglist = my_tar.getnames()
    my_tar.extractall(_dir)
    my_tar.close()
    if force:       
        lsc.mysqldef.ingestredu(imglist, 'yes') # ingest new data into photlco
    else:
        lsc.mysqldef.ingestredu(imglist, 'no') # ingest new data into photlco

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Downloads data from SNEX')
    parser.add_argument("-f", "--file")
    parser.add_argument("-G", "--force-db", action="store_true", help="reingest files even if they already exist")
    args = parser.parse_args()

    if args.file:
        _tarfile = args.file
        ingesttar(_tarfile, args.force_db)
    else:
        print('tar file not included (-f tarfile)')
