# terminal-dangerous-writer

A terminal-based writing app that **deletes everything** if you stop typing for too long.

Inspired by [The Most Dangerous Writing App](https://www.mostdangerouswritingapp.com) — brought to your terminal with no browser required.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

## How it works

Start typing. Don't stop. If you pause for more than 5 seconds, everything you've written is gone. The status bar counts down in real time — green means you're safe, yellow means hurry up, red means you're about to lose it all.

Press `Ctrl+C` at any time to quit and save your work to a file.

## Requirements

- Python 3.10+
- macOS or Linux (uses `termios` / `tty` — not compatible with Windows)

No external dependencies.

## Usage

```bash
python3 dangerous_writer.py
```

### Configuration

Edit the constants at the top of the file:

| Variable | Default | Description |
|---|---|---|
| `TIMEOUT` | `5.0` | Seconds of silence before deletion |
| `WARN_AT` | `2.0` | Seconds remaining when the bar turns red |
| `SAVE_ON_EXIT` | `True` | Save to file on Ctrl+C |
| `OUTPUT_FILE` | `dangerous_output.txt` | Where to save your writing |

## License

[MIT](LICENSE)
