import uuid
import random

from Crypto import Random
from Crypto.Cipher import AES

from logger import Logger

class Authentication(object):
    # These values are public so they can be hardcoded
    shared_prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497C515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
    shared_base = 2;
    g = shared_base
    p = shared_prime
    client_verify_str = "thisisclient"
    server_verify_str = "thisisserver"
    client_str = "CLIENT"
    server_str = "SERVER"

    def __init__(self, shared_key, TCPconn, debug, machine):
        #print "Shared Key: " + str(shared_key) + "Size: " + str(sys.getsizeof(shared_key))
        self.shared_key = b'1234567890123456'
        self.TCPconn = TCPconn
        self.session_key = 0
        self.debug = debug
        self.machine = machine

    def int_to_bytes(self, value):
        b = bytearray()

        while value > 0:
            b.append(value % 256)
            value = value // 256

        b.reverse()
        return b

    def bytes_to_int(self, bytes):
        result = 0;

        for b in bytes:
            result = result * 256 + int(b)
        return result

    def encrypt_message(self, message, session_key):
        iv = Random.new().read(AES.block_size)
        if self.debug:
            Logger.log("-- Encrypting Message --", self.machine)
            Logger.log("IV: " + iv.encode("hex"), self.machine )

        msg = str(message) + (((16 - len(message)) % 16) * ' ') # pad message with spaces
        cipher = AES.new(str(session_key), AES.MODE_CBC, iv)
        ciphertext = iv + cipher.encrypt(msg)
        return ciphertext

    def decrypt_message(self, message, session_key):
        iv = message[0:16]
        if self.debug:
            Logger.log("-- Decrypting Message --", self.machine)
            Logger.log("IV: " + iv.encode("hex"), self.machine )

        cipher = AES.new(str(session_key), AES.MODE_CBC, iv);
        plaintext = cipher.decrypt(message[16:])
        return plaintext

    def get_message(self):
        return self.TCPconn.receive()

    def send(self, message):
        self.TCPconn.send(message)

    def mutualauth(self):
        if (self.machine == self.server_str): # Server Mode
            #Wait for client to reach out
            response = self.get_message()



            #Client response is in the form: ["thisisclient,Ranonce"]
            split_resp = response.split(',',1)
            filler = split_resp[0]
            Ranonce = int(split_resp[1])

            if self.debug:
                Logger.log("Client Response ([thisisclient, Ranonce])", self.machine)
                Logger.log("Filler: " + filler, self.machine)
                Logger.log("Ra-nonce: " + str(hex(Ranonce)), self.machine)
                print "\n"

            if (filler != self.client_verify_str):
                print('Initial Client message is not in the correct format. Received {}'.format(response))
                print('Mutual Authentication failed')
                return False

            #Server response is in the form : ["Rbnonce,E("server",Ranonce,(g^b)modp)]
            Rbnonce = uuid.uuid4().int
            b = random.getrandbits(128)
            gbmodp = pow(self.g, b, self.p)

            if self.debug:
                Logger.log("Constructing Server Response (Rbnonce, [E(server , Ranonce, (g^b)modp)])", self.machine)
                Logger.log("b value: " + str(hex(b)), self.machine)
                Logger.log("Rb-nonce: " + str(hex(Rbnonce)), self.machine)
                Logger.log("(g^b)modp: " + str(hex(gbmodp)), self.machine)
                print "\n"

            serv_resp = self.server_verify_str + "," + str(Ranonce) + "," + str(gbmodp)
            encr_serv_resp = self.encrypt_message(serv_resp,
                                            self.shared_key)

            if self.debug:
                Logger.log("Encrypted message length: " + str(len(encr_serv_resp[16:])), self.machine)

            self.send(str(Rbnonce) + "," + encr_serv_resp)

            #Wait for client's encrypted message             
            encr_client_resp = self.get_message()

            decr_client_resp = self.decrypt_message(encr_client_resp,
                                              self.shared_key)

            #which is in the form: ["E("client",Rbnonce,(g^a)modp)"]
            split_resp = decr_client_resp.split(',')
            filler = split_resp[0]
            received_nonce = int(split_resp[1])
            gamodp = int(split_resp[2])

            if self.debug:
                Logger.log("Client Response ([E(client , Rbnonce, (g^a)modp)])", self.machine)
                Logger.log("Filler: " + str(filler), self.machine)
                Logger.log("Rb-nonce: " + str(hex(received_nonce)), self.machine)
                Logger.log("(g^a)modp: " + str(hex(gamodp)), self.machine)
                print "\n"

            if (filler != self.client_str or received_nonce != Rbnonce):
                print('Encrypted message from client is not correct. Mutual Authentication Failed')
                return False

            self.session_key = self.bytes_to_int(self.int_to_bytes(pow(gamodp, b, self.p))[:16])
            if self.debug:
                Logger.log("Session Key: " + str(hex(self.session_key)), self.machine)

            #At this point, we can be sure that we are talking with the correct client
            #and we have a shared session key
            return True;

        elif (self.machine == self.client_str): # Client Mode
            #Generate a nonce and send this to the server
            #Initiate contact by sending the following message: ["thisisclient,Ranonce"]
            Ranonce = uuid.uuid4().int
            if self.debug:
                Logger.log("Ra-nonce: " + str(hex(Ranonce)), self.machine)
                print "\n"


            self.send(self.client_verify_str + "," + str(Ranonce));

            #Wait for the server response
            #In the form: ["Rbnonce,E("server",Ranonce,(g^b)modp)"]
            serv_resp = self.get_message()

            #Split the message to get the nonce and the encrypted bit
            #decr_server_resp = self.decrypt_message(serv_resp, self.shared_key)
            split_resp = serv_resp.split(',',1)
            Rbnonce = int(split_resp[0])
            encr_server_resp = split_resp[1]

            decr_server_resp = self.decrypt_message(encr_server_resp,
                                              self.shared_key)

            #Split the decrypted message to get the filler, client nonce, and (g^b)modp
            split_resp = decr_server_resp.split(',')
            filler = split_resp[0]
            nonce = int(split_resp[1])
            gbmodp = int(split_resp[2])

            if self.debug:
                Logger.log("Server Response (Rbnonce, [E(server , Ranonce, (g^b)modp)])", self.machine)
                Logger.log("Rbnonce: " + str(hex(Rbnonce)), self.machine)
                Logger.log("Filler: " + filler, self.machine)
                Logger.log("Nonce: " + str(nonce), self.machine)
                Logger.log("(g^b)modp: " + str(hex(gbmodp)), self.machine)
                print "\n"

            if (nonce != Ranonce or filler != self.server_verify_str):
                print('Client is not talking to authorized server. Mutual Authentication failed')
                return False

            #Client responds in the form: ["E(client,Rbnonce,(g^a)modp)"]
            a = random.getrandbits(128)
            gamodp = pow(self.g, a, self.p)

            if self.debug:
                Logger.log("Constructing Client Response ([E(client , Rbnonce, (g^a)modp)])", self.machine)
                Logger.log("A value: " + str(hex(a)), self.machine)
                Logger.log("(g^a)modp: " + str(hex(gamodp)), self.machine)
                print "\n"

            encr_client_resp = self.encrypt_message(self.client_str + "," + str(Rbnonce) + "," + str(gamodp),
                                              self.shared_key)  #TODO Encrpt this using Aes in cbc mode
            self.send(encr_client_resp)

            #Calculate the session key
            self.session_key = self.bytes_to_int(self.int_to_bytes(pow(gbmodp, a, self.p))[:16])

            if self.debug:
                Logger.log("Session Key: " + str(hex(self.session_key)), self.machine)

            #We are now guaranteed to be talking with our server
            #We also now have a shared session key
            return True
        else:
            print "Invalid Machine Type"
            return False

