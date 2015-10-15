import uuid

import TCPconnection

class Authentication(object):

    #These values are public so they can be hardcoded
    shared_prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497C515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
    shared_base = 2;

    def __init__(self, sharedKey, TPconn):
        self.sharedKey = sharedKey
        self.TPconn = TPconn

#client says ["thisisclient,Ranonce]
#server says [Rbnonce,E("server",Ranonce;SharedKey)]
#client says E("client",Rbnonce;SharedKey)
#Server responds with "Authentication Verified" or "Authentication Rejected"
#Where Ranonce = (g^a)modg
#      Rbnonce = (g^b)modg

    def mutualauth(self, machine):
        if(machine == "server"):
            #Wait for client to reach out
            response = TCP.listen() #TODO: OR whatever the listen call is
            split_resp = response.split(',')
            filler = split_resp[0]
            Ranonce = split_resp[1]

            if(filler!="thisisclient"):
                print('Initial Client message is not in the correct format. Received {}'.format(response))
                print('Mutual Authentication failed')
                return False

            Rbnonce = uuid.uuid4().int
            serv_resp = "server,"+Ranonce
            encr_serv_resp = AES.encrypt(serv_resp, self.sharedKey)#TODO Run serv_resp through Aes in cbc mode using shared key
            TCPcon.send("" + Rbnonce + "," + encr_serv_resp) #TODO Actually send it

            #Wait for client's encrypted message
            encr_client_resp = TCP.listen()
            decr_client_resp = AES.derypt(encr_client_resp, self.sharedKey) #TODO: Decrypt encr_client_resp through AES in cbc mode
            split_resp = decr_client_resp.split(',')
            filler = split_resp[0]
            received_nonce = split_resp[1]

            if(filler!="client" or received_nonce!=Rbnonce):
                print('Encrypted message from client is not correct. Mutual Authentication Failed')
		return False
            
            #At this point, we can be sure that we are talking with the correct client
            return True;

        elif(machine == "client"):
            #Generate a nonce and send this to the server
            Ranonce = uuid.uuid4().int
            TCPcon.send("thisisclient," + Ranonce);

            #Wait for the server response
            serv_resp = TCPcon.listen()

            split_resp = serv_resp.split(',')
            Rbnonce = split_resp[0]
            encr_server_resp = split_resp[1]

            decr_server_resp = AES.decrypt(encr_server_resp, self.sharedKey) #TODO: Decrypt this using Aes in cbc mode
            split_resp = decr_server_resp.split(',')

            filler = split_resp[0]
            nonce = split_resp[1]

            if(nonce!=Ranonce or filler!=server):
                print('Client is not talking to authorized server. Mutual Authentication failed')
                return False

            encr_client_resp = AES.encrypt("client,"+Rbnonce, self.sharedKey) #TODO Encrpt this using Aes in cbc mode
            TCPconn.send(encr_client_resp)

            #We are now guaranteed to be talking with our server
            return True



