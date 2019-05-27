from tkinter import *
import os
import socket
import traceback
import threading
import uuid


class Window(Frame):

    def __init__(self, master = None):
        Frame.__init__(self, master)

        self.master = master

        self.init_window()

    def init_window(self):

        self.master.title("GUI")

        self.pack(fill=BOTH, expand=True)

        quit_button = Button(self, text="Quit", command=self.client_exit)
        # quit_button.place(x=0, y=0)
        quit_button.pack(side=LEFT, padx=5)

        open_cmd_button = Button(self, text="Send", command=self.cmd_win)
        # open_cmd_button.place(x=35, y=0)
        open_cmd_button.pack(side=LEFT, padx=5)

        start_server_button = Button(self, text="Start", command=self.start_server)
        start_server_button.pack(side=LEFT, padx=5)

        self.text_box = Text(self.master)
        # text_box.place(x=5, y=30)
        self.text_box.pack(side=BOTTOM, fill=BOTH, expand=True)

    def add_to_window(self, text):
        # msg = self.format(text)

        def append():
            self.text_box.configure(state='normal')
            self.text_box.insert(END, text)
            self.text_box.configure(state='disabled')
            self.text_box.yview(END)
        self.text_box.after(0, append)

    def start_server(self):
        t = threading.Thread(target=HttpServer)
        t.start()

    def cmd_win(self):

        # fields = 'To path', 'From path', 'Text message'
        to_path = ''
        from_path = ''
        global e1
        global e2
        global e3

        def close_win():
            self.command_window.destroy()

        self.command_window = Toplevel(self.master)
        self.command_window.title("Message Window")

        submit_button = Button(self.command_window, text="Submit", command=self.send_msg)
        submit_button.pack(side=TOP)

        close_button = Button(self.command_window, text="Close", command=close_win)
        close_button.pack()

        self.pack(fill=BOTH, expand=1)

        topframe = Frame(self.command_window)
        topframe.pack()
        labele1text = StringVar()
        labele1text.set('To Path: ')
        labele1text = Label(topframe, textvariable=labele1text, height=1)
        labele1text.pack(side="left")
        e1 = Entry(topframe, width=100)
        e1.pack(side=TOP)

        bottomframe = Frame(self.command_window)
        bottomframe.pack(side=BOTTOM)
        labele3text = StringVar()
        labele3text.set('Text Message: ')
        labele3text = Label(bottomframe, textvariable=labele3text, height=1)
        labele3text.pack(side="left")
        e3 = Text(bottomframe, width=100, height=5)
        e3.pack(side=BOTTOM)

        middleframe = Frame(self.command_window)
        middleframe.pack(side=BOTTOM)
        labele2text = StringVar()
        labele2text.set('From Path: ')
        labele2text = Label(middleframe, textvariable=labele2text, height=1)
        labele2text.pack(side="left")
        e2 = Entry(middleframe, width=100)
        e2.pack(side=BOTTOM)

    @staticmethod
    def send_msg():

        to_path = e1.get().rstrip()
        from_path = e2.get().rstrip()
        message = e3.get("1.0", END).rstrip()
        transaction_id = uuid.uuid4()
        transaction_id = str(transaction_id)[:15]
        message_id = uuid.uuid4()
        message_id = str(message_id)[:15]
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
        SEND_message += f'-------{transaction_id}\n'
        app.add_to_window(SEND_message)

    @staticmethod
    def client_exit():
        os._exit(1)


class HttpServer():

    def __init__(self):

        address = ('127.0.0.1', 10000)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("making a server on {0}:{1}".format(*address))
        self.sock.bind(address)
        self.sock.listen(1)

        self.server_content()

    def response_ok(self, body=b"This is a minimal response", mimetype=b"text/plain"):
        """
        returns a basic HTTP response
        Ex:
            response_ok(
                b"<html><h1>Welcome:</h1></html>",
                b"text/html"
            ) ->

            b'''
            HTTP/1.1 200 OK\r\n
            Content-Type: text/html\r\n
            \r\n
            <html><h1>Welcome:</h1></html>\r\n
            '''
        """

        response = b"HTTP/1.1 200 OK\r\n"
        response += b"Content-Type: " + mimetype + b"\r\n"
        response += b"\r\n"
        response += body

        return response


    def response_method_not_allowed(self):
        """Returns a 405 Method Not Allowed response"""

        return b"\r\n".join([
            b"HTTP/1.1 405 Method Not Allowed",
            b"",
            b"You can't do that on this server!"
        ])


    def response_not_found(self, path):
        """Returns a 404 Not Found response"""

        return b"\r\n".join([
            b"HTTP/1.1 404 Not Found",
            b"",
            b"Error encountered while visiting " + path.encode()
        ])


    def parse_request(self, request):
        """
        Given the content of an HTTP request, returns the path of that request.

        This server only handles GET requests, so this method shall raise a
        NotImplementedError if the method of the request is not GET.
        """

        method, path, version = request.split("\r\n")[0].split(" ")

        if method != "GET":
            raise NotImplementedError

        return path


    def response_path(self, path):
        """
        This method should return appropriate content and a mime type.
        """

        content = b"Response Text"
        mime_type = b"text/html"
        return content, mime_type

    def server_content(self):

        try:
            while True:
                print('waiting for a connection')
                conn, addr = self.sock.accept()  # blocking
                try:
                    print('connection - {0}:{1}'.format(*addr))

                    request = ''
                    while True:
                        data = conn.recv(1024)
                        request += data.decode('utf8')

                        if '\r\n\r\n' in request:
                            break

                    # print("Request received:\n{}\n\n".format(request))
                    app.add_to_window(request)
                    # text_box.insert("Request received:\n{}\n\n".format(request))
                    # guimodule.add

                    try:
                        path = self.parse_request(request)

                        content, mimetype = self.response_path(path)

                        response = self.response_ok(
                            body=content,
                            mimetype=mimetype
                        )
                    except NotImplementedError:
                        response = self.response_method_not_allowed()
                    except NameError:
                        response = self.response_not_found(path)

                    app.add_to_window(response)
                    conn.sendall(response)
                except:
                    traceback.print_exc()
                finally:
                    conn.close()

        except KeyboardInterrupt:
            self.sock.close()
            return
        except:
            traceback.print_exc()


if __name__ == "__main__":
    root = Tk()
    root.geometry("600x800")

    app = Window(root)

    root.mainloop()