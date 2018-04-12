class transaction:
    def __init__(self,hash, address, value, tag, timestamp, current_index, last_index, bundle, trunk, branch):
        self.hash = hash
        self.address = address
        self.value = value
        self.tag = tag
        self.timestamp = timestamp
        self.current_index = current_index
        self.last_index = last_index
        self.bundle = bundle
        self.trunk = trunk
        self.branch = branch

    @classmethod
    def from_trytes(cls, tryte_string, hash_string):
        return cls(
            hash = hash_string,
            #signature_message_fragment = tryte_string[0:2187],
            address = tryte_string[2187:2268],
            value = tryte_string[2268:2295],
            tag = tryte_string[2295:2322],
            timestamp = tryte_string[2322:2331],
            #current_index = tryte_string[2331:2340],
            #last_index = tryte_string[2340:2349],
            bundle = tryte_string[2349:2430],
            trunk = tryte_string[2430:2511],
            branch = tryte_string[2511:2592]
            #nonce = tryte_string[2592:2673]
        )

    @classmethod
    def from_zmq(cls, zmq_feed):
        zmq_feed_list = zmq_feed.split()
        #skip topic
        zmq_feed_list.pop(0)
        return cls(
            hash = zmq_feed_list.pop(0),
            address = zmq_feed_list.pop(0),
            value = zmq_feed_list.pop(0),
            tag = zmq_feed_list.pop(0),
            timestamp = int(zmq_feed_list.pop(0)),
            current_index = int(zmq_feed_list.pop(0)),
            last_index = int(zmq_feed_list.pop(0)),
            bundle = zmq_feed_list.pop(0),
            trunk = zmq_feed_list.pop(0),
            branch = zmq_feed_list.pop(0)
        )