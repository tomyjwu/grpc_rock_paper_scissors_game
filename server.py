import tkinter as tk
import socket
import threading
from time import sleep

from concurrent import futures

import logging
import asyncio
import grpc

import rock_paper_scissors_pb2
import rock_paper_scissors_pb2_grpc

window = tk.Tk()
window.title("Sever")

# Top frame consisting of two buttons widgets (i.e. btnStart, btnStop)
topFrame = tk.Frame(window)
btnStart = tk.Button(topFrame, text="Start", foreground="grey", command=lambda : start_server())
btnStart.pack(side=tk.LEFT)
btnStart.configure(fg="grey")
btnStop = tk.Button(topFrame, text="Stop", foreground="grey", command=lambda : stop_server(), state=tk.DISABLED)
btnStop.pack(side=tk.LEFT)
topFrame.pack(side=tk.TOP, pady=(5, 0))

# Middle frame consisting of two labels for displaying the host and port info
middleFrame = tk.Frame(window)
lblHost = tk.Label(middleFrame, text = "Address: X.X.X.X")
lblHost.pack(side=tk.LEFT)
lblPort = tk.Label(middleFrame, text = "Port:XXXX")
lblPort.pack(side=tk.LEFT)
middleFrame.pack(side=tk.TOP, pady=(5, 0))

# The client frame shows the client area
clientFrame = tk.Frame(window)
lblLine = tk.Label(clientFrame, text="**********Client List**********").pack()
scrollBar = tk.Scrollbar(clientFrame)
scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
tkDisplay = tk.Text(clientFrame, height=10, width=30)
tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
scrollBar.config(command=tkDisplay.yview)
tkDisplay.config(yscrollcommand=scrollBar.set, background="#F4F6F7", highlightbackground="grey", state="disabled")
clientFrame.pack(side=tk.BOTTOM, pady=(5, 10))


server = None
client_name = " "
clients = []
clients_names = []
player_data = []

_HANDS = {
    "rock": rock_paper_scissors_pb2.ROCK,
    "paper": rock_paper_scissors_pb2.PAPER,
    "scissors": rock_paper_scissors_pb2.SCISSORS
}

class RockGame(rock_paper_scissors_pb2_grpc.RockPaperScissors):

    def JoinGame(self, request: rock_paper_scissors_pb2.Gamer, context) -> rock_paper_scissors_pb2.GameWelcome:
        print("server received from : " + request.name)
        clients_names.append(request.name)
        update_client_names_display(clients_names)
        gamer_list = rock_paper_scissors_pb2.GamerList(gamers=clients_names)
        return rock_paper_scissors_pb2.GameWelcome(welcome='Welcome, %s!' % request.name, gamer_list=gamer_list)

    def PlayHand(self, request: rock_paper_scissors_pb2.PlayerHand, context) -> rock_paper_scissors_pb2.GameResult:
        print("server received from : " + request.name)
        print("play hand : " + request.hand)
        return rock_paper_scissors_pb2.GameResult(winner_name='winner', player_hands=[])



def grpc_serve():
    global server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rock_paper_scissors_pb2_grpc.add_RockPaperScissorsServicer_to_server(RockGame(), server)
    listen_addr = '[::]:9090'
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    server.start()
    # await server.wait_for_termination()

# Start server function
def start_server():
    btnStart.config(state=tk.DISABLED)
    btnStop.config(state=tk.NORMAL)
    grpc_serve()


# Stop server function
def stop_server():
    global server, clients_names
    btnStart.config(state=tk.NORMAL)
    btnStop.config(state=tk.DISABLED)
    server.stop(None)
    clients_names = []
    update_client_names_display(clients_names)


def accept_clients(the_server, y):
    while True:
        if len(clients) < 2:
            client, addr = the_server.accept()
            clients.append(client)

            # use a thread so as not to clog the gui thread
            threading._start_new_thread(send_receive_client_message, (client, addr))

# Function to receive message from current client AND
# Send that message to other clients
def send_receive_client_message(client_connection, client_ip_addr):
    global server, client_name, clients, player_data, player0, player1

    client_msg = " "

    # send welcome message to client
    client_name = client_connection.recv(4096).decode()
    if len(clients) < 2:
        client_connection.send(b"welcome1")
    else:
        client_connection.send(b"welcome2")

    clients_names.append(client_name)
    update_client_names_display(clients_names)  # update client names display

    if len(clients) > 1:
        sleep(1)

        # send opponent name
        opponent_name = "opponent_name$" + clients_names[1]
        clients[0].send(opponent_name.encode())
        opponent_name = "opponent_name$" + clients_names[0]
        clients[1].send(opponent_name.encode())
        # go to sleep

    while True:
        data = client_connection.recv(4096).decode()
        if not data: break

        # get the player choice from received data
        player_choice = data[11:len(data)]

        msg = {
            "choice": player_choice,
            "socket": client_connection
        }

        if len(player_data) < 2:
            player_data.append(msg)

        if len(player_data) == 2:
            # send player 1 choice to player 2 and vice versa
            opponent_choice = "$opponent_choice" + player_data[1].get("choice")
            player_data[0].get("socket").send(opponent_choice.encode())
            opponent_choice = "$opponent_choice" + player_data[0].get("choice")
            player_data[1].get("socket").send(opponent_choice.encode())

            player_data = []

    # find the client index then remove from both lists(client name list and connection list)
    idx = get_client_index(clients, client_connection)
    del clients_names[idx]
    del clients[idx]
    client_connection.close()

    update_client_names_display(clients_names)  # update client names display


# Return the index of the current client in the list of clients
def get_client_index(client_list, curr_client):
    idx = 0
    for conn in client_list:
        if conn == curr_client:
            break
        idx = idx + 1

    return idx


# Update client name display when a new client connects OR
# When a connected client disconnects
def update_client_names_display(name_list):
    tkDisplay.config(state=tk.NORMAL)
    tkDisplay.delete('1.0', tk.END)

    for c in name_list:
        tkDisplay.insert(tk.END, c+"\n")
    tkDisplay.config(state=tk.DISABLED)


window.mainloop()