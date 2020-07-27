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
from random import randint

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

	# Init class to control the block list
	block_list_class = RollCall()

	# Create socket and bind port to socket
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(ADDR)

	# Start the server listening
	print('sever is starting')
	server.listen()
	print(f"Server is listening on {SERVER}")

	# Whilst the server is listening, send any new connections to their own thread
	while True:
		conn, addr = server.accept()
		thread = threading.Thread(target=handle_client, args=(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur, block_list_class))
		thread.start()
		print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


def handle_client(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur, block_list_class):
	'''This function is for handling each client individually'''

	print(f"[NEW CONNECTION] {addr} connected.")

	# Booleans and counters for managing connection state
	logging_in = True
	logged_in = False
	login_counter = 0

	connected = True
	while connected:

		while logging_in == True:
			'''Start logging in sequence'''
			# print('logging in sequence starting')

			# Receive and decode message
			msg_length = conn.recv(HEADER).decode(FORMAT)
			if msg_length:
				msg_length = int(msg_length)
				msg = conn.recv(msg_length).decode(FORMAT)
				# print(msg)

				# Disconnect msg sent by client after 3 failed login attempts
				if msg == DISCONNECT_MESSAGE:
					print('disconnecting')
					connected = False

				# Ig msg is not disconnect message
				else:
					# Perform creds check
					cred_check, user = check_creds(msg, creds_dict)

					if user in block_list_class.block_list:
						conn.send("Your account has been blocked, try again later".encode(FORMAT))
						connected = False

					# If creds are legit, change connection state to logged_in
					elif cred_check == True:
						conn.send("You are now logged in".encode(FORMAT))
						logged_in = True
						logging_in = False

					# If creds are not legit,
					else:
						# print('credentials check failed')
						# print('the login counter is ', login_counter)

						# If less than 3 attempts taken send try again msg
						if login_counter % 3 != 2:
							conn.send("Invalid login attempt, try again".encode(FORMAT))

						# If 3 attempts have been taken, send acct block msg and sleep
						else:
							conn.send("Your account has been blocked, try again later".encode(FORMAT))
							block_list_class.add_to_block_list(user)
							time.sleep(block_dur)
							block_list_class.del_from_block_list(user)
							connected = False

					login_counter += 1

		if logged_in == True:
			# print('logged in sequence starting')

			# Receive and decode message
			msg_length = conn.recv(HEADER).decode(FORMAT)
			if msg_length:
				msg_length = int(msg_length)
				msg = conn.recv(msg_length).decode(FORMAT)
				# print(msg)

				if msg == 'DL_TempID':
					print('starting tempID sequence for', user)
					tempID = gen_tempID(user)
					conn.send(str(tempID).encode(FORMAT))
					print('tempID sequence is finished for', user)
					print(tempID)

				if msg == 'wait':
					print('waiting for 30s')
					time.sleep(30)
					print('wait is over')

				if msg == DISCONNECT_MESSAGE:
					print('disconnecting')
					connected = False

	print(f"[EXISTING CONNECTION] {addr} disconnected.")

def gen_tempID(user):

	with open('tempIDs.txt') as f:
		tempID_list = f.readlines()

	all_tempIDs = []
	for i in tempID_list:
		all_tempIDs.append(i.split(' ')[1])

	duplicate = True

	while duplicate == True:
		tempID = randint(10000000000000000000, 99999999999999999999)
		if tempID not in all_tempIDs:
			duplicate = False

	start = datetime.datetime.now()
	expire = start + datetime.timedelta(minutes = 15)
	dt_start = start.strftime("%d/%m/%Y %H:%M:%S")
	dt_expire = expire.strftime("%d/%m/%Y %H:%M:%S")

	new_line = str(user) + ' ' + str(tempID) + ' ' + dt_start + ' ' + dt_expire + '\n'
	with open('tempIDs.txt', "a") as f:
		f.write(new_line)

	return tempID

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

def check_creds(msg, creds_dict):

	user = msg.split(' ')[1]
	password = msg.split(' ')[2]

	if user in creds_dict and password == creds_dict[user]:
		return True, user

	return False, user

class RollCall:
	def __init__(self):
		self.block_list = []

	def add_to_block_list(self, user):
		self.block_list.append(user)

	def del_from_block_list(self, user):
		if user in self.block_list:
			self.block_list.remove(user)

if __name__ == "__main__":
	main()

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
