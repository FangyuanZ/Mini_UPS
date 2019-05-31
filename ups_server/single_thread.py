import socket
import threadpool
from threadpool import *
import time
from multiprocessing.pool import ThreadPool  
from multiprocessing import Pool, cpu_count
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import sys
import psycopg2
import world_ups_pb2
import amazon_ups_pb2

# Init trucks info
truck1 = world_ups_pb2.UInitTruck()
truck1.id = 1
truck1.x = 0
truck1.y = 0
truck2 = world_ups_pb2.UInitTruck()
truck2.id = 2
truck2.x = 10
truck2.y = 10

# Connect ups database
conn_db = psycopg2.connect(database="ups", user="postgres", password="passw0rd")
print("Open ups_db successfully!")

cursor_db = conn_db.cursor()
drop_table_sql = "DROP TABLE IF EXISTS ACCOUNT, TRUCK, PACKAGE, SEQACK"
cursor_db.execute(drop_table_sql)
print("All tables dropped!")


cursor_db = conn_db.cursor()
cursor_db.execute('''CREATE TABLE ACCOUNT
      (ID            SERIAL    PRIMARY KEY     NOT NULL,
      USER_NAME      CHAR(30)            NOT NULL,
      EMAIL          CHAR(30)            NOT NULL,
      PASSWORD       CHAR(30)            NOT NULL);''')
print("Table ACCOUNT created successfully")

cursor_db.execute('''CREATE TABLE TRUCK
      (TRUCK_ID      INT   PRIMARY KEY   NOT NULL,
      STATUS         CHAR(30)            NOT NULL,
      POS_X          REAL                NOT NULL,
      POS_Y          REAL                NOT NULL);''')
print("Table TRUCK created successfully")

cursor_db.execute('''CREATE TABLE PACKAGE
      (PACKAGE_ID    INT PRIMARY KEY     NOT NULL,
      USER_NAME      CHAR(30),
      DEST_X         REAL                NOT NULL,
      DEST_Y         REAL                NOT NULL,
      PACK_STATUS    CHAR(30)            NOT NULL,
      TRUCK_ID       INT                 NOT NULL);''')
print("Table PACKAGE created successfully")

cursor_db.execute('''CREATE TABLE SEQACK
      (SEQNUM        INT  PRIMARY KEY    NOT NULL,
      COMMAND        CHAR(30)            NOT NULL,
      WORLD_ID       INT                 NOT NULL);''')
print("Table SEQACK created successfully")

cursor_db.execute("INSERT INTO TRUCK (TRUCK_ID,STATUS,POS_X,POS_Y) \
      VALUES (" + str(truck1.id) + ", 'idle', " + str(truck1.x) + ", " + str(truck1.y) + ")");

cursor_db.execute("INSERT INTO TRUCK (TRUCK_ID,STATUS,POS_X,POS_Y) \
      VALUES (" + str(truck2.id) + ", 'idle', " + str(truck2.x) + ", " + str(truck2.y) + ")");

conn_db.commit()

# Connect to World Simulator
conn_world = socket.socket()
conn_world.connect(('vcm-9254.vm.duke.edu', 12345))
print("Connected to World Simulator!")

# Wait for Amazon server to connect
server_ups = socket.socket()
server_ups.bind(('0.0.0.0', 8000))
server_ups.listen()
print("Waiting for Amazon to connect...")

conn_amazon, addr = server_ups.accept()
print("Connected by ", addr)


def recv_from_world():
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

def recv_from_amazon():
    var_int_buff = []
    while True:
        buf = conn_amazon.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
            
    data = conn_amazon.recv(msg_len)
    if data:
        try:
            print("recv from amazon: ", data)
        except Exception as e:
            print("error", e)
    return data

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
    data = recv_from_world()
    uconnected.ParseFromString(data)
    print("world simulator status: ", uconnected.result)
    return uconnected.worldid

def send_worldID_to_Amazon(worldID):
    u2aWorldID = amazon_ups_pb2.USendWorldID()
    u2aWorldID.worldid = worldID
    u2aWorldID_msg = u2aWorldID.SerializeToString()
    _EncodeVarint(conn_amazon.sendall, len(u2aWorldID_msg))
    conn_amazon.sendall(u2aWorldID_msg)


global_seqnum = 1000
    
def main():

    global glonal_seqnum
    
    worldID = connect_world_simulator()
    send_worldID_to_Amazon(worldID)
    print("worldID = ", worldID)
    
    while True:
        # recv sendTruck from amazon - ok
        print("=== waiting for amazon sendtrucks cmd ===")
        data = recv_from_amazon()
        a2ucmds_sendtrucks = amazon_ups_pb2.AtoUCommands()
        a2ucmds_sendtrucks.ParseFromString(data)
        trucks_to_sent = a2ucmds_sendtrucks.sendtrucks
        print("=== received sendtrucks cmd ===")
        print(a2ucmds_sendtrucks)

        # ====== interact with db to choose truck
        print("=== choose truck ===")
        idle_truck_id = 0
        cursor_db.execute("SELECT TRUCK_ID from TRUCK where STATUS='idle' OR STATUS='delivering'")
        rows = cursor_db.fetchall()
        if len(rows) > 0:
            for row in rows:
                print("TRUCK_ID = ", row[0])
            # choose first idle truck
            idle_truck_id = row[0]
            # update TRUCK table
            cursor_db.execute("UPDATE TRUCK set STATUS = 'traveling' where TRUCK_ID = " + str(idle_truck_id))
            conn_db.commit()

        # ===== interact with db to update package table
        for each_truck in trucks_to_sent:
            for each_pack in each_truck.packages:
                cursor_db.execute("INSERT INTO PACKAGE (PACKAGE_ID,USER_NAME,DEST_X,DEST_Y,PACK_STATUS, TRUCK_ID) \
                VALUES ("+str(each_pack.packageid)+", '"+each_pack.ups_user_name+"', " \
                +str(each_pack.x)+", "+str(each_pack.y)+", 'in warehouse', "+str(idle_truck_id)+" )");
                conn_db.commit()

        
        # send pickup cmd to world - ok
        ucmds_pickup = world_ups_pb2.UCommands()
        ucmds_pickup.simspeed = 10000
        i = 1
        for one_truck in trucks_to_sent:
            each_pickup = world_ups_pb2.UGoPickup()
            each_pickup.truckid = 1
            each_pickup.whid = one_truck.whs.id
            each_pickup.seqnum = i
            ucmds_pickup.pickups.extend([each_pickup])
            i += 1
        ucmds_pickup_req = ucmds_pickup.SerializeToString()
        print("=== Sent GoPickup to world ===")
        print(ucmds_pickup)
        _EncodeVarint(conn_world.sendall, len(ucmds_pickup_req))
        conn_world.sendall(ucmds_pickup_req)


        # insert cmd in SEQACK table
        cursor_db.execute("INSERT INTO SEQACK (SEQNUM,COMMAND,WORLD_ID) \
            VALUES ("+str(global_seqnum)+", 'UGoPickup', "+str(worldID)+")");
        global_seqnum += 1
        conn_db.commit()
        
        # send trucksent to amazon
        u2aresp_trucksent = amazon_ups_pb2.UtoAResponses()
        for each_trucks_to_sent in trucks_to_sent:
            trksent = amazon_ups_pb2.UTruckSent()
            trksent.truckid = 1;
            for each_pack in each_trucks_to_sent.packages:
                trksent.packages.extend([each_pack])
            u2aresp_trucksent.trucksent.extend([trksent])
   
        print("=== Sent TruckSent to amazon ===")
        print(u2aresp_trucksent)
        u2aresp_trucksent_resp = u2aresp_trucksent.SerializeToString()
        print("trucksent after encoded: ", u2aresp_trucksent_resp)
        _EncodeVarint(conn_amazon.sendall, len(u2aresp_trucksent_resp))
        conn_amazon.sendall(u2aresp_trucksent_resp)

        # recv ufinish from world and ensure truck arrives - ok
        print("=== wait for world truckarrived ===")
        while True:
            data = recv_from_world()
            uresp_truckarrive = world_ups_pb2.UResponses()
            uresp_truckarrive.ParseFromString(data)
            print("=== received truckarrived from world ===")
            print(uresp_truckarrive)
            
            if uresp_truckarrive.acks:
                resp_acks = uresp_truckarrive.acks
                # delete ack
                for ack in resp_acks:
                    cursor_db.execute("DELETE from SEQACK where SEQNUM="+str(ack)+";")
                    conn_db.commit()
            if uresp_truckarrive.completions:
                break
            else:
                continue
        # send truck arrived to Amazon - ok
        u2aresp_truckarrive = amazon_ups_pb2.UtoAResponses()
        for one_truck in uresp_truckarrive.completions:
            each_arrive = amazon_ups_pb2.UTruckArrived()
            each_arrive.truckid = one_truck.truckid
            u2aresp_truckarrive.arrived.extend([each_arrive])
        u2aresp_truckarrive_resp = u2aresp_truckarrive.SerializeToString()
        print("=== sent truckarrived to amazon ===")
        print(u2aresp_truckarrive)
        _EncodeVarint(conn_amazon.sendall, len(u2aresp_truckarrive_resp))
        conn_amazon.sendall(u2aresp_truckarrive_resp)
        
        # recv startdelivery from Amazon - ok
        print("=== waiting for startdelivery from amazon ===")
        data = recv_from_amazon()
        a2ucmds_startdelivery = amazon_ups_pb2.AtoUCommands()
        a2ucmds_startdelivery.ParseFromString(data)
        all_deliveries = a2ucmds_startdelivery.startdelivery
        print("=== received startdelivery from amazon ===\n", all_deliveries)

        # db: update status in table package
        for each_delivery in all_deliveries:
            for each_pack in each_delivery.packages:
                cursor_db.execute("UPDATE PACKAGE set PACK_STATUS = 'out for delivery' where PACKAGE_ID = "+str(each_pack.packageid))
                conn_db.commit()
                                                        
        
        # send UGoDeliver to world 
        ucmds_godeliver = world_ups_pb2.UCommands()
        ucmds_godeliver.simspeed = 10000
        for each_delivery in all_deliveries:
            delivery = world_ups_pb2.UGoDeliver()
            delivery.truckid = each_delivery.truckid
            for each_package in each_delivery.packages:
                single_package = world_ups_pb2.UDeliveryLocation()
                single_package.packageid = each_package.packageid
                single_package.x = each_package.x
                single_package.y = each_package.y
                delivery.packages.extend([single_package])
                delivery.seqnum = 10
            ucmds_godeliver.deliveries.extend([delivery])

        print("=== sent GoDeliver to world ===")
        print(ucmds_godeliver)
        ucmds_godeliver_req = ucmds_godeliver.SerializeToString()
        _EncodeVarint(conn_world.sendall, len(ucmds_godeliver_req))
        conn_world.sendall(ucmds_godeliver_req)

        # insert cmd in SEQACK table
        cursor_db.execute("INSERT INTO SEQACK (SEQNUM,COMMAND,WORLD_ID) \
        VALUES ("+str(global_seqnum)+", 'UGoDelivery', "+ worldID +")");
        global_seqnum += 1
        conn_db.commit()
        
        print("=== wait for world DeliverMade ===")
        while True:
            data = recv_from_world()
            uresp_delivered = world_ups_pb2.UResponses()
            uresp_delivered.ParseFromString(data)
            print("=== received world DeliverMade ===")
            print(uresp_delivered)
            if uresp_delivered.acks:
                resp_acks = uresp_delivered.acks
                # delete ack
                for ack in resp_acks:
                    cursor_db.execute("DELETE from SEQACK where SEQNUM="+str(ack)+";")
                    conn_db.commit()
        
            if not uresp_delivered.delivered:    
                continue
            else:
                all_delivered = uresp_delivered.delivered
                # generate deliveryMade response to amazon
                u2aresp_delivered = amazon_ups_pb2.UtoAResponses() 
                for each_delivered in all_delivered:
                    each_delivered_a = amazon_ups_pb2.UDelivered()
                    each_delivered_a.shipid = each_delivered.packageid
                    u2aresp_delivered.delivered.extend([each_delivered_a])
                
                # send delivery msg to Amazon
                print("=== sent delivered to amazon ===")
                print(u2aresp_delivered)
                u2aresp_delivered_resp = u2aresp_delivered.SerializeToString()
                _EncodeVarint(conn_amazon.sendall, len(u2aresp_delivered_resp))
                conn_amazon.sendall(u2aresp_delivered_resp)
            
                # if all delivered, then break
                if uresp_delivered.completions:
                    print("contain completions msg, all delivery made")
                break
                
        
            
    conn_world.close()
    print("conn_world closed")
    
if __name__== "__main__":
	main()
