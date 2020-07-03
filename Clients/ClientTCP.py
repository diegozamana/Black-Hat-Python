import socket

target_host = "www.google.com"
target_port = 80

# Cria um objeto socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Faz o cliente se conectar
client.connect((target_host, target_port))

# Envia alguns dados
client.send("GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# Recebe alguns dados
response = client.recv(4096)

print(response)