'''
Backend would be responsible
- for loading the data
- for making meaningful data structures
- for creating algorithms like Dijkstra
'''

import numpy as np
import pandas as pd
import os
import time

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.join(dir_path, "..", "data")

#paramters
CLOSE_STATIONS = 40

def DataLoading(*filepath):
    '''
    input:  [filepaths of data] filepath = [train_data.csv, train_connections.csv]
    return: [dataframe] train_info_, [Graph] graph_
    processing the data to create dataframes and graph, using helper functions
    '''
    traindata = pd.read_csv(filepath[0])
    newtraindata = traindata[["Latitude", "Longitude", "code"]]
    latandlong = traindata[["Latitude", "Longitude"]]
    formattedtraindata = traindata[["code"]].to_numpy()
    coordinates = latandlong.values.tolist()
    station_to_cords = {}
    
    # in this for loop I am populating the dictionary station_to_cords with the correct data
    for i, j in zip(formattedtraindata, coordinates):
        station_to_cords[i[0]] = j
    
    # calling the creategraph helper function to fill in the graph_ variable with the correct data
    graph_ = CreateGraph(station_to_cords, filepath[1])
    return traindata, graph_


def Distance(coordinate1, coordinate2):
    '''
    input: [list of two elements: latitude and longitude] coordinate 1, same for coordinate 2
    return: The distance in miles between the two coordiantes
    calculates the distance in miles between two coordiante points.
    '''
    # setup the latitude and logitude values to use in the distance formula
    lat1 = np.radians(coordinate1[0])
    lat2 = np.radians(coordinate2[0])
    long1 = np.radians(coordinate1[1])
    long2 = np.radians(coordinate2[1])
    latdif = lat2 - lat1
    longdif = long2 - long1
    
    # calculates the value for the rest of the formula:
    # sin(0.5*(cord1 - cord2))^2 + cos(cord1) * cos(cord2) * sin(0.5 * (cord1 - cord2))^2
    a = (np.sin(latdif / 2)) ** 2 + np.cos(lat1) * np.cos(lat2) * (np.sin(longdif / 2)) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # earth's radius in miles
    radius = 3956
    
    # returns the distance in miles between the two coordiantes (arclength)
    return (c * radius)


def CreateGraph(data, filepath):
    '''
    input:  [Dictionary<string station_code: tuple latitudes>] data, filepath = [train_connections.csv]
    return: [Class Graph instance] graph_
    Creates graph class and populates stations and connections. 
    Ideally we need constant time access to each connection. 
    '''

    connections = pd.read_csv(filepath)
    columns = []
    
    for i in connections.columns:
        columns.append(i)
    
    columns = columns[1:] # columns = [Connection1 Connection2 Connection3 Connection4 Connection5]

    station_names = connections["code"].to_numpy()
    connected_stations = connections[columns].to_numpy()

    graph_ = Graph()

    # adding all stations
    for stn in station_names:
        graph_.add_station(stn, data[stn])

    # adding connections
    for stn, cnnctn in zip(station_names, connected_stations):
        stn_cords = data[stn]
        for con in cnnctn:
            if (con == "None"):
                break
            con_cords = data[con]
            distance = Distance(stn_cords, con_cords)
            graph_.add_connection(stn, con, distance)

    return graph_


def Validity(data, graph, verbose = 0):
    '''
    input:  [dataframe] data_, [Graph] graph
    return: [bool] valid_
    prints a message for each possible error in data entry.
    checks validity of the graph. 
    -graph should be bidirectional,
    -should have all stations
    -should not have multiple unconnected graphs. 
    -should not have a node with no neighbor
    -...
    '''
    error = 0
    stn_codes = list(data["code"])
   
    # looping over each station of graph.
    for stn in graph.get_stations():
        # checking whether station is in our directory
        if (stn.get_id() not in stn_codes):
            error = 1
            print(stn.get_id(), "doesn't seem to exist")
        
        # looping over each connected station
        for ngb in stn.get_connections():

            if stn.get_id() not in graph[ngb].get_connections():
                print(stn.get_id(), "and", ngb, "are not directed.")

            if ngb not in stn_codes:
                error = 1
                print(stn.get_id(), "is connected to", ngb, "but", ngb, "doesn't exist")
            
            # if two connected stations are further than 300 miles something might be off
            if stn.get_weight(ngb) >= 300:
                print(stn.get_id(), " and ", ngb, " seems further than normal.", sep="")
                error = 1
    
    # if no error was seen just output everything seems correct
    if (error == 0 and verbose):
        print("everything seems correct")
        return True
    return False



class Station:

    # each station will be represented by station code, and will have connected stations dictionary
    # connections = {<station name>:<int distance>}
    def __init__(self, station_name, station_coords):
        self.id = station_name
        self.coords = station_coords
        self.connections = {}

    # printing station would be "<station name> : [<station name>, ...]]"
    def __str__(self):
        return str(self.id) + ' : ' + str([x for x in self.connections])

    # adding connection of station, add more raise statements for neightbors
    def add_connection(self, neighbor, weight):
        if (weight <= 0):
            raise Exception("wrong connection weight")
        if type(neighbor) != str:
            raise Exception("wrong key added in connection")
        self.connections[neighbor] = weight

    # return list of connected train station names
    def get_connections(self):
        return self.connections.keys()

    # returns station code
    def get_id(self):
        return self.id

    #returns true if connected stations are closely packed
    def is_closely_packed(self):
        connection_distance = self.connections.values()
        if len(connection_distance) == 0:
            return False
        elif min(connection_distance) < CLOSE_STATIONS:
            return True
        return False

    # returns distance between this station and neighbor
    def get_weight(self, neighbor):
        return self.connections[neighbor]

    # defines <object>[] operator
    def __getitem__(self, i):
        if (type(i) != str):
            raise ValueError("usage: <graph object>[<station code>]")
        if i == self.id:
            return 0
        if i not in self.connections:
            return -1
        return self.connections[i]


class Graph:

    # graph mantains dictionary of stations and number of them. dict = {<stationname>: <Station obj>}
    def __init__(self):
        self.stations = {}
        self.num_stations = 0

    # converts graph to a string so that it can be printed
    def __str__(self):
        result = ""
        for i in self.stations:
            result += self.stations[i].get_id()
            result += " --> "
            for j in self.stations[i].connections:
                result += str(j) + " : " + str(self.stations[i])
            result += "\n"
        return result

    # print only few stations
    def head(self):
        result = ""
        count = 0
        for i in self.stations:
            if (count >= 7):
                break
            count += 1
            result += self.stations[i].get_id()
            result += " --> "
            for j in self.stations[i].connections:
                result += str(j) + " : " + str(self.stations[i].connections[j]) + " , "
            result += "\n"
        return result

    # adds station into stations
    def add_station(self, station_name, station_coords):
        self.num_stations = self.num_stations + 1
        new_station = Station(station_name, station_coords)
        self.stations[station_name] = new_station
        return new_station

    # return object of station given the code
    def get_station(self, n):
        if n in self.stations:
            return self.stations[n]
        else:
            return None

    # adds connection. in theory it's just adding one sided, but our graph should be bidirectional
    def add_connection(self, frm, to, dist):
        if frm not in self.stations:
            raise ValueError("to station is not in station directory")
        if to not in self.stations:
            raise ValueError("to station is not in station directory")

        self.stations[frm].add_connection(to, dist)

    # returns tuple of station objects
    def get_stations(self):
        return self.stations.values()

    # defines <object>[] operator
    def __getitem__(self, i):
        if (type(i) != str):
            raise ValueError("usage: <graph object>[<station code>]")
        if (i not in self.stations):
            raise ValueError("station code not found")
        return self.stations[i]


data_, graph_ = DataLoading(os.path.join(dir_path, "train_data.csv"),os.path.join(dir_path, "train_connections.csv"))
Validity(data_, graph_)

def Dijkstra(src, dest):
    '''
    input:  [string, station code] src, [string, station code] dest, 
            [Graph Object] graph
    output: [Dictionary of distance frm src] dist, [Dictionary of prev nodes] prev
    Finds shortest path between two stations and outputs a list of stations in order
    '''

    dist = {}
    prev = {}
    dist[src] = 0 
    visited = set()
    Q = []

    #populating intialising value
    for v in graph_.stations:
        if v != src:
            dist[v] = 1000000        
            prev[v] = "ABC"       
        Q.append((dist[v], v))
        Q.sort(reverse=True)
    
    #running dijkstra.
    while len(Q) != 0:
        u = Q.pop()[1]
        visited.add(u)        
        for v in graph_[u].connections:
            if v in visited:
                continue
            alt = dist[u] + graph_[u][v]
            temp = dist[v]
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                Q[Q.index((temp, v))] = (alt, v)
                Q.sort(reverse=True)

    return dist, prev



def findPath(src, dest):
    '''
    input:  [string, station code] src, [string, station code] dest, 
    output: [list or array] Path, [bool] true if path found
    Finds shortest path between two stations and outputs a list of stations in order
    USes Dijkstra function.
    '''

    #finding path using dijkstra
    dist, prev = Dijkstra(src, dest)
    path = [dest, ]
    curr = dest
    
    #finding path by backtracking
    while curr != src and curr != "ABC":
        curr = prev[curr]
        path.append(curr)
    if curr == "ABC":
        return [], 0
    
    #return the path
    return path[::-1], 1

# print(data_[data_["code"] == "CHI"])
# print(data_[data_["code"] == "MIA"])
# print(data_[data_["code"] == "LAX"])
# #to check, uncomment this section
# data, graph = DataLoading("./data/train_data.csv", "./data/train_connections.csv")
# print("Raw Data in DataFrame: ")
# print(data.head())
# print("\n" * 2)
# print("Graph Data: ")
# print(graph.head())
# print("\n" * 2)
# print("Accessing distance in constant time:")
# print("Same stations: Graph['CHM']['CHM'] -> ", graph['CHM']['CHM'])
# print("Connected stations: Graph['ABE']['BAL'] -> ", graph['ABE']['BAL'])
# print("Unconnected stations: Graph['ABE']['CHM'] -> ", graph['ABE']['CHM'])
# print("\n" * 2)
# print("Accessing connections in constant time:")
# print("Connected stations: Graph['ABE']['BAL'] -> ", graph['ABE'].get_connections())
