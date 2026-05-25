#!/usr/bin/env python3
"""
Dual DFRobot MAX30102 Heart Rate and Oximeter Sensor test (SEN0344).
Each sensor runs on its own I2C bus because the MAX30102 has a fixed
I2C address (0x57) and cannot be changed via hardware.

Wiring
------
Sensor 1 → I2C-1  : SDA=GPIO2 (Pin 3),  SCL=GPIO3 (Pin 5)
Sensor 2 → I2C-3  : SDA=GPIO6 (Pin 31), SCL=GPIO7 (Pin 26)

Note: On Raspberry Pi 5, dtoverlay=i2c3-pi5 defaults to GPIO6/GPIO7.
GPIO4/GPIO5 are NOT valid for I2C-3 on Pi 5.

    ┌────────────────────────────────────────────────────────────────────┐
    │               RASPBERRY PI 5 — 40-pin GPIO Header                  │
    │                                                                    │
    │    S1 = Sensor 1 (I2C-1)    S2 = Sensor 2 (I2C-3)                │
    │    ══●══ = wire connected    ───── = pin unused                    │
    ├────────────────────────────────────────────────────────────────────┤
    │                                                                    │
    │  LEFT (odd)                       RIGHT (even)                    │
    │                                                                    │
    │  S1·3V3 ══●══ [ 1]  3.3V  │   5V   [ 2] ─────                   │
    │  S1·SDA ══●══ [ 3]  SDA1  │   5V   [ 4] ─────                   │
    │  S1·SCL ══●══ [ 5]  SCL1  │   GND  [ 6] ══●══ S1·GND            │
    │         ───── [ 7] GPIO4  │   TXD  [ 8] ─────                   │
    │         ───── [ 9]   GND  │   RXD  [10] ─────                   │
    │         ───── [11] GPIO17 │ GPIO18 [12] ─────                   │
    │         ───── [13] GPIO27 │   GND  [14] ══●══ S2·GND            │
    │         ───── [15] GPIO22 │ GPIO23 [16] ─────                   │
    │  S2·3V3 ══●══ [17]  3.3V  │ GPIO24 [18] ─────                   │
    │         ───── [19]  MOSI  │   GND  [20] ─────                   │
    │         ───── [21]  MISO  │ GPIO25 [22] ─────                   │
    │         ───── [23]  SCLK  │   CE0  [24] ─────                   │
    │         ───── [25]   GND  │   CE1  [26] ══●══ S2·SCL (GPIO7)    │
    │         ───── [27] ID_SD  │ ID_SC  [28] ─────                   │
    │         ───── [29] GPIO5  │   GND  [30] ─────                   │
    │  S2·SDA ══●══ [31] GPIO6  │ GPIO12 [32] ─────                   │
    │         ───── [33] GPIO13 │   GND  [34] ─────                   │
    │         ───── [35] GPIO19 │ GPIO16 [36] ─────                   │
    │         ───── [37] GPIO26 │ GPIO20 [38] ─────                   │
    │         ───── [39]   GND  │ GPIO21 [40] ─────                   │
    │                                                                    │
    └────────────────────────────────────────────────────────────────────┘

    SENSOR 1 (SEN0344)                    SENSOR 2 (SEN0344)
    ──────────────────────────────        ──────────────────────────────
    Sensor pin │ Pi pin │ Pi name         Sensor pin │ Pi pin │ Pi name
    ───────────┼────────┼────────         ───────────┼────────┼────────
      3V3      │   1    │ 3.3V              3V3       │  17    │ 3.3V
      SDA      │   3    │ GPIO2 (SDA1)      SDA       │  31    │ GPIO6 (SDA3)
      SCL      │   5    │ GPIO3 (SCL1)      SCL       │  26    │ GPIO7 (SCL3)
      GND      │   6    │ GND               GND       │  14    │ GND
      RST      │   —    │ leave NC          RST       │   —    │ leave NC
      NC       │   —    │ leave NC          NC        │   —    │ leave NC

Enable I2C-3 on Raspberry Pi 5 (one-time setup):
    sudo nano /boot/firmware/config.txt
    # Add under [all]: dtoverlay=i2c3-pi5
    # (no extra parameters — defaults to GPIO6/GPIO7)
    sudo reboot
    ls /dev/i2c-*          # expects: i2c-1  i2c-3
    i2cdetect -y 1         # expects 0x57 on bus 1
    i2cdetect -y 3         # expects 0x57 on bus 3

Requirements:
    DFRobot_BloodOxygen_S.py and DFRobot_RTU.py (same directory as this script)
      git clone https://github.com/DFRobot/DFRobot_BloodOxygen_S
      cp DFRobot_BloodOxygen_S/python/raspberry/DFRobot_BloodOxygen_S.py .
      cp DFRobot_BloodOxygen_S/python/raspberry/DFRobot_RTU.py .
    smbus2    → pip install smbus2
    pyserial  → pip install pyserial
    RPi.GPIO  → sudo apt install python3-lgpio && pip install rpi-lgpio

Usage:
    python3 test_sensor.py
"""

import sys
import time
import threading

try:
    # Library renamed class to lowercase 'i2c' in newer versions; alias for clarity
    from DFRobot_BloodOxygen_S import DFRobot_BloodOxygen_S_i2c as DFRobot_BloodOxygen_S_I2C
except ImportError as e:
    print(f"ERROR: DFRobot_BloodOxygen_S library not found ({e}).")
    print("Copy these two files into the same directory as this script:")
    print("  git clone https://github.com/DFRobot/DFRobot_BloodOxygen_S")
    print("  cp DFRobot_BloodOxygen_S/python/raspberry/DFRobot_BloodOxygen_S.py .")
    print("  cp DFRobot_BloodOxygen_S/python/raspberry/DFRobot_RTU.py .")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────────────────────
SENSORS = [
    {"label": "Sensor-1", "bus": 1, "address": 0x57},  # I2C-1 (GPIO2/3, pins 3/5)
    {"label": "Sensor-2", "bus": 3, "address": 0x57},  # I2C-3 (GPIO6/7, pins 31/26)
]
DURATION      = 90   # seconds to collect data
READ_INTERVAL = 1.0  # seconds between readings
# ─────────────────────────────────────────────────────────────────────────────

# Shared lock so print calls from both threads don't interleave
_print_lock = threading.Lock()


def log(label: str, msg: str) -> None:
    with _print_lock:
        print(f"[{label}] {msg}")


def sensor_worker(cfg: dict, stop_event: threading.Event) -> None:
    """Initialise one sensor and stream readings until stop_event is set."""
    label  = cfg["label"]
    sensor = DFRobot_BloodOxygen_S_I2C(cfg["bus"], cfg["address"])

    log(label, f"Initialising on I2C-{cfg['bus']} @ {hex(cfg['address'])} …")
    while not sensor.begin():
        log(label, "begin() failed — check wiring. Retrying in 1 s …")
        time.sleep(1)
        if stop_event.is_set():
            return
    log(label, "Initialised. Starting collection — place finger on sensor.")

    sensor.sensor_start_collect()
    reading_num = 0
    start_time  = time.time()

    try:
        while not stop_event.is_set():
            sensor.get_heartbeat_SPO2()
            hr      = sensor.heartbeat  # bpm
            spo2    = sensor.SPO2       # %
            temp    = sensor.get_temperature_c()  # °C
            elapsed = time.time() - start_time
            reading_num += 1

            log(label,
                f"{elapsed:6.1f}s  #{reading_num:3d}  |  "
                f"HR: {hr:3d} bpm  |  SpO2: {spo2:3d} %  |  Temp: {temp:.1f} °C")

            # Sleep in small increments so we react to stop_event quickly
            for _ in range(int(READ_INTERVAL / 0.1)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)

    finally:
        sensor.sensor_end_collect()
        log(label, f"Stopped. Total readings collected: {reading_num}")


def main() -> None:
    print("=" * 55)
    print("  Dual DFRobot MAX30102 Test  (SEN0344 × 2)")
    print("=" * 55)
    for cfg in SENSORS:
        print(f"  {cfg['label']:10s}  I2C-{cfg['bus']}  addr {hex(cfg['address'])}")
    print(f"  Duration:   {DURATION} s")
    print("=" * 55 + "\n")

    stop_event = threading.Event()

    threads = [
        threading.Thread(
            target=sensor_worker,
            args=(cfg, stop_event),
            name=cfg["label"],
            daemon=True,
        )
        for cfg in SENSORS
    ]

    try:
        for t in threads:
            t.start()

        # Main thread just waits out the duration
        time.sleep(DURATION)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt — stopping sensors …")

    finally:
        stop_event.set()       # signal both worker threads to finish
        for t in threads:
            t.join(timeout=5)  # give each thread up to 5 s to clean up

    print("\nAll sensors stopped. Test complete.")


if __name__ == "__main__":
    main()
