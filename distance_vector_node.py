from simulator.node import Node
from collections import defaultdict
import json 
import copy

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.dvs = {} # node_id : (cost, [path])
        self.costs = {} # (source, destination) : cost
        self.neighbor_dvs = {} #node_id : (time_sent, neighbor_dvs)


    # Return a string
    def __str__(self):
        return f"Node DVS: {self.dvs} | Current Costs: {self.costs}"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1: 
            self.costs[frozenset((self.id, neighbor))] = float("inf")
        else:
            self.costs[frozenset((self.id, neighbor))] = latency
        
        change = self.bf_update()
        if change:
            time = self.get_time()
            self.send_to_neighbors(json.dumps([time, self.id, self.dvs]))


    # Fill in this function
    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        time_sent = message[0]
        source_node = message[1]
        dvs = message[2]
        
        if source_node in self.neighbor_dvs.keys(): 
            if time_sent > self.neighbor_dvs[source_node][0]:
                self.neighbor_dvs[source_node][0]= time_sent
                self.neighbor_dvs[source_node][1] = dvs

        else: 
            print("here")
            self.neighbor_dvs[source_node] = [0, 0]
            self.neighbor_dvs[source_node][0]= time_sent
            self.neighbor_dvs[source_node][1] = dvs

        change = self.bf_update()
        if change: 
            time = self.get_time()
            self.send_to_neighbors(json.dumps([time, self.id, self.dvs]))

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if int(destination) in self.dvs.keys():
            next_hop = self.dvs[destination][1][1]
            return next_hop
        else: 
            return -1

    # Update shortest path based on a link change or an incoming updated dv
    #    if dv changes, send message to neighbors
    def bf_update(self):
        dvs = {self.id : (0, [self.id])}

        #get vertices of graph present in neighbor_dvs
        vertices = []
        for neighbor_id in self.neighbor_dvs.keys():
            neighbor_dvs = self.neighbor_dvs[neighbor_id][1]
            vertices.extend(list(neighbor_dvs.keys()))

        vertices = list(dict.fromkeys(vertices))
        print(vertices)


        for destination in vertices:
            if int(destination) != self.id:
                print("IN LOOP")
                print("DESTINATION", destination)
                destination = int(destination)

                min_dist = float("inf")
                min_path = []

                for neighbor_id in self.neighbor_dvs.keys():
                    neighbor_dvs = self.neighbor_dvs[neighbor_id][1]
                    print(neighbor_dvs.keys())
                    if str(destination) in neighbor_dvs.keys():
                        print("SELF ID", self.id)
                        print("DESTINATION", destination)
                        print(self.costs)
                        dist = self.costs[frozenset((self.id, neighbor_id))] + neighbor_dvs[str(destination)][0]
                        path = copy.deepcopy(neighbor_dvs[str(destination)][1])
                        if self.id in path: continue
                    elif frozenset((self.id, destination)) in self.costs.keys(): 
                        dist = self.costs[frozenset((self.id, destination))]
                        path = [destination]

                    else:
                        dist = float("inf")
                        path = []

                    #compare current min distance with path through this neighbor
                    if dist < min_dist: 
                        min_dist = dist 
                        path.insert(0, self.id)
                        min_path = path 
                
                dvs[destination] = (min_dist, min_path)

        print("CURRENT DVS:", self.dvs)
        print("CHANGED DVS:", dvs)
    
        if dvs != self.dvs: 
            print("UPDATING")
            self.dvs = dvs
            return True  

        return False


