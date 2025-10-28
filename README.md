# GhostBot #

Opensource bot for [Talisman Online](http://www.talismanonline.com) written in python.

Only works on windows at the moment.  
I have tried running on linux via wine, the UI works, but the server doesn't find any of the TO clients.

### Contributions are very welcome ###

I figured a few people could collaborate on this and make something useful for 
everyone with complete control to add or remove features as they wish. Everyone
seems to have crazy UO scripts or their favourite closed source bot app.

### What Works: ###

- Fully configurable, per char config via the UI
- Attack functionality
- Mana / HP Regen
- Scheduled pet re-spawning / feeding
- Fairy logic to heal the team
- Scheduled Buff's
- Automatic sell to NPC
- Item deletion

### How do i use this thing???

Install python, clone this repository, and `pip install .` in the root directory.

- `ghost-bot-server` - Runs the backend.
- `ghost-bot-client` - The UI, you'll do everything in here.

> [!NOTE]
> 
> Not a great user experience, I know... I havent sorted out building this into actual executables yet.

### Roadmap

check out the [issues](https://github.com/chestm007/GhostBot/issues) page

### Special Thanks

[tonirogerio](https://github.com/tonirogerio) - For absolutely invaluable help with finding the right memory pointers