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
        self.neighbors = []


    # Return a string
    def __str__(self):
        return f"Node DVS: {self.dvs} | Current Costs: {self.costs}"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):

        # latency = -1 if delete a link
        if latency == -1: 
            # #loop through own dv and delete entry if neighbor is next hop 
            # dests = copy.deepcopy(list(self.dvs.keys()))
            # for destination in dests: 
            #     if destination != self.id and self.get_next_hop(destination) == neighbor: 
            #         del self.dvs[destination]

            del self.costs[frozenset((self.id, neighbor))]
            del self.neighbor_dvs[neighbor]
            self.neighbors.pop(self.neighbors.index(neighbor))
        else:
            self.costs[frozenset((self.id, neighbor))] = latency
            if neighbor not in self.neighbors: self.neighbors.append(neighbor)

        #update again to see if there is a change
        change = self.bf_update()
        if change:
            time = self.get_time()
            self.send_to_neighbors(json.dumps([time, self.id, self.dvs]))


    # Fill in this function
    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        time_sent = message[0]
        source_node = int(message[1])
        dvs = message[2]

        if source_node not in self.neighbors: self.neighbors.append(source_node)
        if source_node in self.neighbor_dvs.keys(): 
            if time_sent > self.neighbor_dvs[source_node][0]:
                self.neighbor_dvs[source_node][0]= time_sent
                self.neighbor_dvs[source_node][1] = dvs
        else: 
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

        for neighbor in self.neighbors: 
            #check if we have the neighbors dv
            if neighbor in self.neighbor_dvs.keys(): 
                neighbor_dvs = self.neighbor_dvs[neighbor][1]

                for destination in neighbor_dvs.keys(): 
                    destination = int(destination)
                    path = copy.deepcopy(neighbor_dvs[str(destination)][1]) 
                    #make sure current node is not the destination AND self.id is NOT in the path
                    if destination != self.id and self.id not in path:
                        if frozenset((self.id, neighbor)) in self.costs.keys():
                            dist = self.costs[frozenset((self.id, neighbor))] + neighbor_dvs[str(destination)][0]

                        #check if destination is a neighbor in costs and if its shorter than going through neighbor
                        if frozenset((self.id, destination)) in self.costs.keys() and self.costs[frozenset((self.id, destination))] < dist: 
                            dist = self.costs[frozenset((self.id, destination))]
                            path = [destination]

                        #check if there is an entry for this destination
                        if destination in dvs.keys():
                            #see if the distance to dest through neighbor is shorter than the one recorded                    
                            if dist < dvs[destination][0]:
                                dvs[destination][0] = dist
                                path.insert(0, self.id)
                                dvs[destination][1] = path
                        else: 
                            #create instance in dvs
                            dvs[destination] = [0,0]
                            dvs[destination][0] = dist
                            path.insert(0, self.id)
                            dvs[destination][1] = path
            #we don't have the neighbors dv, so make distance the link length and check against stored distance
            else: 
                dist = self.costs[frozenset((self.id, neighbor))]
                path = [self.id, neighbor]
                if neighbor in dvs.keys():
                    #see if the distance to neighbor is shorter than the one recorded                    
                    if dist < dvs[neighbor][0]:
                        dvs[neighbor][0] = dist
                        dvs[neighbor][1] = path
                else: 
                    #create instance in dvs
                    dvs[neighbor] = [0,0]
                    dvs[neighbor][0] = dist
                    dvs[neighbor][1] = path
               

  
        if dvs != self.dvs: 
            self.dvs = dvs
            return True  

        return False

