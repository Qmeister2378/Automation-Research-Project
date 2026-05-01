#!/usr/bin/env python3
"""
SIGLENT SDS1104X HD Digital Oscilloscope Control
4-channel oscilloscope automation
"""

import pyvisa
import time

class SiglentSDS:
    """Class to control SIGLENT SDS1104X HD Oscilloscope"""

    def __init__(self):
        self.rm = None
        self.inst = None
        self.connected = False

    def connect(self, resource=None):
        """
        Connect to the oscilloscope

        Args:
            resource: Optional specific resource string (e.g., 'TCPIP::192.168.1.100::INSTR')
                     If None, will auto-detect
        """
        try:
            print("Connecting to SIGLENT SDS1104X HD...")
            self.rm = pyvisa.ResourceManager()

            if resource:
                target_resource = resource
            else:
                resources = self.rm.list_resources()
                target_resource = None

                print(f"Found resources: {resources}")

                for res in resources:
                    res_upper = res.upper()
                    # Look for SDS oscilloscope identifiers
                    # Product ID 4117 is for SDS oscilloscopes
                    # Exclude SDG (function generator) resources
                    if 'SDG' in res_upper:
                        continue  # Skip function generators
                    if ('SDS' in res_upper or '4117' in res or '1104' in res):
                        target_resource = res
                        print(f"Found oscilloscope: {target_resource}")
                        break

                if not target_resource:
                    print("X Oscilloscope not found!")
                    print("\nAvailable resources:")
                    for res in resources:
                        print(f"  - {res}")
                    print("\nFor LAN connection, use:")
                    print("  scope.connect('TCPIP::192.168.1.100::INSTR')")
                    return False

            # Open connection
            self.inst = self.rm.open_resource(
                target_resource,
                timeout=10000
            )
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.chunk_size = 102400  # Large chunk for waveform data

            # Verify connection
            time.sleep(0.3)
            idn = self.inst.query('*IDN?')
            print(f"Connected: {idn.strip()}")
            self.connected = True
            return True

        except Exception as e:
            print(f"X Connection failed: {e}")
            return False

    def disconnect(self):
        """Close connection to the instrument"""
        if self.inst:
            self.inst.close()
            self.connected = False
            print("Disconnected")

    def check_errors(self):
        """Check for instrument errors"""
        if not self.connected:
            return "Not connected"
        try:
            # Use CMR? for command error register
            error = self.inst.query('CMR?')
            return error.strip()
        except Exception as e:
            return f"Error checking: {e}"

    # ========== Acquisition Control ==========
    def run(self):
        """Start acquisition"""
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            self.inst.write('TRMD AUTO')
            time.sleep(0.1)
            print("Acquisition running")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def stop(self):
        """Stop acquisition"""
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            self.inst.write('STOP')
            time.sleep(0.1)
            print("Acquisition stopped")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_bandwidth_limit(self, channel=1, enabled=True):
        """
        Enable/disable 20MHz bandwidth limit to reject high-frequency noise.

        Args:
            channel: Channel number (1-4)
            enabled: True = BWL ON (20MHz limit), False = BWL OFF (full bandwidth)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            state = 'ON' if enabled else 'OFF'
            self.inst.write(f'C{channel}:BWL {state}')
            time.sleep(0.1)
            print(f"Channel {channel} bandwidth limit: {state} (20MHz)")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_acquisition_mode(self, mode='AVERAGE', count=32):
        """
        Set acquisition mode

        Args:
            mode: 'AVERAGE', 'SAMPLING', or 'HIRES'
            count: Number of averages (4, 8, 16, 32, 64, 128, 256) — only used in AVERAGE mode
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            if mode.upper() == 'AVERAGE':
                self.inst.write(f'ACQW AVERAGE,{count}')
                print(f"Acquisition mode: AVERAGE x{count}")
            elif mode.upper() == 'HIRES':
                self.inst.write('ACQW HRES')
                print("Acquisition mode: HiRes")
            else:
                self.inst.write('ACQW SAMPLING')
                print("Acquisition mode: SAMPLING")
            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def clear_sweeps(self):
        """Clear acquisition averaging buffer (CLSW)"""
        if not self.connected:
            return False
        try:
            self.inst.write('CLSW')
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"X Error clearing sweeps: {e}")
            return False

    def wait_for_trigger(self, timeout=5.0):
        """
        Poll until oscilloscope acquires at least one new waveform (INR? bit 0).

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if triggered within timeout, False otherwise
        """
        if not self.connected:
            return False
        start = time.time()
        while time.time() - start < timeout:
            try:
                inr = self.inst.query('INR?')
                val = int(inr.strip().replace('INR', '').strip())
                if val & 1:  # bit 0 = new signal acquired
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        print("  WARNING: Trigger wait timed out")
        return False

    def single(self):
        """Single trigger acquisition"""
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            self.inst.write('TRMD SINGLE')
            time.sleep(0.1)
            print("Single trigger armed")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def auto_setup(self):
        """Perform auto setup"""
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            self.inst.write('ASET')
            time.sleep(2)  # Auto setup takes time
            print("Auto setup complete")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    # ========== Channel Control ==========
    def enable_channel(self, channel=1):
        """
        Enable a channel

        Args:
            channel: Channel number (1-4)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        if channel not in [1, 2, 3, 4]:
            print("X Invalid channel! Use 1-4")
            return False
        try:
            self.inst.write(f'C{channel}:TRA ON')
            time.sleep(0.1)
            print(f"Channel {channel} enabled")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def disable_channel(self, channel=1):
        """
        Disable a channel

        Args:
            channel: Channel number (1-4)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        if channel not in [1, 2, 3, 4]:
            print("X Invalid channel! Use 1-4")
            return False
        try:
            self.inst.write(f'C{channel}:TRA OFF')
            time.sleep(0.1)
            print(f"Channel {channel} disabled")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_channel_scale(self, channel=1, scale=1.0):
        """
        Set vertical scale (volts/div)

        Args:
            channel: Channel number (1-4)
            scale: Volts per division (e.g., 0.001 for 1mV/div, 1 for 1V/div)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        if channel not in [1, 2, 3, 4]:
            print("X Invalid channel! Use 1-4")
            return False
        try:
            self.inst.write(f'C{channel}:VDIV {scale}V')
            time.sleep(0.1)
            print(f"Channel {channel} scale set to {scale}V/div")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def get_channel_scale(self, channel=1):
        """Get vertical scale for a channel"""
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:VDIV?')
            time.sleep(0.1)
            return response.strip()
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def set_channel_offset(self, channel=1, offset=0):
        """
        Set vertical offset

        Args:
            channel: Channel number (1-4)
            offset: Offset in Volts
        """
        if not self.connected:
            print("X Not connected!")
            return False
        if channel not in [1, 2, 3, 4]:
            print("X Invalid channel! Use 1-4")
            return False
        try:
            self.inst.write(f'C{channel}:OFST {offset}V')
            time.sleep(0.1)
            print(f"Channel {channel} offset set to {offset}V")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_channel_coupling(self, channel=1, coupling='DC'):
        """
        Set channel coupling

        Args:
            channel: Channel number (1-4)
            coupling: 'DC', 'AC', or 'GND'
        """
        if not self.connected:
            print("X Not connected!")
            return False
        if channel not in [1, 2, 3, 4]:
            print("X Invalid channel! Use 1-4")
            return False
        coupling = coupling.upper()
        if coupling not in ['DC', 'AC', 'GND']:
            print("X Invalid coupling! Use DC, AC, or GND")
            return False
        try:
            self.inst.write(f'C{channel}:CPL {coupling}1M')
            time.sleep(0.1)
            print(f"Channel {channel} coupling set to {coupling}")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_probe_attenuation(self, channel=1, attenuation=10):
        """
        Set probe attenuation

        Args:
            channel: Channel number (1-4)
            attenuation: Probe attenuation (1, 10, 100, 1000)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        if channel not in [1, 2, 3, 4]:
            print("X Invalid channel! Use 1-4")
            return False
        try:
            self.inst.write(f'C{channel}:ATTN {attenuation}')
            time.sleep(0.1)
            print(f"Channel {channel} probe attenuation set to {attenuation}X")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    # ========== Timebase Control ==========
    def set_timebase(self, scale):
        """
        Set timebase scale (seconds/div)

        Args:
            scale: Time per division in seconds (e.g., 0.001 for 1ms/div)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            self.inst.write(f'TDIV {scale}S')
            time.sleep(0.1)
            print(f"Timebase set to {scale}s/div")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def get_timebase(self):
        """Get timebase scale"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('TDIV?')
            time.sleep(0.1)
            return response.strip()
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def get_timebase_value(self):
        """Get timebase scale as float (seconds/div)"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('TDIV?')
            time.sleep(0.1)
            # Parse response like "TDIV 1.00E-05S"
            value = response.replace('TDIV', '').replace('S', '').replace('s', '').strip()
            return float(value)
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def get_sample_rate(self):
        """
        Get current sample rate

        Returns:
            Sample rate in Sa/s
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query('SARA?')
            time.sleep(0.1)
            # Parse response like "SARA 1.00E+09Sa/s"
            value = response.replace('SARA', '').replace('Sa/s', '').replace('SA/s', '').strip()
            return float(value)
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def get_memory_depth(self):
        """
        Get current memory depth (number of points)

        Returns:
            Memory depth in points
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query('MSIZ?')
            time.sleep(0.1)
            # Parse response like "MSIZ 14M" or "MSIZ 1.4K"
            value_str = response.replace('MSIZ', '').strip()
            if 'K' in value_str.upper():
                value = float(value_str.upper().replace('K', '')) * 1e3
            elif 'M' in value_str.upper():
                value = float(value_str.upper().replace('M', '')) * 1e6
            elif 'G' in value_str.upper():
                value = float(value_str.upper().replace('G', '')) * 1e9
            else:
                value = float(value_str)
            return int(value)
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def set_memory_depth(self, depth):
        """
        Set memory depth (number of points)

        Args:
            depth: Memory depth - use string like '7K', '70K', '700K', '7M', '70M'
                   or integer for points
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            if isinstance(depth, str):
                self.inst.write(f'MSIZ {depth}')
            else:
                # Convert number to appropriate format
                if depth >= 1e6:
                    self.inst.write(f'MSIZ {depth/1e6:.0f}M')
                elif depth >= 1e3:
                    self.inst.write(f'MSIZ {depth/1e3:.0f}K')
                else:
                    self.inst.write(f'MSIZ {depth}')
            time.sleep(0.2)
            print(f"Memory depth set to {depth}")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    # ========== Trigger Control ==========
    def set_trigger_level(self, level, channel=1):
        """
        Set trigger level

        Args:
            level: Trigger level in Volts
            channel: Trigger source channel (1-4)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            self.inst.write(f'C{channel}:TRLV {level}V')
            time.sleep(0.1)
            print(f"Trigger level set to {level}V on CH{channel}")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_trigger_source(self, channel=1):
        """
        Set trigger source

        Args:
            channel: Trigger source channel (1-4) or 'EXT' for external
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            if isinstance(channel, int):
                self.inst.write(f'TRSE EDGE,SR,C{channel}')
            else:
                self.inst.write(f'TRSE EDGE,SR,{channel}')
            time.sleep(0.1)
            print(f"Trigger source set to {channel}")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def set_trigger_slope(self, slope='RISING'):
        """
        Set trigger slope

        Args:
            slope: 'RISING' or 'FALLING'
        """
        if not self.connected:
            print("X Not connected!")
            return False
        slope = slope.upper()
        if slope == 'RISING':
            slope_cmd = 'POS'
        elif slope == 'FALLING':
            slope_cmd = 'NEG'
        else:
            print("X Invalid slope! Use RISING or FALLING")
            return False
        try:
            self.inst.write(f'C1:TRSL {slope_cmd}')
            time.sleep(0.1)
            print(f"Trigger slope set to {slope}")
            return True
        except Exception as e:
            print(f"X Error: {e}")
            return False

    def get_trigger_status(self):
        """Get trigger status"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('INR?')
            time.sleep(0.1)
            return response.strip()
        except Exception as e:
            print(f"X Error: {e}")
            return None

    # ========== Measurement Functions ==========
    def measure_frequency(self, channel=1):
        """
        Measure frequency on a channel

        Args:
            channel: Channel number (1-4)

        Returns:
            Frequency in Hz (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? FREQ')
            time.sleep(0.1)
            # Parse response like "C1:PAVA FREQ,1.000000E+03Hz"
            if 'FREQ' in response:
                value_str = response.split(',')[1].strip()
                # Handle invalid values like '****'
                if '****' in value_str or value_str == '':
                    return None
                value = value_str.replace('Hz', '').strip()
                return float(value)
            return None
        except (ValueError, IndexError) as e:
            # Silently return None for parse errors (invalid measurements)
            return None
        except Exception as e:
            # Only print unexpected errors
            return None

    def measure_vpp(self, channel=1):
        """
        Measure peak-to-peak voltage (Vpp)

        Args:
            channel: Channel number (1-4)

        Returns:
            Vpp in Volts (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? PKPK')
            time.sleep(0.1)
            if 'PKPK' in response:
                value_str = response.split(',')[1].strip()
                if '****' in value_str or value_str == '':
                    return None
                value_str = value_str.replace('V', '').replace('A', '').strip()
                return float(value_str)
            return None
        except (ValueError, IndexError):
            return None
        except Exception:
            return None

    def measure_amplitude(self, channel=1):
        """
        Measure amplitude (high level − low level, excludes overshoot)

        Args:
            channel: Channel number (1-4)

        Returns:
            Amplitude in Volts (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? AMPL')
            time.sleep(0.1)
            if 'AMPL' in response:
                value_str = response.split(',')[1].strip()
                if '****' in value_str or value_str == '':
                    return None
                value_str = value_str.replace('V', '').replace('A', '').strip()
                return float(value_str)
            return None
        except (ValueError, IndexError):
            return None
        except Exception:
            return None

    def measure_vrms(self, channel=1):
        """
        Measure RMS voltage

        Args:
            channel: Channel number (1-4)

        Returns:
            Vrms in Volts (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? RMS')
            time.sleep(0.1)
            if 'RMS' in response:
                value_str = response.split(',')[1].strip()
                # Handle invalid values like '****'
                if '****' in value_str or value_str == '':
                    return None
                # Remove units (V or A) and convert
                value_str = value_str.replace('V', '').replace('A', '').strip()
                return float(value_str)
            return None
        except (ValueError, IndexError) as e:
            # Silently return None for parse errors (invalid measurements)
            return None
        except Exception as e:
            # Only print unexpected errors
            return None

    def measure_mean(self, channel=1):
        """
        Measure mean voltage

        Args:
            channel: Channel number (1-4)

        Returns:
            Mean voltage in Volts (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? MEAN')
            time.sleep(0.1)
            if 'MEAN' in response:
                value_str = response.split(',')[1].strip()
                # Handle invalid values like '****'
                if '****' in value_str or value_str == '':
                    return None
                # Remove units (V or A) and convert
                value_str = value_str.replace('V', '').replace('A', '').strip()
                return float(value_str)
            return None
        except (ValueError, IndexError) as e:
            # Silently return None for parse errors (invalid measurements)
            return None
        except Exception as e:
            # Only print unexpected errors
            return None

    def measure_max(self, channel=1):
        """
        Measure maximum voltage

        Args:
            channel: Channel number (1-4)

        Returns:
            Max voltage in Volts (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? MAX')
            time.sleep(0.1)
            if 'MAX' in response:
                value_str = response.split(',')[1].strip()
                # Handle invalid values like '****'
                if '****' in value_str or value_str == '':
                    return None
                # Remove units (V or A) and convert
                value_str = value_str.replace('V', '').replace('A', '').strip()
                return float(value_str)
            return None
        except (ValueError, IndexError) as e:
            # Silently return None for parse errors (invalid measurements)
            return None
        except Exception as e:
            # Only print unexpected errors
            return None

    def measure_min(self, channel=1):
        """
        Measure minimum voltage

        Args:
            channel: Channel number (1-4)

        Returns:
            Min voltage in Volts (or None if invalid/out of range)
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? MIN')
            time.sleep(0.1)
            if 'MIN' in response:
                value_str = response.split(',')[1].strip()
                # Handle invalid values like '****'
                if '****' in value_str or value_str == '':
                    return None
                # Remove units (V or A) and convert
                value_str = value_str.replace('V', '').replace('A', '').strip()
                return float(value_str)
            return None
        except (ValueError, IndexError) as e:
            # Silently return None for parse errors (invalid measurements)
            return None
        except Exception as e:
            # Only print unexpected errors
            return None

    def measure_period(self, channel=1):
        """
        Measure signal period

        Args:
            channel: Channel number (1-4)

        Returns:
            Period in seconds
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? PER')
            time.sleep(0.1)
            if 'PER' in response:
                value = response.split(',')[1].replace('S', '').replace('s', '').strip()
                return float(value)
            return None
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def measure_rise_time(self, channel=1):
        """
        Measure rise time

        Args:
            channel: Channel number (1-4)

        Returns:
            Rise time in seconds
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? RISE')
            time.sleep(0.1)
            if 'RISE' in response:
                value = response.split(',')[1].replace('S', '').replace('s', '').strip()
                return float(value)
            return None
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def measure_fall_time(self, channel=1):
        """
        Measure fall time

        Args:
            channel: Channel number (1-4)

        Returns:
            Fall time in seconds
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? FALL')
            time.sleep(0.1)
            if 'FALL' in response:
                value = response.split(',')[1].replace('S', '').replace('s', '').strip()
                return float(value)
            return None
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def measure_duty_cycle(self, channel=1):
        """
        Measure duty cycle

        Args:
            channel: Channel number (1-4)

        Returns:
            Duty cycle in percent
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query(f'C{channel}:PAVA? DUTY')
            time.sleep(0.1)
            if 'DUTY' in response:
                value = response.split(',')[1].replace('%', '').strip()
                return float(value)
            return None
        except Exception as e:
            print(f"X Error: {e}")
            return None

    def get_all_measurements(self, channel=1):
        """
        Get all common measurements for a channel

        Args:
            channel: Channel number (1-4)

        Returns:
            Dictionary with all measurements
        """
        if not self.connected:
            return None

        measurements = {
            'channel': channel,
            'frequency': self.measure_frequency(channel),
            'period': self.measure_period(channel),
            'amplitude_vpp': self.measure_amplitude(channel),
            'vrms': self.measure_vrms(channel),
            'mean': self.measure_mean(channel),
            'max': self.measure_max(channel),
            'min': self.measure_min(channel),
            'rise_time': self.measure_rise_time(channel),
            'fall_time': self.measure_fall_time(channel),
            'duty_cycle': self.measure_duty_cycle(channel),
        }
        return measurements

    def print_measurements(self, channel=1):
        """Print formatted measurements for a channel"""
        meas = self.get_all_measurements(channel)
        if meas:
            print(f"\nChannel {channel} Measurements:")
            print("-" * 40)

            freq = meas.get('frequency')
            if freq is not None:
                if freq >= 1e6:
                    print(f"  Frequency:  {freq/1e6:.3f} MHz")
                elif freq >= 1e3:
                    print(f"  Frequency:  {freq/1e3:.3f} kHz")
                else:
                    print(f"  Frequency:  {freq:.3f} Hz")

            period = meas.get('period')
            if period is not None:
                if period < 1e-6:
                    print(f"  Period:     {period*1e9:.3f} ns")
                elif period < 1e-3:
                    print(f"  Period:     {period*1e6:.3f} us")
                else:
                    print(f"  Period:     {period*1e3:.3f} ms")

            vpp = meas.get('amplitude_vpp')
            if vpp is not None:
                print(f"  Vpp:        {vpp:.3f} V")

            vrms = meas.get('vrms')
            if vrms is not None:
                print(f"  Vrms:       {vrms:.3f} V")

            mean = meas.get('mean')
            if mean is not None:
                print(f"  Mean:       {mean:.3f} V")

            vmax = meas.get('max')
            if vmax is not None:
                print(f"  Max:        {vmax:.3f} V")

            vmin = meas.get('min')
            if vmin is not None:
                print(f"  Min:        {vmin:.3f} V")

            rise = meas.get('rise_time')
            if rise is not None:
                if rise < 1e-6:
                    print(f"  Rise Time:  {rise*1e9:.3f} ns")
                elif rise < 1e-3:
                    print(f"  Rise Time:  {rise*1e6:.3f} us")
                else:
                    print(f"  Rise Time:  {rise*1e3:.3f} ms")

            fall = meas.get('fall_time')
            if fall is not None:
                if fall < 1e-6:
                    print(f"  Fall Time:  {fall*1e9:.3f} ns")
                elif fall < 1e-3:
                    print(f"  Fall Time:  {fall*1e6:.3f} us")
                else:
                    print(f"  Fall Time:  {fall*1e3:.3f} ms")

            duty = meas.get('duty_cycle')
            if duty is not None:
                print(f"  Duty Cycle: {duty:.1f}%")

    # ========== Screenshot ==========
    def save_screenshot(self, filename='screenshot.png'):
        """
        Capture and save a screenshot from the oscilloscope

        Args:
            filename: Output filename (PNG format)
        """
        if not self.connected:
            print("X Not connected!")
            return False
        try:
            # Request screenshot data
            self.inst.write('SCDP')
            time.sleep(0.5)

            # Read binary data
            raw_data = self.inst.read_raw()

            # Save to file
            with open(filename, 'wb') as f:
                f.write(raw_data)

            print(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            print(f"X Error saving screenshot: {e}")
            return False


def demo():
    """Demonstration of oscilloscope control"""

    print("=" * 70)
    print("SIGLENT SDS1104X HD Oscilloscope Demo")
    print("=" * 70)
    print()

    # Create instance and connect
    scope = SiglentSDS()

    if not scope.connect():
        print("Failed to connect!")
        print("\nMake sure the oscilloscope is:")
        print("1. Powered on")
        print("2. Connected via USB or LAN")
        print("\nFor LAN: scope.connect('TCPIP::192.168.1.100::INSTR')")
        return

    print()
    print("-" * 70)
    print("Demo: Reading measurements from Channel 1")
    print("-" * 70)

    # Enable channel 1
    scope.enable_channel(1)

    # Run auto setup to configure for current signal
    print("\nRunning auto setup...")
    scope.auto_setup()

    # Wait for stabilization
    time.sleep(1)

    # Print all measurements
    scope.print_measurements(channel=1)

    print("\nPress Enter to continue...")
    input()

    # Show timebase info
    print("\nTimebase settings:")
    print(f"  {scope.get_timebase()}")

    print("\nChannel 1 scale:")
    print(f"  {scope.get_channel_scale(1)}")

    print("\nPress Enter to exit...")
    input()

    # Disconnect
    print()
    scope.disconnect()

    print("\nDemo complete!")


if __name__ == "__main__":
    demo()
