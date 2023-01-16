
## Setup

### USB UART Driver
When you plug in the ESP32 to your USB port, you need to make sure you see it as a device. On mac you need to install a driver.

https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads

When that gets installed, you get a tty, like this: `/dev/tty.usbserial-130`

screen can be used to connect to the tty it provides.

```
screen /dev/tty.usbserial-130 115200
```

Only one process can attach to that TTY at once. You need to kill the screen when exiting, not detach. So use `Ctrl+A` then `Ctrl+\` to detach and kill. `screen -ls` should show no sockets when everything's killed.

### micropython firmware install

Then this is what's used to flash firmware.
https://github.com/espressif/esptool

You can pip install esptool to get this in the venv

then...

```
(venv) user@system ~/src/esp32 $ esptool.py chip_id
esptool.py v4.4
Found 4 serial ports
Serial port /dev/cu.usbserial-130
Connecting....
Detecting chip type... Unsupported detection protocol, switching and trying again...
Connecting....
Detecting chip type... ESP32
Chip is ESP32-D0WD-V3 (revision v3.0)
Features: WiFi, BT, Dual Core, 240MHz, VRef calibration in efuse, Coding Scheme None
Crystal is 40MHz
MAC: 24:4c:ab:f7:a0:1c
Uploading stub...
Running stub...
Stub running...
Warning: ESP32 has no Chip ID. Reading MAC instead.
MAC: 24:4c:ab:f7:a0:1c
Hard resetting via RTS pin...
(venv) user@system ~/src/esp32 $
```

steps to flash with micropython using esptool:

```
(venv) user@system ~/src/esp32 $ esptool.py --chip esp32 --port /dev/cu.usbserial-130 erase_flash
esptool.py v4.4
Serial port /dev/cu.usbserial-130
Connecting....
Chip is ESP32-D0WD-V3 (revision v3.0)
Features: WiFi, BT, Dual Core, 240MHz, VRef calibration in efuse, Coding Scheme None
Crystal is 40MHz
MAC: 24:4c:ab:f7:a0:1c
Uploading stub...
Running stub...
Stub running...
Erasing flash (this may take a while)...
Chip erase completed successfully in 13.6s
Hard resetting via RTS pin...
(venv) user@system ~/src/esp32 $
```

Then flash with micropython. I pulled down the generic esp32 binary from here.
https://micropython.org/download/esp32/

```
(venv) user@system ~/src/esp32 $ esptool.py --chip esp32 --port /dev/cu.usbserial-130 write_flash -z 0x1000 esp32-20220618-v1.19.1.bin
esptool.py v4.4
Serial port /dev/cu.usbserial-130
Connecting....
Chip is ESP32-D0WD-V3 (revision v3.0)
Features: WiFi, BT, Dual Core, 240MHz, VRef calibration in efuse, Coding Scheme None
Crystal is 40MHz
MAC: 24:4c:ab:f7:a0:1c
Uploading stub...
Running stub...
Stub running...
Configuring flash size...
Flash will be erased from 0x00001000 to 0x0017efff...
Compressed 1560976 bytes to 1029132...
Wrote 1560976 bytes (1029132 compressed) at 0x00001000 in 99.9 seconds (effective 125.0 kbit/s)...
Hash of data verified.
Leaving...
Hard resetting via RTS pin...
```

## Sending code to the ESP32 from your IDE
You should be able to run with ampy. pip install adafruit-ampy to get this binary in the venv.

```
(venv) user@system ~/src/esp32 $ ampy --port /dev/tty.usbserial-130 run main.py
your mother
(venv) user@system ~/src/esp32 $ 
```

You can add `-n` to the run command above to make it return immediately and not look for output.

## WebREPL
You can connect to the esp's python terminal over the network. Connect to wifi in the code. Then open the webrepl html locally and connect to it in a browser.

If you want to have the esp boot with this enabled, you can do that by getting on the esp's python shell and

`import webrepl_setup`

That's going to ask if you want to default to ON at boot or not. Then ask for a password to use when connecting to this interface over the network.

# References

https://docs.micropython.org/en/latest/esp32/quickref.html
https://learn.adafruit.com/micropython-basics-esp8266-webrepl/access-webrepl
