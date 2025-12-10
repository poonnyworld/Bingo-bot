import discord
import os
import asyncio
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))
APP_ID = os.getenv('DISCORD_APP_ID')

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class BingoBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=APP_ID
        )

    async def setup_hook(self):
        self.add_view(SubmissionView()) 
        await self.tree.sync()
        print("✅ Slash commands synced!")

bot = BingoBot()

# --- 3. View for Admin to Delete Channel ---
class AdminDeleteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🗑️ Delete Channel", style=discord.ButtonStyle.danger)
    async def delete_channel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await interaction.channel.delete()

# --- 2. View for User to Confirm Submission ---
class UserReviewView(View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="✅ Confirm & Close Ticket", style=discord.ButtonStyle.primary)
    async def confirm_close(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You cannot perform this action.", ephemeral=True)

        button.disabled = True
        await interaction.response.edit_message(view=self)

        await interaction.channel.send(f"🔒 **Confirmed!** Closing ticket in **10 seconds**...")
        
        await asyncio.sleep(10)

        try:
            if interaction.guild.me.top_role > self.user.top_role:
                await interaction.channel.set_permissions(self.user, overwrite=None)
            else:
                await interaction.channel.send("⚠️ Note: Cannot auto-remove user due to role hierarchy (Admin/Staff).")
        except Exception as e:
            print(f"Error removing permissions: {e}")

        # Notify Admin to Delete
        embed = discord.Embed(
            title="🔒 Ticket Locked",
            description=f"Ticket closed by {self.user.mention}.\nAdmin, please delete this channel when ready.",
            color=discord.Color.dark_grey()
        )
        await interaction.channel.send(embed=embed, view=AdminDeleteView())

# --- 1. Main Submission Button ---
class SubmissionView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📤 Submit Prediction", style=discord.ButtonStyle.green, custom_id="bingo_submit_btn")
    async def submit_button_callback(self, interaction: discord.Interaction, button: Button):
        
        user = interaction.user
        guild = interaction.guild
        
        # --- Create Channel Logic ---
        base_name = f"bingo-{user.name}"
        channel_name = "".join(c for c in base_name if c.isalnum() or c in "-_").lower()

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"⚠️ You already have an open ticket: {existing_channel.mention}. Please finish that one first.", 
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Permissions Logic
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        # Safety Check: Only add user overwrite if Bot > User
        if guild.me.top_role > user.top_role:
            overwrites[user] = discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=True, 
                attach_files=True,
                read_message_history=True 
            )
        
        current_category = interaction.channel.category 
        try:
            temp_channel = await guild.create_text_channel(
                name=channel_name, 
                overwrites=overwrites, 
                category=current_category,
                reason="Bingo Submission Temp Channel"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error creating channel: {e}", ephemeral=True)
            return
        
        # Notify User
        if guild.me.top_role <= user.top_role:
             await interaction.followup.send(f"✅ **Temp channel created!** {temp_channel.mention}\n(Note: As an Admin/Staff, you should see it automatically)", ephemeral=True)
        else:
             await interaction.followup.send(f"✅ **Temp channel created!** Please go to {temp_channel.mention} and send your bingo there", ephemeral=True)

        # --- Embed Instructions inside Temp Channel ---
        instruction_embed = discord.Embed(
            title="📸 Upload Your Prediction",
            description=f"Welcome {user.mention}!\n\nPlease **upload your Bingo image** in this channel.\nOnce uploaded, you will be asked to confirm.",
            color=discord.Color.gold()
        )
        instruction_embed.set_footer(text="⏳ This channel will close automatically in 10 minutes if inactive.")
        
        await temp_channel.send(embed=instruction_embed)

        # --- Wait for Image Logic ---
        def check(m):
            return m.channel.id == temp_channel.id and m.author.id == user.id and len(m.attachments) > 0

        try:
            message = await bot.wait_for('message', check=check, timeout=600.0)
            
            try:
                target_channel = bot.get_channel(TARGET_CHANNEL_ID)
                if not target_channel:
                    raise Exception(f"Admin Channel ID {TARGET_CHANNEL_ID} not found.")

                file = await message.attachments[0].to_file()
                
                # Admin Log
                admin_embed = discord.Embed(title="🎲 New Bingo Submission", color=discord.Color.blue())
                admin_embed.set_author(name=user.display_name, icon_url=user.avatar.url if user.avatar else None)
                admin_embed.set_image(url=f"attachment://{file.filename}")
                admin_embed.set_footer(text=f"User ID: {user.id}")
                admin_embed.timestamp = discord.utils.utcnow()

                sent_message = await target_channel.send(embed=admin_embed, file=file)
                
                # User Feedback inside Temp Channel
                feedback_embed = discord.Embed(
                    title="✅ Submission Received!",
                    description="You have sent the image below. Is this correct?",
                    color=discord.Color.green()
                )
                if sent_message.attachments:
                    feedback_embed.set_image(url=sent_message.attachments[0].url)
                
                await temp_channel.send(content=user.mention, embed=feedback_embed, view=UserReviewView(user))

            except Exception as e:
                print(f"Error sending image: {e}")
                error_embed = discord.Embed(
                    title="❌ Error Processing Image",
                    description=f"Could not forward your image to the admin channel.\n**Reason:** `{e}`",
                    color=discord.Color.red()
                )
                await temp_channel.send(embed=error_embed)

        except asyncio.TimeoutError:
            try:
                await temp_channel.send(f"{user.mention} ⏰ **Time's up!** No image detected. Closing channel...")
                await asyncio.sleep(3)
                await temp_channel.delete()
            except:
                pass

# --- Setup Command with Parameters (Reward Removed) ---
@bot.tree.command(name="setup_bingo", description="Setup the Bingo submission button with event details")
@app_commands.describe(
    event_name="Name of the event (e.g., 'Bingo v3.0')"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_bingo(interaction: discord.Interaction, event_name: str): # <--- ลบ reward ออกจากตรงนี้
    
    embed = discord.Embed(
        title=f"🔮 Bingo Prediction: {event_name}",
        description="Click the button below to submit your prediction image!\nA private channel will be created for you.",
        color=discord.Color.gold()
    )
    
    # ลบ field ของ Reward ออก
    embed.add_field(name="📋 Instructions", value="1. Click 'Submit Prediction'\n2. Upload your image in the new channel\n3. Confirm submission", inline=False)

    await interaction.response.send_message(embed=embed, view=SubmissionView())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

bot.run(TOKEN)