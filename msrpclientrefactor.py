"""
Message format:
        transaction_object definition:
            0: transaction_id
            1: request_type
            2: response_code
            3: to_path
            4: from_path
            5: message_id
            6: byte_range
            7: content_type
            8: success_report
            9: failure_report
            10: body
            11: decode

"""

import tkinter as tk
import threading
import select, socket, queue
import logging
from os import _exit, environ
from uuid import uuid4
from time import sleep


LOG_FORMAT = "%(asctime)s %(filename)s:%(lineno)-3d %(levelname)s %(message)s"

FORMATTER = logging.Formatter(LOG_FORMAT)

CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setFormatter(FORMATTER)

LOGGER = logging.getLogger()
LOGGER.addHandler(CONSOLE_HANDLER)
LOGGER.setLevel('DEBUG')

global SEND_message, message_queues, outputs, object_dictionary, SERVER_IP, SERVER_PORT
SEND_message = None
message_queues = {}
outputs = []
object_dictionary = {}

if 'TEST_HOST_IP' in environ:
    SERVER_IP = environ('TEST_HOST_IP')
else:
    SERVER_IP = '127.0.0.1'

if 'TEST_HOST_PORT' in environ:
    SERVER_PORT = environ('TEST_HOST_PORT')
else:
    SERVER_PORT = 10000


class Window(tk.Frame):
    """
    Main application class and window management.
    """

    def __init__(self, master=None):

        tk.Frame.__init__(self, master)

        self.master = master
        self.master.title("Client")

        self.pack(fill=tk.BOTH, expand=True)

        quit_button = tk.Button(self, text="Quit", command=self.client_exit)
        quit_button.pack(side=tk.LEFT, padx=5)

        self.open_cmd_button = tk.Button(self, text="Send", command=self.cmd_win)
        self.open_cmd_button.pack(side=tk.LEFT, padx=5)

        self.start_server_button = tk.Button(self, text="Start", command=self.start_server)
        self.start_server_button.pack(side=tk.LEFT, padx=5)

        self.success_checkbox = tk.IntVar()
        checkbutton1 = tk.Checkbutton(self, text="Success report", variable=self.success_checkbox)
        checkbutton1.pack(side=tk.LEFT)

        self.failure_checkbox = tk.IntVar()
        checkbutton2 = tk.Checkbutton(self, text="Failure report", variable=self.failure_checkbox)
        checkbutton2.pack(side=tk.LEFT)

        self.report_checkbox = tk.IntVar()
        checkbutton3 = tk.Checkbutton(self, text="Add report headers", variable=self.report_checkbox)
        checkbutton3.pack(side=tk.LEFT)

        self.error_response = tk.IntVar()
        checkbutton4 = tk.Checkbutton(self, text="Send 400 response.", variable=self.error_response)
        checkbutton4.pack(side=tk.LEFT)

        self.text_box = tk.Text(self.master)
        self.text_box.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def start_server(self):
        """ Start TCP server connection in seperator thread. """

        self.start_server_button.config(state=tk.DISABLED)

        t = threading.Thread(target=self.server_content)
        t.start()

    def add_to_window(self, text):
        """ Adds text to the main log window. """

        text = text + '\n'

        def append():
            self.text_box.configure(state='normal')
            self.text_box.insert(tk.END, text)
            self.text_box.configure(state='disabled')
            self.text_box.yview(tk.END)
        self.text_box.after(0, append)

    def cmd_win(self):
        """ Opens a new window for entering a new text message. """

        global e1
        global e2
        global e3

        self.open_cmd_button.config(state=tk.DISABLED)

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
        """ Formats and puts the MSRP message into the queue for sending to the server. """

        logging.debug(f'Sucess report status: {self.success_checkbox.get()}')
        logging.debug(f'Sucess report status: {self.failure_checkbox.get()}')
        logging.debug('Creating new message to send.')
        global SEND_message
        to_path = e1.get().rstrip()
        from_path = e2.get().rstrip()
        message = e3.get("1.0", tk.END).rstrip()
        transaction_id = uuid4()
        transaction_id = str(transaction_id)[:15]
        transaction_id = transaction_id.replace('-', '')
        message_id = uuid4()
        message_id = str(message_id)[:15]
        message_id = message_id.replace('-', '')
        message_length = (len(message))
        content_type = 'text/plain'

        SEND_message = f'MSRP {transaction_id} SEND\r\n'
        SEND_message += f'To-Path: {to_path}\r\n'
        SEND_message += f'From-Path: {from_path}\r\n'
        SEND_message += f'Message-ID: {message_id}\r\n'
        if self.report_checkbox.get():
            if self.success_checkbox.get():
                SEND_message += f'Success-Report: yes\r\n'
            else:
                SEND_message += f'Success-Report: no\r\n'
            if self.failure_checkbox.get():
                SEND_message += f'Failure-Report: yes\r\n'
            else:
                SEND_message += f'Failure-Report: no\r\n'
        SEND_message += f'Byte-Range: 1-{message_length}/{message_length}\r\n'
        SEND_message += f'Content-Type: {content_type}\r\n'
        SEND_message += '\r\n'
        SEND_message += f'{message}\r\n'
        SEND_message += f'-------{transaction_id}$\r\n'

        for aQueue in message_queues:
            logging.debug('Adding new message to output queue.')
            message_queues[aQueue].put(SEND_message.encode('utf8'))
            outputs.append(aQueue)

    def send_report(self, message_object):
        """ Formats and puts the MSRP REPORT message into the output gueue. """

        transaction_id = uuid4()
        transaction_id = str(transaction_id)[:15]
        transaction_id = transaction_id.replace('-', '')

        SEND_message = f'MSRP {transaction_id} REPORT\r\n'
        SEND_message += f'To-Path: {message_object[4]}\r\n'
        SEND_message += f'From-Path: {message_object[3]}\r\n'
        SEND_message += f'Message-ID: {message_object[5]}\r\n'
        SEND_message += f'Byte-Range: 1-{message_object[6]}/{message_object[6]}\r\n'
        SEND_message += f'Status: 000 200 OK\r\n'
        SEND_message += f'-------{transaction_id}$\r\n'

        for aQueue in message_queues:
            logging.debug('Adding new message to output queue.')
            message_queues[aQueue].put(SEND_message.encode('utf8'))
            outputs.append(aQueue)

    def send_200_response(self, message_object, response_code):
        """ Formats and puts a 200 response into the output queue. """

        if response_code == '200':
            SEND_message = f'MSRP {message_object[0]} 200 OK\r\n'
        else:
            SEND_message = f'MSRP {message_object[0]} 400 Bad Request\r\n'

        SEND_message += f'To-Path: {message_object[4]}\r\n'
        SEND_message += f'From-Path: {message_object[3]}\r\n'
        SEND_message += f'-------{message_object[0]}$\r\n'

        for aQueue in message_queues:
            logging.debug('Adding 200 response to output queue.')
            message_queues[aQueue].put(SEND_message.encode('utf8'))
            outputs.append(aQueue)

        sleep(1)
        logging.debug(f'Success status: {message_object[8]}')
        if response_code == '200':
            if message_object[8] == 'yes':  # check success report request
                logging.debug("Success report request true, send REPORT")
                self.send_report(message_object)

    def message_decode(self, content):
        """ Decodes a received message and populates the transaction object list. """

        transaction_id = None
        request_type = None
        response_code = None
        to_path = None
        from_path = None
        message_id = None
        byte_range = None
        content_type = None
        success_report = None
        failure_report = None
        body = None
        decode = True

        try:
            for line in content.splitlines():
                if line[:7] == "-------":
                    pass
                elif line[:4] == "MSRP":
                    scratch = line.split(" ")
                    transaction_id = scratch[1].strip()
                    if scratch[2].strip() == "SEND":
                        request_type = "SEND"
                    elif scratch[2].strip() == "REPORT":
                        request_type = "REPORT"
                    else:
                        response_code = scratch[2]
                else:
                    scratch = line.split(":")
                    logging.debug(f'Print line debug: {scratch}')
                    if scratch[0] == "To-Path":
                        to_path = scratch[1].strip()
                    elif scratch[0] == "From-Path":
                        from_path = scratch[1].strip()
                    elif scratch[0] == "Message-ID":
                        message_id = scratch[1].strip()
                    elif scratch[0] == "Content-Type":
                        content_type = scratch[1].strip()
                    elif scratch[0] == "Byte-Range":
                        byte_range = scratch[1].split("/")[1].strip()
                    elif scratch[0] == "Success-Report":
                        success_report = scratch[1].strip()
                        logging.debug(f'Success report decoded as: {success_report}')
                    elif scratch[0] == "Failure-Report":
                        failure_report = scratch[1].strip()
                    elif scratch[0] == "\r\n":
                        pass
                    else:
                        body = scratch[0].strip()
        except IndexError:
            pass
        except ValueError:
            logging.error("Message decode failure.")
            logging.error(content)
            decode = False

        transaction_object = [
            transaction_id,
            request_type,
            response_code,
            to_path,
            from_path,
            message_id,
            byte_range,
            content_type,
            success_report,
            failure_report,
            body,
            decode
        ]
        logging.debug("Message decode complete.")

        return transaction_object

    def server_content(self):
        """ Starts and manages main TCP socket connection to the server. """

        global SEND_message, message_queues, outputs
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.connect((SERVER_IP, SERVER_PORT))
        logging.debug(f"connected to {SERVER_IP}:{SERVER_PORT}")

        inputs = [client]
        outputs = []
        client.setblocking(False)
        message_queues[client] = queue.Queue()

        while inputs:
            logging.debug('Socket wait.')
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs, 1)
            logging.debug('Socket go.')
            data = ""
            decoded_data = ""
            for s in readable:
                logging.debug('Reading data next.')
                while data != b'$':
                    try:
                        data = s.recv(1)
                        decoded_data += data.decode("utf-8")
                    except (BlockingIOError, socket.error):
                        logging.debug('Error occurred, continue.')
                        sleep(0.5)
                        break

                self.add_to_window(decoded_data)
                logging.debug('Done reading data.')

                decoded_message = self.message_decode(decoded_data)
                if decoded_message[1] == "SEND":
                    if self.error_response.get():
                        self.send_200_response(decoded_message, '400')
                    else:
                        self.send_200_response(decoded_message, '200')

            for s in writable:
                logging.debug('Sending data next.')

                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    outputs.remove(s)
                else:
                    s.send(next_msg)
                    self.add_to_window(next_msg.decode('utf8'))
                    outputs.remove(s)
                    logging.debug('Data sent.')

            for s in exceptional:
                logging.debug('Exception handling.')
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]

    @staticmethod
    def client_exit():
        _exit(1)


class MSRPServer(tk.Frame):

    app = tk.Tk()
    app.geometry("700x600")
    main_app = Window(app)
    app.mainloop()


if __name__ == "__main__":

    MSRPServer()
