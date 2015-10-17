import uuid
import random
from Crypto import Random
from Crypto.Cipher import AES

import TCPconnection


class Authentication(object):
    # These values are public so they can be hardcoded
    shared_prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497C515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
    shared_base = 2;
    g = shared_base
    p = shared_prime

    def __init__(self, shared_key, TCPconn):
        self.shared_key = shared_key
        self.TCPconn = TCPconn
        self.session_key = "SessionKey"

    def encrypt_message(self, message, session_key):
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(str(session_key)[0:7], AES.MODE_CBC, iv)
        ciphertext = iv + cipher.encrypt(message)
        return ciphertext

    def decrypt_message(self, message, session_key):
        iv = message[0:16]
        cipher = AES.new(str(session_key)[0:7], AES.MODE_CBC, iv);
        plaintext = cipher.decrypt(message[17:])
        return plaintext

    def get_message(self):
        return self.TCPconn.recv(1024)

    def send(self, message):
        self.TCPconn.send(message)

    def mutualauth(self, machine):
        if (machine == "server"):
            #Wait for client to reach out
            print "listening!"
            response = self.get_message()  #TODO: OR whatever the listen call is

            print(response)
            #Client response is in the form: ["thisisclient,Ranonce"]
            split_resp = response.split(',')
            filler = split_resp[0]
            Ranonce = int(split_resp[1])

            if (filler != "thisisclient"):
                print('Initial Client message is not in the correct format. Received {}'.format(response))
                print('Mutual Authentication failed')
                return False

            #Server response is in the form : ["Rbnonce,E("server",Ranonce,(g^b)modp)]
            Rbnonce = uuid.uuid4()
            b = random.getrandbits(2048)
            print "Rbnonce: " + str(Rbnonce)
            print "B: " + str(b)
            gbmodp = pow(self.g, b, self.p)
            print "gbmodp: " + str(gbmodp)
            serv_resp = "server," + str(Ranonce) + "," + str(gbmodp)
            print "Serv Response: " + serv_resp
            encr_serv_resp = self.encrypt_message(serv_resp,
                                            self.shared_key)  #TODO Run serv_resp through Aes in cbc mode using shared key
            self.send("" + str(Rbnonce) + "," + encr_serv_resp)  #TODO Actually send it

            #Wait for client's encrypted message             
            encr_client_resp = self.get_message()
            print "Encr Client Resp: " + encr_client_resp

            decr_client_resp = decrypt_message(encr_client_resp,
                                              self.shared_key)  #TODO: Decrypt encr_client_resp through AES in cbc mode

            print "Decr Client Resp: " + decr_client_resp
            #which is in the form: ["E("client",Rbnonce,(g^a)modp)"]
            split_resp = decr_client_resp.split(',')
            filler = split_resp[0]
            received_nonce = split_resp[1]
            gamodp = int(split_resp[2])

            if (filler != "client" or received_nonce != Rbnonce):
                print('Encrypted message from client is not correct. Mutual Authentication Failed')
                return False

            self.sessionKey = pow(gamodp, b, self.p)
            #At this point, we can be sure that we are talking with the correct client
            #and we have a shared session key
            return True;

        elif (machine == "client"):
            #Generate a nonce and send this to the server
            #Initiate contact by sending the following message: ["thisisclient,Ranonce"]
            Ranonce = uuid.uuid4().int
            print "Ra Nonce: " + str(Ranonce)

            self.send("thisisclient," + str(Ranonce));  #TODO: Change this to however we are sending the message

            #Wait for the server response
            #In the form: ["Rbnonce,E("server",Ranonce,(g^b)modp)"]
            serv_resp = self.get_message()
            print "Serv Resp: " + str(serv_resp)

            #Split the message to get the nonce and the encrypted bit
            split_resp = serv_resp.split(',')
            Rbnonce = int(split_resp[0])
            encr_server_resp = split_resp[1]

            decr_server_resp = self.decrypt_message(encr_server_resp,
                                              self.shared_key)  #TODO: Decrypt this using Aes in cbc mode

            print "Decr Serv Resp: " + decr_server_resp
            #Split the decrypted message to get the filler, client nonce, and (g^b)modp
            split_resp = decr_server_resp.split(',')
            filler = split_resp[0]
            nonce = int(split_resp[1])
            gbmodp = int(split_resp[2])

            if (nonce != Ranonce or filler != "server"):
                print('Client is not talking to authorized server. Mutual Authentication failed')
                return False

            #Client responds in the form: ["E(client,Rbnonce,(g^a)modp)"]
            a = random.getrandbits(2048)
            print "A: " + str(a)
            gamodp = pow(self.g, a, self.p)
            print "gamodp: " + str(gamodp)

            encr_client_resp = self.encrypt_message("client," + str(Rbnonce) + "," + str(gamodp),
                                              self.shared_key)  #TODO Encrpt this using Aes in cbc mode
            self.send(encr_client_resp)

            #Calculate the session key
            self.sessionKey = pow(gbmodp, a, self.p)

            #We are now guaranteed to be talking with our server
            #We also now have a shared session key
            return True
        else:
            print "invalid machien type"

