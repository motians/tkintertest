from tkinter import *
import socket
import os
import mimetypes
import guimodule
import traceback

import threading


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
        quit_button.pack()

        open_cmd_button = Button(self, text="Send", command=self.cmd_win)
        # open_cmd_button.place(x=35, y=0)
        open_cmd_button.pack()

        start_server_button = Button(self, text="Start", command=self.start_server)
        start_server_button.pack()

        self.text_box = Text(self.master)
        # text_box.place(x=5, y=30)
        self.text_box.pack(side=BOTTOM, fill=BOTH, expand=True)

        # text_box.insert(END, "Does this work?")
        # self.start_server()

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

        self.command_window = Toplevel(self.master)
        self.command_window.title("Command Window")

        self.command_window.geometry("400x300")

        self.pack(fill=BOTH, expand=1)

    def client_exit(self):
        # sys.exit()
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

        If the requested path is a directory, then the content should be a
        plain-text listing of the contents with mimetype `text/plain`.

        If the path is a file, it should return the contents of that file
        and its correct mimetype.

        If the path does not map to a real location, it should raise an
        exception that the server can catch to return a 404 response.

        Ex:
            response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                                b"text/html")

            response_path('/images/sample_1.png')
                            -> (b"A12BCF...",  # contents of sample_1.png
                                b"image/png")

            response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                                 b"text/plain")

            response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

        """

        # new_location = os.path.join(CWD, path.lstrip("/"))
        #
        # if not os.path.exists(new_location):
        #     raise NameError
        #
        # if os.path.isdir(new_location):
        #     content = "\n".join(os.listdir(new_location)).encode()
        #     mime_type = b"text/plain"
        # elif new_location.rsplit(".", 1)[1] == 'py':
        #     content = os.popen('python {}'.format(new_location)).read().encode()
        #     mime_type = b"text/html"
        # else:
        #     with open(new_location, "rb") as file:
        #         content = file.read()
        #         mime_type = mimetypes.guess_type(path)[0].encode()

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

                    print("Request received:\n{}\n\n".format(request))
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
    root = guimodule.Tk()
    root.geometry("600x800")

    app = Window(root)

    root.mainloop()