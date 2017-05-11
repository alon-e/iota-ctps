import time
import sys

from tangle import tangle


def main(path,resolution,auth_key,api_url,slack_key):
    t = tangle(path,resolution,auth_key,api_url,slack_key)

    while True:
        t.incremental_read()
        t.print_stats()
        time.sleep(t.resolution)


if __name__ == '__main__':

    if len(sys.argv) <3:
        print 'usage: ctps.py [path_to_export] [sample_interval] (auth_key) (url) (slack_key)'
        exit(1)

    if len(sys.argv) <4:
        auth_key = None
        api_url = None
        slack_key = None
    elif len(sys.argv) <5:
        auth_key = sys.argv[3]
        api_url = None
        slack_key = None
    else:
        auth_key = sys.argv[3]
        api_url = sys.argv[4]
        slack_key = sys.argv[5]




    main(sys.argv[1],sys.argv[2],auth_key,api_url,slack_key)
