'''
Written By: Ben McCoy, July 2020
Python 3.7.3

server.py
'''
import argparse
import socket
import threading
import datetime
import time

def main():

	#Parse the arguments from command line
	parser = argparse.ArgumentParser()
	parser.add_argument('server_port', type=int,
						help='server port number to communicate with clients')
	parser.add_argument('block_duration', type=int,
						help='The length of time a user is blocked after failing authentication')
	args = parser.parse_args()

	HEADER = 64
	PORT = 5050
	SERVER = socket.gethostbyname(socket.gethostname())
	ADDR = (SERVER, PORT)
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"
	print(ADDR)

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(ADDR)

	print('sever is starting')
	server.listen()
	print(f"Server is listening on {SERVER}")
	while True:
		conn, addr = server.accept()
		thread = threading.Thread(target=handle_client, args=(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE))
		thread.start()
		print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

def handle_client(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE):
	print(f"[NEW CONNECTION] {addr} connected.")

	connected = True
	while connected:
		msg_length = conn.recv(HEADER).decode(FORMAT)
		if msg_length:
			msg_length = int(msg_length)
			msg = conn.recv(msg_length).decode(FORMAT)
			if msg == DISCONNECT_MESSAGE:
				connected = False
			print(f"[{addr}] {msg}")

			conn.send("ACKNOWLEDGED".encode(FORMAT))

	conn.close()

if __name__ == "__main__":
	main()
