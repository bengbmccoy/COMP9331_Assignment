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

	HEADER = 64
	PORT = 5050
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"
	SERVER = socket.gethostbyname(socket.gethostname())
	ADDR = (SERVER, PORT)



	# Start connection
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(ADDR)

	'''Start login sequence'''
	logged_in = False
	while logged_in == False:
		# Get login details
		user, password = get_login_details()
		# print(user, password)

		login_message = 'login' + ' ' + user + ' ' + password
		send(login_message, FORMAT, HEADER, client)

		return_msg = (client.recv(2048).decode(FORMAT))
		print(return_msg)

		if return_msg == "You are now logged in":
			logged_in = True
		elif return_msg == "Your account has been blocked, try again later":
			'''Disconnect sequence'''
			print('Disconnecting')
			send(DISCONNECT_MESSAGE, FORMAT, HEADER, client)
			exit()

	while logged_in == True:
		print('What is your next action?')
		action = input()

		if action == 'Download_tempID':
			pass

		if action == 'wait':
			'''Ask the server to wait'''
			wait_msg = 'wait'
			send(wait_msg, FORMAT, HEADER, client)

		if action == 'logout':
			'''Disconnect sequence'''
			print('Disconnecting')
			send(DISCONNECT_MESSAGE, FORMAT, HEADER, client)
			exit()

def get_login_details():
	'''Prrompts the user for their username and login details and returns both.'''

	user = input("Enter your username : ")
	password = input("Enter your password : ")

	return user, password

def send(msg, FORMAT, HEADER, client):
	message = msg.encode(FORMAT)
	msg_length = len(message)
	send_length = str(msg_length).encode(FORMAT)
	send_length += b' ' * (HEADER - len(send_length))
	client.send(send_length)
	client.send(message)


if __name__ == "__main__":
	main()
