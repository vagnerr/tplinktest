import sys
import time
import socket
import json
import threading


# https://stackoverflow.com/questions/21017698/converting-int-to-bytes-in-python-3
def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'big')


# Based on: https://github.com/softScheck/tplink-smartplug/blob/master/tplink-smartplug.py
def encrypt(string):
    key = 171
    result = b"\0\0\0\0"
    for i in string:
        a = key ^ i
        key = a
        result += int_to_bytes(a)
    return result


def decrypt(string):
    key = 171
    result = b""
    for i in string:
        a = key ^ i
        key = i
        result += int_to_bytes(a)
    return result


def send_hs_command(address, port, cmd):
    data = b""

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_sock.connect((address, port))
        tcp_sock.send(encrypt(cmd))
        data = tcp_sock.recv(2048)
    except socket.error:
        print("Socket closed.", file=sys.stderr)
    finally:
        tcp_sock.close()
    return data


def store_metrics(current, voltage, power):
    return
    current_time = time.time()

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_sock.connect(("localhost", 2003))
        tcp_sock.send("hs110-tv.voltage {0} {1} \n".format(voltage, current_time).encode())
        tcp_sock.send("hs110-tv.current {0} {1} \n".format(current, current_time).encode())
        tcp_sock.send("hs110-tv.power {0} {1} \n".format(power, current_time).encode())
    except socket.error:
        print("Unable to open socket on graphite-carbon.", file=sys.stderr)
    finally:
        tcp_sock.close()


def run():
    threading.Timer(15.0, run).start()

    data = send_hs_command("172.16.1.75", 9999, b'{"emeter":{"get_realtime":{}}}')

    if not data:
        print("No data returned on power request.", file=sys.stderr)
        store_metrics(0, 0, 0)
        return

    decrypted_data = decrypt(data[4:]).decode()
    json_data = json.loads(decrypted_data)
    emeter = json_data["emeter"]["get_realtime"]

    if not emeter:
        print("No emeter data returned on power request.", file=sys.stderr)
        store_metrics(0, 0, 0)
        return

    store_metrics(emeter["current"], emeter["voltage"], emeter["power"])

    print("Stored values, current: {0}, voltage: {1}, power: {2}".format(
        emeter["current"], emeter["voltage"], emeter["power"]))


run()


