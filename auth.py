import uuid
import random

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256

from logger import Logger
from mac import *


class Authentication(object):
    # These values are public so they can be hardcoded
    shared_prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497C515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
    shared_base = 2;
    g = shared_base
    p = shared_prime
    client_verify_str = "thisisclient"
    server_verify_str = "thisisserver"
    client_str = "CLIENT"

    def __init__(self, shared_key, conn, app, debug=False, is_server=False):
        # We need to generate two keys - one for encrypting
        # the message and one for sending a MAC message
        self.debug = debug
        self.conn = conn
        self.is_server = is_server
        self.app = app

        sha256_hash = SHA256.new()
        sha256_hash.update(str(shared_key))
        self.shared_key = sha256_hash.digest()
        sha256_hash = SHA256.new()
        sha256_hash.update(str(self.shared_key))
        self.mac_key = sha256_hash.digest()

        print "Shared Key: " + self.shared_key
        print "Mac Key: " + self.mac_key

    def encrypt_message(self, message, session_key):

        iv = Random.new().read(AES.block_size)

        Logger.log("-- Encrypting Message --", self.is_server)
        Logger.log("IV: " + iv.encode("hex"), self.is_server)

        msg = str(message) + (((16 - len(message)) % 16) * ' ')  # pad message with spaces
        mac = get_mac(msg, self.mac_key, session_key, self.debug, self.is_server)
        cipher = AES.new(str(session_key), AES.MODE_CBC, iv)
        ciphertext = iv + cipher.encrypt(msg) + mac
        return ciphertext

    def decrypt_message(self, message, session_key):
        iv = message[0:16]

        Logger.log("-- Decrypting Message --", self.is_server)
        Logger.log("IV: " + iv.encode("hex"), self.is_server)

        sent_mac = message[-16:]
        cipher = AES.new(str(session_key), AES.MODE_CBC, iv);
        plaintext = cipher.decrypt(message[16:-16])

        if (verify_integrity(sent_mac, plaintext, self.mac_key, session_key)):
            valid = True
        else:
            valid = False
        return plaintext, valid

    def get_sessionkey(self):
        return self.session_key

    def get_mackey(self):
        return self.mac_key

    def wait_for_continue(self):
        if self.app.debug:
            while not self.app.continue_pressed:
                pass
            self.app.continue_pressed = False

    def int_to_bytes(self, value):
        b = bytearray()

        while value > 0:
            b.append(value % 256)
            value = value // 256

        return b

    def bytes_to_string(self, bytes):
        key = ''
        for b in bytes:
            key += "0x{:02x}".format(b)[2:4]
        # Logger.log("b: "+ "0x{:02x}".format(b))
        # Logger.log("bytes to string: " + key)
        return key

    def get_message(self):
        msg = None
        while not msg and not self.conn.waiting:
            msg = self.conn.receive()
        return msg

    def send(self, message):
        self.conn.send(message)

    def mutualauth(self):
        if self.is_server:
            # Server Mode

            Logger.log("### Server waiting for key authentication contact...", self.is_server)
            # Wait for client to reach out
            response = self.get_message()

            # Client response is in the form: ["thisisclient,Ranonce"]
            try:
                split_resp = response.split(',', 1)
                filler = split_resp[0]
                Ranonce = int(split_resp[1])
            except:
                Logger.log("Server reponse in unexpected format", is_server=True)
                return False

            if self.debug:
                Logger.log("Client Response ([thisisclient, Ranonce])", is_server=True)
                Logger.log("Filler: " + filler, is_server=True)
                Logger.log("Ra-nonce: " + str(hex(Ranonce)), is_server=True)
                print "\n"

            self.wait_for_continue()

            if (filler != self.client_verify_str):
                print('Initial Client message is not in the correct format. Received {}'.format(response))
                print('Mutual Authentication failed')
                return False

            # Server response is in the form : ["Rbnonce,E("server",Ranonce,(g^b)modp)]
            Rbnonce = uuid.uuid4().int
            b = random.getrandbits(2048)
            gbmodp = pow(self.g, b, self.p)

            if self.debug:
                print "\n"
                Logger.log("Constructing Server Response (Rbnonce, [E(server , Ranonce, (g^b)modp)])", is_server=True)
                Logger.log("b value: " + str(hex(b)), is_server=True)
                Logger.log("shared key" + self.shared_key, True)
                Logger.log("Rb-nonce: " + str(hex(Rbnonce)), is_server=True)
                Logger.log("(g^b)modp: " + str(hex(gbmodp)), is_server=True)
                print "\n"

            self.wait_for_continue()

            # Create response, encrypt and send
            serv_resp = self.server_verify_str + "," + str(Ranonce) + "," + str(gbmodp)
            encr_serv_resp = self.encrypt_message(serv_resp,
                                                  self.shared_key)

            if self.debug:
                Logger.log("Encrypted message length: " + str(len(encr_serv_resp[16:])), is_server=True)

            self.send(str(Rbnonce) + "," + encr_serv_resp)

            # Wait for client's encrypted message
            encr_client_resp = self.get_message()

            # which is in the form: ["E("client",Rbnonce,(g^a)modp)"]
            try:
                decr_client_resp, valid = self.decrypt_message(encr_client_resp, self.shared_key)

                if (valid == False):  # check cbc validation
                    Logger.log("CBC Mac validation failed", self.is_server)
                    return False

                split_resp = decr_client_resp.split(',')
                filler = split_resp[0]
                received_nonce = int(split_resp[1])
                gamodp = int(split_resp[2])
            except:
                Logger.log("Server reponse in unexpected format", is_server=True)
                return False

            self.wait_for_continue() # continue, debug mode

            if self.debug:
                print "\n"
                Logger.log("Client Response ([E(client , Rbnonce, (g^a)modp)])", is_server=True)
                Logger.log("Filler: " + str(filler), is_server=True)
                Logger.log("Received-nonce: " + str(hex(received_nonce)), is_server=True)
                Logger.log("(g^a)modp: " + str(hex(gamodp)), is_server=True)
                print "\n"

            if (filler != self.client_str or received_nonce != Rbnonce):
                print('Encrypted message from client is not correct. Mutual Authentication Failed')
                print "FAIL:"
                print "FILLER:" + filler + "."
                print "RB_NONCE:" + str(hex(Rbnonce)) + "."
                return False

            self.wait_for_continue()
            self.session_key = self.bytes_to_string(self.int_to_bytes(pow(gamodp, b, self.p))[:16])
            if self.debug:
                Logger.log("Session Key: " + str(self.session_key), is_server=True)

            b = 0  # forget b - value for PFS

            # At this point, we can be sure that we are talking with the correct client
            # and we have a shared session key
            return True;

        else:
            # Client Mode

            # Generate a nonce and send this to the server
            # Initiate contact by sending the following message: ["thisisclient,Ranonce"]
            Logger.log("### Client initiating Key Authentication.. ", self.is_server)

            Ranonce = uuid.uuid4().int
            if self.debug:
                print "\n"
                Logger.log("Ra-nonce: " + str(hex(Ranonce)))
                print "\n"

            self.send(self.client_verify_str + "," + str(Ranonce));

            # Wait for the server response
            # In the form: ["Rbnonce,E("server",Ranonce,(g^b)modp)"]
            serv_resp = self.get_message()

            # Split the message to get the nonce and the encrypted bit
            # decr_server_resp = self.decrypt_message(serv_resp, self.shared_key)
            try:
                split_resp = serv_resp.split(',', 1)
                Rbnonce = int(split_resp[0])
                encr_server_resp = split_resp[1]
            except:
                Logger.log("Server reponse in unexpected format")
                return False

            decr_server_resp, valid = self.decrypt_message(encr_server_resp,
                                                           self.shared_key)

            if (valid == False):  # check cbc mac validation
                Logger.log("CBC Mac validation failed", self.is_server)
                return False

            # Split the decrypted message to get the filler, client nonce, and (g^b)modp
            try:
                split_resp = decr_server_resp.split(',')
                filler = split_resp[0]
                nonce = int(split_resp[1])
                gbmodp = int(split_resp[2])
            except:
                Logger.log("Server reponse in unexpected format")
                return False

            if self.debug:
                print "\n"
                Logger.log("Server Response (Rbnonce, [E(server , Ranonce, (g^b)modp)])")
                Logger.log("Rbnonce: " + str(hex(Rbnonce)))
                Logger.log("Filler: " + filler)
                Logger.log("Nonce: " + str(nonce))
                Logger.log("(g^b)modp: " + str(hex(gbmodp)))
                print "\n"

            if (nonce != Ranonce or filler != self.server_verify_str):
                print('Client is not talking to authorized server. Mutual Authentication failed')
                return False

            # Client responds in the form: ["E(client,Rbnonce,(g^a)modp)"]
            a = random.getrandbits(2048)
            gamodp = pow(self.g, a, self.p)

            if self.debug:
                print "\n"
                Logger.log("Constructing Client Response ([E(client , Rbnonce, (g^a)modp)])")
                Logger.log("a value: " + str(hex(a)))
                Logger.log("(g^a)modp: " + str(hex(gamodp)))
                print "\n"

            encr_client_resp = self.encrypt_message(self.client_str + "," + str(Rbnonce) + "," + str(gamodp),
                                                    self.shared_key)  # TODO Encrpt this using Aes in cbc mode
            self.send(encr_client_resp)

            # Calculate the session key
            self.session_key = self.bytes_to_string(self.int_to_bytes(pow(gbmodp, a, self.p))[:16])

            a = 0  # forget a value for PFS
            if self.debug:
                Logger.log("Session Key: " + str(self.session_key))

            # We are now guaranteed to be talking with our server
            # We also now have a shared session key
            return True
