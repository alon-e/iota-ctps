import math
import networkx as nx
import time

import sys
from terminaltables import AsciiTable

import api
import data

MOVING_AVG_WINDOW = 10 * 60 * 1000 * 1000


def get_poisson_peak(confirmed_times):
    #return sorted(confirmed_times)[len(confirmed_times) / 2 + len(confirmed_times) % 2 - 1]
    return int(sum(confirmed_times)/len(confirmed_times))
    # if len(confirmed_times) == 1:
    #     return confirmed_times[0]
    # t_max = max(confirmed_times) + 1
    # bins = len(confirmed_times)
    # bin_size = t_max/float(bins)
    # buckets = [0 for n in range(bins)]
    # for t in confirmed_times:
    #     buckets[int(math.floor(t/bin_size))] += 1
    #return int(math.floor(buckets.index(max(buckets))*bin_size + bin_size/2))

class analytics:

    def __init__(self,tangle,do_width,do_poisson):
        self.tangle = tangle
        self.data = data.data()
        self.counter = 0

        self.last_slack_broadcast = 0
        self.slack_broadcast_threshold = 10 * 60 * 1000 * 1000

        self.do_width = do_width
        self.do_poisson = do_poisson

        self.confirmed = set()


    def analyze(self):
        if self.do_width:
            self.mark_height()

        self.mark_milestone_descendants_confirmed()
        self.add_stats()
        try:
            self.broadcast_data()
        except:
            pass
        try:
            self.print_stats()
        except:
            pass
        try:
            if self.do_width:
                self.calc_width()
        except:
            pass
        try:
            if self.do_poisson:
                self.calc_confirmation_time()
        except:
            pass



    def add_stats(self):
        num_txs = num_ctxs = tps = ctps = width = avg_c_t = alltime_avg_tps = alltime_avg_ctps = c_rate = 0

        # total tx:
        # count num of nodes in graph
        num_txs = self.tangle.pruned_tx + self.tangle.graph.number_of_nodes()

        # confirmed tx:
        # count all descendants milestones
        Cnodes = filter(lambda (n, d): (d.has_key('confirmed') and d['confirmed'] == True), self.tangle.graph.nodes(data=True))
        num_ctxs = self.tangle.pruned_tx + len(Cnodes)

        # if self.counter > 0:
        #     # TPS
        #     prev_num_tx = self.data.numTxs[self.data.last_index()]
        #     tps = (num_txs - prev_num_tx) / (self.tangle.resolution * 1.0)
        #     # CTPS
        #     prev_num_ctx = self.data.numCtxs[self.data.last_index()]
        #
        #     if num_ctxs == 0:
        #         num_ctxs = prev_num_ctx
        #
        #     ctps = (num_ctxs - prev_num_ctx) / (self.tangle.resolution * 1.0)

        # Tangle Width
        # count all tx in given height
        # TODO


        # Average Confirmation Time
        if self.confirmed:
            confirmed_times = [self.tangle.graph.node[k]['confirmationTime'] for k in self.confirmed]
            avg_c_t = get_poisson_peak(confirmed_times)
            avg_c_t = time.strftime('%H:%M:%S', time.gmtime(avg_c_t))
        elif self.counter > 0:
            avg_c_t = self.data.avgCTime[self.data.last_index()]


        # Confirmation rate
        # moving avg
        #(totCtx(N) - totCtx(N - 1)) / (totTx(N) - totTx(N - 1))

        window_samples = (MOVING_AVG_WINDOW / self.tangle.res_ns) - 1
        if self.counter > window_samples:

            delta_ctxs = num_ctxs - self.data.numCtxs[self.data.last_index() - window_samples]
            delta_txs = num_txs - self.data.numTxs[self.data.last_index() - window_samples]

            #10 minutes  avg tps
            tps = delta_txs / float((window_samples + 1) * self.tangle.resolution)
            ctps = delta_ctxs / float((window_samples + 1) * self.tangle.resolution)

            alltime_avg_tps = num_txs / float(self.data.last_index() * self.tangle.resolution)
            alltime_avg_ctps = num_ctxs / float(self.data.last_index() * self.tangle.resolution)

            c_rate = delta_ctxs / (delta_txs * 1.0)

        self.counter += 1
        t = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(self.tangle.prev_timestamp / 1000 / 1000))

        self.data.append(t,
                         num_txs,
                         num_ctxs,
                         '{:.1%}'.format(c_rate),
                         '{:.1f}'.format(tps),
                         '{:.1f}'.format(ctps),
                         width,
                         avg_c_t,
                         '{:.1f}'.format(alltime_avg_tps),
                         '{:.1f}'.format(alltime_avg_ctps))




    def prune_confirmed_transactions(self):
        milestones_to_remove = []
        tx_to_prune = []



        for milestone in self.tangle.milestones:
            if self.tangle.graph.node[milestone].has_key('confirmed') and self.tangle.graph.node[milestone]['confirmed']:
                milestones_to_remove.append(milestone)
                to_prune = nx.descendants(self.tangle.graph, milestone)
                for p in to_prune:
                    tx_to_prune.append(p)

        remove_milestones = [self.tangle.milestones.pop(m) for m in milestones_to_remove]

        tx_to_prune_unique = list(set(tx_to_prune))
        if self.tangle.prune and len(tx_to_prune_unique) > 30000:
            self.tangle.graph.remove_nodes_from(tx_to_prune_unique)
            self.tangle.pruned_tx += len(tx_to_prune_unique)

            # print "pruning:",len(tx_to_prune_unique)


    def mark_milestone_descendants_confirmed(self):
        self.confirmed = set()
        NCnodesIter = []
        NCnodes = filter(lambda (n, d): (not d.has_key('confirmed') or (d.has_key('confirmed') and d['confirmed'] == False)),self.tangle.graph.nodes(data=True))
        for n,d in NCnodes:
            NCnodesIter.append(n)
        NCGraph = self.tangle.graph.subgraph(NCnodesIter)

        for milestone in sorted(self.tangle.milestones, key=self.tangle.milestones.get):
            try:
                descendants = nx.descendants(NCGraph, milestone)
                if descendants:
                    milestone_index = self.tangle.milestones.get(milestone)
                    milestone_timestamp = self.tangle.graph.node[milestone]['timestamp']
                    for d in descendants:
                        if self.tangle.graph.node[d].has_key('confirmed') and not self.tangle.graph.node[d]['confirmed']:
                            self.confirmed.add(d)
                            self.tangle.graph.node[d]['confirmed'] = True
                            self.tangle.graph.node[d]['confirmationTime'] = milestone_timestamp - self.tangle.graph.node[d]['timestamp']
                            self.tangle.graph.node[d]['confirmingMilestone'] = milestone_index
            except:
                print "milestone missing"

        self.prune_confirmed_transactions()


    def broadcast_data(self):

        data = self.data
        index = self.data.last_index()
        json = {
            'ctps': data.ctps[index],
            'tps':  data.tps[index],
            'numTxs': data.numTxs[index],
            'numCtxs': data.numCtxs[index],
            'cRate': data.cRate[index],
            'maxCtps': data.maxCtps[index],
            'maxTps': data.maxTps[index]

        }
        #write feed to file
        with open('feed.out', 'w+') as f:
            f.write(str(json))

        #send json to api endpoint
        if self.tangle.auth_key and self.tangle.latest_milestone_index > self.tangle.milestone_to_broadcast_after:
            res = api.API(json, self.tangle.auth_key, self.tangle.api_url)
            print res

        t = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(self.tangle.prev_timestamp / 1000 / 1000))
        slack_string = ''
        if self.tangle.testnet:
            slack_string = 'TESTNET: '
        slack_string += "{}: {} (of {}) confirmed transactions / {} Confirmation rate / TPS: {} CTPS: {} / {} milestones".format(
            t,
            json['numCtxs'],
            json['numTxs'],
            json['cRate'],
            data.tps[index],
            data.ctps[index],
            self.tangle.latest_milestone_index)
        # send slack only every X time
        if (  self.tangle.prev_timestamp > self.last_slack_broadcast + self.slack_broadcast_threshold):
            self.last_slack_broadcast = self.tangle.prev_timestamp

            print slack_string
            #send slack channel msg
            if self.tangle.slack_key and self.tangle.latest_milestone_index > self.tangle.milestone_to_broadcast_after:
                res = api.API_slack(slack_string, self.tangle.slack_key)
                print res


    def print_stats(self):
        full_table_data = [['timestamp', 'Total Tx.', 'Confirmed Tx.', 'Conf. rate', 'TPS', 'CTPS', 'Tangle width',
                       'avg. confirmation time', 'all-time avg. TPS', 'all-time avg. CTPS', 'max TPS', 'max CTPS']]
        short_table_data = [['timestamp', 'Total Tx.', 'Confirmed Tx.', 'Conf. rate', 'TPS', 'CTPS', 'Tangle width',
                       'avg. confirmation time', 'all-time avg. TPS', 'all-time avg. CTPS', 'max TPS', 'max CTPS']]

        for (c, d) in enumerate(self.data.all):
            full_table_data.append(d)
            if c > self.tangle.prev_print - self.tangle.lines_to_show:
                self.tangle.prev_print = c
                short_table_data.append(d)

        with open(self.tangle.output_short, 'w+') as f:
            f.write(AsciiTable(short_table_data).table)

        with open(self.tangle.output_full, 'w+') as f:
            f.write(AsciiTable(full_table_data).table)
        pass

    ###################################
    # WIDTH related
    ###################################
    def calc_width(self):
        hist = {}

        hist_milestone = {}
        hist_confirmed = {}
        hist_unconfirmed_tips = {}
        hist_unconfirmed_non_tips = {}
        hist_milestone_data = {}

        for n in self.tangle.graph.nodes():
            if not self.tangle.graph.node[n].has_key('height'):
                continue

            height = self.tangle.graph.node[n]['height']

            if not hist.has_key(height):
                hist[height] = 0
            hist[height] += 1

            # hist_confirmed
            if self.tangle.graph.node[n].has_key('is_milestone') and self.tangle.graph.node[n]['is_milestone']:
                if not hist_milestone.has_key(height):
                    hist_milestone[height] = 0
                    hist_milestone_data[height] = []
                hist_milestone[height] += 1
                hist_milestone_data[height].append(n)
                continue

            # hist_confirmed
            if self.tangle.graph.node[n].has_key('confirmed') and self.tangle.graph.node[n]['confirmed']:
                if not hist_confirmed.has_key(height):
                    hist_confirmed[height] = 0
                hist_confirmed[height] += 1
                continue

            # hist_unconfirmed_tips
            if self.tangle.graph.in_degree(n) == 0:
                if not hist_unconfirmed_tips.has_key(height):
                    hist_unconfirmed_tips[height] = 0
                hist_unconfirmed_tips[height] += 1
                continue

            # hist_unconfirmed_non_tips
            if not hist_unconfirmed_non_tips.has_key(height):
                hist_unconfirmed_non_tips[height] = 0
            hist_unconfirmed_non_tips[height] += 1
            continue

        with open('width.out', 'w+') as f:
            f.write(
                "height " + "Total_width " + "milestone " + "confirmed " + "unconfirmed_tips " + "unconfirmed_non_tips" + '\n')

            for key in sorted(hist):
                line = str(key) + " " + str(hist[key]) + " "
                if hist_milestone.has_key(key):
                    line += str(hist_milestone[key]) + " "
                else:
                    line += "0" + " "
                if hist_confirmed.has_key(key):
                    line += str(hist_confirmed[key]) + " "
                else:
                    line += "0" + " "

                if hist_unconfirmed_tips.has_key(key):
                    line += str(hist_unconfirmed_tips[key]) + " "
                else:
                    line += "0" + " "

                if hist_unconfirmed_non_tips.has_key(key):
                    line += str(hist_unconfirmed_non_tips[key]) + " "
                else:
                    line += "0" + " "

                line += '\n'
                f.write(line)

        with open('width.hist', 'w+') as f:
            f.write("milestone: # " + "confirmed: * " + "unconfirmed_non_tips: = " + "unconfirmed_tips: + " + '\n\n')

            for key in reversed(sorted(hist)):
                line = '{:7d}'.format(key) + " " + '{:4d}'.format(hist[key]) + " "

                if hist_milestone.has_key(key):
                    # print milestone details
                    line += "".join((['[#{:<6d} / {:10d}] #'.format(self.tangle.graph.node[n]['index'],
                                                                    self.tangle.graph.node[n]['timestamp']) for n in
                                      hist_milestone_data[key]]))
                else:
                    line += " " * 23

                if hist_confirmed.has_key(key):
                    line += hist_confirmed[key] * '*'

                if hist_unconfirmed_non_tips.has_key(key):
                    line += hist_unconfirmed_non_tips[key] * '='

                if hist_unconfirmed_tips.has_key(key):
                    line += hist_unconfirmed_tips[key] * '+'

                line += '\n'
                f.write(line)

        pass


    def mark_height(self):
        for n in self.tangle.graph.nodes():
            if self.tangle.graph.node[n].has_key('height'):
                continue
            if n == self.tangle.all_nines:
                self.tangle.graph.node[n]['height'] = 0
                continue
            self.mark_height_for_node(n)

        pass


    def mark_height_for_node(self, n):
        current = n
        hops = 0
        hops_list = [n]
        while True:
            if not self.tangle.graph.node[current].has_key('trunk'):
                return

            current = self.tangle.graph.node[current]['trunk']
            if not self.tangle.graph.has_node(current):
                return

            hops += 1

            if self.tangle.graph.node[current].has_key('height'):
                hops += self.tangle.graph.node[current]['height']
                break

            hops_list.append(current)

        for h in hops_list:
            self.tangle.graph.node[h]['height'] = hops
            hops -= 1

    def calc_confirmation_time(self):
        conf_times = []
        conf_index = []
        for n in self.tangle.graph.nodes():
            if self.tangle.graph.node[n].has_key('confirmed') and self.tangle.graph.node[n]['confirmed']:
                conf_times.append(str(self.tangle.graph.node[n]['confirmingMilestone']) + " " + str(self.tangle.graph.node[n]['confirmationTime']))

        with open('conf_times.out', 'w+') as f:
            for ct in conf_times:
                f.write(str(ct) + '\n')
        pass




