# BUG: Suppressed error while changing names

import discord
import datetime
import dotenv
import os
from json import loads
from typing import Union
import time
import sys
import aiohttp
import asyncio
sys.path.append('..')
import kurokami
from discord.ext import tasks, commands

class Query():
    def __init__(self, name, cid, delay: float):
        self.name = name
        self.channel = cid
        self.delay = delay
        self.cb = tasks.loop(seconds=delay)(self._cb_impl)

    async def _cb_impl(self):
        s = time.time()
        await self.query_cb()
        print(f"{self.name}, time taken: {time.time() - s}")
    
    async def query_cb(self):
        item_name = self.name
        folder = today = datetime.datetime.now().strftime("%Y_%m_%d")
        timestamp = datetime.datetime.now().strftime("%H_%M_%S")
        new_filename = f'./output/{folder}/{timestamp}_{item_name}.csv'
        csv_files = []
        if not os.path.exists(f'./output/{folder}'):
            if not os.path.exists('./output'):
                os.makedirs('./output')
            else: # Possibly a new date
                os.makedirs(f'./output/{folder}') # create for today, after making a snapshot of before
        output_dir = './output/'
        all_folders = [name for name in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, name))]
        folder_dates = sorted([datetime.datetime.strptime(folder, "%Y_%m_%d").date() for folder in all_folders])
    
        while True: # Get the latest folder
            if len(folder_dates) == 0:
                print("No latest file found. Probably is the first time running this script, skipping comparison")
                folder = None
                break
            else:
                folder = str(folder_dates.pop(-1)).replace("-", "_")
                csv_files = [file for file in os.listdir(f'./output/{folder}') if file.endswith(f'{item_name}.csv')]
                if len(csv_files) != 0:
                    break
                elif folder != today:
                    print(f"{folder} does not contain any CSV files")
                    # os.rmdir(f'./output/{folder}')

        if folder:
            folder = str(folder).replace("-", "_") # overwrite the current folder with the latest date known, for getting the last csv file
            sorted_files = sorted(csv_files)
            if sorted_files:
                last_file_path = os.path.join(f'./output/{folder}', sorted_files[-1])
            
            new_results = await kurokami.main({"i": item_name, "p": 1, "o": new_filename, "t": False, "s": False, "c": last_file_path})
        else:
            new_results = await kurokami.main({"i": item_name, "p": 1, "o": new_filename, "t": False, "s": False})

        for result in new_results:
            seller_name, seller_url, item_name, item_img, item_url, time_posted, condition, price = result
            if len(price) == 1:
                price = price[0]
            else:
                price = f"{price[0]} ~~{price[1]}~~"
            cat_fact = await fetch_cat_fact()
            emb=discord.Embed(title=item_name, url=item_url, 
            description=f"# {price}\nPosted: {time_posted}\nSeller: [{seller_name}]({seller_url})\nCondition: {condition}", 
            color=0x00ff00) # timestamp=datetime.datetime.now()
            # emb.set_author(name=client.get_user(494483880410349595).name, icon_url=client.get_user(494483880410349595).display_avatar)
            emb.set_author(name="speckly")
            emb.set_footer(text=cat_fact)
            emb.set_image(url=item_img)
            CHANNEL = client.get_channel(self.channel)
            await CHANNEL.send(embed=emb)

class MyClient(discord.Client): # TODO: Use commands.Bot which is painful to transition to
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.tasks = {}

    async def on_ready(self):
        print(f'{timestamp()}: Logged in as {client.user} (ID: {client.user.id})')
    
    async def setup_hook(self):
        MY_GUILD = discord.Object(id=1093515712900902912)
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
    

dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
client = MyClient(intents=intents)

def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def fetch_cat_fact():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://catfact.ninja/fact", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    cat_fact = data["fact"]
                else:
                    cat_fact = f"Meowerror: HTTP status {response.status}"
    except aiohttp.ClientError as e:
        cat_fact = f"Meowerror: {e}"
    return cat_fact

@client.tree.command(description='Create thread')
@discord.app_commands.describe(item="Name of the item to query", delay="Delay in seconds")
async def create_thread(interaction: discord.Interaction, item: str, delay: int):
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    else:
        await interaction.response.send_message(f"Creating thread: {item}")
        cid = interaction.channel_id
        thread = Query(name=item, cid=cid, delay=delay)
        thread.cb.start()

        last_task = client.tasks.get(item)
        if last_task:
            await interaction.followup.send(f"Warning: this thread ```{item}``` exists in channel {last_task.channel}. This existing query will be cancelled")
            last_task.cb.cancel()
        for stored_item in client.tasks:
            if client.tasks[stored_item].channel == cid:
                await interaction.followup.send(f"Warning: another thread ```{stored_item}``` uses this channel. Consider terminating either to avoid conflict")
        client.tasks[item] = thread
        await interaction.followup.send(content=f"{item} thread created successfully")

@client.tree.command(description='View threads')
async def view_threads(interaction: discord.Interaction):
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    elif client.tasks != {}:
        out_str = "\n".join([f"{item} in channel_id {client.tasks[item].channel}" for item in client.tasks])
        await interaction.response.send_message(out_str)
    else:
        await interaction.response.send_message("No tasks are running")

@client.tree.command(description='Stop thread')
@discord.app_commands.describe(name='Name of the thread to stop, must be existing, get list of threads with /view_threads')
async def delete_thread(interaction: discord.Interaction, name: str=''):
    if interaction.user.id != 494483880410349595:
        await interaction.response.send_message("Not authorised to use this")
        print(f"Unauthorised access: {interaction.user.id}")
    elif name == '':
        await interaction.response.send_message("Missing item name, stopping all current threads in this channel instead")
        cid = interaction.channel_id
        for stored_item in client.tasks:
            if client.tasks[stored_item].channel == cid:
                client.tasks[stored_item].cb.cancel()
                client.tasks[stored_item] = None
                await interaction.followup.send(f"Stopped thread {stored_item} located in current channel")
        
    else:
        thread = client.tasks.get(name)
        if thread:
            thread.cb.cancel()
            await interaction.response.send_message(f"Thread {name} stopped successfully")
            del client.tasks[name]
        else:
            await interaction.response.send_message(f"Thread {name} does not exist. View list of threads with /view_threads")
        
if __name__ == "__main__":
    client.run(os.getenv('TOKEN'))