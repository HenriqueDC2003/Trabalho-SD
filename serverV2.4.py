import socket
import select
import os
import datetime
import pytz
import threading
from collections import deque

# Modelo: Classe para rastrear mensagens
class MessageModel:
    def __init__(self):
        self.messages = deque(maxlen=15)

    def add_message(self, message):
        self.messages.append(message)

    def get_recent_messages(self):
        return list(self.messages)

# Modelo: Classe para rastrear usuários
class UserModel:
    def __init__(self):
        self.users = {}

    def register_user(self, client, username):
        if username not in self.users.values():
            self.users[client] = username
            return True
        return False

    def get_username(self, client):
        return self.users.get(client)

# Controlador: Lógica principal do servidor
class ServerController:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.inputs = [self.server]

        self.message_model = MessageModel()
        self.user_model = UserModel()

    def start(self):
        print(f"Servidor ouvindo na porta {self.port}...")
        while True:
            readable, _, _ = select.select(self.inputs, [], [])
            for sock in readable:
                if sock == self.server:
                    client, addr = self.server.accept()
                    print(f"Nova conexão de {addr}")
                    self.inputs.append(client)
                    threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        while True:
            data = client.recv(1024).decode('utf-8')
            if not data:
                print(f"Cliente {client.getpeername()} desconectado.")
                self.inputs.remove(client)
                del self.user_model.users[client]
                client.close()
                break
            else:
                self.handle_client_data(client, data)

    def handle_client_data(self, client, data):
        if client not in self.user_model.users:
            if data.strip().startswith("@login "):
                username = data.strip()[7:]
                if self.user_model.register_user(client, username):
                    client.send("Login bem-sucedido!".encode('utf-8'))
                    print(f"Cliente {client.getpeername()} agora é {username}")
                else:
                    client.send("Nome de usuário já em uso. Tente novamente.".encode('utf-8'))
            else:
                client.send("Você deve fazer login primeiro.".encode('utf-8'))
        else:
            if data.strip() == "@ordenar":
                client.send("Enviando últimas 15 mensagens ordenadas por horário...".encode('utf-8'))
                recent_messages = self.message_model.get_recent_messages()
                for message in recent_messages:
                    client.send(message.encode('utf-8'))
            elif data.startswith("@upload "):
                self.upload_file(client, data[8:])
            elif data.startswith("@download "):
                self.download_file(client, data[10:])
            else:
                self.handle_chat_message(client, data)

    def handle_chat_message(self, client, message_text):
        username = self.user_model.get_username(client)
        hora_atual_br = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
        hora_envio = hora_atual_br.strftime('%H:%M')
        message = f"({hora_envio}) {username}: {message_text}"
        print(message)
        self.message_model.add_message(message)
        for client_socket in self.user_model.users.keys():
            if client_socket != client:
                client_socket.send(message.encode('utf-8'))
		# Receive the file data from the client
def upload_file(self, client, filename):
    try:
        file_data = client.recv(1024)
        if not file_data:
            print(f"Upload failed for {filename}")
            return

        # Specify a directory to store uploaded files
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Create the file path for the uploaded file
        file_path = os.path.join(upload_dir, filename)

        # Write the received data to the file
        with open(file_path, "wb") as file:
            while file_data:
                file.write(file_data)
                file_data = client.recv(1024)

        print(f"File '{filename}' uploaded successfully")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def download_file(self, client, filename):
    try:
        # Specify the directory where the files are stored
        download_dir = "uploads"
        file_path = os.path.join(download_dir, filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            client.send(f"File '{filename}' not found on the server.".encode('utf-8'))
            return

        # Send the file to the client
        with open(file_path, "rb") as file:
            file_data = file.read(1024)
            while file_data:
                client.send(file_data)
                file_data = file.read(1024)

        print(f"File '{filename}' sent to {self.user_model.get_username(client)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    server_controller = ServerController('0.0.0.0', 19000)
    server_controller.start()

