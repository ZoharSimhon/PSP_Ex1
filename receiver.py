import socket
#in order to hash the file using md5 algorithm
import hashlib

# initialize global variables:
PRXY2_IP = '127.0.0.1'
PROXY2_PORT = 58000
FILE_NAME = "recieved_file_final.jpeg"

def ask_file_tcp():
    serverAddress = (PRXY2_IP, PROXY2_PORT)
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


#main:

#first, get the file from proxy2 according tcp
ask_file_tcp()

# finally, hash of the file accordig md5 algorithm
hash_md5()
