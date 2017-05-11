import os

import networkx as nx
import time

from terminaltables import AsciiTable

import iota

import analytics
from transaction import transaction
import api

PRUNE = False
MARK_AS_START = 0


class tangle:


    def __init__(self,path,resolution,auth_key,api_url,slack_key):

        #filesystem
        self.directory = path
        self.output_short = './table.out'
        self.output_full  = './table.full'

        #parser
        self.resolution = int(resolution)
        self.res_ns = self.resolution * 1000* 1000
        self.prev_timestamp = 0

        #graph
        self.graph = nx.MultiDiGraph()
        self.COOR = 'XNZBYAST9BETSDNOVQKKTBECYIPMF9IPOZRWUPFQGVH9HJW9NDSQVIPVBWU9YKECRYGDSJXYMZGHZDXCA'
        self.all_nines = '999999999999999999999999999999999999999999999999999999999999999999999999999999999'
        self.first = []
        self.prune = PRUNE
        self.milestones = {}
        self.latest_milestone = 0
        self.milestone_count = 0
        self.pruned_tx = 0

        #analytics
        self.analytics = analytics.analytics(self)


        #api
        self.broadcast_max_tps = 0
        self.broadcast_max_ctps = 0
        self.prev_print = 0
        self.lines_to_show = 10

        self.auth_key = auth_key
        self.api_url = api_url
        self.slack_key = slack_key



    def add_tx_to_tangle(self, tx):

        self.graph.add_node(tx.hash, tx=tx, confirmed=False, trunk=tx.trunk_transaction_hash)
        self.graph.add_edge(tx.hash, tx.branch_transaction_hash)
        self.graph.add_edge(tx.hash, tx.trunk_transaction_hash)

        timestamp = iota.int_from_trits(iota.TryteString(tx.timestamp).as_trits())
        self.graph.node[tx.hash]['timestamp'] = timestamp

        if tx.address == self.COOR:
            self.graph.node[tx.hash]['is_milestone'] = True

            index = iota.int_from_trits(iota.TryteString(tx.tag).as_trits())
            self.graph.node[tx.hash]['index'] = index

            self.latest_milestone = tx.hash
            self.milestones[tx.hash] = 1
            self.milestone_count +=1


    def incremental_read(self):

        #read files in dir
        for file in sorted(os.listdir(self.directory)):
            try:
                # for each file
                with open(self.directory + file) as f:
                    timestamp = int(file.split('.')[0])

                    #read only newer files
                    if self.prev_timestamp < timestamp:

                        hash = f.readline().strip('\r\n')
                        trytes = f.readline().strip('\r\n')
                        neighbor = f.readline().strip('\r\n')
                        #height = int(f.readline().strip('\r\n').split('Height: ')[1])

                        #parse fields
                        tx = transaction(trytes,hash)

                        #add to graph
                        self.add_tx_to_tangle(tx)

                        if len(self.first) < MARK_AS_START:
                            self.graph.node[tx.hash]["height"] = 0
                            self.first.append(tx.hash)

                        #stats:
                        if (self.prev_timestamp/self.res_ns < timestamp/self.res_ns):
                            print 'reading',file,'...'
                            self.prev_timestamp = timestamp
                            self.analytics.analyze()
            except:
                pass

    def print_stats(self):
        self.analytics.print_stats()

