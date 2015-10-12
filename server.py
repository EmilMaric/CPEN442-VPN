from socket import *

serverPort = 12000
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print ('The server is ready to receive')
connectionSocket, addr = serverSocket.accept()

while(1):
    sentence = connectionSocket.recv(1024)
    capitalizedSentence = sentence.decode('utf-8').upper()
    print(capitalizedSentence)
    connectionSocket.send(capitalizedSentence.encode('utf-8'))
    '''connectionSocket.close()'''
