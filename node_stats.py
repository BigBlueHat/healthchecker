
import stats_buffer
import util_cli as util

class NodeList:
    def run(self, accessor, threshold=None):
        result = []
        for node, node_info in stats_buffer.nodes.iteritems():
            if node_info['status'] == "healthy":
                result.append({"host" : node_info['host'], "ip": node, "port": node_info['port'], "version" :node_info['version'], "os": node_info['os'], "status" :node_info['status']})
            else:
                result.append({"host" : node_info['host'], "ip": node, "port": node_info['port'], "version" :"N/A", "os": "N/A", "status" :node_info['status']})
        return result

class NumNodes:
    def run(self, accessor, threshold=None):
        return len(stats_buffer.nodes)

class NumDownNodes:
    def run(self, accessor, threshold=None):
        return len(filter(lambda (a, b): b["status"]=="down" or b["status"]=="unhealthy", stats_buffer.nodes.items()))

class NumWarmupNodes:
    def run(self, accessor, threshold=None):
        return len(filter(lambda (a, b): b["status"]=="warmup", stats_buffer.nodes.items()))

class NumFailOverNodes:
    def run(self, accessor, threshold=None):
        return len(filter(lambda (a, b): b.has_key("clusterMembership") and b["clusterMembership"]!="active", stats_buffer.nodes.items()))

class BucketList:
    def run(self, accessor, threshold=None):
        result = []
        for bucket, bucketinfo in stats_buffer.bucket_info.iteritems():
            result.append({"name": bucket, "type": bucketinfo["bucketType"]})

        return result

class NodeStorageStats:
    def run(self, accessor, threshold=None):
        result = []
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            if values["StorageInfo"].has_key("hdd"):
                result.append({"ip": values["host"],
                           "port": values["port"],
                           "type" : "hdd",
                           "free": util.size_label(values["StorageInfo"]["hdd"]["free"]),
                           "quotaTotal" : util.size_label(values["StorageInfo"]["hdd"]["quotaTotal"]),
                           "used" : util.size_label(values["StorageInfo"]["hdd"]["used"]),
                           "usedByData" : util.size_label(values["StorageInfo"]["hdd"]["usedByData"]),
                           "total" : util.size_label(values["StorageInfo"]["hdd"]["total"])})
            if values["StorageInfo"].has_key("ram"):
                result.append({"ip": values["host"],
                           "port": values["port"],
                           "type" : "ram",
                           "quotaTotal" : util.size_label(values["StorageInfo"]["ram"]["quotaTotal"]),
                           "used" : util.size_label(values["StorageInfo"]["ram"]["used"]),
                           "usedByData" : util.size_label(values["StorageInfo"]["ram"]["usedByData"]),
                           "total" : util.size_label(values["StorageInfo"]["ram"]["total"])})
        return result

class NodeSystemStats:
    def run(self, accessor, threshold=None):
        result = []
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            result.append({"ip": values["host"],
                           "port": values["port"],
                           "cpuUtilization" :util.pretty_float(values["systemStats"]["cpu_utilization_rate"]),
                           "swapTotal": util.size_label(values["systemStats"]["swap_total"]),
                           "swapUsed" : util.size_label(values["systemStats"]["swap_used"]),
                           "currentItems" : values["systemStats"]["currentItems"],
                           "currentItemsTotal" : values["systemStats"]["currentItemsTotal"],
                           "replicaCurrentItems" : values["systemStats"]["replicaCurrentItems"]})

        return result

class ConnectionTrend:
    def run(self, accessor, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                trend.append((node, a, vals[-1]))
            result[bucket] = trend
        return result

class CalcTrend:
    def run(self, accessor, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                trend.append((node, a))
            result[bucket] = trend
        return result

class NodePerformanceStats:
    def run(self, accessor, threshold=None):
        result = {}
        if threshold.has_key(accessor["name"]):
            threshold_val = threshold[accessor["name"]]
        elif accessor.has_key("threshold"):
            threshold_val = accessor["threshold"]
        else:
            threshold_val = None
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            stats = []
            for node, stats_info in bucket_stats.iteritems():
                if accessor["counter"] not in stats_info.keys():
                    stats.append((node, "N/A"))
                    continue
                for key, value in stats_info.iteritems():
                    if key.find(accessor["counter"]) >= 0:
                        if accessor.has_key("threshold"):
                            if int(value) > threshold_val:
                                stats.append((node, (key, value)))
                        else:
                            if accessor.has_key("unit"):
                                if accessor["unit"] == "time":
                                    stats.append((node, util.time_label(value)))
                                elif accessor["unit"] == "size":
                                    stats.append((node, util.size_label(int(value))))
                            else:
                                stats.append((node, (key,value)))
            result[bucket] = stats
        return result

NodeCapsule = [
    {"name" : "NodeStatus",
     "ingredients" : [
        {
            "name" : "nodeList",
            "description" : "Node list",
            "code" : "NodeList",
        },
        {
            "name" : "numNodes",
            "description" : "Number of nodes",
            "code" : "NumNodes",
        },
        {
            "name" : "numDownNodes",
            "description" : "Number of down nodes",
            "code" : "NumDownNodes",
        },
        {
            "name" : "numWarmupNodes",
            "description" : "Number of warmup nodes",
            "code" : "NumWarmupNodes",
        },
        {
            "name" : "numFailedOverNodes",
            "description" : "Number of nodes failed over",
            "code" : "NumFailOverNodes",
        },
      ],
      "clusterwise" : False,
      "nodewise" : True,
      "perNode" : False,
      "perBucket" : False,
    },
    {"name" : "NumberOfConnection",
    "ingredients" : [
        {
            "name" : "connectionTrend",
            "description" : "Connection trend",
            "counter" : "curr_connections",
            "scale" : "minute",
            "code" : "ConnectionTrend",
            "threshold" : {
                "high" : 1000,
            },
            "symptom" : "Number of connections '{0}' reaches connection maximum '{1}'",
        },
     ],
     "nodewise" : True,
     "perNode" : True,
    },
    {"name" : "OOMError",
     "ingredients" : [
        {
            "name" : "oomErrors",
            "description" : "OOM errors",
            "counter" : "ep_oom_errors",
            "scale" : "hour",
            "code" : "CalcTrend",
        },
        {
            "name" : "tempOomErrors",
            "description" : "Temporary OOM errors",
            "counter" : "ep_tmp_oom_errors",
            "scale" : "hour",
            "code" : "CalcTrend",
        },
     ]
    },
    {"name" : "bucketList",
     "ingredients" : [
        {
            "name" : "bucketList",
            "description" : "Bucket list",
            "code" : "BucketList",
        },
     ],
     "nodewise" : True,
    },
    {"name" : "nodeStorageStats",
     "ingredients" : [
        {
            "name" : "nodeStorageStats",
            "description" : "Node storage stats",
            "code" : "NodeStorageStats",
        },
     ],
     "nodewise" : True,
    },
    {"name" : "nodeSystemStats",
     "ingredients" : [
        {
            "name" : "nodeSystemStats",
            "description" : "Node system stats",
            "code" : "NodeSystemStats",
        },
     ],
     "nodewise" : True,
    },
    {"name" : "checkpointPerformance",
     "ingredients" : [
        {
            "name" : "openCheckPoint",
            "description" : "Items for open checkpoints",
            "counter" : "num_checkpoint_items",
            "code" : "NodePerformanceStats",
            "threshold" : 1000,
            "symptom" : "Number of items in a checkpoint '{0}' reaches threshold '{1}'",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "diskPerformance",
     "ingredients" : [
        {
            "name" : "diskCommit",
            "description" : "Average disk commit time",
            "counter" : "disk_commit",
            "code" : "NodePerformanceStats",
            "unit" : "time",
        },
        {
            "name" : "diskUpdate",
            "description" : "Average disk update time",
            "counter" : "disk_update",
            "code" : "NodePerformanceStats",
            "unit" : "time",
        },
        {
            "name" : "diskInsert",
            "description" : "Average disk insert time",
            "counter" : "disk_insert",
            "code" : "NodePerformanceStats",
            "unit" : "time",
        },
        {
            "name" : "diskDelete",
            "description" : "Average disk delete time",
            "counter" : "disk_del",
            "code" : "NodePerformanceStats",
            "unit" : "time",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "AverageDocumentSize",
     "ingredients" : [
        {
            "name" : "averageDocumentSize",
            "description" : "Average document size",
            "counter" : "item_alloc_sizes",
            "code" : "NodePerformanceStats",
            "unit" : "size",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "MemoryUsage",
     "ingredients" : [
        {
            "name" : "totalMemoryUsage",
            "description" : "Total memory usage",
            "counter" : "total_heap_bytes",
            "code" : "NodePerformanceStats",
            "unit" : "size",
        },
        {
            "name" : "totalFragmentation",
            "description" : "Total memory fragmentation",
            "counter" : "total_fragmentation_bytes",
            "code" : "NodePerformanceStats",
            "unit" : "size",
        },
        {
            "name" : "totalInternalMemory",
            "description" : "Total internal memory usage",
            "counter" : "mem_used",
            "code" : "NodePerformanceStats",
            "unit" : "size",
        },
        {
            "name" : "overhead",
            "description" : "Memory overhead",
            "counter" : "ep_overhead",
            "scale" : "hour",
            "code" : "NodePerformanceStats",
            "unit" : "size",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "EPEnginePerformance",
     "ingredients" : [
        {
            "name" : "flusherState",
            "description" : "Engine flusher state",
            "counter" : "ep_flusher_state",
            "code" : "NodePerformanceStats",
        },
        {
            "name" : "flusherCompleted",
            "description" : "Flusher completed",
            "counter" : "ep_flusher_num_completed",
            "code" : "NodePerformanceStats",
        },
        {
            "name" : "avgItemLoadTime",
            "description" : "Average item loaded time",
            "counter" : "ep_bg_load_avg",
            "code" : "NodePerformanceStats",
            "unit" : "time"
        },
        {
            "name" : "avgItemWaitTime",
            "description" : "Average item waited time",
            "counter" : "ep_bg_wait_avg",
            "code" : "NodePerformanceStats",
            "unit" : "time",
        },
     ],
     "perNode" : True,
    },
]


