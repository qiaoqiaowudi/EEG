import socket
from multiprocessing import Process

def handle(visit_socket):
    while True:
        request_data = visit_socket.recv(1)
        print(request_data)
        if request_data == bytes('+', encoding='utf-8'):
            break
    visit_socket.close()

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)   # 创建服务器的socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 8000))  # 设置自己的服务端口
    server_socket.listen(128)           # 实现监听

    while True:
        visit_socket,visit_address = server_socket.accept()
        print("%s %s已将链接" % visit_address)
        handle_process = Process(target=handle, args=(visit_socket,))
        handle_process.start(),
        visit_socket.close()