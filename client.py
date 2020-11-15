
import tkinter as tk
from tkinter import PhotoImage
from tkinter import messagebox
import socket
from time import sleep
import threading

import logging
import asyncio
import grpc

import rock_paper_scissors_pb2
import rock_paper_scissors_pb2_grpc

"""Proof of concept: integrate tkinter, asyncio and async iterator.

Terry Jan Reedy, 2016 July 25
"""

from random import randrange as rr

your_name = ""
opponent_name = ""
game_round = 0
game_timer = 4
your_choice = ""
opponent_choice = ""
TOTAL_NO_OF_ROUNDS = 3
your_score = 0
opponent_score = 0

# network client
client = None
HOST_ADDR = "0.0.0.0"
HOST_PORT = 9090

class App(tk.Tk):

    def __init__(self, loop, interval=1/20):
        super().__init__()
        self.loop = loop
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.tasks = []
        # self.tasks.append(loop.create_task(self.rotator(1/60, 2)))
        self.tasks.append(self.loop.create_task(self.updater(interval)))

    def init_game_ui(self):
        # MAIN GAME WINDOW
        window_main = self
        window_main.title("Game Client")
        top_welcome_frame= tk.Frame(window_main)
        lbl_name = tk.Label(top_welcome_frame, text = "Name:")
        lbl_name.pack(side=tk.LEFT)
        self.ent_name = tk.Entry(top_welcome_frame)
        self.ent_name.pack(side=tk.LEFT)
        btn_connect = tk.Button(top_welcome_frame, text="Connect", command=lambda : self.connect())
        btn_connect.pack(side=tk.LEFT)
        top_welcome_frame.pack(side=tk.TOP)

        top_message_frame = tk.Frame(window_main)
        lbl_line = tk.Label(top_message_frame, text="***********************************************************").pack()
        self.lbl_welcome = tk.Label(top_message_frame, text="")
        self.lbl_welcome.pack()
        self.lbl_line_server = tk.Label(top_message_frame, text="***********************************************************")
        self.lbl_line_server.pack_forget()
        top_message_frame.pack(side=tk.TOP)

        self.top_frame = tk.Frame(window_main)
        top_left_frame = tk.Frame(self.top_frame, highlightbackground="green", highlightcolor="green", highlightthickness=1)
        self.lbl_your_name = tk.Label(top_left_frame, text="Your name: " + your_name, font = "Helvetica 13 bold")
        self.lbl_opponent_name = tk.Label(top_left_frame, text="Opponent: " + opponent_name)
        self.lbl_your_name.grid(row=0, column=0, padx=5, pady=8)
        self.lbl_opponent_name.grid(row=1, column=0, padx=5, pady=8)
        top_left_frame.pack(side=tk.LEFT, padx=(10, 10))


        top_right_frame = tk.Frame(self.top_frame, highlightbackground="green", highlightcolor="green", highlightthickness=1)
        self.lbl_game_round = tk.Label(top_right_frame, text="Game round (x) starts in", foreground="blue", font = "Helvetica 14 bold")
        self.lbl_timer = tk.Label(top_right_frame, text=" ", font = "Helvetica 24 bold", foreground="blue")
        self.lbl_game_round.grid(row=0, column=0, padx=5, pady=5)
        self.lbl_timer.grid(row=1, column=0, padx=5, pady=5)
        top_right_frame.pack(side=tk.RIGHT, padx=(10, 10))

        self.top_frame.pack_forget()

        self.middle_frame = tk.Frame(window_main)

        lbl_line = tk.Label(self.middle_frame, text="***********************************************************").pack()
        lbl_line = tk.Label(self.middle_frame, text="**** GAME LOG ****", font = "Helvetica 13 bold", foreground="blue").pack()
        lbl_line = tk.Label(self.middle_frame, text="***********************************************************").pack()

        round_frame = tk.Frame(self.middle_frame)
        self.lbl_round = tk.Label(round_frame, text="Round")
        self.lbl_round.pack()
        self.lbl_your_choice = tk.Label(round_frame, text="Your choice: " + "None", font = "Helvetica 13 bold")
        self.lbl_your_choice.pack()
        self.lbl_opponent_choice = tk.Label(round_frame, text="Opponent choice: " + "None")
        self.lbl_opponent_choice.pack()
        self.lbl_result = tk.Label(round_frame, text=" ", foreground="blue", font = "Helvetica 14 bold")
        self.lbl_result.pack()
        round_frame.pack(side=tk.TOP)

        final_frame = tk.Frame(self.middle_frame)
        lbl_line = tk.Label(final_frame, text="***********************************************************").pack()
        self.lbl_final_result = tk.Label(final_frame, text=" ", font = "Helvetica 13 bold", foreground="blue")
        self.lbl_final_result.pack()
        lbl_line = tk.Label(final_frame, text="***********************************************************").pack()
        final_frame.pack(side=tk.TOP)

        self.middle_frame.pack_forget()

        button_frame = tk.Frame(window_main)
        photo_rock = PhotoImage(file=r"rock.gif")
        photo_paper = PhotoImage(file = r"paper.gif")
        photo_scissors = PhotoImage(file = r"scissors.gif")

        btn_rock = tk.Button(button_frame, text="Rock", command=lambda : self.choice("rock"), state=tk.DISABLED, image=photo_rock)
        btn_paper = tk.Button(button_frame, text="Paper", command=lambda : self.choice("paper"), state=tk.DISABLED, image=photo_paper)
        btn_scissors = tk.Button(button_frame, text="Scissors", command=lambda : self.choice("scissors"), state=tk.DISABLED, image=photo_scissors)
        btn_rock.grid(row=0, column=0)
        btn_paper.grid(row=0, column=1)
        btn_scissors.grid(row=0, column=2)
        button_frame.pack(side=tk.BOTTOM)

    async def rotator(self, interval, d_per_tick):
        canvas = tk.Canvas(self, height=600, width=600)
        canvas.pack()
        deg = 0
        color = 'black'
        arc = canvas.create_arc(100, 100, 500, 500, style=tk.CHORD,
                                start=0, extent=deg, fill=color)
        while await asyncio.sleep(interval, True):
            deg, color = deg_color(deg, d_per_tick, color)
            canvas.itemconfigure(arc, extent=deg, fill=color)

    async def updater(self, interval):
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()

    def game_logic(self, you, opponent):
        winner = ""
        rock = "rock"
        paper = "paper"
        scissors = "scissors"
        player0 = "you"
        player1 = "opponent"

        if you == opponent:
            winner = "draw"
        elif you == rock:
            if opponent == paper:
                winner = player1
            else:
                winner = player0
        elif you == scissors:
            if opponent == rock:
                winner = player1
            else:
                winner = player0
        elif you == paper:
            if opponent == scissors:
                winner = player1
            else:
                winner = player0
        return winner


    def enable_disable_buttons(self, todo):
        if todo == "disable":
            btn_rock.config(state=tk.DISABLED)
            btn_paper.config(state=tk.DISABLED)
            btn_scissors.config(state=tk.DISABLED)
        else:
            btn_rock.config(state=tk.NORMAL)
            btn_paper.config(state=tk.NORMAL)
            btn_scissors.config(state=tk.NORMAL)

    def connect(self):
        global your_name
        if len(self.ent_name.get()) < 1:
            tk.messagebox.showerror(title="ERROR!!!", message="You MUST enter your first name <e.g. John>")
        else:
            your_name = self.ent_name.get()
            self.lbl_your_name["text"] = "Your name: " + your_name
            # connect_to_server(your_name)
            self.tasks.append(self.loop.create_task(self.join_game(your_name)))

    def count_down(self, my_timer, nothing):
        global game_round
        if game_round <= TOTAL_NO_OF_ROUNDS:
            game_round = game_round + 1

        self.lbl_game_round["text"] = "Game round " + str(game_round) + " starts in"

        while my_timer > 0:
            my_timer = my_timer - 1
            print("game timer is: " + str(my_timer))
            self.lbl_timer["text"] = my_timer
            sleep(1)

        self.enable_disable_buttons("enable")
        self.lbl_round["text"] = "Round - " + str(game_round)
        self.lbl_final_result["text"] = ""


    def choice(self, arg):
        global your_choice, client, game_round
        your_choice = arg
        self.lbl_your_choice["text"] = "Your choice: " + your_choice

        if client:
            str_data = "Game_Round"+str(game_round)+your_choice
            client.send(str_data.encode())
            self.enable_disable_buttons("disable")

    async def join_game(self, name):
        async with grpc.aio.insecure_channel('localhost:9090') as channel:
            stub = rock_paper_scissors_pb2_grpc.RockPaperScissorsStub(channel)
            response = await stub.JoinGame(rock_paper_scissors_pb2.Gamer(name=name))
        print("join received: " + response.welcome)




    def receive_message_from_server(self, sck, m):
        global your_name, opponent_name, game_round
        global your_choice, opponent_choice, your_score, opponent_score

        while True:
            from_server = sck.recv(4096).decode()

            if not from_server: break

            if from_server.startswith("welcome"):
                if from_server == "welcome1":
                    self.lbl_welcome["text"] = "Server says: Welcome " + your_name + "! Waiting for player 2"
                elif from_server == "welcome2":
                    self.lbl_welcome["text"] = "Server says: Welcome " + your_name + "! Game will start soon"
                self.lbl_line_server.pack()

            elif from_server.startswith("opponent_name$"):
                opponent_name = from_server.replace("opponent_name$", "")
                self.lbl_opponent_name["text"] = "Opponent: " + opponent_name
                self.top_frame.pack()
                self.middle_frame.pack()

                # we know two users are connected so game is ready to start
                threading._start_new_thread(self.count_down, (game_timer, ""))
                self.lbl_welcome.config(state=tk.DISABLED)
                self.lbl_line_server.config(state=tk.DISABLED)

            elif from_server.startswith("$opponent_choice"):
                # get the opponent choice from the server
                opponent_choice = from_server.replace("$opponent_choice", "")

                # figure out who wins in this round
                who_wins = self.game_logic(your_choice, opponent_choice)
                round_result = " "
                if who_wins == "you":
                    your_score = your_score + 1
                    round_result = "WIN"
                elif who_wins == "opponent":
                    opponent_score = opponent_score + 1
                    round_result = "LOSS"
                else:
                    round_result = "DRAW"

                # Update GUI
                self.lbl_opponent_choice["text"] = "Opponent choice: " + opponent_choice
                self.lbl_result["text"] = "Result: " + round_result

                # is this the last round e.g. Round 5?
                if game_round == TOTAL_NO_OF_ROUNDS:
                    # compute final result
                    final_result = ""
                    color = ""

                    if your_score > opponent_score:
                        final_result = "(You Won!!!)"
                        color = "green"
                    elif your_score < opponent_score:
                        final_result = "(You Lost!!!)"
                        color = "red"
                    else:
                        final_result = "(Draw!!!)"
                        color = "black"

                    self.lbl_final_result["text"] = "FINAL RESULT: " + str(your_score) + " - " + str(opponent_score) + " " + final_result
                    self.lbl_final_result.config(foreground=color)

                    self.enable_disable_buttons("disable")
                    game_round = 0

                # Start the timer
                threading._start_new_thread(self.count_down, (game_timer, ""))


        sck.close()


def deg_color(deg, d_per_tick, color):
    deg += d_per_tick
    if 360 <= deg:
        deg %= 360
        color = '#%02x%02x%02x' % (rr(0, 256), rr(0, 256), rr(0, 256))
    return deg, color

loop = asyncio.get_event_loop()
app = App(loop)
app.init_game_ui()
loop.run_forever()
loop.close()
