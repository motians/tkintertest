import tkinter as tk
import os
import threading
import uuid
import select, socket, queue

global SEND_message, message_queues, outputs
SEND_message = None
message_queues = {}
outputs = []

class Window(tk.Frame):


    def __init__(self, master = None):

        tk.Frame.__init__(self, master)

        self.master = master
        self.master.title("Server")

        self.pack(fill=tk.BOTH, expand=True)

        quit_button = tk.Button(self, text="Quit", command=self.client_exit)
        quit_button.pack(side=tk.LEFT, padx=5)

        open_cmd_button = tk.Button(self, text="Send", command=self.cmd_win)
        open_cmd_button.pack(side=tk.LEFT, padx=5)

        start_server_button = tk.Button(self, text="Start", command=self.start_server)
        start_server_button.pack(side=tk.LEFT, padx=5)

        self.text_box = tk.Text(self.master)
        self.text_box.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


    def start_server(self):

        t = threading.Thread(target=self.server_content)
        t.start()


    def add_to_window(self, text):

        def append():
            self.text_box.configure(state='normal')
            self.text_box.insert(tk.END, text)
            self.text_box.configure(state='disabled')
            self.text_box.yview(tk.END)
        self.text_box.after(0, append)

    def cmd_win(self):

        global e1
        global e2
        global e3

        def close_win():
            self.command_window.destroy()

        self.command_window = tk.Toplevel(self.master)
        self.command_window.title("Message Window")

        submit_button = tk.Button(self.command_window, text="Submit", command=self.send_msg)
        submit_button.pack(side=tk.TOP)

        close_button = tk.Button(self.command_window, text="Close", command=close_win)
        close_button.pack()

        self.pack(fill=tk.BOTH, expand=1)

        topframe = tk.Frame(self.command_window)
        topframe.pack()
        labele1text = tk.StringVar()
        labele1text.set('To Path: ')
        labele1text = tk.Label(topframe, textvariable=labele1text, height=1)
        labele1text.pack(side="left")
        e1 = tk.Entry(topframe, width=100)
        e1.pack(side=tk.TOP)

        bottomframe = tk.Frame(self.command_window)
        bottomframe.pack(side=tk.BOTTOM)
        labele3text = tk.StringVar()
        labele3text.set('Text Message: ')
        labele3text = tk.Label(bottomframe, textvariable=labele3text, height=1)
        labele3text.pack(side="left")
        e3 = tk.Text(bottomframe, width=100, height=5)
        e3.pack(side=tk.BOTTOM)

        middleframe = tk.Frame(self.command_window)
        middleframe.pack(side=tk.BOTTOM)
        labele2text = tk.StringVar()
        labele2text.set('From Path: ')
        labele2text = tk.Label(middleframe, textvariable=labele2text, height=1)
        labele2text.pack(side="left")
        e2 = tk.Entry(middleframe, width=100)
        e2.pack(side=tk.BOTTOM)

    def send_msg(self):

        global SEND_message
        to_path = e1.get().rstrip()
        from_path = e2.get().rstrip()
        message = e3.get("1.0", tk.END).rstrip()
        transaction_id = uuid.uuid4()
        transaction_id = str(transaction_id)[:15]
        transaction_id = transaction_id.replace('-','')
        message_id = uuid.uuid4()
        message_id = str(message_id)[:15]
        message_id = message_id.replace('-','')
        message_length = (len(message))
        content_type = 'text/plain'

        SEND_message = f'MSRP {transaction_id} SEND\n'
        SEND_message += f'To-Path: {to_path}\n'
        SEND_message += f'From-Path: {from_path}\n'
        SEND_message += f'Message-ID: {message_id}\n'
        SEND_message += f'Byte-Range: 1-{message_length}/{message_length}\n'
        SEND_message += f'Content-Type: {content_type}\n'
        SEND_message += '\n'
        SEND_message += f'{message}\n'
        SEND_message += f'-------{transaction_id}$\n'

        for aQueue in message_queues:
            message_queues[aQueue].put(SEND_message.encode('utf8'))
            outputs.append(aQueue)
            print('added to message queue')

    def server_content(self):

        global SEND_message, message_queues, outputs
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        server.bind(('127.0.0.1', 10000))
        server.listen(5)
        print(f'Listening on 127.0.0.1:10000')
        inputs = [server]


        while inputs:
            print('in while')
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs, 1)
            print('after select.select')

            for s in readable:
                print('in readable')
                if s is server:
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    inputs.append(connection)
                    message_queues[connection] = queue.Queue()
                    print('connected')
                else:
                    data = s.recv(1024)

                    self.add_to_window(data.decode("utf-8"))
                    print(data.decode("utf-8"))
                    # if data:
                    #     message_queues[s].put(data)
                    #     if s not in outputs:
                    #         outputs.append(s)
                    # else:
                    #     if s in outputs:
                    #         outputs.remove(s)
                    #     inputs.remove(s)
                    #     s.close()
                    #     del message_queues[s]

            for s in writable:
                print('in writable')
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    outputs.remove(s)
                else:
                    s.send(next_msg)
                    self.add_to_window(next_msg)
                    outputs.remove(s)


            for s in exceptional:
                print('in exceptional')
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]

    @staticmethod
    def client_exit():
        os._exit(1)

class MSRPServer(tk.Frame):

    app = tk.Tk()
    app.geometry("600x800")
    main_app = Window(app)
    app.mainloop()


if __name__ == "__main__":

    MSRPServer()