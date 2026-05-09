#!/usr/bin/env python3
"""
Test file for DFRobot MAX30102 Heart Rate and Oximeter Sensor (SEN0344)
Uses the DFRobot_BloodOxygen_S Python library for Raspberry Pi.

Requirements:
    - Library cloned from https://github.com/DFRobot/DFRobot_BloodOxygen_S
    - I2C enabled on Raspberry Pi (raspi-config > Interfacing Options > I2C)
    - Sensor wired via I2C (default address: 0x57)
    - smbus2 installed: pip install smbus2

Usage:
    python3 test_sensor.py
"""

import sys
import time

# The DFRobot_BloodOxygen_S.py library must be in the same directory
# or on your PYTHONPATH (found at python/raspberry/ in the repo).
try:
    from DFRobot_BloodOxygen_S import DFRobot_BloodOxygen_S_I2C
except ImportError:
    print("ERROR: DFRobot_BloodOxygen_S library not found.")
    print("Clone the repo and run this script from python/raspberry/:")
    print("  git clone https://github.com/DFRobot/DFRobot_BloodOxygen_S")
    print("  cd DFRobot_BloodOxygen_S/python/raspberry")
    sys.exit(1)

# ── Configuration ────────────────────────────────────────────────────────────
I2C_BUS     = 1      # /dev/i2c-1 (standard on Raspberry Pi)
I2C_ADDRESS = 0x57   # Default I2C address for SEN0344
DURATION    = 90     # How long to collect data, in seconds
READ_INTERVAL = 1.0  # Seconds between readings
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 45)
    print("  DFRobot MAX30102 Sensor Test (SEN0344)")
    print("=" * 45)
    print(f"  I2C bus:     {I2C_BUS}")
    print(f"  I2C address: {hex(I2C_ADDRESS)}")
    print(f"  Duration:    {DURATION} seconds")
    print("=" * 45)

    # Initialise sensor over I2C
    sensor = DFRobot_BloodOxygen_S_I2C(I2C_BUS, I2C_ADDRESS)

    print("\nInitialising sensor...")
    while not sensor.begin():
        print("  begin() failed — check wiring and I2C address. Retrying in 1 s...")
        time.sleep(1)
    print("  Sensor initialised successfully.\n")

    # Start data collection
    print("Starting data collection — place finger on sensor now.")
    print("(Heart rate updates every ~4 seconds; keep finger still)\n")
    sensor.sensorStartCollect()

    start_time = time.time()
    reading_num = 0

    try:
        while time.time() - start_time < DURATION:
            # Fetch latest heart rate and SpO2 values into _sHeartbeatSPO2
            sensor.getHeartbeatSPO2()

            heart_rate  = sensor._sHeartbeatSPO2.Heartbeat  # beats per minute
            spo2        = sensor._sHeartbeatSPO2.SPO2       # percentage
            temperature = sensor.getTemperature_C()          # °C
            elapsed     = time.time() - start_time

            reading_num += 1
            print(f"[{elapsed:5.1f}s] #{reading_num:3d} | "
                  f"Heart Rate: {heart_rate:3d} bpm | "
                  f"SpO2: {spo2:3d}% | "
                  f"Board Temp: {temperature:.1f} °C")

            time.sleep(READ_INTERVAL)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected — stopping early.")

    finally:
        # Always stop collection cleanly
        sensor.sensorEndCollect()
        print("\nSensor stopped. Test complete.")
        print(f"Total readings collected: {reading_num}")


if __name__ == "__main__":
    main()