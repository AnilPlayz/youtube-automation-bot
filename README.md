# 🎮 Automated Minecraft Facts YouTube Shorts Creator

An AI-powered, fully automated pipeline that generates and publishes viral **Minecraft Facts YouTube Shorts** on a schedule (every 3 hours) using **GitHub Actions**.

---

## ✨ Features

- 🤖 **100% Unique AI Scripts**: Uses Google Gemini to generate viral, high-retention Minecraft trivia scripts with hooks, twists, and CTAs. History is saved to prevent duplicate topics.
- 🗣️ **Realistic AI Voiceover**: Uses Microsoft Edge neural TTS (`edge-tts`) with word-level boundary sync for rapid caption animation.
- 🧑‍🎨 **Custom Player Skin & Avatar**: Displays your Minecraft player character (via username or `skin.png`) with animated talking/bobbing reaction overlays.
- 💬 **Viral Shorts Subtitles**: Rapid word-by-word pop-up captions styled in high-visibility bright yellow with dark outlines and active-word highlights.
- 💧 **Custom Watermark**: Customizable channel handle / logo badge overlay.
- 🎵 **Audio Mixing & Ducking**: Background music automatically mixed and ducked under voiceover.
- 🚀 **Zero-Maintenance 3-Hour Automation**: Runs on GitHub Actions cron (`0 */3 * * *`), builds the video in the cloud, publishes it to YouTube, and commits history.

---

## 📁 Repository Structure

```
paro/
├── .github/workflows/
│   └── youtube_shorts_cron.yml   # 3-hour scheduled GitHub Actions workflow
├── assets/
│   ├── gameplay/                 # Minecraft background MP4 gameplay videos
│   ├── music/                    # Background music MP3 tracks
│   ├── fonts/                    # Custom .ttf fonts for subtitles
│   └── skins/                    # Player skin (skin.png or cached 3D renders)
├── config/
│   └── config.yaml               # Master settings (watermark, player, voice, etc.)
├── data/
│   └── used_topics.json          # Topic memory to prevent duplicate videos
├── src/
│   ├── config_loader.py          # Configuration manager
│   ├── script_generator.py       # AI script creation with Gemini API
│   ├── tts_engine.py             # Neural TTS & word timestamp extraction
│   ├── skin_renderer.py          # Minecraft 3D skin fetcher & animator
│   ├── video_composer.py         # 9:16 Video assembly & subtitle renderer
│   ├── youtube_uploader.py       # Headless YouTube Data API v3 uploader
│   └── setup_oauth.py            # Local helper to obtain YouTube OAuth tokens
├── main.py                       # CLI & Pipeline entrypoint
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment secrets template
└── README.md
```

---

## ⚡ Quick Start (Local Testing)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and add your Gemini API Key (get a free key at [Google AI Studio](https://aistudio.google.com)):
```env
GEMINI_API_KEY=your_gemini_api_key_here
MINECRAFT_USERNAME=YourMinecraftName
WATERMARK_TEXT=@YourChannelHandle
```

### 3. Generate a Test Short (Dry Run)
```bash
python main.py --dry-run
```
Your rendered 9:16 Short MP4 will be saved in `output/` ready to watch!

---

## ⚙️ Customization (`config/config.yaml`)

Edit [`config/config.yaml`](config/config.yaml) to customize your Shorts:

| Setting | Description | Default |
| :--- | :--- | :--- |
| `channel.watermark_text` | Channel handle watermark | `@MineCraftShorts` |
| `channel.watermark_position` | Watermark corner | `top_right` |
| `player.minecraft_username` | Your Minecraft in-game username | `Steve` |
| `player.render_type` | `isometric_bust`, `2d_avatar`, `full_body` | `isometric_bust` |
| `player.avatar_animation` | `talking_bob`, `breathe`, `static` | `talking_bob` |
| `voice.tts_voice` | AI Voice (`en-US-ChristopherNeural`, etc.) | `en-US-ChristopherNeural` |
| `voice.tts_rate` | Speech speed (+10% to +15% recommended) | `+12%` |
| `youtube.privacy_status` | Video visibility (`public`, `unlisted`, `private`) | `public` |

---

## ☁️ GitHub Actions Setup (Automated 3-Hour Publishing)

To run the automation in the cloud every 3 hours:

### Step 1: Push This Code to a GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit of Minecraft Shorts Automation"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 2: Obtain YouTube API Credentials
1. Visit [Google Cloud Console](https://console.cloud.google.com) and create a project.
2. Enable **YouTube Data API v3**.
3. Under **OAuth consent screen**, select **External** and set Publishing Status to **Testing** or **In Production**.
4. Under **Credentials**, create an **OAuth client ID** (Application type: **Desktop App**).
5. Run the local OAuth helper to get your Refresh Token:
   ```bash
   python src/setup_oauth.py
   ```

### Step 3: Add GitHub Secrets & Variables
Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**:

#### Repository Secrets (Required):
- `GEMINI_API_KEY`: Your Gemini API key from [AI Studio](https://aistudio.google.com).
- `YOUTUBE_CLIENT_ID`: Your Google OAuth Client ID.
- `YOUTUBE_CLIENT_SECRET`: Your Google OAuth Client Secret.
- `YOUTUBE_REFRESH_TOKEN`: The refresh token generated by `setup_oauth.py`.

#### Repository Variables (Optional):
- `MINECRAFT_USERNAME`: Your Minecraft username (e.g. `Dream`, `MumboJumbo`, or your own).
- `WATERMARK_TEXT`: Your channel watermark handle (e.g. `@MinecraftFactsDaily`).

### Step 4: Grant Workflow Write Permissions
Go to **Settings** -> **Actions** -> **General** -> **Workflow permissions** -> Select **Read and write permissions** (so GitHub Actions can push updated `data/used_topics.json`).

### Step 5: Test via GitHub Actions UI
1. Go to the **Actions** tab on your GitHub repository.
2. Select **YouTube Shorts 3-Hour Automation**.
3. Click **Run workflow** -> Select `dry_run: true` (or leave false to publish directly to YouTube!).

---

## 🎬 Custom Gameplay & Music

- **Gameplay footage**: Drop vertical or horizontal Minecraft gameplay videos into `assets/gameplay/`. The composer will automatically select random clips and crop them to 9:16 vertical.
- **Background music**: Drop chill C418-style / lofi beats into `assets/music/`.
- **Player Skin file**: Alternatively, place your `skin.png` into `assets/skins/skin.png` instead of using a username.
