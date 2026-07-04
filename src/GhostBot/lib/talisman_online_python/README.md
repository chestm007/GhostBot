# Talisman Online Python

Scripts, functions and modules I use to create bots in the Talisman Online game.

### Website
[https://tonyrogerio.com.br](https://tonyrogerio.com.br)

### Youtube
[https://www.youtube.com/@tonyr0xx](https://www.youtube.com/@tonyr0xx)

### PIX
`dae13311-4775-4973-849f-ad7d17ccbe8c`

### PAYPAL
`tonirogerio7@gmail.com`

### DISCORD
`tonirogerio7`

## Pointers Module

**Set the process ID before testing the functions.**

```python
# Testing the code
pid = 972  # Replace 972 with the correct process PID
```

## Keyboard Module

**Example of how to send a key to the game:**

1. Set the window's `hwnd`. Example: `hwnd = 972`. This will be the target, i.e., the game window that will receive the command.
2. Set a key. Example: `next_target = 'TAB'`

**Command to send the TAB key using the `keyboard.py` module:**
```python
send(hwnd, next_target)
```
## Mouse Module

**Set the target window and import the module.**
```python
import mouse

hwnd = 0x000E0398
xPos, yPos = 75, 75

mouse.left(hwnd, xPos, yPos)
```

## Deleter.py

**Just the function I use to delete items, note that it's configured for my use, you'll need to configure the mouse and keyboard commands according to your project**


