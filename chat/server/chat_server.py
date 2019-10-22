import socket, pickle
from threading import Thread
from time import sleep
from sys import exit
from os.path import isfile
from copy import copy


class Client(object):
    def __init__(self, addr, name='', conn=''):
        self.conn, self.addr, self.name = conn, addr, name

    def send(self, msg):
        self.conn.send(msg.encode())

    def send_all(self, msg, lst_group):
        for person in lst_group:
            if person.name != self.name:
                person.send(msg)


class Server(object):
    def kill(self):
        self.is_alive = False
        self.killed = True


    def change_state(self):
        self.is_alive = not self.is_alive


    def show_log(self):
        cl_count = len(self.log_clients_list)
        if not cl_count:
            print('The log file is empty')
            return

        print('The number of clients:', cl_count)
        for client in self.log_clients_list:
            print('Clients name:', client.name, '|||', 'Clients IP:', client.addr)


    def make_log_list(self, clear=False):
        if isfile(self.log_clients_list_filename) and not clear:
            with open(self.log_clients_list_filename, 'rb') as log_file:
                self.log_clients_list = pickle.load(log_file)
        else:
            with open(self.log_clients_list_filename, 'wb') as log_file:
                self.log_clients_list = []
                pickle.dump(self.log_clients_list, log_file)


    def clear_log(self):
        self.make_log_list(clear=True)
        print('Log file cleared')


    def __init__(self, log_filename='clients_list'):
        self.sock = socket.socket()

        self.is_alive, self.killed = True, False
        self.delimiter = ';;'

        self.log_clients_list_filename = log_filename
        self.make_log_list()
        self.curr_clients_list = []


    def receive_message(self, conn, delimit=None):
        if delimit is None:
            delimit = self.delimiter

        mess = ''
        while not mess.endswith(delimit):
            try:
                mess += conn.recv(1024).decode()
            except ConnectionResetError:
                print('Anonymous does not sent the name. Authorization fault.')
                break
        else:
            mess = mess[:-(len(delimit))]
        return mess


    def client_authorization(self, conn, addr):
        def make_order_to_reg(msg='Enter your name: '):
            msg += self.delimiter
            new_client = Client(addr)
            conn.send(msg.encode())

            name = self.receive_message(conn)
            if name == 'quit' or name == '':
                return
            for client in self.log_clients_list:
                if name == client.name:
                    return make_order_to_reg('This name is already reserved. Try another: ')

            new_client.name = name
            conn.send((f'Hello, {new_client.name}! You may enter your messages ("quit" to exit):' + self.delimiter).encode())
            return new_client

        for client in self.log_clients_list:
            if client.addr == addr:
                conn.send((f'Hello, {client.name}! You may enter your messages ("quit" to exit):' + self.delimiter).encode())
                print(f"{client.name} logged in net")
                return client
        else:  # он тут не обязателен, мне так читать проще
            new_client = make_order_to_reg()
            if new_client is not None:
                print(f"{new_client.name} logged in net")
                self.log_clients_list.append(copy(new_client))
                with open(self.log_clients_list_filename, 'rb+') as log_file:
                    # понимаю, что это оооочень не оптимальный подход, но пока лень переделывать
                    pickle.dump(self.log_clients_list, log_file)
                return new_client


    def main(self):
        def start_client(conn, addr, curr_client=None):
            if curr_client is None:
                #  conn я специально добавляю потом, потому сокет нельзя сериализовать
                curr_client = self.client_authorization(conn, addr)
                if curr_client:
                    curr_client.conn = conn
                    self.curr_clients_list.append(curr_client)
                    curr_client.send_all(f"{curr_client.name} logged in net" + self.delimiter, self.curr_clients_list)
                else:  # if client.name == 'quit'
                    return

            while self.is_alive:
                try:
                    msg = self.receive_message(curr_client.conn)
                except ConnectionResetError:
                    print(f'{curr_client.name} disconnected while server was stopped')
                    msg = 'quit_already'

                if msg == 'quit' or msg == 'quit_already':
                    if msg == 'quit':
                        curr_client.conn.close()

                    print("{} logged out of net".format(curr_client.name))
                    curr_client.send_all(f"{curr_client.name} logged out of net" + self.delimiter, self.curr_clients_list)
                    self.curr_clients_list.remove(curr_client)
                    break
                else:
                    msg = f'< {curr_client.name} > {msg}'
                    curr_client.send_all(msg + self.delimiter, self.curr_clients_list)
            else:
                if not self.killed:
                    while not self.is_alive:
                        sleep(1)

                    start_client(conn, addr, curr_client=curr_client)

        def awaiting_connection(resume=False):
            if not resume:
                self.sock.listen()

            while self.is_alive:
                conn, addr = self.sock.accept()
                addr = addr[0]
                Thread(target=start_client, args=(conn, addr)).start()
            else:
                if not self.killed:
                    while not self.is_alive:
                        sleep(1)
                    awaiting_connection(resume=True)

        self.sock.bind((self.host, self.port))  # server host, port
        awaiting_connection()


    def start(self, host, port):
        self.host, self.port = host, port
        print(f'Server based on {host}:{port}')

        main_thread = Thread(target=self.main, daemon=True)
        main_thread.start()


_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_.connect(("8.8.8.8", 80))
host = _.getsockname()[0]
_.close()
port = 32280
server = Server()
server.start(host, port)


func_dict = { 'kill' : server.kill, 'stop' : server.change_state, 'resume' : server.change_state,
              'show log' : server.show_log, 'clear log' : server.clear_log }


while True:
    command = input("Available commands: 'kill', 'stop', 'resume', 'show log', 'clear log'\n").lower()
    if command in func_dict.keys():
        func_dict[command]()
        if command == 'kill':
            exit()
    else:
        print('Incorrect command name!')
