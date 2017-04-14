import os

import iota
import networkx as nx
import time

import sys
from terminaltables import AsciiTable


class tangle:


    def __init__(self,path,resolution):

        self.directory = path
        self.output = './table.out'
        self.graph = nx.DiGraph()
        self.resolution = resolution
        self.res_ms = self.resolution * 1000
        self.prev_timestamp = 0

        self.prev_print = 0
        self.lines_to_show = 10
        self.data = []
        self.counter = 0

        self.milestones = []
        self.COOR = 'XNZBYAST9BETSDNOVQKKTBECYIPMF9IPOZRWUPFQGVH9HJW9NDSQVIPVBWU9YKECRYGDSJXYMZGHZDXCA'

    def add_tx_to_tangle(self, tx):
        if str(tx.address.as_json_compatible()) == self.COOR:
            self.milestones.append(tx.hash)

        self.graph.add_node(tx.hash, tx=tx)
        self.graph.add_edge(tx.hash, tx.branch_transaction_hash)
        self.graph.add_edge(tx.hash, tx.trunk_transaction_hash)



    def incremental_read(self):

        #read files in dir
        for file in sorted(os.listdir(self.directory)):
            # for each file
            with open(self.directory + file) as f:
                timestamp = int(file.split('.')[0])

                #read only newer files
                if self.prev_timestamp < timestamp:

                    hash = f.readline().strip('\n')
                    trytes = f.readline().strip('\n')
                    neighbor = f.readline().strip('\n')

                    #parse fields

                    tx = iota.Transaction.from_tryte_string_and_hash(trytes,hash)
                    #add to graph
                    self.add_tx_to_tangle(tx)


                    #stats:
                    if (self.prev_timestamp/self.res_ms < timestamp/self.res_ms):
                        print 'reading',file,'...'
                        self.prev_timestamp = timestamp
                        self.add_stats()
                # else:
                #     print 'skipping',file,'...'

    def print_stats(self):
        table_data = [['timestamp','Total Tx.', 'Confirmed Tx.', 'Conf. rate','TPS', 'CTPS', 'Tangle width', 'avg. confirmation time']]
        for (c,d) in enumerate(self.data):
            if c>self.prev_print - self.lines_to_show:
                self.prev_print = c
                table_data.append(d)  # created needs +2 for genesis

        table = AsciiTable(table_data)
        print(table.table)

        with open(self.output, 'w+') as f:
            f.write(table.table)

    def add_stats(self):

        num_txs = num_ctxs = tps = ctps = width = avg_c_t = 0

        # total tx:
        # count num of nodes in graph
        num_txs = self.graph.number_of_nodes()

        # confirmed tx:
        # count all descendants milestones
        ancestors = []
        for milestone in reversed(self.milestones):
            try:
                ancestors.append(nx.ancestors(self.graph, milestone))
            except:
                print "milestone missing"

        flatten = [item for sublist in ancestors for item in sublist]
        flatten = list(set(flatten))

        num_ctxs = len(flatten)


        if self.counter > 0:
            # TPS
            prev_num_tx = self.data[self.counter - 1][1]
            tps = (num_txs - prev_num_tx) / (self.resolution * 1.0)

            # CTPS
            prev_num_ctx = self.data[self.counter - 1][2]

            if num_ctxs == 0:
                num_ctxs = prev_num_ctx

            ctps = (num_ctxs - prev_num_ctx) / (self.resolution * 1.0)


        # Tangle Width
        # count all tx in given height
        #TODO

        # Average Confirmation Time
        # TODO


        self.counter +=1
        self.data.append([self.prev_timestamp, num_txs, num_ctxs, '{:.1%}'.format(num_ctxs / (num_txs * 1.0)), tps, ctps,width, avg_c_t])

        #self.data.append([self.counter * self.resolution, num_txs, num_ctxs, '{:.1%}'.format(num_ctxs/(num_txs*1.0)),tps, ctps, width, avg_c_t])

def main(path,resolution):
    t = tangle(path,resolution)
    while True:
        t.incremental_read()
        t.print_stats()
        time.sleep(t.resolution)

if __name__ == '__main__':

    if len(sys.argv) <3:
        print 'usage: ctps.py [path_to_export] [sample_interval]'
        exit(1)


    main(sys.argv[1],sys.argv[2])