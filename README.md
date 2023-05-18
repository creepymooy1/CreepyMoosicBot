# CreepyMoosicBot

CreepyMoosicBot is a private Discord bot built using discord.py that allows users to play and queue music in their Discord servers.

## Features

As of 5/8/23, CreepyMoosicBot supports the following features:

- `!play [url or query]`: Plays a song from YouTube.
- `!stop`: Stops playing and clears the song queue.
- `!skip`: Skips the current song.
- `!pause`: Pauses the current song.
- `!resume`: Resumes playing the current song.
- `!queue`: Displays the current song queue.
- `!removequeue [position]`: Removes a song from the queue at the specified position.
- `!playing`: Displays the currently playing song.
- `!ping`: Pings the bot to check if it's responsive.
- `!search [query]`: Provides the top 10 URLs for a given YouTube query.
- `!announce [message]` (Only for authorized users): Sends a message to the "general" channel of all servers. (Hidden command for maintenance purposes)

## Installation

To run CreepyMoosicBot, follow these steps:

1. Clone this repository to your local machine.
2. Install the required dependencies by running the following command:

`pip install -r requirements.txt`

The bot should now be online and ready to use!

## Usage

Once the bot is running and connected to your Discord server, you can start using the available commands mentioned in the Features section. Simply type the commands in a text channel where the bot is present.
