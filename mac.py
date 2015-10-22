from Crypto.Cipher import AES

from logger import Logger

def get_mac(msg, mac_key, session_key, debug, is_server):
    # cbc-mac requires zeros initialization vector
    iv = b'x\00' * 8

    cipher = AES.new(str(session_key), AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(msg)

    # The mac is the last block of the message
    # block size here is 128 bits or 16 bytes.
    # To get the last block, we simply use
    # string splicing
    mac = ciphertext[-16:]

    # Now, encrypt the mac using self.mac_key
    # We can use ecb mode here since its only
    # one block
    cipher = AES.new(str(mac_key), AES.MODE_ECB)
    encr_mac = cipher.encrypt(mac)

    if debug:
        Logger.log("Cipher text is: " + ciphertext, is_server=is_server)
        Logger.log("Unencrypted mac is: " + mac, is_server=is_server)
        Logger.log("Encrypted mac is: " + encr_mac, is_server=is_server)

    # Return the encr_mac
    return encr_mac

    # encr_mac -> encrypted mac from other machine
    # plaintext -> plain text from which the mac was computed from


def verify_integrity(encr_mac, plaintext, mac_key, session_key):
    iv = b'x\00' * 8 # mac initialization vector is 0

    # calculate the expected value of the mac
    cipher = AES.new(str(session_key), AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(plaintext)

    # Get the last block
    mac = ciphertext[-16:]

    # Now encrypt this mac
    cipher = AES.new(str(mac_key), AES.MODE_ECB)
    expected_mac = cipher.encrypt(mac)

    if (expected_mac == encr_mac):
        return True
    else:
        return False
