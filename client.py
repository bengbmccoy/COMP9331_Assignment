'''
Written By: Ben McCoy, July 2020
Python 3.7.3

client.py
'''

import argparse
import socket


def main():

	#Parse the arguments from command line
	parser = argparse.ArgumentParser()
	parser.add_argument('server_IP', type=int,
						help='server IP address to communicate with server')
	parser.add_argument('server_port', type=int,
						help='server port number to communicate with server')
	parser.add_argument('client_udp_port', type=int,
						help='Port number for client to listen for traffic')
	args = parser.parse_args()

	# Parse the args into useful variables
	srvr_IP = args.server_IP
	srvr_port = args.server_port
	client_udp_port = args.client_udp_port

	# Info for the socket
	HEADER = 64
	PORT = 5050
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"
	SERVER = socket.gethostbyname(socket.gethostname())
	ADDR = (SERVER, PORT)


	# Start connection
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(ADDR)

	# initial state variables
	logged_in = False
	user = None

	'''Start login sequence'''
	while logged_in == False:

		# Get user and password if user = None, or just password if user not None
		user, password = get_login_details(user)

		# send login message to server
		login_message = 'login' + ' ' + user + ' ' + password
		send(login_message, FORMAT, HEADER, client)

		# receive return message from sender
		return_msg = (client.recv(2048).decode(FORMAT))
		print(return_msg)

		# if successful login, set state to logged_in = True
		if return_msg == "You are now logged in":
			logged_in = True

		# if return message is block message, disconnect and exit script
		elif return_msg == "Your account has been blocked, try again later":
			'''Disconnect sequence'''
			print('Disconnecting')
			send(DISCONNECT_MESSAGE, FORMAT, HEADER, client)
			exit()

	'''Start post-login sequence'''
	while logged_in == True:

		# Ask user for prompt
		print('What is your next action?')
		action = input()

		# Send the download_tempID message and receive tempID
		if action == 'Download_tempID':
			temp_ID_msg = 'DL_TempID'
			send(temp_ID_msg, FORMAT, HEADER, client)
			return_msg = (client.recv(2048).decode(FORMAT))
			tempID = return_msg
			print('TempID:', tempID)

		# For Debugging
		elif action == 'wait':
			wait_msg = 'wait'
			send(wait_msg, FORMAT, HEADER, client)

		# Logout and disconnect sequence
		elif action == 'logout':
			send(DISCONNECT_MESSAGE, FORMAT, HEADER, client)
			exit()

		# If prompt not recognized, print error
		else:
			print('Error. Invalid command')

def get_login_details(user):
	'''Prrompts the user for their username and login details and returns both.
	If user is None, just ask for password'''

	# If user is None, ask user for user and pass, else, just ask for pass
	if user == None:
		user = input("Enter your username : ")
	password = input("Enter your password : ")

	return user, password

def send(msg, FORMAT, HEADER, client):
	'''The send message function'''

	message = msg.encode(FORMAT)
	msg_length = len(message)
	send_length = str(msg_length).encode(FORMAT)
	send_length += b' ' * (HEADER - len(send_length))
	client.send(send_length)
	client.send(message)


if __name__ == "__main__":
	main()
