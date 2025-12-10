# 🎱 Discord Bingo Prediction Bot

A Discord bot designed to manage **Bingo Prediction events**. It allows users to submit their prediction images privately via temporary channels (ticket system), which are then automatically forwarded to a secure admin channel.

## ✨ Features

* **Event Setup:** Admins can create a permanent submission button using `/setup_bingo`.
* **Ticket System:** Clicking the button creates a private temporary channel for the user.
* **Privacy Focused:** Only the user and admins can see the submission process.
* **Image Forwarding:** User submissions are automatically forwarded to a specific Admin-only channel.
* **Auto-Cleanup:** Temporary channels are deleted after submission or if inactive for 10 minutes.
* **Smart Permissions:** Handles role hierarchy checks to prevent permission errors.
* **Docker Ready:** Includes `Dockerfile` and `docker-compose.yml` for easy deployment.

## 🛠️ Prerequisites

* Python 3.10+
* Docker & Docker Compose (Optional, for server deployment)
* A Discord Bot Token with **Message Content Intent** enabled.

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <your-project-folder>
```

### 2. Configure Environment Variables
Create a .env file in the root directory and add the following:
```env
DISCORD_TOKEN=your_bot_token_here
DISCORD_APP_ID=your_application_id_here
TARGET_CHANNEL_ID=your_admin_channel_id_here
```
  Note: TARGET_CHANNEL_ID must be the integer ID of the text channel where images will be sent.

### 3. Run Locally (Python)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

### 4. Run with Docker (Recommended for VPS)
```bash
# Build and run in background
docker compose up -d --build

# Check logs
docker compose logs -f
```

___

## 🎮 Usage Guide

### For Admins
1.  Navigate to the text channel where you want the event announcement to appear.
2.  Type the slash command:
    ```
    /setup_bingo event_name:"Your Event Name"
    ```
3.  The bot will generate an Embed message with a **"Submit Prediction"** button.

### For Users
1.  Click the **"Submit Prediction"** button.
2.  A private temporary channel (e.g., `#bingo-username`) will be created for you.
3.  Upload your **Bingo Image** into that channel.
4.  The bot will show a preview. Click **"Confirm & Close Ticket"**.
5.  Your image will be forwarded to the staff, and the temporary channel will be deleted automatically.

---

## 🔐 Permissions & Troubleshooting (Important!)

If the bot fails to create channels or forward images, please check the following settings in your Discord Server.

### 1. Fix "Missing Permissions" (Error 50013)
**Cause:** The Bot's role is lower than the User's role in the hierarchy.
**Solution:**
* Go to **Server Settings > Roles**.
* Drag the **BOT's Role** to the **TOP** of the list (It must be higher than the roles of the users/admins attempting to submit).

### 2. Fix "Missing Access" (Error 50001)
**Cause:** The bot cannot see or write to the destination Admin channel.
**Solution:**
* Go to the `TARGET_CHANNEL_ID` channel (e.g., `#bingo-submit-admin-only`).
* Click **Edit Channel > Permissions**.
* Add the Bot's role and allow these permissions:
    * ✅ **View Channel** (Crucial)
    * ✅ Send Messages
    * ✅ Attach Files
    * ✅ Embed Links

### 3. Temp Channel Creation Issues
**Cause:** The bot lacks permission in the specific Category.
**Solution:**
* Right-click the **Category** where the public bingo channel is located.
* Go to **Edit Category > Permissions**.
* Add the Bot's role and allow:
    * ✅ **Manage Channels**
    * ✅ **Manage Permissions**
    * ✅ View Channels

---

## 📂 Project Structure

Here is the recommended file structure for the project:

```text
.
├── .env                   # Stores sensitive data (Token, App ID, IDs) - NEVER COMMIT THIS
├── .gitignore             # Tells Git which files to ignore (e.g., .env, venv/)
├── .dockerignore          # Tells Docker which files to skip during build
├── docker-compose.yml     # Configuration to run the bot with Docker Compose
├── Dockerfile             # Instructions to build the Python environment container
├── main.py                # The main source code of the bot
└── requirements.txt       # List of required Python libraries (discord.py, python-dotenv)
```

---

## 👤 Author

**Sirawitch Butryojantho**
* **Developer & System Architect**
* Created for the **Phantom Blade Zero** global community.
* Github: [@poonnyworld](https://github.com/poonnyworld/)
* Discord: `poonrighthere#7210`
