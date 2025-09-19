import discord
from discord.ext import commands, tasks
from discord.ui import View, Select
from flask import Flask
import threading
import os
import itertools

# ---------------- Config ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_CHANNELS = [1418534707917881525, 1418527229867982908]

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Role Data ----------------
role_categories = {
    "ยืนยันตัวตน": {"🌌 Dreamer": discord.Color.dark_blue()},
    "เพศ": {"♂️ ผู้ชาย": discord.Color.blue(), "♀️ ผู้หญิง": discord.Color.pink(), "⚪ ไม่ระบุ": discord.Color.light_grey()},
    "อายุ": {"🔹 18-": discord.Color.teal(), "🔸 18+": discord.Color.orange(), "🔺 25+": discord.Color.red()},
    "ความสัมพันธ์": {"💖 โสด": discord.Color.green(), "💕 มีแฟนแล้ว": discord.Color.red(), "🤐 เป็นความลับ": discord.Color.purple(), "✨ หัวใจยังว่าง": discord.Color.gold()}
}
zone_roles = {"🎨 Dream Artist": discord.Color.blurple(), "👾 Dream Gamer": discord.Color.dark_purple()}

# ---------------- GIF คงที่ ----------------
THUMBNAIL_GIF = "https://cdn.discordapp.com/attachments/1418349035508465684/1418610929699913770/IMG_20250919_215215.jpg?ex=68cebfe2&is=68cd6e62&hm=d308866d8f09ca6f5cd48764e6f4f9009be28bb2e5ac9b327301365caa84bd2f"
BACKGROUND_GIF = "https://cdn.discordapp.com/attachments/1418349035508465684/1418666984618594314/Dreambg.gif?ex=68cef416&is=68cda296&hm=c1f6f6d2aae376debba8acbc43f8e9b65e64c4ecd10213e950dd0f23079eb83c"

# ---------------- Helpers ----------------
async def set_role(member: discord.Member, role_name: str, category: str):
    guild = member.guild
    roles_in_category = [discord.utils.get(guild.roles, name=r) for r in role_categories[category].keys()]
    for r in roles_in_category:
        if r in member.roles:
            await member.remove_roles(r)
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        await member.add_roles(role)
        return True
    return False

# ---------------- Select Menus ----------------
class RoleSelect(Select):
    def __init__(self, category: str):
        options = [discord.SelectOption(label=r) for r in role_categories[category].keys()]
        super().__init__(placeholder=f"เลือก {category} ของคุณ…", options=options, min_values=1, max_values=1)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        role_name = self.values[0]
        success = await set_role(interaction.user, role_name, self.category)
        if success:
            await interaction.response.send_message(f"✅ คุณได้ยศ **{role_name}** ในหมวด **{self.category}** แล้ว!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ ไม่พบยศ ลองให้แอดมินสร้างก่อนครับ", ephemeral=True)

class ZoneSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=r) for r in zone_roles.keys()]
        super().__init__(placeholder="เลือกโซนของคุณ…", options=options, min_values=1, max_values=len(zone_roles))

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        for r_name in zone_roles.keys():
            role = discord.utils.get(guild.roles, name=r_name)
            if role in member.roles:
                await member.remove_roles(role)
        for role_name in self.values:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)
        await interaction.response.send_message(f"✅ คุณเลือกโซน: {', '.join(self.values)}", ephemeral=True)

class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        for category in role_categories:
            self.add_item(RoleSelect(category))

class ZoneView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ZoneSelect())

# ---------------- Embed Colors ----------------
color_cycle = itertools.cycle([
    discord.Color.red(), discord.Color.orange(), discord.Color.gold(),
    discord.Color.green(), discord.Color.blue(), discord.Color.purple()
])

posted_embeds = {}

# ---------------- Commands ----------------
@bot.command()
async def create_roles(ctx):
    for category, roles in role_categories.items():
        for role_name, color in roles.items():
            if not discord.utils.get(ctx.guild.roles, name=role_name):
                await ctx.guild.create_role(name=role_name, color=color)
    for role_name, color in zone_roles.items():
        if not discord.utils.get(ctx.guild.roles, name=role_name):
            await ctx.guild.create_role(name=role_name, color=color)
    await ctx.send("✅ สร้าง Roles ทั้งหมดเรียบร้อยแล้ว!")

@bot.command()
async def post_roles(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        await ctx.send("❌ คำสั่งนี้ใช้ได้เฉพาะช่องที่กำหนด", delete_after=10)
        return
    embed = discord.Embed(
        title="🌌 Dream Realm – ระบบยศ",
        description="เลือกยศของคุณตามหมวดหมู่ด้านล่าง\n`⚠️ กรุณาเลือกจากล่างขึ้นบนนะคะ`",
        color=next(color_cycle)
    )
    embed.set_thumbnail(url=THUMBNAIL_GIF)
    embed.set_image(url=BACKGROUND_GIF)
    embed.set_footer(text="✨ Dream Realm")
    view = RoleView()
    msg = await ctx.send(embed=embed, view=view)
    posted_embeds[msg.id] = msg

@bot.command()
async def post_zones(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        await ctx.send("❌ คำสั่งนี้ใช้ได้เฉพาะช่องที่กำหนด", delete_after=10)
        return
    embed = discord.Embed(
        title="🎮 Dream Realm – เลือกโซนกิจกรรม",
        description="เลือกโซนที่คุณสนใจ 🎨👾\n✅ เลือกได้หลายโซนตามต้องการ",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=THUMBNAIL_GIF)
    embed.set_footer(text="✨ Dream Realm")
    view = ZoneView()
    msg = await ctx.send(embed=embed, view=view)
    posted_embeds[msg.id] = msg

# ---------------- Rainbow Embed Task ----------------
@tasks.loop(seconds=10)
async def rainbow_embed():
    for msg in posted_embeds.values():
        try:
            embed = msg.embeds[0]
            embed.color = next(color_cycle)
            await msg.edit(embed=embed)
        except:
            continue

# ---------------- On Ready ----------------
@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์แล้ว: {bot.user}")
    rainbow_embed.start()
    activity = discord.Game(name="Dream Realm 🌌")
    await bot.change_presence(status=discord.Status.idle, activity=activity)

# ---------------- Flask Healthcheck ----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running! ✅"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ---------------- Run Flask + Bot ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
