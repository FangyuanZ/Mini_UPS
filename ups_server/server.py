import socket
import threadpool
from threadpool import *
import time
from multiprocessing.pool import ThreadPool  
from multiprocessing import Pool, cpu_count
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import sys
import world_ups_pb2
import amazon_ups_pb2
import threading
from handle_messages import recv_from_world, recv_from_amazon, handle_world_message, handle_amazon_message

# Init trucks info
truck1 = world_ups_pb2.UInitTruck()
truck1.id = 1
truck1.x = 0
truck1.y = 0
truck2 = world_ups_pb2.UInitTruck()
truck2.id = 2
truck2.x = 10
truck2.y = 10


# start two threads to handle messages from amazon and world
def connect_world_simulator():
    # UConnect message to world simulator
    uconnect = world_ups_pb2.UConnect()
    uconnect.trucks.extend([truck1, truck2])
    uconnect.isAmazon = False   
    conn_world_req = uconnect.SerializeToString()
    _EncodeVarint(conn_world.sendall, len(conn_world_req))
    conn_world.sendall(conn_world_req)
    
    # UConnected from world simulator
    uconnected = world_ups_pb2.UConnected()
    data = recv_world_id()
    uconnected.ParseFromString(data)
    print("world simulator status: ", uconnected.result)
    return uconnected.worldid

def send_worldID_to_Amazon(worldID):
    u2aWorldID = amazon_ups_pb2.USendWorldID()
    u2aWorldID.worldid = worldID
    u2aWorldID_msg = u2aWorldID.SerializeToString()
    _EncodeVarint(conn_amazon.sendall, len(u2aWorldID_msg))
    conn_amazon.sendall(u2aWorldID_msg)

def recv_world_id():
    var_int_buff = []
    while True:
        buf = conn_world.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break            
    data = conn_world.recv(msg_len)
    if data:
        try:
            print("recv from world: ", data)
        except Exception as e:
            print("error", e)
    return data

# Connect ups database
#conn_db = psycopg2.connect(database="ups_db", user="postgres", password="passw0rd")
#print("Open ups_db successfully!")

# Connect to World Simulator
conn_world = socket.socket()
conn_world.connect(('vcm-9254.vm.duke.edu', 12345))
print("Connected to World Simulator!")
world_id = connect_world_simulator()
print("world_id = ", world_id)

# Wait for Amazon server to connect
server_ups = socket.socket()
server_ups.bind(('0.0.0.0', 8000))
server_ups.listen()
print("Waiting for Amazon to connect...")

conn_amazon, addr = server_ups.accept()
print("Amazon connected by ", addr)




def main():
    world_thread = threading.Thread(target = recv_from_world, args = (conn_world, conn_amazon))
    amazon_thread = threading.Thread(target = recv_from_amazon, args = (conn_world, conn_amazon))
    while True:
        pass

    conn_world.close()
    print("conn_world closed")
    


    
if __name__== "__main__":
  main()

            

