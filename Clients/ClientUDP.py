import socket

target_host = "127.0.0.1"
target_port = 80

# Cria um objeto socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Envia alguns dados
client.sendto("AAABBBCCC", (target_host, target_port))

#Recebe alguns dados
data, addr = client.recvfrom(4096)

print(data)