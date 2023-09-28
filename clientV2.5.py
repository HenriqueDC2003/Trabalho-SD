import socket
import select
import sys
import datetime
import pytz
import threading
import os

class Client:
    def __init__(self, server_ip, port=19000):
        self.server_ip = server_ip
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logged_in = False

    def connect(self):
        try:
            self.client.connect((self.server_ip, self.port))
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {str(e)}")
            sys.exit(1)

    def send_username(self):
        if not self.logged_in:
            username = input("Digite seu nome de usuário: ")
            self.client.send(username.encode('utf-8'))
            response = self.client.recv(1024).decode('utf-8')
            if response == "Login bem-sucedido!":
                self.logged_in = True
            print(response)

    def receive_messages(self):
        while True:
            self.send_username()  # Solicita o nome de usuário no início
            socket_list = [sys.stdin, self.client]
            rs, _, _ = select.select(socket_list, [], [])

            for sock in rs:
                if sock == self.client:
                    message = sock.recv(1024).decode('utf-8')
                    if not message:
                        print("Desconectado do servidor.")
                        sys.exit(0)
                    else:
                        print(message + '\n')
                        if message.startswith("@download "):
                            self.download_file(message[10:])
                else:
                    self.handle_user_input()

    def handle_user_input(self):
        message = sys.stdin.readline().strip()

        if message == "@sair":
            print("Desconectando do servidor...")
            self.client.send(message.encode('utf-8'))
            self.client.close()
            sys.exit(0)
        elif message.startswith("@upload "):
            file_path = message.split(" ")[1].strip()
            self.upload_file(file_path)
        elif message.startswith("@download "):
            self.client.send(message.encode('utf-8'))
        else:
            hora_atual_br = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
            hora_envio = hora_atual_br.strftime('%H:%M')
            print(f"({hora_envio}) {message}")
            self.client.send(message.encode('utf-8'))

        def upload_file(self, file_path):
            try:
                with open(file_path, 'rb') as file:
                    filename = os.path.basename(file_path)
                    self.client.send(f"@upload {filename}".encode('utf-8'))
                    response = self.client.recv(1024).decode('utf-8')
                    if response == "Ready to receive":
                        self.client.sendall(file.read())
                        print(f"File '{filename}' uploaded successfully.")
                    else:
                        print(response)
            except FileNotFoundError:
                print(f"File '{file_path}' not found.")
            except Exception as e:
                print(f"Error during file upload: {str(e)}")

    def download_file(self, filename):
        try:
            self.client.send(f"@download {filename}".encode('utf-8'))
            response = self.client.recv(1024).decode('utf-8')

            if response.startswith("File not found"):
                print(response)
                return

            if response == "Ready to send":
                with open(filename, 'wb') as file:
                    while True:
                        data = self.client.recv(1024)
                        if not data:
                            break
                        file.write(data)
                print(f"File '{filename}' downloaded successfully.")
            else:
                print(response)
        except Exception as e:
            print(f"Error during file download: {str(e)}")        

def main():
    if len(sys.argv) < 2:
        print("usage: client SERVER_IP [PORT]")
        sys.exit(1)

    server_ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 19000

    client = Client(server_ip, port)
    client.connect()

    receive_thread = threading.Thread(target=client.receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        pass

if __name__ == "__main__":
    main()

