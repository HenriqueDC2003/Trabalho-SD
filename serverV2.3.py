import socket
import select
import sys
import os
import datetime
import pytz
import threading

# Dicionário para rastrear os nomes de usuário e suas conexões
users = {}

# Lista para rastrear as mensagens
messages = []

# Diretório para salvar os arquivos enviados pelos clientes
UPLOADS_DIRECTORY = "uploads"

def main():
  # Criar o diretório de uploads se ele não existir
  if not os.path.exists(UPLOADS_DIRECTORY):
    os.makedirs(UPLOADS_DIRECTORY)

  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind(('0.0.0.0', 19000))
  server.listen(5)
  inputs = [server]

  print("Servidor ouvindo na porta 19000...")

  def client_handler(client):
    while True:
      data = client.recv(1024).decode('utf-8')
      if not data:
        print(f"Cliente {client.getpeername()} desconectado.")
        inputs.remove(client)
        del users[client]
        client.close()
        break
      else:
        if client not in users:
          # Se o cliente não está registrado, é um pedido de login
          if data not in users.values():
            users[client] = data
            client.send("Login bem-sucedido!".encode('utf-8'))
            print(f"Cliente {client.getpeername()} agora é {data}")
          else:
            client.send("Nome de usuário já em uso. Tente novamente.".encode('utf-8'))
        else:
          # Mensagem de chat, upload de arquivo ou download de arquivo
          if data.strip() == "@ordenar":
            client.send("Enviando últimas 15 mensagens ordenadas por horário...".encode('utf-8'))
            send_recent_messages(client)
          elif data.startswith("@upload "):
            upload_file(client, data[8:])
          elif data.startswith("@download "):
            download_file(client, data[10:])
          else:
            # Adicione a hora de envio em Brasília à mensagem
            hora_atual_br = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
            hora_envio = hora_atual_br.strftime('%H:%M')
            message = f"({hora_envio}) {users[client]}: {data}"
            print(message)
            messages.append(message)
            for client_socket in users.keys():
              if client_socket != client:
                client_socket.send(message.encode('utf-8'))

  while True:
    readable, _, _ = select.select(inputs, [], [])
    for sock in readable:
      if sock == server:
        client, addr = server.accept()
        print(f"Nova conexão de {addr}")
        inputs.append(client)
        threading.Thread(target=client_handler, args=(client,)).start()

def send_recent_messages(client_socket):
  recent_messages = messages[-15:]
  for message in recent_messages:
    client_socket.send(message.encode('utf-8'))

def upload_file(client_socket, filename):


  # Cria um caminho para o arquivo no diretório de uploads
  file_path = os.path.join(UPLOADS_DIRECTORY, filename)

  # Abre o arquivo para escrita
  with open(file_path, "wb") as f:
    # Recebe o arquivo do cliente
    client_socket.recvfile(f)

  # Fecha o arquivo
  f.close()

  # Envia uma mensagem de confirmação para o cliente
  client_socket.send("Arquivo recebido com sucesso!".encode('utf-8'))

def download_file(client_socket, filename):


  # Cria um caminho para o arquivo no diretório de uploads
  file_path = os.path.join(UPLOADS_DIRECTORY, filename)

  # Verifica se o arquivo existe
  if not os.path.exists(file_path):
    client_socket.send("Arquivo não encontrado.".encode('utf-8'))
    return

  # Abre o arquivo para leitura
  with open(file_path, "rb") as f:
    # Envia o arquivo para o cliente
    client_socket.sendfile(f)

  # Fecha o arquivo
  f.close()

  # Envia uma mensagem de confirmação para o cliente
  client_socket.send("Arquivo enviado com sucesso!".encode('utf-8'))

if __name__ == "__main__":
  main()
