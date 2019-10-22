from socket import socket
from tkinter import *
from threading import Thread
from sys import exit


def console_print():
    global messages_count
    if len(messages) > messages_count:
        console.configure(state='normal')  # enable insert
        console.insert(END, messages[messages_count] + '\n')
        console.yview(END)  #  autoscroll
        console.configure(state='disabled')  # disable editing
        messages_count += 1

    root.after(1, console_print)


def quit_client(send=True):
    if send:
        try:
            sock.send(('quit' + delimiter).encode())
            sock.close()
        except ConnectionResetError:
            quit_client(send=False)
    root_chat.destroy()
    exit()


def send_data(data_to_send='', delimit=None):
    if not delimit:
        delimit = delimiter
    data_to_send = send_area.get()
    send_area.delete(0, END)
    try:
        sock.send((data_to_send + delimit).encode())
    except ConnectionAbortedError:
        messages.append('Connection is lost. Cant send data')
    except ConnectionResetError:
        messages.append('Server was killed by God(sys_admin)')
    else:
        if data_to_send == 'quit':
            quit_client(send=False)
        else:
            messages.append(data_to_send)


def receiver(delimit=None):
    if not delimit:
        delimit = delimiter
    received_data = ''
    try:
        while not received_data.endswith(delimit):
            received_data += sock.recv(1024).decode()
        else:
            received_data = received_data[:-(len(delimit))]
    except ConnectionAbortedError:
        pass
    except OSError:
        pass
    else:
        messages.append(received_data)
        Thread(target=receiver).start()
    

def main(event=None, host='localhost', port=32280):  # event прилетит в случае, если мы запустим main через <Return>
    global console, send_area, root_chat
    host_from_butt = host_butt.get()
    port_from_butt = port_butt.get()
    if host_from_butt: host = host_from_butt
    if port_from_butt: port = port_from_butt
    root.destroy()

    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        input('Подключение не установлено, т.к. конечный компьютер отверг запрос на подключение')
    else:
        root_chat = Tk()
        root_chat_width = SCREEN_WIDTH // 2
        root_chat_height = SCREEN_HEIGHT // 4 * 3
        root_chat_width_pos = SCREEN_WIDTH // 4
        root_chat_height_pos = SCREEN_HEIGHT // 6
        root_chat.title("Vord's Chat Client")
        root_chat.geometry(f'{root_chat_width}x{root_chat_height}+{root_chat_width_pos}+{root_chat_height_pos}')
        console = Text(root_chat, state='disabled', font=FONT)
        console.pack(fill="both", expand=True)

        entry_frame = Frame(root_chat)
        send_area = Entry(entry_frame, width=50, font=FONT)
        send_area.pack(side=LEFT, padx=15)
        send_area.focus_set()
        send_data_butt = Button(entry_frame, text='send', fg='green', font=FONT, command=send_data)
        send_data_butt.pack(side=LEFT, padx=5)
        quit_butt = Button(entry_frame, text='quit', fg='red', font=FONT, command=quit_client)
        quit_butt.pack(side=LEFT, padx=5)
        send_area.bind('<Return>', send_data)
        entry_frame.pack(pady=10)

        Thread(target=receiver).start()
        console_print()


sock = socket()

root = Tk()

SCREEN_WIDTH = root.winfo_screenwidth()
SCREEN_HEIGHT = root.winfo_screenheight()

root_width = SCREEN_WIDTH // 7
root_height = SCREEN_HEIGHT // 6
root_width_pos = SCREEN_WIDTH // 3
root_height_pos = SCREEN_HEIGHT // 3
root.geometry(f'{root_width}x{root_height}+{root_width_pos}+{root_height_pos}')
root.title('Client')

FONT = 'Helvetica 14'
Label(root, text='Enter host ip', font=FONT).pack()
host_butt = Entry(root)
host_butt.pack()
Label(root, text='Enter host port', font=FONT).pack()
port_butt = Entry(root)
port_butt.pack()
Button(root, text='Continue', font=FONT, fg='green', command=main).pack(padx=5, pady=10)
root.bind('<Return>', main)
root.focus_set()

console = ''
send_area = ''
root_chat = ''
messages = []
messages_count = len(messages)
delimiter = ';;'


root.mainloop()
