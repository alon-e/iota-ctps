class data:
    def __init__(self):
        self.timestamp = []
        self.tps = []
        self.ctps = []
        self.numTxs = []
        self.numCtxs = []
        self.cRate = []
        self.maxTps = []
        self.maxCtps = []
        self.avgTps = []
        self.avgCtps = []
        self.width = []
        self.avgCTime = []
        self.counter = -1

        self.all = []

        self.save_max_tps = 0
        self.save_max_ctps = 0


    def append(self,prev_timestamp,num_txs,num_ctxs,c_rate,tps,ctps,width,avg_c_t,avg_tps,avg_ctps):
        self.timestamp.append(prev_timestamp)
        self.numTxs.append(num_txs)
        self.numCtxs.append(num_ctxs)
        self.cRate.append(c_rate)
        self.tps.append(tps)
        self.ctps.append(ctps)
        self.width.append(width)
        self.avgCTime.append(avg_c_t)
        self.avgTps.append(avg_tps)
        self.avgCtps.append(avg_ctps)
        self.counter +=1

        if self.save_max_tps < float(tps):
            self.save_max_tps = float(tps)
        if self.save_max_ctps < float(ctps):
            self.save_max_ctps = float(ctps)

        self.maxTps.append(self.save_max_tps)
        self.maxCtps.append(self.save_max_ctps)

        self.all.append(self.get())

    def get(self,i =-1):
        if i == -1:
            i = self.counter
        output = [self.timestamp[i],
                  self.numTxs[i],
                  self.numCtxs[i],
                  self.cRate[i],
                  self.tps[i],
                  self.ctps[i],
                  self.width[i],
                  self.avgCTime[i],
                  self.avgTps[i],
                  self.avgCtps[i],
                  self.maxTps[i],
                  self.maxCtps[i]
                  ]
        return output

    def last_index(self):
        return self.counter

