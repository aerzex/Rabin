import sys 
import os
import secrets
import json
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'algorithms'))
sys.path.append(lib_path)
from algorithms import algorithm_fast_pow, algorithm_euclid_extended, algorithm_generate_prime, algorithm_comprasion, algorithm_second_degree_comparison
import hashlib

def generate_keys(size):
    while True:
        p, q = algorithm_generate_prime(size // 2, 50), algorithm_generate_prime(size // 2, 50)
        if p % 4 == 3 and q % 4 == 3:
                break
    N = p * q

    pub_key = {
         "N": N
    }
    scrt_key = {
         "prime1": p,
         "prime2": q
    }

    save_keys(scrt_key, pub_key)
    
    return pub_key, scrt_key


def encrypt(pub_key, message):
    N = pub_key["N"]
    block_size = (N.bit_length() + 7) // 8
    hash_length = 32
    max_msg_len = block_size - 3 - hash_length - 8
    
    encoded = message.encode('utf-8')
    blocks = [encoded[i:i + max_msg_len] for i in range(0, len(encoded), max_msg_len)]
    enc_blocks = []
    for block in blocks: 
        hash_digest = hashlib.sha256(block).digest()[:hash_length]
        data_with_hash = block + hash_digest

        pad_length = block_size - len(data_with_hash) - 3
        if pad_length < 8:
            raise ValueError("Message too long for Rabin block")
        
        padding = generate_padding(pad_length)
        padded_block = padding + data_with_hash #\x00\x02 + padding + \x00 + data_with_hash
        int_block = int.from_bytes(padded_block, 'big')
        enc_block = algorithm_fast_pow(int_block, 2, N)
        enc_blocks.append(enc_block)
    
    return enc_blocks


def decrypt(scrt_key, enc_message):
    p, q = scrt_key["prime1"], scrt_key["prime2"]
    N = p * q
    block_size = (N.bit_length() + 7) // 8
    _, Yp, Yq = algorithm_euclid_extended(p, q)

    dec_blocks = []
    for block in enc_message:
        Mp, Mq = algorithm_second_degree_comparison(block, p)[0], algorithm_second_degree_comparison(block, q)[0]
        M1 = (Yp * p * Mq + Yq * q * Mp) % N
        M2 = N - M1
        M3 = (Yp * p * Mq - Yq * q * Mp) % N
        M4 = N - M3

        possible_blocks = [
            M1.to_bytes(block_size, byteorder='big'),
            M2.to_bytes(block_size, byteorder='big'),
            M3.to_bytes(block_size, byteorder='big'),
            M4.to_bytes(block_size, byteorder='big')
        ]

        for dec_block in possible_blocks:
            padding_end = dec_block.find(b'\x00', 2)
            if padding_end != -1:
                data_with_hash = dec_block[padding_end + 1:]
                message_part = data_with_hash[:-32] 
                hash_digest = data_with_hash[-32:]

                if hashlib.sha256(message_part).digest()[:32] == hash_digest:
                    dec_blocks.append(message_part)
                    break

    return b''.join(dec_blocks).decode('utf-8')


def generate_padding(length):
    while True:
        padding = secrets.token_bytes(length)
        if all(byte != 0 for byte in padding):
            return b'\x00\x02' + padding + b'\x00'
        
def save_keys(scrt_key, pub_key):
    with open("Rabin/src/rabin_keys/pub_key.json", "w", encoding="utf-8") as json_file:
        json.dump(pub_key, json_file, ensure_ascii=False, indent=4)
    with open("Rabin/src/rabin_keys/scrt_key.json", "w", encoding="utf-8") as json_file:
        json.dump(scrt_key, json_file, ensure_ascii=False, indent=4)


        
def main():
    size = int(input("Enter size of N: "))
    message_en = "If I don’t like a thing, I don’t like it, that’s all; and there is no reason under the sun why I should ape a liking for it just because the majority of my fellow-creatures like it, or make believe they like it. I can’t follow the fashions in the things I like or dislike."
    message_ru = "Если мне что-то не нравится, значит, не нравится, и все тут; так с какой стати, спрашивается, я стану делать вид, будто мне это нравится, только потому, что большинству моих соплеменников это нравится или они воображают, что нравится. Не могу я что-то любить или не любить по велению моды."
    pub_key, scrt_key = generate_keys(size)
    enc_message = encrypt(pub_key, message_ru)
    dec_message = decrypt(scrt_key, enc_message)
    print(enc_message)
    print(dec_message)


    
main()