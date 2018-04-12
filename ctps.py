"""Usage:
  ctps.py (-e DIR | -s PORT) [-i INTERVAL] [options]


  Options:
      -h --help                                 show this help message and exit
      --version                                 show version and exit
      --testnet                                 sets Coordinator address to testnet Coo
      -e DIR --export_folder=DIR                export folder
      -s PORT --subscribe=PORT                  subscribe to IRI zmq publications
      --host=HOST                               zmq host [default: localhost]

      -i INTERVAL --interval=INTERVAL           sampling interval [default: 30]
      --auth_key=AUTH_KEY                       authentication key for url api endpoint
      --url=URL                                 url api endpoint
      --slack_key=SLACK_KEY                     slack token
      --width                                   calculate & plot width histogram
      --poisson                                 calculate & plot confirmation time distribution

      --prune                                   prune confirmed transactions
      
"""

import time
import sys

from docopt import docopt

from tangle import tangle


def main(config_map_global):
    t = tangle(config_map_global)

    if config_map_global["--export_folder"]:
        while True:
            t.incremental_read()
            t.print_stats()
            time.sleep(t.resolution)
    if config_map_global["--subscribe"]:
        t.continuous_read()


if __name__ == '__main__':
    config_map_global = docopt(__doc__)
    main(config_map_global)
