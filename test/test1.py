#!/usr/bin/env python 
# -*- coding: utf-8 -*-


import json
import os
import tarfile
import zipfile
import subprocess
import shutil
import shlex
from optparse import OptionParser
import mapsmos


# get configurations file info
# get dissPath, FTP arbo path

# retrieving args
usage = 'usage : %prog [options]'
parser = OptionParser(usage)
parser.add_option('-d',
                  '--diss_path',
                  type='string',
                  dest='diss_path',
                  help='Chemin de l espace de dissemination')
(options, args) = parser.parse_args()

if options.diss_path:
  diss_path = str(options.diss_path.strip())
else:
    print "Le chemin de l espace de dissemination est manquant"
    exit(1)

# checking mapsmos executable
if not os.path.exists('mapsmos.py'):
    print "L executable mapsmos.py n existe pas"
    exit(1)

# temporary directory
tmpdir = "/tmp/prd_to_process"
if not os.path.exists(tmpdir):
  os.makedirs(tmpdir)

# create dir MAP
if not os.path.exists(diss_path):
  print "Erreur le chemin de dissemination " + diss_path + " n existe pas"
  exit(1)
else:
  ftp_diss_path = diss_path + os.sep + "FTP"
  # checking ftp_diss_path
  if not os.path.exists(ftp_diss_path):
    print "Le repertoire de dissemination FTP " + ftp_diss_path + " n existe pas"
    exit(1)

  print "Nettoyage des cartes"
  map_diss_path = diss_path + os.sep + "MAP"
  ## LM
  print "diss_path : " + map_diss_path

  if not os.path.exists(map_diss_path):
      os.makedirs(diss_path + os.sep + "MAP")
  else:
    # loop through MAP arbo
    for root, directories, filenames in os.walk(map_diss_path):
      for filename in filenames:
        file_map_path = os.path.join(root,filename)
        ftp_dir = root.replace('/MAP/', '/FTP/', 1)

        ftp_file = None
        file_to_match = filename.split('.')[0]
        for loop_file in os.listdir(ftp_dir):
          if loop_file.startswith(file_to_match):
            ftp_file = loop_file
            break
        if ftp_file is None:
          print "Le produit associee a la carte " + filename + " n existe pas"
          os.remove(file_map_path)
          # removing empty parent file
          curr_dir = os.path.dirname(file_map_path)
          while curr_dir != map_diss_path:
            if os.path.exists(curr_dir) and len(os.listdir(curr_dir)) == 0:
              os.rmdir(curr_dir)
              print "Repertoire vide supprime : " + curr_dir
              curr_dir = os.path.dirname(curr_dir)
            else:
              break

  print "Generation des cartes"
  mapsmos_conf = open("mapsmos.json")
  mapsmos_prd = json.load(mapsmos_conf)["META"].keys()
  mapsmos_conf.close()

  # LM
  for m in mapsmos_prd:
    print "mapsmos_prd : " + m

  print "ftp_diss_path : " + ftp_diss_path

  # loop through FTP arbo
  for root, directories, filenames in os.walk(ftp_diss_path):
     # LM
     print "root : " + root 

     # for directory in directories:
     # print os.path.join(root, directory)
     for filename in filenames:
      # LM
      print "filename : " + filename

      to_process = False
      if (filename.endswith('.tgz') or filename.endswith('.zip')
        or filename.endswith('.nc') or filename.endswith('.DBL')):
        for prd in mapsmos_prd:
          # LM
          #print "prd : " + prd

          if prd in filename:
            file_ftp_path = os.path.join(root,filename)
            # check if map already exists
            map_dir = root.replace('/FTP/', '/MAP/', 1)
            # LM
            print "map_dir : " + map_dir

            map_file = None
            if os.path.exists(map_dir):
              file_to_match = filename.split('.')[0]
              # LM
              print "file_to_match : " + file_to_match

              for loop_file in os.listdir(map_dir):
                if loop_file.startswith(file_to_match):
                  map_file = loop_file
                  print "La carte associee au produit " + filename + " existe deja"
                  break

            if map_file is None:
              # LM
              print "map_file is None..."
              if filename.endswith('.tgz'):
                # untar
                tar = tarfile.open(file_ftp_path)
                tar.extractall(tmpdir)
                tar.close()
              elif filename.endswith('.zip'):
                # unzip
                with zipfile.ZipFile(file_ftp_path, "r") as z:
                    z.extractall(tmpdir)
              elif filename.endswith('.nc') or filename.endswith('.DBL'):
                 shutil.copy(file_ftp_path, tmpdir)
                 file_to_process = os.path.join(tmpdir, filename)

              map_dir = root.replace('/FTP/', '/MAP/', 1)
              if not os.path.exists(map_dir):
                os.makedirs(map_dir)

              file_to_process = None
              for loop_file in os.listdir(tmpdir):
                if loop_file.endswith(".nc") or loop_file.endswith(".DBL"):
                  file_to_process = os.path.join(tmpdir, loop_file)
                  break

              if file_to_process:

                # LM
                print "file to process..."
                try:
                  mapsmos.mapsmos(file_to_process, map_dir)
                  print "succes de la generation de la carte a partir du produit " + os.path.basename(file_to_process)
                except Exception as err:
                  print ("echec de la generation de la carte a partir du produit " + os.path.basename(file_to_process) +
                         " avec le code erreur " + str(err))
                  
              # cleaning temporary files
              for file_to_clean in os.listdir(tmpdir):
                os.remove(os.path.join(tmpdir, file_to_clean))
              # stop the mapsmos_prd loop
              break
print "Fin de la generation des cartes"
# cleaning
os.rmdir(tmpdir)
exit(0)
