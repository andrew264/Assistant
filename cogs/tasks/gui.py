# Imports
import asyncio
import threading
import tkinter as tk
from os import getpid
from tkinter import ttk
from typing import Optional

import disnake
import psutil
from disnake.ext import commands

from EnvVariables import Owner_ID
from assistant import Client, colour_gen, all_activities, available_clients, human_bytes, time_delta

font = 'Bahnschrift SemiBold SemiConden'


class App(tk.Tk):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.timer: Optional[threading.Timer] = None
        self.bot = client
        self.wm_title("Andrew's Assistant")
        self.iconphoto(True, tk.PhotoImage(file="./data/icon.png"))
        self.geometry("1000x500")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # create notebook
        self.tabControl = ttk.Notebook(self)
        self.tabControl.pack(expand=1, fill="both")
        # create tabs
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        self.tab1.pack(expand=1, fill="both")
        self.tab2.pack(expand=1, fill="both")
        # add tabs to notebook
        self.tabControl.add(self.tab1, text="Guild/VC")
        self.tabControl.add(self.tab2, text='Stats')
        # set style
        self.tk.call("source", "sun-valley.tcl")
        self.tk.call("set_theme", "dark")
        self.Refresher()
        self.mainloop()

    def tab_1(self):
        for label in list(self.tab1.children.values()):
            label.destroy()
        # Connected As
        ttk.Label(self.tab1, text=f"Connected as {self.bot.user}", font=(font, 15), ) \
            .pack(anchor='w', side=tk.TOP)
        # Guilds
        ttk.Label(self.tab1, text=f"Guilds Available ({len(self.bot.guilds)}):", font=(font, 12), ) \
            .pack(anchor='w', side=tk.TOP)
        for guild in self.bot.guilds:
            ttk.Label(self.tab1, text=f"\t{guild.name}: ({guild.id}) ({len(guild.members)} members)",
                      font=(font, 12), foreground='#ff867e', ).pack(anchor='w', side=tk.TOP)
        # Voice Channels
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if vc.members:
                    ttk.Label(self.tab1, text=f"🔊 {vc.name}:", font=(font, 12),
                              foreground=f'{colour_gen(guild.id)}', ).pack(anchor='w', side=tk.TOP)
                    for member in vc.members:
                        # Member
                        name = f"{member.display_name} "
                        if not (member.voice.self_deaf or member.voice.deaf):
                            name += "🎧"
                        if not (member.voice.self_mute or member.voice.mute):
                            name += "🎙️"
                        if member.voice.self_stream or member.voice.self_video:
                            name += " 📺"

                        ttk.Label(self.tab1, text=f"\t{name}", font=(font, 11),
                                  foreground=f'{member.colour}', ).pack(anchor='w', side=tk.TOP)
                        # Member Client
                        ttk.Label(self.tab1, text=f"\t\t{available_clients(member)}", font=('Bahnschrift', 10),
                                  foreground=f'{member.colour}', ).pack(anchor='w', side=tk.TOP)
                        # Member Activity
                        activities = all_activities(member)
                        for key, value in activities.items():
                            if value:
                                ttk.Label(self.tab1, text=f"\t\t{key}: {value}", font=('Bahnschrift', 10),
                                          foreground=f'{member.colour}', ).pack(anchor='w', side=tk.TOP)
        # client latency
        try:
            ping = max(int(self.bot.latency * 1000), 0)
        except OverflowError:
            return
        ttk.Label(self.tab1, text=f"PING: {ping} ms", font=(font, 10)) \
            .pack(anchor='e', side=tk.BOTTOM)
        # show my online status
        user = disnake.utils.get(self.bot.get_all_members(), id=Owner_ID)
        ttk.Label(self.tab1, text=f"{user}: {available_clients(user)}", font=(font, 10), ) \
            .pack(anchor='w', side=tk.BOTTOM)

    def tab_2(self):
        for label in list(self.tab2.children.values()):
            label.destroy()
        # Create Table
        table = ttk.Treeview(self.tab2, columns=('name', 'value'), show='headings', height=10)
        table.heading('name', text='Name', anchor=tk.CENTER)
        table.column('name', anchor=tk.CENTER)
        table.heading('value', text='Value', anchor=tk.CENTER)
        table.column('value', anchor=tk.CENTER)
        # Bot User
        table.insert('', 'end', values=('Bot', f"{self.bot.user} ({self.bot.user.id})"))
        # Bot Activity
        table.insert('', 'end', values=(
            'Status', f"{self.bot.status.name.title()} {self.bot.activity.type.name.title()} {self.bot.activity.name}"))
        # Bot Uptime
        table.insert('', 'end', values=('Uptime', f"{time_delta(self.bot.start_time)}"))
        # Bot Latency
        try:
            ping = max(int(self.bot.latency * 1000), 0)
        except OverflowError:
            return
        table.insert('', 'end', values=('Ping', f"{ping} ms"))
        # Bot Guilds and Members
        table.insert('', 'end', values=('No. of Guilds', f"{len(self.bot.guilds)}"))
        table.insert('', 'end', values=('No. of Users', f"{len(self.bot.users)}"))
        # Socket Event Counter
        table.insert('', 'end', values=('Socket Send', f"{self.bot.events['socket_send']}"))
        table.insert('', 'end', values=('Socket Receive', f"{self.bot.events['socket_receive']}"))
        # Message Event Counter
        table.insert('', 'end', values=('Messages Received', f"{self.bot.events['messages']}"))
        # Presence Event Counter
        table.insert('', 'end', values=('Presence Updates', f"{self.bot.events['presence_update']}"))
        # Memory Usage
        used_memory = psutil.Process(getpid()).memory_info().rss
        table.insert('', 'end', values=('Memory Usage', f"{human_bytes(used_memory)}"))
        # CPU Usage
        table.insert('', 'end', values=('CPU Usage', f"{psutil.cpu_percent()}%"))
        table.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def Refresher(self):
        # Guilds/VC
        self.tab_1()
        # Bot Stats
        self.tab_2()
        self.timer = threading.Timer(2.5, self.Refresher)
        self.timer.start()

    def on_closing(self):
        self.timer.cancel()
        self.destroy()


class UI(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener('on_ready')
    async def start_gui(self):
        thread = threading.Thread(target=App, args=(self.client,))
        thread.start()
        print("GUI started")
        while thread.is_alive():
            await asyncio.sleep(2)
        else:
            print("GUI stopped")
            await self.client.close()


def setup(client: Client):
    client.add_cog(UI(client))
