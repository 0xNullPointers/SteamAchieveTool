# Steam Achievement Downloader

A Python script to download achievement data and icons of Steam games from either SteamDB or Steam Community.

## Features

- Fetch achievement data from SteamDB or Steam Community
- Download achievement icons in original quality
- Save achievement metadata in JSON format
- Multithreaded download for faster performance
- Silent mode for automation scripts

## Installation

### Using the Executable (.exe)
No installation required. Simply download `achievements.exe` and run it from the command line.

### Using Python Script
1. Ensure you have Python 3.9 or higher installed
2. Install required packages:
```bash
pip install -r requirements.txt
```
3. Download `achievements.py`

## Usage

### Basic Command Structure

```bash
# Using executable
achievements.exe <appid> [options]

# Using Python script
python achievements.py <appid> [options]
```

### Arguments

- `appid` (required): The Steam Application ID of the game
  - e.g., for https://store.steampowered.com/app/730/, the appid is 730

### Options

- `--steam`: Use Steam Community as the data source instead of SteamDB

- `--silent` or `-s`: Suppress all console output

### Examples

```bash
# Basic usage (fetches from SteamDB)
achievements.exe 730

# Silent mode with Steam Community
achievements.exe 730 --steam --silent
```

## Limitations

- SteamDB method may not work for all games
- Some games may have region-locked achievements
- Hidden achievements may have limited information
- Rate limiting may occur with many requests

## Credits

This tool uses data from:
- [SteamDB](https://steamdb.info/)
- [Steam Community](https://steamcommunity.com/)

Steam and all related properties are trademarks of Valve Corporation.