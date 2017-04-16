import os

import networkx as nx
import time

import sys
from terminaltables import AsciiTable

import urllib2
import json

TIMEOUT = 7

def API(request,auth,url):

    stringified = json.dumps(request)
    headers = {'content-type': 'application/json', 'Authorization': auth}

    try:
        request = urllib2.Request(url=url, data=stringified, headers=headers)
        returnData = urllib2.urlopen(request,timeout=TIMEOUT).read()
    except:
        print url, "Timeout!"
        print '\n    ' + repr(sys.exc_info())
        return

    response = json.loads(returnData)
    return response




class transaction:
    def __init__(self,tryte_string, hash_string):
        self.hash = hash_string
        #self.signature_message_fragment = tryte_string[0:2187]
        self.address = tryte_string[2187:2268]
        self.value = tryte_string[2268:2295]
        #self.tag = tryte_string[2295:2322]
        self.timestamp = tryte_string[2322:2331]
        #self.current_index = tryte_string[2331:2340]
        #self.last_index = tryte_string[2340:2349]
        self.bundle_hash = tryte_string[2349:2430]
        self.trunk_transaction_hash = tryte_string[2430:2511]
        self.branch_transaction_hash = tryte_string[2511:2592]
        #self.nonce = tryte_string[2592:2673]

class tangle:


    def __init__(self,path,resolution,auth_key,api_url):

        self.directory = path
        self.output = './table.out'
        self.graph = nx.MultiDiGraph()
        self.resolution = int(resolution)
        self.res_ms = self.resolution * 1000
        self.prev_timestamp = 0

        self.prev_print = 0
        self.lines_to_show = 10
        self.data = []
        self.counter = 0
        self.milestones = {}

        self.COOR =      'XNZBYAST9BETSDNOVQKKTBECYIPMF9IPOZRWUPFQGVH9HJW9NDSQVIPVBWU9YKECRYGDSJXYMZGHZDXCA'
        self.all_nines = '999999999999999999999999999999999999999999999999999999999999999999999999999999999'

        self.pruned_tx = 0

        self.broadcast_max_tps = 0
        self.broadcast_max_ctps = 0

        self.auth_key = auth_key
        self.api_url = api_url

        self.first = None

    def add_tx_to_tangle(self, tx):

        self.graph.add_node(tx.hash, tx=tx, confirmed=False, branch= tx.branch_transaction_hash, trunk =tx.trunk_transaction_hash)
        self.graph.add_edge(tx.hash, tx.branch_transaction_hash)
        self.graph.add_edge(tx.hash, tx.trunk_transaction_hash)

        if tx.address == self.COOR:
            self.milestones[tx.hash] = 1
            self.graph.node[tx.hash]['milestone'] = True

            #self.mark_descendants_confirmed(tx.hash)


    def incremental_read(self):

        #read files in dir
        for file in sorted(os.listdir(self.directory)):
            # for each file
            with open(self.directory + file) as f:
                timestamp = int(file.split('.')[0])

                #read only newer files
                if self.prev_timestamp < timestamp:

                    hash = f.readline().strip('\r\n')
                    trytes = f.readline().strip('\r\n')
                    neighbor = f.readline().strip('\r\n')

                    #parse fields
                    tx = transaction(trytes,hash)

                    #add to graph
                    self.add_tx_to_tangle(tx)

                    if self.first == None:
                        self.first = hash

                    #stats:
                    if (self.prev_timestamp/self.res_ms < timestamp/self.res_ms):
                        print 'reading',file,'...'
                        self.prev_timestamp = timestamp
                        self.add_stats()



    def print_stats(self):
        table_data = [['timestamp','Total Tx.', 'Confirmed Tx.', 'Conf. rate','TPS', 'CTPS', 'Tangle width', 'avg. confirmation time']]
        for (c,d) in enumerate(self.data):
            if c>self.prev_print - self.lines_to_show:
                self.prev_print = c
                table_data.append(d)  # created needs +2 for genesis

        table = AsciiTable(table_data)
        #print(table.table)

        with open(self.output, 'w+') as f:
            f.write(table.table)

    def add_stats(self):

        num_txs = num_ctxs = tps = ctps = width = avg_c_t = 0

        # total tx:
        # count num of nodes in graph
        num_txs = self.pruned_tx + self.graph.number_of_nodes()


        self.mark_milestone_descendants_confirmed()

        # confirmed tx:
        # count all descendants milestones
        Cnodes = filter(lambda (n, d): (d.has_key('confirmed') and d['confirmed'] == True), self.graph.nodes(data=True))
        num_ctxs = self.pruned_tx + len(Cnodes)


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
        self.data.append([self.prev_timestamp, num_txs, num_ctxs, '{:.1%}'.format(num_ctxs / (num_txs * 1.0)), '{:.1f}'.format(tps), '{:.1f}'.format(ctps),width, avg_c_t])
        self.broadcast_data([self.prev_timestamp, num_txs, num_ctxs, '{:.1f}'.format(100 * num_ctxs / (num_txs * 1.0)), '{:.1f}'.format(tps), '{:.1f}'.format(ctps),width, avg_c_t])


    def prune_confirmed_transactions(self):
        milestones_to_remove = []
        tx_to_prune = []
        for milestone in self.milestones:
            if self.graph.node[milestone].has_key('confirmed') and self.graph.node[milestone]['confirmed']:
                milestones_to_remove.append(milestone)
                to_prune = nx.descendants(self.graph, milestone)
                for p in to_prune:
                    tx_to_prune.append(p)

        remove_milestones = [self.milestones.pop(m) for m in milestones_to_remove]
        tx_to_prune_unique = list(set(tx_to_prune))
        remove_transactions = [self.graph.remove_node(p) for p in tx_to_prune_unique]
        self.pruned_tx += len(tx_to_prune_unique)

        #print "pruning:",len(tx_to_prune_unique)

    def mark_milestone_descendants_confirmed(self):

        self.prune_confirmed_transactions()

        descendants = []
        for milestone in self.milestones:
            try:
                descendants.append(nx.descendants(self.graph, milestone))
            except:
                print "milestone missing"

        flatten = [item for sublist in descendants for item in sublist]
        flatten = list(set(flatten))
        for f in flatten:
            self.graph.node[f]['confirmed'] = True



    def broadcast_data(self, data):
        if self.broadcast_max_tps < float(data[4]):
            self.broadcast_max_tps = float(data[4])
        if self.broadcast_max_ctps < float(data[5]):
            self.broadcast_max_ctps = float(data[5])


        json = {
            'ctps': data[5],
            'tps': data[4],
            'numTxs': data[1],
            'numCtxs': data[2],
            'cRate': data[3],
            'maxCtps': self.broadcast_max_ctps,
            'maxTps': self.broadcast_max_tps

        }
        with open('feed.out', 'w+') as f:
            f.write(str(json))
        if self.auth_key:
            res = API(json,self.auth_key,api_url)
            print res
        pass

    def mark_height(self):
        if self.graph.has_node(self.first):
            self.graph.node[self.first]['height'] = 0

        indeg = self.graph.in_degree()
        tip_index = [n for n in indeg if indeg[n] == 0]

        for tip in tip_index:
            self.mark_height_recursive(tip)
        for milestone in self.milestones:
            self.mark_height_recursive(milestone)

        pass


    def mark_height_recursive(self,hash):
        if self.graph.node[hash].has_key('height'):
            return

        if not self.graph.node[hash].has_key('tx'):
            return

        trunk = self.graph.node[hash]['trunk']
        if not self.graph.has_node(trunk):
            return

        if self.graph.node[trunk].has_key('height'):
            self.graph.node[hash]['height'] = self.graph.node[trunk]['height'] + 1
            return

        self.mark_height_recursive(trunk)

        pass

    def plot_height(self):
        self.mark_height()

        hist = {}
        for n in self.graph.nodes():
            node = self.graph.node[n]
            if not node:
                continue

            if node.has_key('height'):

                if not hist.has_key(node['height']):
                    hist[node['height']] = 0

                hist[node['height']] +=1
        for h in hist.keys():
            print h,':',hist[h]
        print self.graph.number_of_nodes()

        pass


def main(path,resolution,auth_key,api_url):
    t = tangle(path,resolution,auth_key,api_url)
    while True:
        t.incremental_read()
        t.print_stats()
        t.plot_height()
        time.sleep(t.resolution)

if __name__ == '__main__':

    if len(sys.argv) <3:
        print 'usage: ctps.py [path_to_export] [sample_interval] (auth_key) (url)'
        exit(1)

    if len(sys.argv) <4:
        auth_key = None
        api_url = None
    elif len(sys.argv) <5:
        auth_key = sys.argv[3]
    else:
        auth_key = sys.argv[3]
        api_url = sys.argv[4]




    main(sys.argv[1],sys.argv[2],auth_key,api_url)
