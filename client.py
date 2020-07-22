'''
Written By: Ben McCoy, July 2020
Python 3.7.3

client.py
'''

import socket


def main():




	HEADER = 64
	PORT = 5050
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"
	SERVER = socket.gethostbyname(socket.gethostname())
	ADDR = (SERVER, PORT)

	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(ADDR)

	send("Suh World", FORMAT, HEADER, client)
	send("Suh BEN", FORMAT, HEADER, client)
	send(DISCONNECT_MESSAGE, FORMAT, HEADER, client)

def send(msg, FORMAT, HEADER, client):
	message = msg.encode(FORMAT)
	msg_length = len(message)
	send_length = str(msg_length).encode(FORMAT)
	send_length += b' ' * (HEADER - len(send_length))
	client.send(send_length)
	client.send(message)
	print(client.recv(2048))

if __name__ == "__main__":
	main()
