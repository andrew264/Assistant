# Andrew's Assistant

A multipurpose Discord bot built using the `discord.py` library. It includes a variety of features such as games, information commands, moderation tools, music playback, and more.

---
## Features

### Administration

*   **DM Relay:** Relays direct messages (DMs) to the bot owner, allowing for communication with users through the bot.
*   **Eval Command:** Executes Python code directly within Discord (owner-only).
*   **Lavalink Node Manager:** Updates and manages Lavalink nodes for music playback.
*   **Manage Extensions:** Load, unload, reload, sync, and desync bot extensions/cogs.
*   **Update Avatar:** Updates the bot's avatar (owner-only).

### Error Handling

*   **Error Handler:** Handles command errors gracefully, providing user-friendly feedback and logging detailed error information.

### Games

*   **Funny:** Fun commands like `/kill`, `/pp`, `/flames`.
*   **Hand Cricket:** Play a game of hand cricket using button-based UI.
*   **Rock Paper Scissors:** Play rock-paper-scissors against other users or the bot.
*   **TicTacToe:** Play TicTacToe with another user or an AI opponent.
*   **Voting System:** Set up and manage polls/voting using an Elo rating system.

### Information

*   **Add Intro:** Allows users to add a short introduction about themselves.
*   **Assistant Info:** Displays information and statistics about the bot.
*   **Avatar:** Shows a user's avatar.
*   **Guild Info:** Shows information and statistics about the Discord server (guild).
*   **User Info:** Shows detailed information about a user, including their activity, last seen time, etc.

### Miscellaneous

*   **Audio Clips:** Plays various audio clips in voice channels.
*   **Delete Messages:** Deletes messages in bulk. Has a command to delete messages by user ID or specific content.
*   **Reddit Commands:** Fetches and displays memes and NSFW content from Reddit.
*   **Translator:** Translates text using Google Translate, including inline translation within messages.
*   **Urban Dictionary:** Looks up word definitions from Urban Dictionary.
*   **Utilities:** General utility commands like `echo` and `ping`.

### Music

*   **Commands:** Standard music commands like `/play`, `/skip`, `/stop`, `/loop`, `/volume`, `/skipto`, `/seek`.
*   **Filters:** Applies audio filters like _nightcore_, _vaporwave_, _bass boost_, _treble boost_, and _8D_.
*   **Lyrics:** Fetches lyrics from Genius based on the currently playing song, a search query, or Spotify activity.
*   **Music Tasks:** Handles automatic music bot activity updates, disconnects when idle, and plays the next track in the queue.
*   **Now Playing:** Shows detailed information about the currently playing song in a persistent, interactive UI.

### Tasks

*   **Color Roles:** Manages color roles using button-based UI.
*   **Last Seen:** Tracks when users were last seen online, typing, or in voice channels.
*   **Surveillance:** Logs edited/deleted messages, nickname changes, status updates, voice channel activity, and more.
___
## Dependencies

The bot uses the following main Python libraries:

*   `discord.py`: The Discord API wrapper.
*   `wavelink`: A Lavalink wrapper for music playback.
*   `motor`: For asynchronous interaction with MongoDB.
*   `asyncpraw`: Asynchronous Python Reddit API Wrapper.
*   `lyricsgenius`: Access song lyrics from Genius.
*   `googletrans`: For text translation.
*   `aiohttp`: For making HTTP requests.
*   `cachetools`: For in-memory caching.
*   `thefuzz`: For fuzzy string matching.
*   `pyyaml`: For YAML parsing.
*   `pydantic`: For data validation and settings management.
*   `psutil`: For retrieving system and process information.

All dependencies are listed in `requirements.txt`.

---
## Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/andrew264/Assistant
    cd Assistant
    ```
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Create a config file:**
    *   Create a `config.yaml` file in the `config` directory. You can use `config/example.yaml` as a template.
4. **Configure settings:**
    *   Fill in the required values in `config.yaml`:
        *   `DISCORD_TOKEN`: Your Discord bot token.
        *   `OWNER_ID`: Your Discord user ID.
        *   `HOME_GUILD_ID`: The ID of your main Discord server.
        *   `DM_RECIPIENTS_CATEGORY`: ID of category channel where DMs will be relayed.
        *   `MONGO_URI`: Your MongoDB connection string (optional, but required for some features).
        *   `LAVA_CONFIG`: Lavalink configuration (if you're using music features).
        *   `REDDIT_CONFIG`: Reddit API credentials (if you're using Reddit commands).
        *   `GENIUS_TOKEN`: Genius API token (if you're using the lyrics command).
        *   `LOGGING_GUILDS`: Guilds and channels for logging (required for surveillance).
    *   Set other optional configuration values as needed.
5. **Configure Audio Clips (optional):**
    *   Place audio clip files (`.mp3`) inside the `resources/audio_clips` directory, organized in subfolders named after guild IDs where the clips will be available.
6. **Run the bot:**
    ```bash
    python main.py
    ```
### Notes:

*   **Permissions:** Make sure the bot has the necessary permissions in your Discord server to perform its functions (e.g., manage messages, manage roles, connect to voice channels, create webhooks, etc.).
*   **MongoDB:** Some features, like user introductions and last seen tracking, require a MongoDB database. If you don't configure `MONGO_URI`, those features will be disabled.
*   **Lavalink:** For music features to work, you need a running Lavalink server and have to configure its details in `config.yaml`.
*   **API Keys:** Certain features like Reddit integration, Genius lyrics, and Tenor GIFs require API keys. You need to obtain those keys and add them to the `config.yaml`.
*   **Owner-only Commands:** Some commands are restricted to the bot owner (specified by `OWNER_ID`).
*   **DM Relay:** DMs sent to the bot will be relayed to channels under the category specified by `DM_RECIPIENTS_CATEGORY`. The channels must have a topic with format `USERID:user_id` for it to work correctly.

---
## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. (You might want to create a LICENSE file).
