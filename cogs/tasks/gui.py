# Imports
import threading
import tkinter as tk

import disnake
from disnake.ext import commands

from EnvVariables import Owner_ID
from assistant import Client, colour_gen, all_activities, available_clients


class App(tk.Tk):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.bot = client
        self.wm_title("Andrew's Assistant")
        self.iconphoto(True, tk.PhotoImage(file="./data/icon.png"))
        self.geometry("1000x500")
        self.configure(background="#2C2F33")
        self.protocol("WM_DELETE_WINDOW", self.callback)
        self.Refresher()
        self.mainloop()

    def Draw(self):
        font = 'Bahnschrift SemiBold SemiConden'
        bg = "#2C2F33"
        for label in list(self.children.values()):
            label.destroy()
        tk.Label(self, text=f"Connected as {self.bot.user}", font=(font, 15), bg=bg,
                 fg='#0ee3ff').pack(anchor='w', side=tk.TOP)
        tk.Label(self, text=f"PING: {int(self.bot.latency * 1000)} ms", font=(font, 10), bg=bg,
                 fg='#0ee3ff').pack(anchor='e', side=tk.BOTTOM)
        user = disnake.utils.get(self.bot.get_all_members(), id=Owner_ID)
        tk.Label(self, text=f"{user}: {available_clients(user)}", font=(font, 10), bg=bg,
                 fg='#0ee3ff').pack(anchor='w', side=tk.BOTTOM)
        tk.Label(self, text=f"Guilds Available ({len(self.bot.guilds)}):", font=(font, 12), bg=bg,
                 fg='#0ee3ff').pack(anchor='w', side=tk.TOP)
        for guild in self.bot.guilds:
            tk.Label(self, text=f"\t{guild.name}: ({guild.id}) ({len(guild.members)} members)", font=(font, 12), bg=bg,
                     fg='#ff867e', ).pack(anchor='w', side=tk.TOP)
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if vc.members:
                    tk.Label(self, text=f"🔊 {vc.name}:", font=(font, 12), bg=bg,
                             fg=f'{colour_gen(guild.id)}', ).pack(anchor='w', side=tk.TOP)
                    for member in vc.members:
                        name = f"{member.display_name} "
                        if not (member.voice.self_deaf or member.voice.deaf):
                            name += "🎧"
                        if not (member.voice.self_mute or member.voice.mute):
                            name += "🎙️"
                        if member.voice.self_stream or member.voice.self_video:
                            name += " 📺"

                        tk.Label(self, text=f"\t{name}", font=(font, 11), bg=bg,
                                 fg=f'{member.colour}', ).pack(anchor='w', side=tk.TOP)
                        tk.Label(self, text=f"\t\t{available_clients(member)}", font=('Bahnschrift', 10), bg=bg,
                                 fg=f'{member.colour}', ).pack(anchor='w', side=tk.TOP)
                        activities = all_activities(member)
                        for key, value in activities.items():
                            if value:
                                tk.Label(self, text=f"\t\t{key}: {value}", font=('Bahnschrift', 10), bg=bg,
                                         fg=f'{member.colour}', ).pack(anchor='w', side=tk.TOP)

    def Refresher(self):
        self.Draw()
        threading.Timer(1, self.Refresher).start()

    def bot_info(self):
        str1 = f"{self.bot.user}  is connected to the following guild:"
        for guild in self.bot.guilds:
            str1 += f"\n\t> {guild.name}: ({guild.id}) with {len(guild.members)} members"
        return str1

    def callback(self):
        self.quit()


class UI(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener('on_ready')
    async def start_gui(self):
        thread = threading.Thread(target=App, args=(self.client,))
        thread.start()
        print("GUI started")


def setup(client: Client):
    client.add_cog(UI(client))
