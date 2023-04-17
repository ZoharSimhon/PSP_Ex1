import socket
#In order to send a dictionary in bytes
import pickle
#In order to handle with timeout
#in order to hash the file using md5 algorithm
import hashlib

# initialize global variables:
SERVER_IP = '127.0.0.1'
SERVER_PORT = 58000
FILE_NAME = "recieved_file_proxy2.jpeg"
# proxy1's details:
PROXY1_IP = '127.0.0.1'
PROXY1_PORT = 57000
# rudp variables
TIMEOUT = 1.5
CURRENT_WINDOW = 1
PACKET_CAPACITY = 2048


def ask_file_rudp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as clientSocket:
        addr = (PROXY1_IP,PROXY1_PORT)
        #timeout for the SYN packet
        clientSocket.settimeout(TIMEOUT)
        #send a syn ack - and get the size of the file 
        recievedACKPacket = send_SYN_packet(clientSocket, addr)
        fileSize = recievedACKPacket["Data"]
        
        #create an array to save the data in order
        fileDataInBytes = [b""] * fileSize
        
        #make the socket's methods into non-blocking methods
        clientSocket.setblocking(False)
        
        run = True
        
        #receiving data loop
        while run:
            recievedPSHPacket, addr = handle_with_recieved_packet(clientSocket)
            #check if we have got a PSH packet - one chunck of data 
            if recievedPSHPacket != None and recievedPSHPacket["Flag"] == "[PSH]":
                #build a new packet inorder to send an ACK nessage to the server 
                flag= "[ACK]"
                seq = recievedPSHPacket["Seq"]
                data = b"I have got this chunck"
                currentWindow = recievedPSHPacket["Win"]
                fileDataInBytes[seq-1] = recievedPSHPacket["Data"]
                send_packet_to_client(clientSocket, addr, flag, seq, data, currentWindow)
            #check if we have got a FYN packet - because we have got the whole file
            if recievedPSHPacket != None and recievedPSHPacket["Flag"] == "[FYN]":
                run = False
        
        #send a FYN,ACK message , in order to finish the connection with the server
        #we make a for loop to solve the case that the FYN,ACK packet gets lost  
        for i in range (1,6):
            flag= "[FYN,ACK]"
            seq = fileSize+i
            data = b"I have got the whole file"
            currentWindow = b""
            send_packet_to_client(clientSocket, addr, flag, seq, data, currentWindow)
        
        create_file(fileDataInBytes, fileSize)

def create_file(fileDataInBytes, fileSize):
    #open the file in write bytes mode 
    file = open(FILE_NAME, 'wb')
    #write the file in order
    for i in range (fileSize):
        data = fileDataInBytes[i] 
        file.write(data)
    file.close()
        
def send_SYN_packet(clientSocket, addr):
    clientSocket.setblocking(True)
    run = True
    #try to send the FYN message until we get an ACK
    #we make a while loop to solve the case that the FYN,ACK packet gets lost  
    while run:
        flag = "[SYN]"
        seq = 0
        data= b"Please send the file"
        send_packet_to_client(clientSocket, addr, flag, seq, data, CURRENT_WINDOW)
        # get an ack message from the server
        recievedACKPacket = handle_with_recieved_packet(clientSocket)[0]   
        #if we have got an ack message - then we can stop running and and send the data 
        if recievedACKPacket != None and recievedACKPacket["Flag"] == "[SYN,ACK]":
            run = False
    return recievedACKPacket

def send_packet_to_client(clientSocket, addr, flag, seq, data, currentWindow):
    #First, we build the packet we want to send
    buildPacket = {"Flag": flag, "Seq": seq,  "Win": currentWindow, "Data": data}
    #Second, we convert the packet into bytes
    #Finally, we send the packet to the client
    clientSocket.sendto(pickle.dumps(buildPacket), addr)    

def handle_with_recieved_packet(clientSocket):
    #try to recieve a packet from the client
    try:
        recievedPacketInBytes, addr = clientSocket.recvfrom(PACKET_CAPACITY)
    #if we didn't recieve a packet - we send a None tupple
    except OSError:
        return None, None
    recievedPacket = pickle.loads(recievedPacketInBytes)
    #print the received packet
    print("received packet:")
    print(recievedPacket)
    return recievedPacket, addr

def hash_md5():
    # open the file in write bytes mode
    with open(FILE_NAME,"rb") as file:
        data = file.read()
        md5hash = hashlib.md5(data)
        result = md5hash.hexdigest()
    # print the function's result
    print("the hash of the file accordig md5 algorithm is: \n", result)

def send_file_tcp():
    #open a tcp (SOCK_STREAM) socket in order to handle the clients
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        #Often the activation of the method bind() falls with the message "Address already in use". 
        #In order to allow reuse of port we added the following code:
        yes=1
        clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, yes)
        #Link an address and port with a socket is carried out by the method bind().
        clientSocket.bind((SERVER_IP, SERVER_PORT))
        #After the bind operation the receiver goes into standby mode (TCP) by call the method listen().
        clientSocket.listen()
        print("Proxy2 server is listening...")
        #Ejecting a connection request from the request queue is performed by call the method accept() (TCP).
        #When a sender connects the method returns a new socket object representing the connection.
        #Information is inserted about the client that is connecting.
        connection, address = clientSocket.accept()
        with connection:
            #open the file in read bytes mode 
            file = open(FILE_NAME, 'rb')
            #send all the file to the client
            connection.sendall(file.read())
            #close the file
            file.close()



#main:

#first, get the file from the sender according rudp
ask_file_rudp()

# second, hash of the file accordig md5 algorithm
hash_md5()

#then, send the file to proxy2 according tcp
send_file_tcp()