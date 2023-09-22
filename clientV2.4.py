import socket
import select
import sys
import datetime
import pytz
import threading
import os

def main():
    if len(sys.argv) < 2:
        print("usage: client SERVER_IP [PORT]")
        sys.exit(1)

    ip_address = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 19000

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip_address, port))

    logged_in = False

    def receive_messages():
        nonlocal logged_in
        while True:
            if not logged_in:
                username = input("Digite seu nome de usuário: ")
                client.send(username.encode('utf-8'))
                response = client.recv(1024).decode('utf-8')
                if response == "Login bem-sucedido!":
                    logged_in = True
                    print(response)
                else:
                    print(response)
            else:
                socket_list = [sys.stdin, client]
                rs, _, _ = select.select(socket_list, [], [])

                for sock in rs:
                    if sock == client:
                        message = sock.recv(1024).decode('utf-8')
                        if not message:
                            print("Desconectado do servidor.")
                            sys.exit(0)
                        else:
                            print(message)
                            if message.startswith("@download "):
                                download_file(client, message[10:])
                    else:
                        message = sys.stdin.readline()
                        if message.strip() == "@sair":
                            print("Desconectando do servidor...")
                            client.send(message.encode('utf-8'))
                            client.close()
                            sys.exit(0)
                        elif message.startswith("@upload "):
                            file_path = message.split(" ")[1].strip()
                            upload_file(client, file_path)
                        elif message.startswith("@download "):
                            client.send(message.encode('utf-8'))
                        else:
                            hora_atual_br = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
                            hora_envio = hora_atual_br.strftime('%H:%M')
                            print(f"({hora_envio}) {message}")
                            client.send(message.encode('utf-8'))

    def upload_file(client_socket, file_path):
        try:
            # Verifique se o arquivo existe
            if not os.path.exists(file_path):
                print(f"O arquivo '{file_path}' não existe.")
                return

            # Enviar o comando de upload para o servidor
            client_socket.send(f"@UPLOAD {os.path.basename(file_path)}".encode('utf-8'))

            # Aguarde a confirmação do servidor
            response = client_socket.recv(1024).decode('utf-8')
            if response != "OK":
                print(f"O servidor não está pronto para receber o arquivo: {response}")
                return

            # Abra o arquivo e envie seus dados para o servidor
            with open(file_path, 'rb') as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    client_socket.send(data)

            print(f"Arquivo '{file_path}' enviado com sucesso para o servidor.")
        except Exception as e:
            print(f"Erro ao enviar o arquivo: {str(e)}")

    def download_file(client_socket, filename):
        try:
            # Envie uma solicitação de download ao servidor
            client_socket.send(f"@download {filename}".encode('utf-8'))

            # Receba o tamanho do arquivo do servidor
            file_size = int(client_socket.recv(1024).decode('utf-8'))
            if file_size == -1:
                print(f"Arquivo '{filename}' não encontrado no servidor.")
                return

            # Confirme a recepção do tamanho do arquivo
            client_socket.send("OK".encode('utf-8'))

            # Abra um arquivo local para salvar o arquivo recebido
            with open(filename, 'wb') as file:
                received_size = 0
                while received_size < file_size:
                    data = client_socket.recv(1024)
                    file.write(data)
                    received_size += len(data)

            print(f"Arquivo '{filename}' baixado com sucesso.")
        except Exception as e:
            print(f"Erro ao baixar o arquivo: {str(e)}")

    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        pass

if __name__ == "__main__":
    main()
