import os

import networkx as nx
import time

import zmq
from terminaltables import AsciiTable

import iota

import analytics
from transaction import transaction
import api

MARK_AS_START = 0


class tangle:


    def __init__(self,config_map_global):

        #filesystem
        self.directory = config_map_global['--export_folder']
        self.output_short = './table.out'
        self.output_full  = './table.full'

        #zmq
        self.subscribe = config_map_global['--subscribe']
        self.topic = "tx"

        #parser
        self.resolution = int(config_map_global['--interval'])
        self.res_ns = self.resolution * 1000* 1000
        self.prev_timestamp = 0

        #graph
        self.graph = nx.MultiDiGraph()
        if (config_map_global['--testnet']):
            self.COOR = 'XNZBYAST9BETSDNOVQKKTBECYIPMF9IPOZRWUPFQGVH9HJW9NDSQVIPVBWU9YKECRYGDSJXYMZGHZDXCA'
            self.testnet = True
        else:
            self.COOR = 'KPWCHICGJZXKE9GSUDXZYUAPLHAKAHYHDXNPHENTERYMMBQOPSQIDENXKLKCEYCPVTZQLEEJVYJZV9BWU'
            self.testnet = False
        self.all_nines = '999999999999999999999999999999999999999999999999999999999999999999999999999999999'
        self.first = []
        self.prune = config_map_global['--prune']
        self.milestones = {}

        self.latest_milestone = 0
        self.latest_milestone_index = 0
        self.milestone_count = 0
        self.pruned_tx = 0

        #analytics
        self.analytics = analytics.analytics(self,config_map_global['--width'],config_map_global['--poisson'])

        #api
        self.milestone_to_broadcast_after = 0
        if os.path.isfile("milestone_to_broadcast_after.index"):
            self.milestone_to_broadcast_after = int(open("milestone_to_broadcast_after.index","r+").read())


        self.broadcast_max_tps = 0
        self.broadcast_max_ctps = 0
        self.prev_print = 0
        self.lines_to_show = 10

        self.auth_key = config_map_global['--auth_key']
        self.api_url = config_map_global['--url']
        self.slack_key = config_map_global['--slack_key']



    def add_tx_to_tangle(self, tx):

        self.graph.add_node(tx.hash, tx=tx, confirmed=False, trunk=tx.trunk_transaction_hash)
        self.graph.add_edge(tx.hash, tx.branch_transaction_hash)
        self.graph.add_edge(tx.hash, tx.trunk_transaction_hash)

        timestamp = tx.timestamp
        value = tx.value
        current_index = tx.current_index
        if not self.subscribe:
            timestamp = iota.int_from_trits(iota.TryteString(timestamp).as_trits())
            value = iota.int_from_trits(iota.TryteString(value).as_trits())
            current_index = iota.int_from_trits(iota.TryteString(current_index).as_trits())

        self.graph.node[tx.hash]['timestamp'] = timestamp
        self.graph.node[tx.hash]['value'] = value
        self.graph.node[tx.hash]['current_index'] = current_index

        self.graph.node[tx.hash]['address'] = tx.address
        self.graph.node[tx.hash]['bundle'] = tx.bundle_hash

        if tx.address == self.COOR:
            self.graph.node[tx.hash]['is_milestone'] = True

            index = iota.int_from_trits(iota.TryteString(tx.tag).as_trits())
            self.graph.node[tx.hash]['index'] = index

            self.latest_milestone = tx.hash
            self.milestones[tx.hash] = index
            if self.latest_milestone_index < index:
                self.latest_milestone_index = index
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

    def continuous_read(self):
        # connect to zmq
        # Socket to talk to server
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:%s" % self.subscribe)

        # Subscribe to topic
        topicfilter = self.topic
        socket.setsockopt(zmq.SUBSCRIBE, topicfilter)


        # read feed continuously
        while(True):
            current_timestamp = time.time() * 1000 * 1000

            #read & add transaction
            string = ""
            try:
                string = socket.recv()
                topic, hash, address, value, tag, timestamp, current_index, last_index, bundle, trunk, branch = string.split()
                # parse fields
                tx = transaction(hash, address, value, tag, timestamp, current_index, last_index, bundle, trunk, branch)
                # add to graph
                self.add_tx_to_tangle(tx)

                if len(self.first) < MARK_AS_START:
                    self.graph.node[tx.hash]["height"] = 0
                    self.first.append(tx.hash)
            except:
                print "error:",string
                pass
            # if interval has past - analyze.
            if (self.prev_timestamp + self.res_ns < current_timestamp ):
                print 'reading', int(current_timestamp), '...'
                self.prev_timestamp = current_timestamp
                self.analytics.analyze()

