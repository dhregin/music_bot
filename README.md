# music_bot
discord music bot from nem dhregin // blackmage compendium.

I made this bot because other bots told me to subcsribe and I didn't want to. Then I was like "what if we do x and what if we do y and what if we sing songs in the rain and hold hands" and now here we are.

Ideally I'll be hosting the backbone on a cloud provider of my choice and it will work with several servers. The code here is primarily for audit purposes incase you're wary about what you're adding to your server.

Commands:

?play
?pause
?resume
?stop


Should have adequate caching and multi threading limited to 5 threads but we'll see how it goes.  It will likely need to be expanded and larger server infrastructure provisoined to support it at some point, but currently this is in dev so if it gets overloaded, heh, oopsies.

Add the bot to any server with this link: https://discord.com/oauth2/authorize?client_id=1313639246342651946&permissions=1729521119656256&integration_type=0&scope=bot
As it is in Dev, it may or may not work at any given time (i.e servers down, too much traffic, etc)

# Music Bot Setup Guide

## Prerequisites


If having difficulty importing or download ffmpeg, try it from here.
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz
tar -xf ffmpeg.tar.xz
sudo mv ffmpeg /usr/local/bin/
sudo mv ffprobe /usr/local/bin/

