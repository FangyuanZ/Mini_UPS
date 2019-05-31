from multiprocessing.pool import ThreadPool  
from multiprocessing import Pool, cpu_count
import psycopg2

def recv_from_world(conn_world, conn_amazon):
    while True:
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

        new_thread = threading.Thread(target = handle_world_message, args = (conn_world, conn_amazon, data))


def recv_from_amazon(conn_world, conn_amazon):
    while True:
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
        
        new_thread = threading.Thread(target = handle_amazon_message, args = (conn_world, conn_amazon, data))



def handle_world_message(conn_world, conn_amazon, data):
    print("=== receive message from world ===")
    uresps = world_ups_pb2.UResponses()         # response from world
    u2aresps = amazon_ups_pb2.UtoAResponses()   # response to be generated sending to amazon
    ack_to_world = world_ups_pb2.UCommands()    # command (ack) to be sent to world

    uresps.ParseFromString(data)

    if uresps.completions:
        print("=== received truckarrived from world ===\n")
        uresp_truckarrive = uresps.completions
        print(uresp_truckarrive)
        # generate u2aresps.arrived
        for one_truckarrive in uresp_truckarrive:
            # check if completions.status == "arrive warehouse"
            arrive_warehouse = "arrive warehouse"
            #if one_truckarrive.status == arrive_warehouse
            print("=== truck arrived at warehouse ===")
            each_arrive = amazon_ups_pb2.UTruckArrived()    
            each_arrive.truckid = one_truckarrive.truckid
            u2aresps.arrived.extend([each_arrive])
            # ack = completions.seqnum
            ack_to_world.acks.extend([one_truckarrive.seqnum])
            print("=== Add truckarrive to UtoAResponses ===")
            #if one_truckarrive.status == "idle"
            print("=== all packages delivered ===")
    
    if uresp.delivered:
        print("=== received world DeliverMade ===\n")
        # generate u2aresps.delivered
        delivered_packs = uresp_delivered.delivered
        print(delivered_packs)
            
        for each_delivered in delivered_packs:
            each_delivered_a = amazon_ups_pb2.UDelivered()
            each_delivered_a.shipid = each_delivered.packageid
            u2aresps.delivered.extend([each_delivered_a])
            # ack = delivered.seqnum
            ack_to_world.acks.extend([each_delivered.seqnum])
    
    # send u2aresps to amazon
    u2aresps_str = u2aresps.SerializeToString()
    _EncodeVarint(conn_amazon.sendall, len(u2aresps_str))
    conn_amazon.sendall(u2aresps_str)
    print("=== sent delivered to amazon ===")
    
    # send ack_to_world back to world
    ack_to_world_str = ack_to_world.SerializeToString()
    _EncodeVarint(conn_world.sendall, len(ack_to_world_str))
    conn_world.sendall(ack_to_world_str)




def handle_amazon_message(conn_world, conn_amazon, data):
    print("=== receive message from amazon ===\n")
    a2ucmds = amazon_ups_pb2.AtoUCommands()     # command from amazon
    ucmds = world_ups_pb2.UCommands()           # command to be generate sending to world
    u2aresps = amazon_ups_pb2.UtoAResponses()   # response to be generate sending to amazon

    a2ucmds.ParseFromString(data)

    if a2ucmds.sendtrucks:
        print("=== received sendtrucks from amazon ===\n")
        # get sendtrucks info from AtoUCommands()
        trucks_to_sent = a2ucmds_sendtrucks.sendtrucks
        print(trucks_to_sent)

        # generate ucmds.pickups, prepare to send it to world 
        i = 1
        for one_truck in trucks_to_sent:
            each_pickup = world_ups_pb2.UGoPickup()
            each_pickup.truckid = 1    # needs to be checked whether this truck is ok
            each_pickup.whid = one_truck.whs.id
            each_pickup.seqnum = i     # need to be modified later
            ucmds.pickups.extend([each_pickup])
            i += 1
        print("=== Add UGoPickup in UCommands ===")

        # check ack from world and then go on
        
        # generate u2aresps.trucksent, send it back to amazon
        trksent = amazon_ups_pb2.UTruckSent()
        trksent.truckid = 1;
        for each_pack in trucks_to_sent[0].packages:
            trksent.packages.extend([each_pack])
        u2aresps.trucksent.extend([trksent])
        u2aresps_str = u2aresps.SerializeToString()
        _EncodeVarint(conn_amazon.sendall, len(u2aresps_str))
        conn_amazon.sendall(u2aresps_str)
        print("=== Send trucksent back to amazon ===")


    if a2ucmds.startDelivery:
        print("=== received startdelivery from amazon ===\n")
        # get startDelivery info from AtoUCommands()
        all_deliveries = a2ucmds_startdelivery.startdelivery
        print(all_deliveries)

        # generate ucmds.deliveries, prepare to send it to world
        j = 2000
        for each_delivery in all_deliveries:
            delivery = world_ups_pb2.UGoDeliver()
            delivery.truckid = each_delivery.truckid
            for each_package in each_delivery.packages:
                single_package = world_ups_pb2.UDeliveryLocation()
                single_package.packageid = each_package.packageid
                single_package.x = each_package.x
                single_package.y = each_package.y
                delivery.packages.extend([single_package])
                delivery.seqnum = j     # needs to be modified
                j += 1
            ucmds.deliveries.extend([delivery])
        print("=== Add GoDeliver in UCommands ===")

    # send ucmds to world
    ucmds_str = ucmds.SerializeToString()
    _EncodeVarint(conn_world.sendall, len(ucmds_str))
    conn_world.sendall(ucmds_str)
    print("=== Send UCommands to world ===")

