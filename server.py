'''
Written By: Ben McCoy z3464555, July 2020
Python 3.7.3
server.py

Example command line usage:
$ python .\server.py [server_port] [block_duration]
$ python .\server.py 5050 10

This script was written for the Term 2, 2020 COMP9331 Assignment.

This script is server.py and acts as the server for a simulated BlueTrace app,
the server provides tempIDs and stores contact logs that are uploaded by clients
of the server who have logged in and been authenticated. The server script can
handle multiple simultaneous clients on multiple threads and uses TCP connections
to communicate with clients. When a client uses the command "logout" the client
and server connection is closed.

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

	# Parse the args into useful variables
	block_dur = args.block_duration
	srvr_port = args.server_port

	# Get the IP address of current machine
	SERVER = socket.gethostbyname(socket.gethostname())

	# Info for the socket
	HEADER = 64
	PORT = srvr_port
	ADDR = (SERVER, PORT)
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"

	# Get a dict of credentials with the users as keys and the passwords as values
	creds_dict = get_creds()

	# Init class to control the block list
	block_list_class = RollCall()

	# Create socket and bind port to socket
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(ADDR)

	# Start the server listening
	server.listen()
	print(f"Server is listening on {SERVER}")

	# Whilst the server is listening, send any new connections to their own thread
	while True:
		conn, addr = server.accept()
		thread = threading.Thread(target=handle_client, args=(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur, block_list_class))
		thread.start()
		print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


def handle_client(conn, addr, HEADER, FORMAT, DISCONNECT_MESSAGE, creds_dict, block_dur, block_list_class):
	'''This function is for handling each client individually.
	Initially the client must go through the login sequence and once successfully
	logged in they can go through the post login sequence.'''

	print(f"[NEW CONNECTION] {addr} connected.")

	# Booleans and counters for managing new connection state
	logging_in = True
	logged_in = False
	login_counter = 0
	connected = True

	# Start infinite listening loop
	while connected:

		while logging_in == True:
			'''Start logging in sequence'''

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
					logged_in = True

				# If msg is not disconnect message
				else:
					# Perform creds check and get username
					cred_check, user = check_creds(msg, creds_dict)

					# If the user is currently blocked send blocked message and
					# disconenct
					if user in block_list_class.block_list:
						conn.send("Your account has been blocked, try again later".encode(FORMAT))
						connected = False
						break

					# If creds are legit, change connection state to logged_in
					elif cred_check == True:
						conn.send("Welcome to the BlueTrace Simulator!".encode(FORMAT))
						logged_in = True
						logging_in = False

					# If creds are not legit,
					else:
						# If less than 3 login attempts taken send try again msg
						if login_counter % 3 != 2:
							conn.send("Invalid login attempt, try again".encode(FORMAT))

						# If 3 attempts have been taken, send acct block msg,
						# Update the block list and then wait for the block
						# duration before unblocking
						else:
							conn.send("Your account has been blocked, try again later".encode(FORMAT))
							connected = False

							block_thread = threading.Thread(target=block_thread_func, args=[user, block_dur, block_list_class])
							block_thread.daemon = True
							block_thread.start()

							break

					login_counter += 1

		if logged_in == True:
			'''Start Post Login Sequence'''

			# Receive and decode message
			msg_length = conn.recv(HEADER).decode(FORMAT)
			if msg_length:
				msg_length = int(msg_length)
				msg = conn.recv(msg_length).decode(FORMAT)
				# print(msg)

				# If msg is DL_tempID, print username on server output, generate
				# a unique tempID with start and expiry times, place the info in
				# a string and send it to the client and print tempID on server
				# output
				if msg == 'DL_TempID':
					print('User:', user)
					tempID, dt_start, dt_expire = gen_tempID(user)
					tempID_str = str(tempID) + ' ' + dt_start + ' ' + dt_expire
					conn.send(tempID_str.encode(FORMAT))
					print('TempID:', tempID)

				# If msg is disonnect msg, then break the conneciton
				if msg == DISCONNECT_MESSAGE:
					connected = False
					break

				# If client uses Upload_contact_log command
				if msg == 'upload':
					# Send ready for upload message and init the log_list
					conn.send('upload_ready'.encode(FORMAT))
					log_list = []

					# Loop until fin_upload message is sent from client
					return_msg = None
					while return_msg != 'fin_upload':

						# Receive and decode message
						msg_length = conn.recv(HEADER).decode(FORMAT)
						if msg_length:
							msg_length = int(msg_length)
							return_msg = conn.recv(msg_length).decode(FORMAT)

						# Add contact to log_list
						log_list.append(return_msg)

					# process the log list
					log_list.pop()
					print('Received contact log from:', user)
					for i in log_list:
						print(i + ';')

					print('Contact log checking:')

					# Open tempIDs.txt and readlines into a list
					with open('tempIDs.txt') as f:
						tempID_list = f.readlines()

					# for each contact uploaded from client find the tempID
					for i in log_list:
						ID = (i.split(' ')[0])

						# for each user in tempIDs.txt find the tempID
						for j in tempID_list:
							j_ID = j.split(' ')[1]

							# If the client log and txt tempIDs line up, print info
							if ID == j_ID:
								j_user = j.split(' ')[0]
								COVID_time = str(i.split(' ')[1]) + ' ' + str(i.split(' ')[2])
								print(j_user, COVID_time, ID + ';')
								# print(COVID_time)
								# print(ID + ';')

	# Print disconnected message
	print(f"[EXISTING CONNECTION] {user, addr} disconnected.")

def block_thread_func(user, block_dur, block_list_class):
	'''This function adds a user to the block list stored in the RollCall class,
	then waits for a period of the block duration before removing the user from
	the block list'''
	
	block_list_class.add_to_block_list(user)
	time.sleep(block_dur)
	block_list_class.del_from_block_list(user)


def gen_tempID(user):
	'''This function takes a user name, opens the tempIDs.txt file gets a list of
	existing tempIDs, generates a new tempID randomly, checks the tempID has not
	already been allocated, generates a new tempID if it is a duplicate and then
	saves the user, tempID, time generated and expiry time, before returning the
	tempID'''

	# Open tempIDs.txt and readlines into a list
	with open('tempIDs.txt') as f:
		tempID_list = f.readlines()

	# Get a list of existing tempIDs already in the file
	all_tempIDs = []
	for i in tempID_list:
		all_tempIDs.append(i.split(' ')[1])

	# Generate a non-dupliacte tempID randomly
	duplicate = True
	while duplicate == True:
		tempID = randint(10000000000000000000, 99999999999999999999)
		if tempID not in all_tempIDs:
			duplicate = False

	# Get the start and expiry time of the tempID
	start = datetime.datetime.now()
	expire = start + datetime.timedelta(minutes = 15)
	dt_start = start.strftime("%d/%m/%Y %H:%M:%S")
	dt_expire = expire.strftime("%d/%m/%Y %H:%M:%S")

	# Save the new tempID and details into tempIDs.txt
	new_line = str(user) + ' ' + str(tempID) + ' ' + dt_start + ' ' + dt_expire + '\n'
	with open('tempIDs.txt', "a") as f:
		f.write(new_line)

	return tempID, dt_start, dt_expire

def get_creds():
	'''This function opens the credentials.txt file and reads each line into a
	list. The function then iterates through the list and adds each user and
	password to a dict with the key as the user and the value as the password.
	Finally, the dict is returned.'''

	# Open credentials.txt add each line to list and strip any whitespace
	with open('credentials.txt') as f:
		cred_list = f.readlines()
		cred_list = [x.strip() for x in cred_list]

	# Create a dict with keys as usernames and values as passwords using list
	creds_dict = {}
	for cred in cred_list:
		cred_deets = cred.split(' ')
		creds_dict[cred_deets[0]] = cred_deets[1]

	return creds_dict

def check_creds(msg, creds_dict):
	'''This function takes a msg received by the server and the credentials dict
	It then splits the message into user and passwrod and checks that the user
	is in the creds_dict and that the password is the same as in the creds_dict
	Returns True if user in dict and passwords match, else returns False'''

	# split the message into user and password
	user = msg.split(' ')[1]
	password = msg.split(' ')[2]

	# Perform check on user and password
	if user in creds_dict and password == creds_dict[user]:
		return True, user

	return False, user

class RollCall:
	'''This class is to control the block list and ensure that users blocked
	from one IP address cannot login via a second IP adress'''

	# Init an empty list
	def __init__(self):
		self.block_list = []

	# Function to add user to block list
	def add_to_block_list(self, user):
		self.block_list.append(user)

	# Function to delete user from block list
	def del_from_block_list(self, user):
		if user in self.block_list:
			self.block_list.remove(user)

if __name__ == "__main__":
	main()
