'''
Written By: Ben McCoy, July 2020
Python 3.7.3

server.py

ToDo:
- Fix login sequence from being in an endless loop that prints all the time.
-
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

	# Parse the args into useful variable
	block_dur = args.block_duration

	# Info for the socket
	HEADER = 64
	PORT = 5050
	SERVER = socket.gethostbyname(socket.gethostname())
	ADDR = (SERVER, PORT)
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"

	# Get a dict of credentials with the users as keys and the passwords as values
	creds_dict = get_creds()
	# print(creds_dict)

	# Create socket and bind port to socket
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(ADDR)

	# Start the server listening
	print('sever is starting')
	server.listen()
	print(f"Server is listening on {SERVER}")
	while True:
		conn, addr = server.accept()
		thread = threading.Thread(target=handle_client, args=(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur))
		thread.start()
		print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

def get_creds():
	'''This function opens the credentials.txt file and reads each line into a
	list. The function then iterates through the list and adds each user and
	password to a dict with the key as the user and the value as the password.
	Finally, the dict is returned.'''


	with open('credentials.txt') as f:
		cred_list = f.readlines()
		cred_list = [x.strip() for x in cred_list]

	creds_dict = {}
	for cred in cred_list:
		cred_deets = cred.split(' ')
		creds_dict[cred_deets[0]] = cred_deets[1]

	return creds_dict

def handle_client(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur):
	print(f"[NEW CONNECTION] {addr} connected.")

	logging_in = True
	logged_in = False
	login_counter = 0

	connected = True
	while connected:

		while logging_in == True:
			'''Start logging in sequence'''
			# print('logging in sequence starting')

			msg_length = conn.recv(HEADER).decode(FORMAT)
			if msg_length:
				msg_length = int(msg_length)
				msg = conn.recv(msg_length).decode(FORMAT)
				# print(msg)

				if msg == DISCONNECT_MESSAGE:
					print('disconnecting')
					connected = False

				else:
					cred_check = check_creds(msg, creds_dict)
					if cred_check == True:
						conn.send("You are now logged in".encode(FORMAT))
						logged_in = True
						logging_in = False

					else:
						# print('credentials check failed')
						# print('the login counter is ', login_counter)
						if login_counter % 3 != 2:
							conn.send("Invalid login attempt, try again".encode(FORMAT))
						else:
							conn.send("Your account has been blocked, try again later".encode(FORMAT))
							time.sleep(block_dur)
					login_counter += 1

		if logged_in == True:
			# print('logged in sequence starting')

			msg_length = conn.recv(HEADER).decode(FORMAT)
			if msg_length:
				msg_length = int(msg_length)
				msg = conn.recv(msg_length).decode(FORMAT)
				# print(msg)

				if msg == 'wait':
					print('waiting for 30s')
					time.sleep(30)
					print('wait is over')

				if msg == DISCONNECT_MESSAGE:
					print('disconnecting')
					connected = False

	print(f"[EXISTING CONNECTION] {addr} disconnected.")

# def handle_client(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur):
# 	print(f"[NEW CONNECTION] {addr} connected.")
#
# 	connected = True
# 	while connected:
# 		msg_length = conn.recv(HEADER).decode(FORMAT)
# 		if msg_length:
# 			msg_length = int(msg_length)
# 			msg = conn.recv(msg_length).decode(FORMAT)
# 			print(msg)
#
# 			if msg[:5] == 'login':
# 				'''Start login sequence'''
#
# 				logged_in = False
# 				login_counter = 0
#
# 				while logged_in == False:
#
# 					cred_check = check_creds(msg, creds_dict)
# 					if cred_check == True:
# 						conn.send("You are now logged in".encode(FORMAT))
# 						logged_in = True
#
# 					else:
# 						if login_counter % 3 != 2:
# 							conn.send("Invalid login attempt, try again".encode(FORMAT))
# 						else:
# 							conn.send("your account has been blocked, try again later".encode(FORMAT))
# 							time.sleep(block_dur)
# 					print(login_counter)
# 					login_counter += 1
#
# 			if msg == DISCONNECT_MESSAGE:
# 				connected = False
# 			print(f"[{addr}] {msg}")
#
# 			conn.send("ACKNOWLEDGED".encode(FORMAT))
#
# 	conn.close()

def check_creds(msg, creds_dict):

	user = msg.split(' ')[1]
	password = msg.split(' ')[2]

	if user in creds_dict and password == creds_dict[user]:
		return True

	return False

if __name__ == "__main__":
	main()
