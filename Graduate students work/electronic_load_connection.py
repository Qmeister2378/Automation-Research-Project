#!/usr/bin/env python3
"""
Rigol DL3021 DC Electronic Load Control
Programmable electronic load automation
"""

import pyvisa
import time

class RigolDL3021:
    """Class to control Rigol DL3021 Electronic Load"""

    def __init__(self):
        self.rm = None
        self.inst = None
        self.connected = False

    def connect(self, resource=None):
        """
        Connect to the electronic load

        Args:
            resource: Optional specific resource string (e.g., 'TCPIP::192.168.1.100::INSTR')
                     If None, will auto-detect
        """
        try:
            print("Connecting to Rigol DL3021...")
            self.rm = pyvisa.ResourceManager()

            if resource:
                # Use specified resource
                target_resource = resource
            else:
                # Auto-detect Rigol device
                resources = self.rm.list_resources()
                target_resource = None

                for res in resources:
                    # Check for Rigol vendor ID (6833 decimal = 0x1AB1) or device identifiers
                    if '6833' in res or 'DL3' in res or 'RIGOL' in res.upper() or '1AB1' in res:
                        target_resource = res
                        break

                if not target_resource:
                    print("✗ Rigol DL3021 not found!")
                    print("\nAvailable resources:")
                    for res in resources:
                        print(f"  - {res}")
                    print("\nFor LAN connection, use:")
                    print("  load.connect('TCPIP::192.168.1.100::INSTR')")
                    return False

            # Open connection
            self.inst = self.rm.open_resource(
                target_resource,
                timeout=3000
            )
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'

            # Verify connection
            time.sleep(0.2)
            idn = self.inst.query('*IDN?')
            print(f"✓ Connected: {idn.strip()}")
            self.connected = True
            return True

        except Exception as e:
            print(f"✗ Connection failed: {e}")
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

    # Input Control
    def turn_on_input(self):
        """Turn on the electronic load input"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write('INP ON')
            time.sleep(0.1)
            print("✓ Input turned ON")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def turn_off_input(self):
        """Turn off the electronic load input"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write('INP OFF')
            time.sleep(0.1)
            print("✓ Input turned OFF")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_input_state(self):
        """Get input state"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('INP?')
            time.sleep(0.1)
            return response.strip()
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Mode Control
    def set_mode_cc(self):
        """Set to Constant Current (CC) mode"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write('FUNC CC')
            time.sleep(0.1)
            print("✓ Mode set to Constant Current (CC)")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def set_mode_cv(self):
        """Set to Constant Voltage (CV) mode"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write('FUNC CV')
            time.sleep(0.1)
            print("✓ Mode set to Constant Voltage (CV)")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def set_mode_cr(self):
        """Set to Constant Resistance (CR) mode"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write('FUNC CR')
            time.sleep(0.1)
            print("✓ Mode set to Constant Resistance (CR)")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def set_mode_cp(self):
        """Set to Constant Power (CP) mode"""
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write('FUNC CP')
            time.sleep(0.1)
            print("✓ Mode set to Constant Power (CP)")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_mode(self):
        """Get current operating mode"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('FUNC?')
            time.sleep(0.1)
            return response.strip()
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Current Control (CC Mode)
    def set_current(self, current):
        """
        Set load current (for CC mode)

        Args:
            current: Current in Amps (0-30A for DL3021)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write(f'CURR {current}')
            time.sleep(0.1)
            print(f"✓ Current set to {current}A")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_current_setting(self):
        """Get current setting"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('CURR?')
            time.sleep(0.1)
            return float(response.strip())
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Voltage Control (CV Mode)
    def set_voltage(self, voltage):
        """
        Set load voltage (for CV mode)

        Args:
            voltage: Voltage in Volts (0-150V for DL3021)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write(f'VOLT {voltage}')
            time.sleep(0.1)
            print(f"✓ Voltage set to {voltage}V")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_voltage_setting(self):
        """Get voltage setting"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('VOLT?')
            time.sleep(0.1)
            return float(response.strip())
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Resistance Control (CR Mode)
    def set_resistance(self, resistance):
        """
        Set load resistance (for CR mode)

        Args:
            resistance: Resistance in Ohms
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write(f'RES {resistance}')
            time.sleep(0.1)
            print(f"✓ Resistance set to {resistance}Ω")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_resistance_setting(self):
        """Get resistance setting"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('RES?')
            time.sleep(0.1)
            return float(response.strip())
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Power Control (CP Mode)
    def set_power(self, power):
        """
        Set load power (for CP mode)

        Args:
            power: Power in Watts (0-200W for DL3021)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False
        try:
            self.inst.write(f'POW {power}')
            time.sleep(0.1)
            print(f"✓ Power set to {power}W")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def get_power_setting(self):
        """Get power setting"""
        if not self.connected:
            return None
        try:
            response = self.inst.query('POW?')
            time.sleep(0.1)
            return float(response.strip())
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Measurement Functions
    def measure_voltage(self):
        """
        Measure actual input voltage

        Returns:
            Measured voltage in Volts
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query('MEAS:VOLT?')
            time.sleep(0.1)
            voltage = float(response.strip())
            return voltage
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def measure_current(self):
        """
        Measure actual input current

        Returns:
            Measured current in Amps
        """
        if not self.connected:
            return None
        try:
            response = self.inst.query('MEAS:CURR?')
            time.sleep(0.1)
            current = float(response.strip())
            return current
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def measure_power(self):
        """
        Measure actual power

        Returns:
            Measured power in Watts (calculated from V*I)
        """
        if not self.connected:
            return None
        try:
            voltage = self.measure_voltage()
            current = self.measure_current()

            if voltage is not None and current is not None:
                power = voltage * current
                return power
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    # Combined Setup
    def setup_cc_mode(self, current, input_on=False):
        """
        Configure for Constant Current mode

        Args:
            current: Current in Amps
            input_on: Turn on input after configuration (default: False)
        """
        if not self.connected:
            print("✗ Not connected!")
            return False

        print(f"\nConfiguring CC mode:")
        success = True

        # Set mode
        if not self.set_mode_cc():
            success = False

        # Set current
        if not self.set_current(current):
            success = False

        # Turn on input if requested
        if input_on and success:
            if not self.turn_on_input():
                success = False

        return success

    def get_status(self):
        """
        Get complete status of the load

        Returns:
            Dictionary with mode, settings, and measurements
        """
        if not self.connected:
            return None

        try:
            mode = self.get_mode()
            status = {
                'mode': mode,
                'voltage_measured': self.measure_voltage(),
                'current_measured': self.measure_current(),
                'power_measured': self.measure_power(),
                'input_state': self.get_input_state()
            }

            # Get setting based on mode
            if mode == 'CC':
                status['current_set'] = self.get_current_setting()
            elif mode == 'CV':
                status['voltage_set'] = self.get_voltage_setting()
            elif mode == 'CR':
                status['resistance_set'] = self.get_resistance_setting()
            elif mode == 'CP':
                status['power_set'] = self.get_power_setting()

            return status
        except Exception as e:
            print(f"✗ Error getting status: {e}")
            return None

    def print_status(self):
        """Print formatted status"""
        status = self.get_status()
        if status:
            print(f"\nRigol DL3021 Status:")
            print(f"  Mode:         {status.get('mode', 'N/A')}")
            print(f"  Input State:  {status.get('input_state', 'N/A')}")

            if 'current_set' in status:
                print(f"  Current Set:  {status['current_set']:.3f}A")
            if 'voltage_set' in status:
                print(f"  Voltage Set:  {status['voltage_set']:.3f}V")
            if 'resistance_set' in status:
                print(f"  Resistance:   {status['resistance_set']:.3f}Ω")
            if 'power_set' in status:
                print(f"  Power Set:    {status['power_set']:.3f}W")

            v_meas = status.get('voltage_measured')
            c_meas = status.get('current_measured')
            p_meas = status.get('power_measured')

            if v_meas is not None:
                print(f"  Voltage Meas: {v_meas:.3f}V")
            if c_meas is not None:
                print(f"  Current Meas: {c_meas:.3f}A")
            if p_meas is not None:
                print(f"  Power Meas:   {p_meas:.3f}W")


def demo():
    """Demonstration of electronic load control"""

    print("=" * 70)
    print("Rigol DL3021 Electronic Load Demo")
    print("=" * 70)
    print()

    # Create instance and connect
    load = RigolDL3021()

    if not load.connect():
        print("Failed to connect!")
        print("\nMake sure the device is:")
        print("1. Powered on")
        print("2. Connected via USB or")
        print("3. Connected to network (use: load.connect('TCPIP::IP_ADDRESS::INSTR'))")
        return

    print()
    print("-" * 70)
    print("Demo: Setting up CC mode with 1A load")
    print("-" * 70)

    # Configure CC mode: 1A
    load.setup_cc_mode(current=1.0, input_on=True)

    # Wait for stabilization
    time.sleep(0.5)

    # Display status
    load.print_status()

    print("\nInput is now ON with 1A load")
    print("Press Enter to turn off and exit...")
    input()

    # Turn off input
    load.turn_off_input()

    # Disconnect
    print()
    load.disconnect()

    print("\nDemo complete!")


if __name__ == "__main__":
    demo()
