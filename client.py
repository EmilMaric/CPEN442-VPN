from socket import *


serverName = '192.168.1.75'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
sentence = input('Input lowercase sentence:')
clientSocket.send(sentence.encode('utf-8'))
modifiedSentence = clientSocket.recv(1024)
print ('From Server:', modifiedSentence)
clientSocket.close()
