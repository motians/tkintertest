import guimodule
import threading
import http_server

if __name__ == "__main__":
    root = guimodule.Tk()
    root.geometry("500x400")

    app = guimodule.Window(root)

    root.mainloop()

