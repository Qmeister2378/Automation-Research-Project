#!/usr/bin/env python3
"""
SIGLENT SDG 2042X Control Script
Uses python-usbtmc for reliable USB communication
"""

import usbtmc
import time


# SDG 2042X USB IDs: Vendor=0xF4EC (62700), Product=0x1102 (4354)
SDG_VENDOR_ID = 0xF4EC
SDG_PRODUCT_ID = 0x1102


class USBTMCWrapper:
    """Wrapper around usbtmc.Instrument to match pyvisa interface"""

    def __init__(self, instrument):
        self._inst = instrument

    def write(self, command):
        try:
            self._inst.write(command)
            time.sleep(0.1)
        except Exception as e:
            # If write fails, try flushing and retrying once
            try:
                self.flush()
                time.sleep(0.1)
                self._inst.write(command)
                time.sleep(0.1)
            except:
                raise e

    def query(self, command):
        # Use write + read separately (ask() has buffer issues on SDG2042X)
        self._inst.write(command)
        time.sleep(0.1)
        return self._inst.read()

    def read_raw(self, size=1024):
        return self._inst.read_raw(size)

    def flush(self):
        """Drain any stale data from the USB read buffer"""
        old_timeout = self._inst.timeout
        self._inst.timeout = 0.2  # Short timeout for flush
        for _ in range(10):
            try:
                self._inst.read_raw(1024)
            except:
                break
            time.sleep(0.05)
        self._inst.timeout = old_timeout

    def close(self):
        self._inst.close()


class SiglentSDG:
    """Class to control SIGLENT SDG function generator"""

    def __init__(self):
        self.rm = None
        self.inst = None
        self.connected = False

    def connect(self, max_retries=3):
        """
        Connect to the function generator using python-usbtmc

        Args:
            max_retries: Maximum number of connection attempts (default: 3)
        """
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    print(f"  Retry attempt {attempt}/{max_retries}...")
                    time.sleep(3)

                print("Connecting to SIGLENT SDG 2042X...")

                # Close any existing connection
                if self.inst:
                    try:
                        self.inst.close()
                    except:
                        pass
                    self.inst = None

                # Connect using usbtmc directly
                raw_inst = usbtmc.Instrument(SDG_VENDOR_ID, SDG_PRODUCT_ID)
                raw_inst.timeout = 15  # Increased timeout for slow operations

                # Wrap it so the rest of the code works the same
                self.inst = USBTMCWrapper(raw_inst)

                # Flush any stale data left from previous sessions
                self.inst.flush()
                time.sleep(0.3)

                # Verify connection
                idn = self.inst.query('*IDN?')
                idn_str = idn.strip()
                print(f"✓ Connected: {idn_str}")

                if 'Siglent' not in idn_str and 'SDG' not in idn_str.upper():
                    print(f"  Warning: IDN looks garbled, retrying...")
                    self.inst.close()
                    self.inst = None
                    if attempt < max_retries:
                        continue
                    else:
                        return False

                self.connected = True
                return True

            except Exception as e:
                error_msg = str(e)
                print(f"✗ Connection attempt {attempt} failed: {error_msg}")

                if self.inst:
                    try:
                        self.inst.close()
                    except:
                        pass
                    self.inst = None

                if attempt >= max_retries:
                    print("\n  Troubleshooting steps:")
                    print("  1. Unplug the USB cable from the function generator")
                    print("  2. Wait 5 seconds")
                    print("  3. Plug it back in")
                    print("  4. Make sure no other program is using the device")
                    print("  5. Run the script again")

        return False

    def disconnect(self):
        """Close connection to the instrument"""
        if self.inst:
            try:
                self.inst.close()
            except:
                pass
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
    
    def test_connection(self):
        """Test if the connection is still alive by sending a simple query"""
        if not self.connected or not self.inst:
            return False
        try:
            # Try a simple query with short timeout
            old_timeout = None
            if hasattr(self.inst, '_inst') and hasattr(self.inst._inst, 'timeout'):
                old_timeout = self.inst._inst.timeout
                self.inst._inst.timeout = 2
            idn = self.inst.query('*IDN?')
            if old_timeout is not None and hasattr(self.inst, '_inst'):
                self.inst._inst.timeout = old_timeout
            return True
        except:
            return False
    
    def reconnect(self):
        """Attempt to reconnect to the function generator"""
        print("  Attempting to reconnect to function generator...")
        self.connected = False
        if self.inst:
            try:
                self.inst.close()
            except:
                pass
            self.inst = None
        return self.connect(max_retries=2)

    # Channel Output Control
    def turn_on_output(self, channel=1, max_retries=3):
        """Turn on output for specified channel (1 or 2)"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        
        # Flush any stale data and wait for device to be ready
        try:
            self.inst.flush()
        except:
            pass
        time.sleep(0.3)  # Give device time to process previous commands
        
        for attempt in range(1, max_retries + 1):
            try:
                # Test connection before attempting write
                if attempt > 1:
                    if not self.test_connection():
                        print("  Connection lost, attempting reconnect...")
                        if not self.reconnect():
                            return False
                        time.sleep(0.5)
                
                self.inst.write(f'C{channel}:OUTP ON')
                time.sleep(0.2)  # Small delay after write
                print(f"✓ Channel {channel} output turned ON")
                return True
            except Exception as e:
                error_msg = str(e)
                if 'timeout' in error_msg.lower() or '60' in error_msg:
                    # Timeout error - try reconnecting
                    if attempt < max_retries:
                        wait_time = attempt * 0.5
                        print(f"✗ Error: {error_msg}")
                        print(f"  Connection may be unstable, reconnecting...")
                        if self.reconnect():
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"  Reconnection failed, retrying in {wait_time:.1f}s...")
                            time.sleep(wait_time)
                    else:
                        print(f"✗ Error: {error_msg}")
                        print(f"  Failed after {max_retries} attempts")
                        return False
                elif attempt < max_retries:
                    wait_time = attempt * 0.5
                    print(f"✗ Error: {error_msg}")
                    print(f"  Retrying in {wait_time:.1f}s... (attempt {attempt}/{max_retries})")
                    time.sleep(wait_time)
                    try:
                        self.inst.flush()
                    except:
                        pass
                else:
                    print(f"✗ Error: {error_msg}")
                    print(f"  Failed after {max_retries} attempts")
                    return False
        return False

    def turn_off_output(self, channel=1, max_retries=2):
        """Turn off output for specified channel (1 or 2)"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        
        for attempt in range(1, max_retries + 1):
            try:
                self.inst.write(f'C{channel}:OUTP OFF')
                time.sleep(0.1)
                print(f"✓ Channel {channel} output turned OFF")
                return True
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries:
                    print(f"✗ Error: {error_msg}")
                    print(f"  Retrying... (attempt {attempt}/{max_retries})")
                    time.sleep(0.5)
                else:
                    print(f"✗ Error: {error_msg}")
                    return False
        return False

    def get_output_state(self, channel=1, max_retries=2):
        """Get output state for specified channel"""
        if not self.connected:
            return None
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.inst.query(f'C{channel}:OUTP?')
                return response.strip()
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries:
                    time.sleep(0.3)
                else:
                    print(f"✗ Error: {error_msg}")
                    return None
        return None

    # Waveform Configuration
    def set_sine_wave(self, channel=1, frequency=1000, amplitude=1.0, offset=0):
        """
        Set a sine wave output

        Args:
            channel: Channel number (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Volts
            offset: DC offset in Volts
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            cmd = f'C{channel}:BSWV WVTP,SINE,FRQ,{frequency}HZ,AMP,{amplitude}V,OFST,{offset}V'
            self.inst.write(cmd)
            print(f"✓ Channel {channel} set to SINE: {frequency}Hz, {amplitude}V, {offset}V offset")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def set_square_wave(self, channel=1, frequency=1000, amplitude=1.0, offset=0, duty=50):
        """
        Set a square wave output

        Args:
            channel: Channel number (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Volts
            offset: DC offset in Volts
            duty: Duty cycle in percent (0-100)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            cmd = f'C{channel}:BSWV WVTP,SQUARE,FRQ,{frequency}HZ,AMP,{amplitude}V,OFST,{offset}V,DUTY,{duty}'
            self.inst.write(cmd)
            print(f"✓ Channel {channel} set to SQUARE: {frequency}Hz, {amplitude}V, {duty}% duty")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def set_ramp_wave(self, channel=1, frequency=1000, amplitude=1.0, offset=0, symmetry=50):
        """
        Set a ramp/triangle wave output

        Args:
            channel: Channel number (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Volts
            offset: DC offset in Volts
            symmetry: Symmetry in percent (0-100)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            cmd = f'C{channel}:BSWV WVTP,RAMP,FRQ,{frequency}HZ,AMP,{amplitude}V,OFST,{offset}V,SYM,{symmetry}'
            self.inst.write(cmd)
            print(f"✓ Channel {channel} set to RAMP: {frequency}Hz, {amplitude}V, {symmetry}% symmetry")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def set_dc_level(self, channel=1, voltage=0):
        """
        Set DC output level

        Args:
            channel: Channel number (1 or 2)
            voltage: DC voltage level
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            cmd = f'C{channel}:BSWV WVTP,DC,OFST,{voltage}V'
            self.inst.write(cmd)
            print(f"✓ Channel {channel} set to DC: {voltage}V")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_waveform_info(self, channel=1):
        """Get current waveform settings"""
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:BSWV?')
            return response.strip()
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def set_frequency(self, channel=1, frequency=1000, max_retries=3):
        """Change frequency without affecting other parameters"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        
        # Flush and wait before frequency change
        try:
            self.inst.flush()
        except:
            pass
        time.sleep(0.2)
        
        for attempt in range(1, max_retries + 1):
            try:
                # Test connection if retrying
                if attempt > 1:
                    if not self.test_connection():
                        print("  Connection lost, attempting reconnect...")
                        if not self.reconnect():
                            return False
                        time.sleep(0.5)
                
                cmd = f'C{channel}:BSWV FRQ,{frequency}HZ'
                self.inst.write(cmd)
                time.sleep(0.2)  # Wait for device to process
                print(f"✓ Channel {channel} frequency set to {frequency}Hz")
                return True
            except Exception as e:
                error_msg = str(e)
                if 'timeout' in error_msg.lower() or '60' in error_msg:
                    if attempt < max_retries:
                        wait_time = attempt * 0.5
                        print(f"✗ Error: {error_msg}")
                        print(f"  Connection may be unstable, reconnecting...")
                        if self.reconnect():
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"  Reconnection failed, retrying in {wait_time:.1f}s...")
                            time.sleep(wait_time)
                    else:
                        print(f"✗ Error: {error_msg}")
                        return False
                elif attempt < max_retries:
                    wait_time = attempt * 0.5
                    time.sleep(wait_time)
                    try:
                        self.inst.flush()
                    except:
                        pass
                else:
                    print(f"✗ Error: {error_msg}")
                    return False
        return False

    def set_amplitude(self, channel=1, amplitude=1.0):
        """Change amplitude without affecting other parameters"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            cmd = f'C{channel}:BSWV AMP,{amplitude}V'
            self.inst.write(cmd)
            print(f"✓ Channel {channel} amplitude set to {amplitude}V")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False


def demo():
    """Demonstration of function generator control"""

    print("=" * 60)
    print("SIGLENT SDG 2042X Automation Demo")
    print("=" * 60)
    print()

    # Create instance and connect
    fg = SiglentSDG()

    if not fg.connect():
        print("Failed to connect!")
        return

    print()
    print("-" * 60)
    print("Demo: Setting up Channel 1 with 1kHz sine wave")
    print("-" * 60)

    # Configure Channel 1: 1kHz sine wave, 2V amplitude
    fg.set_sine_wave(channel=1, frequency=1000, amplitude=2.0, offset=0)

    # Turn on output
    fg.turn_on_output(channel=1)

    # Check current settings
    print("\nCurrent Channel 1 settings:")
    print(fg.get_waveform_info(channel=1))

    print("\nOutput is now ON. You should see a 1kHz, 2V sine wave on Channel 1")
    print("Press Enter to continue...")
    input()

    # Change frequency
    print("\nChanging frequency to 5kHz...")
    fg.set_frequency(channel=1, frequency=5000)
    time.sleep(1)

    print("Press Enter to continue...")
    input()

    # Change to square wave
    print("\nChanging to square wave at 2kHz...")
    fg.set_square_wave(channel=1, frequency=2000, amplitude=2.0, duty=50)
    time.sleep(1)

    print("Press Enter to turn off output and exit...")
    input()

    # Turn off output
    fg.turn_off_output(channel=1)

    # Disconnect
    print()
    fg.disconnect()

    print("\nDemo complete!")


if __name__ == "__main__":
    demo()
