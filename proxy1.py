import socket
#in order to hash the file using md5 algorithm
import hashlib
#In order to send a dictionary in bytes
import pickle
#In order to handle with timeout
from threading import Timer

# initialize global variables:
SERVER_IP = '127.0.0.1'
SERVER_PORT = 57000
FILE_NAME = "recieved_file_prox1.jpeg"
# sender's details:
SENDER_IP = '127.0.0.1'
SENDER_PORT = 56000
#variables for the send_file_rudp() method
DATA_IN_BYTES = []
FILE_SIZE = 0
#The steps we have are: Slow Start, Congestion Avoidance, Congestion Detection
CC_STEP = "Slow Start"  
THRESHOLD_WINDOW = 16
CURRENT_WINDOW = 1
CURRENT_SENT_WITHOUT_ACK = 0
TIMEOUT = 1.5
PACKET_CAPACITY = 2048
#We reduce the data size in each packet, 
#in order to save bits in the packet for the rest of the information we need to send 
PACKET_DATE_SIZE = (int)((4/5)*PACKET_CAPACITY)

def ask_file_tcp():
    serverAddress = (SENDER_IP, SENDER_PORT)
    #create a tcp socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        #connect to the server with the serverAddress (ip, port)
        clientSocket.connect(serverAddress)
        
        #open a file in write bytes mode to recieve the data
        file = open(FILE_NAME,"wb")
        
        #get the data in chuncks
        run = True
        #while we still get data - keep running
        while run:
            print("Receiving...")
            #append the new data to the opened file
            data = clientSocket.recv(1024)
            if data != b"":
                file.write(data)
            else:
                run = False
        #close the file
        file.close()
        
        print("Done Receiving the file from the tcp redirect server")

def hash_md5():
    # open the file in write bytes mode
    with open(FILE_NAME,"rb") as file:
        data = file.read()
        md5hash = hashlib.md5(data)
        result = md5hash.hexdigest()
    # print the function's result
    print("the hash of the file accordig md5 algorithm is: \n", result)

def send_file_rudp():
    #declare the global variables
    global CC_STEP, THRESHOLD_WINDOW, CURRENT_WINDOW, CURRENT_SENT_WITHOUT_ACK, TIMEOUT, DATA_IN_BYTES
    
    #First, read the file, and divide in=t to chuncks into DATA_IN_BYTES array-list 
    read_and_divide_file()
    
    #open a udp (SOCK_DGRAM) socket in order to handle the clients
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as serverSocket:
        #Often the activation of the method bind() falls with the message "Address already in use". 
        #In order to allow reuse of port we added the following code:
        yes=1
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, yes)
        #Link an address and port with a socket is carried out by the method bind().
        serverSocket.bind((SERVER_IP, SERVER_PORT))
        print("The redirect rudp server is listening...")
        
        #an infinty loop - inorder to handle the incoming requests
        while True:
            #get a new client
            recievedPacket, addr = handle_with_recieved_packet(serverSocket)
            #check if we have got a syn packet - packet from a new client 
            if recievedPacket != None and recievedPacket["Flag"] == "[SYN]":
                #send to the client the FILE_SIZE
                flag = "[SYN,ACK]"
                seq = 0
                data= FILE_SIZE
                send_packet_to_client(serverSocket, addr, flag, seq, data,CURRENT_WINDOW)
                
                #initialize the variables before we send the file
                #initialize those three variables according to the Slow Start step
                CURRENT_WINDOW = 1
                CC_STEP = "Slow Start"  
                CURRENT_SENT_WITHOUT_ACK = 0
                #an array that represents which packets we received ACK for
                #the array is indexed according to the sequence number   
                packetsStatus = [False] * (FILE_SIZE + 1)
                #the run variable equals to True as long as we need to send packets, and  false otherwise
                run = True
                #an index in order to follow which packets we need to send
                i = 0
                #represents the latest sequence number that we have got an ack message for its in a row 
                latestSeqAcked = 0
                #initialize those two variables in order to check three duplicate case
                threeDupCount = 0
                ThreeDupSeq = 0

                #make the socket's methods into non-blocking methods
                serverSocket.setblocking(False)
                
                while run:
                    # find the packet that hasn't send yet
                    while i < FILE_SIZE and packetsStatus[i] == True:
                        i += 1

                    # send a chunck of data to the client
                    if i <= FILE_SIZE and CURRENT_SENT_WITHOUT_ACK < CURRENT_WINDOW:
                        #build a new packet inorder to send one chunck of data 
                        flag= "[PSH]"
                        seq = i
                        data = DATA_IN_BYTES[i-1]
                        send_packet_to_client(serverSocket, addr, flag, seq, data, CURRENT_WINDOW)
                        #start a timer to the i-th packet - and handle this packet if the timer is done
                        timer = Timer(TIMEOUT, handle_timeout_in_packet, (packetsStatus,i))
                        timer.start()
                        #update those two variables - increase in 1
                        CURRENT_SENT_WITHOUT_ACK += 1
                        i += 1                        

                    # get an ack message from the client
                    recievedACKPacket = handle_with_recieved_packet(serverSocket)[0]

                    #if we have got an ack packet
                    if recievedACKPacket != None and recievedACKPacket["Flag"] == "[ACK]":
                        #update the status of the packet to True
                        seqACK = recievedACKPacket["Seq"]
                        packetsStatus[seqACK] = True
                        #decrease the number of the packets that have sent and didn't get an ack
                        CURRENT_SENT_WITHOUT_ACK -= 1
                        
                        #update i - inorder to send again lost packets
                        if latestSeqAcked != seqACK:
                            i = latestSeqAcked
                        
                        #update lastest acked packet
                        while latestSeqAcked < seqACK and packetsStatus[latestSeqAcked]:
                            latestSeqAcked += 1
                        
                        #handle with three duplicate ACK message
                        threeDupCount += 1
                        if seqACK != ThreeDupSeq:
                            ThreeDupSeq = seqACK
                            threeDupCount = 1
                        if threeDupCount == 3:
                            #according to the CC we need to go back to step Congestion Avoidance 
                            CC_STEP = "Congestion Avoidance"
                            #according to the Congestion Avoidance we need to decrease the window in a half
                            CURRENT_WINDOW = (int)(CURRENT_WINDOW / 2)
                            print("three duplicate ACK for sequence number:", seqACK)

                        #in case we have done to send the whole file
                        print("latestSeqAcked:" ,latestSeqAcked, "FILE_SIZE", FILE_SIZE)
                        if latestSeqAcked == FILE_SIZE:
                            run = False

                        # chceck the threshold
                        if THRESHOLD_WINDOW <= CURRENT_WINDOW:
                            CURRENT_WINDOW = (int)(CURRENT_WINDOW / 2)
                            CC_STEP = "Congestion Avoidance"
                    
                    #if we in step Slow Start - then increase the window in two
                    if CC_STEP == "Slow Start" and CURRENT_WINDOW <= THRESHOLD_WINDOW -2:
                        CURRENT_WINDOW += 2
                    
                    #if we in step Congestion Avoidance - then increase the window in one
                    if CC_STEP == "Congestion Avoidance" and CURRENT_WINDOW <= THRESHOLD_WINDOW -1:
                        CURRENT_WINDOW += 1
                        
                #send a FYN packet to the client
                send_FYN_packet(serverSocket, addr,i)
                                                        
def send_FYN_packet(serverSocket, addr,i):
    serverSocket.setblocking(True)
    run = True
    #try to send the FYN message until we get an ACK
    while run:
        flag= "[FYN]"
        seq = i
        data = b"The file is sent"
        send_packet_to_client(serverSocket, addr, flag, seq, data, CURRENT_WINDOW)
        # get an ack message from the client
        recievedACKPacket = handle_with_recieved_packet(serverSocket)[0]        
        if recievedACKPacket != None and recievedACKPacket["Flag"] == "[FYN,ACK]":
            run = False

def handle_timeout_in_packet(packetsStatus, i):
    # if we didn't get an ACK message to the i-th packet
    if packetsStatus[i] == False:
        # set the step back to Slow Start
        #declare the global variables
        global CURRENT_SENT_WITHOUT_ACK, CC_STEP, CURRENT_WINDOW
        #intilize the variables according to step Slow Start
        CURRENT_SENT_WITHOUT_ACK = 0
        CURRENT_WINDOW = 1
        CC_STEP = "Slow Start" 
        #print the timeout to the terminal 
        print("we have got timeout for seq=", i)

def read_and_divide_file():
    #declare the global variables
    global FILE_NAME, DATA_IN_BYTES, PACKET_DATE_SIZE, FILE_SIZE
    #open the file in read bytes mode 
    file = open(FILE_NAME, 'rb')
    #append the file to DATA_IN_BYTES in chuncks in size of PACKET_DATE_SIZE
    #handle the first chunck
    dataInChunck = file.read(PACKET_DATE_SIZE)
    DATA_IN_BYTES.append(dataInChunck)
    
    i = 0
    #while we didn't read the whole file:
    while DATA_IN_BYTES[i] != b"":
        #append the file to DATA_IN_BYTES in chuncks in size of PACKET_DATE_SIZE     
        dataInChunck = file.read(PACKET_DATE_SIZE)
        DATA_IN_BYTES.append(dataInChunck)
        i += 1
    
    #calculate the nummber of packets that we need to send        
    FILE_SIZE = len(DATA_IN_BYTES)
    
    #close the file
    file.close()
    
def send_packet_to_client(serverSocket, addr, flag, seq, data, currentWindow):
    #First, we build the packet we want to send
    buildPacket = {"Flag": flag, "Seq": seq,  "Win": currentWindow, "Data": data}
    #Second, we convert the packet into bytes
    #Finally, we send the packet to the client
    serverSocket.sendto(pickle.dumps(buildPacket), addr)    

def handle_with_recieved_packet(serverSocket):
    #try to recieve a packet from the client
    try:
        recievedPacketInBytes, addr = serverSocket.recvfrom(PACKET_CAPACITY)
    #if we didn't recieve a packet - we send a None tupple
    except OSError:
        return None, None
    recievedPacket = pickle.loads(recievedPacketInBytes)
    #print the received packet
    print("received packet:")
    print(recievedPacket)
    return recievedPacket, addr


#main:

#first, get the file from the sender according tcp
ask_file_tcp()

# second, hash of the file accordig md5 algorithm
hash_md5()

#then, send the file to proxy2 according rudp
send_file_rudp()

