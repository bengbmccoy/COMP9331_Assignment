'''
Written By: Ben McCoy, July 2020
Python 3.7.3

client.py

Example command line usage:
$ python .\client.py 192.168.1.9 5050 6969
'''

import argparse
import socket
import threading
import sys
import datetime
import time

def main():

	#Parse the arguments from command line
	parser = argparse.ArgumentParser()
	parser.add_argument('server_IP', type=str,
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
	PORT = srvr_port
	FORMAT = 'utf-8'
	DISCONNECT_MESSAGE = "!DISCONNECT"
	SERVER = srvr_IP
	# SERVER = socket.gethostbyname(socket.gethostname())
	ADDR = (SERVER, PORT)

	# Start beacon listening thread
	beacon_thread = threading.Thread(target=beacon_listen, args=[client_udp_port])
	beacon_thread.daemon = True
	beacon_thread.start()


	# Start connection
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(ADDR)

	# initial state variables
	logged_in = False
	user = None
	tempID = None
	BTver = 1

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
		if return_msg == "Welcome to the BlueTrace Simulator!":
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
			tempID = return_msg.split(' ')[0]
			dt_start = return_msg.split(' ')[1] + ' ' + return_msg.split(' ')[2]
			dt_expire = return_msg.split(' ')[3] + ' ' + return_msg.split(' ')[4]
			print('TempID:', tempID)

		# upload contact log sequence
		elif action == 'Upload_contact_log':
			# Get list of contacts
			with open('z3464555_contactlog.txt') as f:
				contactlog_list = f.readlines()

			# send action is uplaod msg and get return msg
			send('upload', FORMAT, HEADER, client)
			return_msg = (client.recv(2048).decode(FORMAT))

			# If server is ready for upload
			if return_msg == 'upload_ready':

				# For each contact in the contact log list, send the log_str
				for i in contactlog_list:
					log_str = str((i.strip()))
					send(log_str, FORMAT, HEADER, client)
					print(log_str + ';')

			# Send upload complete message
			send('fin_upload', FORMAT, HEADER, client)

		# Beacon protocol
		elif action[:6] == 'Beacon':

			# Check that the client currently has a tempID, else exit this protocol
			if tempID == None:
				print('First download a tempID')
				continue

			# Check that an IP and poort were given, else exit this protocol
			try:
				dest_IP = action.split(' ')[1]
				dest_port = int(action.split(' ')[2])
			except:
				print('Please provide dest_IP and dest_port with command')
				continue

			# create socket object, send tempID, dt_start and dt_expire
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			beacon_str = tempID + dt_start + dt_expire + str(BTver)
			sock.sendto(beacon_str.encode(), (dest_IP, dest_port))
			print(tempID, dt_start, dt_expire + ';')
			# print(dt_start)
			# print(dt_expire)

		# Logout and disconnect sequence
		elif action == 'logout':
			send(DISCONNECT_MESSAGE, FORMAT, HEADER, client)
			sys.exit()

		# If prompt not recognized, print error
		else:
			print('Error. Invalid command')

def beacon_listen(udp_port):
	'''This function handles the beacon listening thread'''

	# Setup listening socket on udp_port
	beacon_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	address = (socket.gethostbyname(socket.gethostname()), udp_port)
	beacon_sock.bind(address)

	# Create an infinite listening loop
	while True:

		# Look for data from the beacon_socket
		data, addr = beacon_sock.recvfrom(59)

		# If data is received, decode and print contents and more
		if data:

			# decode the message into various parts
			recv_tempID = data[:20].decode()
			recv_str_start = data[20:39].decode()
			recv_str_expire = data[39:58].decode()

			# print contents
			print('Recieved beacon:')
			print(recv_tempID, recv_str_start, recv_str_expire + ';')
			# print(recv_str_start)
			# print(recv_str_expire)

			# get the current datetime as datetime obj and string, print string
			dt_cur_time = datetime.datetime.now()
			str_cur_time = dt_cur_time.strftime("%d/%m/%Y %H:%M:%S")
			print('The current time is:', str_cur_time)

			# convert received datetime strings to datetime objects
			recv_dt_start = datetime.datetime.strptime(recv_str_start, '%d/%m/%Y %H:%M:%S')
			recv_dt_expire = datetime.datetime.strptime(recv_str_expire, '%d/%m/%Y %H:%M:%S')

			# Check that the tempID is valid,
			if dt_cur_time >= recv_dt_start and dt_cur_time <= recv_dt_expire:
				print('The beacon is valid')

				# start a thread to add this tempID to the conctatlog for 3 mins
				save_str = recv_tempID + ' ' + recv_str_start + ' ' + recv_str_expire + '\n'
				save_thread = threading.Thread(target=save_3_mins, args=[save_str])
				save_thread.daemon = True
				save_thread.start()

			# Beacon is invalid
			else:
				print('The beacon is invalid')

def save_3_mins(save_str):
	'''This function handles writing and removing items from the contact log'''

	# Add the save_str as a new line
	with open("z3464555_contactlog.txt", "a") as f:
		f.write(save_str)

	# Wait for 3 minutes
	time.sleep(180)

	# Get the contents of the file as list and delete save_str
	with open("z3464555_contactlog.txt", "r+") as f:
		old = f.readlines()
	old.remove(save_str)

	# Overwrite the file with the list with save_str deleted
	with open("z3464555_contactlog.txt", "w") as f:
		for item in old:
			f.write("%s" % item)


def get_login_details(user):
	'''Prompts the user for their username and login details and returns both.
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
