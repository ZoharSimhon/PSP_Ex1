import socket
#in order to hash the file using md5 algorithm
import hashlib
#In order to make a progress bar
from tqdm import tqdm
from time import sleep

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
        
        # recieve the file size
        data = clientSocket.recv(1024)
        sizeFile = int(data.decode())
        numberOfChuncks = int(sizeFile/1024) + 4
        sleep(1)
        
        #open a file in write bytes mode to recieve the data
        file = open(FILE_NAME,"wb")
        
        #get the data in chuncks
        run = True
        while run:
            #for the progress bar
            for _ in tqdm(range(numberOfChuncks), ascii =" ∙○●",desc= "downloading..." ):
                #append the new data to the opened file
                data = clientSocket.recv(1024)
                sleep(0.01)
                if data != b"":
                    file.write(data)
                else:
                    run = False
        #close the file
        file.close()
        
        print("Done Receiving the file from proxy2 server\n")

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
