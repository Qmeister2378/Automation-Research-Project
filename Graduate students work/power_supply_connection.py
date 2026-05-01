#!/usr/bin/env python3
"""
SIGLENT SPD 3303C DC Power Supply Control
Triple channel programmable DC power supply automation
"""

import pyvisa
import time

class SiglentSPD:
    """Class to control SIGLENT SPD 3303C Power Supply"""

    def __init__(self):
        self.rm = None
        self.inst = None
        self.connected = False

    def connect(self, max_retries=3):
        """
        Connect to the power supply with retry logic
        
        Args:
            max_retries: Maximum number of connection attempts (default: 3)
        """
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    print(f"  Retry attempt {attempt}/{max_retries}...")
                    time.sleep(2)  # Wait before retry
                
                print("Connecting to SIGLENT SPD 3303C...")
                
                # Close any existing connection first
                if self.inst:
                    try:
                        self.inst.close()
                    except:
                        pass
                    self.inst = None
                
                self.rm = pyvisa.ResourceManager()
                resources = self.rm.list_resources()

                # Find SIGLENT power supply
                spd_resource = None
                for res in resources:
                    if 'SPD' in res or '5168' in res:
                        spd_resource = res
                        break

                if not spd_resource:
                    print("✗ SIGLENT power supply not found!")
                    print(f"  Available resources: {resources}")
                    if attempt < max_retries:
                        continue
                    return False

                # Open connection with specific settings for SPD
                # Use longer timeout and try to clear any stale connections
                self.inst = self.rm.open_resource(
                    spd_resource,
                    timeout=5000  # Increased timeout
                )
                self.inst.read_termination = '\n'
                self.inst.write_termination = '\n'
                
                # Clear any pending errors
                try:
                    self.inst.write('*CLS')  # Clear status
                except:
                    pass

                # Verify connection with longer delay
                time.sleep(0.5)  # Increased delay after opening
                
                # Try to query with timeout handling
                idn = self.inst.query('*IDN?')
                print(f"✓ Connected: {idn.strip()}")
                self.connected = True
                return True

            except Exception as e:
                error_msg = str(e)
                print(f"✗ Connection attempt {attempt} failed: {error_msg}")
                
                # Clean up on error
                if self.inst:
                    try:
                        self.inst.close()
                    except:
                        pass
                    self.inst = None
                
                # If it's a pipe error and not the last attempt, suggest fixes
                if 'Pipe' in error_msg or '32' in error_msg:
                    if attempt < max_retries:
                        print("  Pipe error detected. Trying to recover...")
                        time.sleep(3)  # Longer wait for pipe errors
                    else:
                        print("\n  Troubleshooting steps:")
                        print("  1. Unplug the USB cable from the power supply")
                        print("  2. Wait 5 seconds")
                        print("  3. Plug it back in")
                        print("  4. Make sure no other program is using the device")
                        print("  5. Try running the script again")
                elif attempt < max_retries:
                    time.sleep(1)
        
        return False

    def disconnect(self):
        """Close connection to the instrument"""
        if self.inst:
            self.inst.close()
            self.connected = False
            print("✓ Disconnected")

    def check_errors(self):
        """Check for instrument errors"""
        if not self.connected:
            return "Not connected"
        try:
            error = self.inst.query('SYST:ERR?')
            return error.strip()
        except Exception as e:
            return f"Error checking: {e}"

    # Output Control
    def turn_on_output(self, channel=1):
        """
        Turn on output for specified channel (1, 2, or 3)

        Args:
            channel: Channel number (1, 2, or 3)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        if channel not in [1, 2, 3]:
            print("✗ Invalid channel! Use 1, 2, or 3")
            return False
        try:
            self.inst.write(f'OUTP CH{channel},ON')
            time.sleep(0.1)
            print(f"✓ Channel {channel} output turned ON")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def turn_off_output(self, channel=1):
        """
        Turn off output for specified channel (1, 2, or 3)

        Args:
            channel: Channel number (1, 2, or 3)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        if channel not in [1, 2, 3]:
            print("✗ Invalid channel! Use 1, 2, or 3")
            return False
        try:
            self.inst.write(f'OUTP CH{channel},OFF')
            time.sleep(0.1)
            print(f"✓ Channel {channel} output turned OFF")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    # Voltage Control
    def set_voltage(self, channel=1, voltage=0):
        """
        Set voltage for specified channel

        Args:
            channel: Channel number (1, 2, or 3)
            voltage: Voltage in Volts (0-32V for CH1/CH2, 0-5V for CH3)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        if channel not in [1, 2, 3]:
            print("✗ Invalid channel! Use 1, 2, or 3")
            return False
        try:
            self.inst.write(f'CH{channel}:VOLT {voltage}')
            time.sleep(0.1)
            print(f"✓ Channel {channel} voltage set to {voltage}V")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_voltage_setting(self, channel=1):
        """Get voltage setting for specified channel"""
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'CH{channel}:VOLT?')
            time.sleep(0.1)
            return float(response.strip())
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Current Control
    def set_current(self, channel=1, current=0):
        """
        Set current limit for specified channel

        Args:
            channel: Channel number (1, 2, or 3)
            current: Current in Amps (0-3.2A for CH1/CH2, 0-3.2A for CH3)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        if channel not in [1, 2, 3]:
            print("✗ Invalid channel! Use 1, 2, or 3")
            return False
        try:
            self.inst.write(f'CH{channel}:CURR {current}')
            time.sleep(0.1)
            print(f"✓ Channel {channel} current limit set to {current}A")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_current_setting(self, channel=1):
        """Get current limit setting for specified channel"""
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'CH{channel}:CURR?')
            time.sleep(0.1)
            return float(response.strip())
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Measurement Functions
    def measure_voltage(self, channel=1):
        """
        Measure actual output voltage

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            Measured voltage in Volts
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'MEAS:VOLT? CH{channel}')
            time.sleep(0.1)
            voltage = float(response.strip())
            return voltage
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def measure_current(self, channel=1):
        """
        Measure actual output current

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            Measured current in Amps
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'MEAS:CURR? CH{channel}')
            time.sleep(0.1)
            current = float(response.strip())
            return current
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def measure_power(self, channel=1):
        """
        Calculate actual output power from voltage and current measurements

        Note: Direct power query (MEAS:POWE?) causes USB pipe errors on some units,
        so we calculate it from V*I instead, which is more reliable.

        Args:
            channel: Channel number (1, 2, or 3)

        Returns:
            Calculated power in Watts (V * I)
        """
        if not self.connected:
            return None
        try:
            # Calculate power from voltage and current (avoids USB pipe error)
            voltage = self.measure_voltage(channel)
            current = self.measure_current(channel)

            if voltage is not None and current is not None:
                power = voltage * current
                return power
            return None
        except Exception as e:
            print(f"✗ Error calculating power: {e}")
            return None

    # Combined Setup
    def setup_channel(self, channel=1, voltage=0, current=1.0, output_on=False):
        """
        Configure a channel with voltage, current limit, and optionally turn it on

        Args:
            channel: Channel number (1, 2, or 3)
            voltage: Voltage in Volts
            current: Current limit in Amps
            output_on: Turn on output after configuration (default: False)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False

        print(f"\nConfiguring Channel {channel}:")
        success = True

        # Set voltage
        if not self.set_voltage(channel, voltage):
            success = False

        # Set current limit
        if not self.set_current(channel, current):
            success = False

        # Turn on output if requested
        if output_on and success:
            if not self.turn_on_output(channel):
                success = False

        return success

    def get_channel_status(self, channel=1):
        """
        Get complete status of a channel

        Returns:
            Dictionary with voltage setting, current setting, and measured values
        """
        if not self.connected:
            return None

        try:
            status = {
                'channel': channel,
                'voltage_set': self.get_voltage_setting(channel),
                'current_set': self.get_current_setting(channel),
                'voltage_measured': self.measure_voltage(channel),
                'current_measured': self.measure_current(channel),
                'power_measured': self.measure_power(channel),
            }
            return status
        except Exception as e:
            print(f"✗ Error getting channel status: {e}")
            return None

    def print_channel_status(self, channel=1):
        """Print formatted channel status"""
        status = self.get_channel_status(channel)
        if status:
            print(f"\nChannel {channel} Status:")

            v_set = status['voltage_set']
            print(f"  Voltage Set:  {v_set:.3f}V" if v_set is not None else "  Voltage Set:  N/A")

            c_set = status['current_set']
            print(f"  Current Set:  {c_set:.3f}A" if c_set is not None else "  Current Set:  N/A")

            v_meas = status['voltage_measured']
            print(f"  Voltage Meas: {v_meas:.3f}V" if v_meas is not None else "  Voltage Meas: N/A")

            c_meas = status['current_measured']
            print(f"  Current Meas: {c_meas:.3f}A" if c_meas is not None else "  Current Meas: N/A")

            p_meas = status['power_measured']
            if p_meas is not None:
                print(f"  Power Meas:   {p_meas:.3f}W")
            else:
                # Calculate power manually if measurement fails
                if v_meas is not None and c_meas is not None:
                    calc_power = v_meas * c_meas
                    print(f"  Power Calc:   {calc_power:.3f}W (calculated)")
                else:
                    print(f"  Power Meas:   N/A")

    def turn_off_all_outputs(self):
        """Turn off all channel outputs"""
        print("\nTurning off all outputs...")
        for ch in [1, 2, 3]:
            self.turn_off_output(ch)


def demo():
    """Demonstration of power supply control"""

    print("=" * 70)
    print("SIGLENT SPD 3303C Power Supply Demo")
    print("=" * 70)
    print()

    # Create instance and connect
    ps = SiglentSPD()

    if not ps.connect():
        print("Failed to connect!")
        print("\nIf you see 'Pipe error', try:")
        print("1. Unplug the USB cable from the power supply")
        print("2. Wait 5 seconds")
        print("3. Plug it back in")
        print("4. Run this script again")
        return

    print()
    print("-" * 70)
    print("Demo: Setting up Channel 1 with 5V, 1A limit")
    print("-" * 70)

    # Configure Channel 1: 5V, 1A current limit
    ps.setup_channel(channel=1, voltage=5.0, current=1.0, output_on=True)

    # Wait for output to stabilize
    time.sleep(0.5)

    # Display status
    ps.print_channel_status(channel=1)

    print("\nOutput is now ON. Channel 1 should show 5V")
    print("Press Enter to turn off and exit...")
    input()

    # Turn off all outputs
    ps.turn_off_all_outputs()

    # Disconnect
    print()
    ps.disconnect()

    print("\nDemo complete!")


if __name__ == "__main__":
    demo()
