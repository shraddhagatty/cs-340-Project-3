import json
from collections import defaultdict
from simulator.node import Node


class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        self.sequence_numbers = defaultdict(int) #Dictionary to store sequence number for each neighbors
        self.cost = defaultdict(dict) #Dictionary to store shortest path
        self.shortest_paths = {}
        self.messages = {}

    # Return a string
    def __str__(self):
        #"Rewrite this function to define your node dump printout"
        cost_str = ", ".join([f"({key}: {value})" for key, value in self.cost.items()])
        return f"Node ID: {self.id}, Cost: {cost_str}"


    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 del from cost dictionary
        if latency == -1:
            del self.cost[self.id][neighbor]
            del self.cost[neighbor][self.id]
        else: 
            self.cost[self.id][neighbor] = latency
            self.cost[neighbor][self.id] = latency

        #update shortest path after link update
        self.update_shortest_paths()

        # Increment if the link is newly added 
        if (self.id,neighbor) in self.messages:
            self.sequence_numbers[(self.id,neighbor)] += 1
        else:
            self.sequence_numbers[(self.id,neighbor)] = 0
            #m = json.dumps([self.id,neighbor,latency,self.sequence_numbers[(self.id,neighbor)]])
            #send message to all links about the new link
            for msg_id,msg in  self.messages.items():
                #message = json.dumps(msg)
                self.send_to_neighbor(neighbor, json.dumps(msg))
           
        m = [self.id,neighbor,latency,self.sequence_numbers[(self.id,neighbor)]]
        self.messages[(self.id,neighbor)] = m
        self.send_to_neighbors(json.dumps(m))

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # Unpack the incoming message
        msg = json.loads(m)
        source =msg[0]
        destination= msg[1]
        cost = msg[2]
        seq_num = msg[3]

       # print(f"before: {msg}")

       # Compare received sequence number with stored sequence number for the link
        if (source, destination) in self.sequence_numbers:
            message = self.messages[(source, destination)]
            if message[3] > seq_num:
                self.send_to_neighbor(source, json.dumps(message))
                return 
            if message[3] == seq_num:
                return

       # print(f"self.messages[link_key] : {self.messages[link_key]} msg :{msg}")
        # Store incoming message seq num is highere
        self.sequence_numbers[(source, destination)] = seq_num
        self.messages[(source, destination)] = msg

       # print(f"self.messages[(source, destination)] : {self.messages[(source, destination)]}")
        # Update link cost and shortest paths
        if cost == -1: 
            if destination in self.cost[source]:
                del self.cost[source][destination]
                del self.cost[destination][source]
        else:
            self.cost[source][destination] = cost
            self.cost[destination][source] = cost

        #print(f"Cost: {self.cost}")

        self.update_shortest_paths()
        self.send_to_neighbors(json.dumps(msg))

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.shortest_paths:
            return self.shortest_paths[destination]
        else:
            return -1

    
    def update_shortest_paths(self):
       # Initialize variables
        INF = float('inf') 
        distances = {node: INF for node in self.cost.keys()}  # Dictionary to store shortest distances
        previous_nodes = {}  # Dictionary to store previous nodes

        # distance of the current node  0
        distances[self.id] = 0

        # While there are unvisited nodes
        while distances:
            # Get the unvisited node with the smallest distance
            current_node = min(distances, key=lambda node: distances[node])

            for neighbor,cost in self.cost[current_node].items():
                # Calculate the distance from the current node to the neighbor
                if neighbor not in distances:
                    continue
                distance = distances[current_node] + cost

                # Update the distance if it's shorter than the current distance
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node

            del distances[current_node]

        # Store the shortest paths in self.shortest_paths
        self.shortest_paths = {}
        for node in previous_nodes:
            if node != self.id:
                #path = []
                current_node = node
                # Backtrack to find the shortest path
                while previous_nodes[current_node] != self.id:
                  #  path.insert(0, current_node)
                    current_node = previous_nodes.get(current_node)
                # Store the shortest path for the current node
                self.shortest_paths[node] = current_node  # Exclude the starting node (current node)  

