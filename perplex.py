#!/usr/bin/env python
# Perplex - Plex-base Movie Renamer
# Copyright (c) 2015 Konrad Rieck (konrad@mlsec.org)

import argparse
import sqlite3
import os
import shutil
import json
import gzip

import progressbar as pb

# Default path to metadata database
dbpath = "Plug-in Support/Databases/com.plexapp.plugins.library.db"

def build_db(plex_dir, movies = {}):
    """ Build movie database from sqlite database """

    dbfile = os.path.join(plex_dir, *dbpath.split("/"))
    db = sqlite3.connect(dbfile)

    # Select only movies with year
    query = """
        SELECT id, title, year FROM metadata_items
        WHERE metadata_type = 1 AND year """

    for row in db.execute(query):
        movies[row[0]] = (row[1], row[2], [])

    # Get files for each movie
    query = """
        SELECT mp.file FROM media_items AS mi, media_parts AS mp
        WHERE mi.metadata_item_id = %s AND mi.id = mp.media_item_id """

    for id in movies:
        for file in db.execute(query % id):
            movies[id][2].append(file[0])

    db.close()
    return movies


def build_map(movies, mapping = []):
    """ Build mapping to new names """

    for title, year, files in movies.values():
        for i, old_name in enumerate(files):
            _, ext = os.path.splitext(old_name)

            template = "%s (%s)/%s (%s)" % (title, year, title, year)
            template += " - %.2d" % i if len(files) > 1 else ""
            template += ext

            new_name = os.path.join(*template.split("/"))
            mapping.append((old_name, new_name))

    return mapping


def copy_rename(mapping, dest):

    pbar = pb.ProgressBar()
    for old_name, new_name in pbar(mapping):
        dp = os.path.join(dest, os.path.dirname(new_name))
        fp = os.path.join(dp, os.path.basename(new_name))

	try:
            if not os.path.exists(dp):
                os.makedirs(dp)

	    if not os.path.exists(fp):
                shutil.copy(old_name, fp)
                
        except Exception, e:
            print str(e)	
            


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Plex-based Movie Renamer.')
    parser.add_argument('--plex', metavar='<dir>', type=str,
                        help='set directory of Plex database.')
    parser.add_argument('--dest', metavar='<dir>', type=str,
                        help='copy and rename files to directory')
    parser.add_argument('--save', metavar='<file>', type=str,
                        help='save mapping of movie titles')
    parser.add_argument('--load', metavar='<file>', type=str,
                        help='load mapping of movie titles')

    args = parser.parse_args()

    if args.plex:
        movies = build_db(args.plex)
        mapping = build_map(movies)
    elif args.load:
        mapping = json.load(gzip.open(args.load))
    else:
        print "Error: Provide a Plex database or database of movie titles."
        sys.exit(-1)

    if args.save:
        json.dump(mapping, gzip.open(args.save, 'w'))

    if args.dest:
        copy_rename(mapping, args.dest)