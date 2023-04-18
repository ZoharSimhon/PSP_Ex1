import socket
from time import sleep
# in order to hash the file using md5 algorithm
import hashlib
# in order to find the size file
import os

# initialize global variables:
SERVER_IP = '127.0.0.1'
SERVER_PORT = 56000
FILE_NAME = "file_to_send.jpeg"


def hash_md5():
    # open the file in write bytes mode
    with open(FILE_NAME, "rb") as file:
        data = file.read()
        md5hash = hashlib.md5(data)
        result = md5hash.hexdigest()
    # print the function's result
    print("the hash of the file accordig md5 algorithm is: \n", result)


def size_file():
    file_stat = os.stat(FILE_NAME)
    size = str(file_stat.st_size)
    return size


def send_file_tcp():
    # open a tcp (SOCK_STREAM) socket in order to handle the clients
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocket:
        # Often the activation of the method bind() falls with the message "Address already in use".
        # In order to allow reuse of port we added the following code:
        yes = 1
        clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, yes)
        # Link an address and port with a socket is carried out by the method bind().
        clientSocket.bind((SERVER_IP, SERVER_PORT))
        # After the bind operation the receiver goes into standby mode (TCP) by call the method listen().
        clientSocket.listen(10)
        print("The sender server is listening...")
        # Ejecting a connection request from the request queue is performed by call the method accept() (TCP).
        # When a sender connects the method returns a new socket object representing the connection.
        # Information is inserted about the client that is connecting.
        connection, address = clientSocket.accept()
        with connection:
            # send the file size
            print("send the size file")
            size = size_file()
            print(size)
            connection.send(size.encode())

            sleep(0.5)

            print("start sending the file\n")
            # open the file in read bytes mode
            file = open(FILE_NAME, 'rb')
            # send all the file to the client
            connection.sendall(file.read())
            # close the file
            file.close()

# main:


# first, hash of the file accordig md5 algorithm
hash_md5()

# then, send the file to proxy1 according tcp
send_file_tcp()
