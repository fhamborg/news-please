# This tool combines all json files written by news-please in one new file, one line per
# json source document.
# This output can then be used by Apache Hive (and therefore by Amazon Athena).
import getopt
import glob
import json
import logging
import os
import sys


def get_files_by_ext(dirpath, pattern='*'):
    if not os.path.exists(dirpath):
        raise Exception("Path %s doesn't exit." % dirpath)

    a = glob.glob(os.path.join(dirpath, "**", pattern), recursive=True)
    a.sort(key=lambda s: os.path.getmtime(s))
    return a


def combine_json_files(source_folder, output_path):
    paths = get_files_by_ext(source_folder, pattern="*.json")
    with open(output_path, 'w') as of:
        for p in paths:
            with open(p, 'rb') as f:
                json_input = f.readline()
            of.write(json_input.decode("utf-8"))
            of.write("\n")
    pass



def print_usage():
    print("combine_json_output.py source_folder=<path to folder with json files>")

def start(argv):
    try:
        opts, args = getopt.getopt(argv, "dh", longopts=["source_folder=", 'output_path='])
    except getopt.GetoptError:
        logging.exception("Problem while parsing options.")
        print_usage()
        sys.exit(2)

    output_path = source_folder = None
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit(0)
        elif opt == '--source_folder':
            source_folder = arg
        elif opt == '--output_path':
            output_path = arg

    combine_json_files(source_folder, output_path)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')  # include timestamp

if __name__ == '__main__':
    start(sys.argv[1:])

