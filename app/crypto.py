import hashlib
import sha3

def keccak256(s):
    # Ethereum uses keccak256 as it's cryptographic hash
    key = sha3.keccak_256()
    k.update(s)
    return k.digest()∑