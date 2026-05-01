#!/usr/bin/env python3
"""
Full Combined Automation - All Four Instruments
- Power Supply: Sweeps 5V, 10V, 15V
- Electronic Load: Sweeps 5Ω, 10Ω, 15Ω, 20Ω
- Function Generator: Sweeps 95, 97.5, 100, 102.5, 105 kHz
- Oscilloscope: Captures measurements at each combination

Total test points: 3 voltages × 4 resistances × 5 frequencies = 60 combinations
Each instrument operates independently (not physically connected to each other)
"""

from power_supply_connection import SiglentSPD
from electronic_load_connection import RigolDL3021
from function_generator_connection import SiglentSDG
from oscilloscope_connection import SiglentSDS
import time
import csv
from datetime import datetime


def connect_all_instruments():
    """Connect to all four instruments with proper delays"""
    instruments = {}

    print("=" * 70)
    print("Connecting to all instruments...")
    print("=" * 70)

    # 1. Power Supply
    print("\n[1/4] Connecting to Power Supply (SPD 3303C)...")
    ps = SiglentSPD()
    if not ps.connect():
        print("  X Failed to connect to power supply!")
        return None
    print("  OK Power supply connected")
    instruments['ps'] = ps
    time.sleep(1)

    # 2. Electronic Load
    print("\n[2/4] Connecting to Electronic Load (DL3021)...")
    load = RigolDL3021()
    if not load.connect():
        print("  X Failed to connect to electronic load!")
        ps.disconnect()
        return None
    print("  OK Electronic load connected")
    instruments['load'] = load
    time.sleep(1)

    # 3. Function Generator
    print("\n[3/4] Connecting to Function Generator (SDG)...")
    fg = SiglentSDG()
    if not fg.connect():
        print("  X Failed to connect to function generator!")
        ps.disconnect()
        load.disconnect()
        return None
    print("  OK Function generator connected")
    instruments['fg'] = fg
    time.sleep(1)

    # 4. Oscilloscope
    print("\n[4/4] Connecting to Oscilloscope (SDS)...")
    scope = SiglentSDS()
    if not scope.connect():
        print("  X Failed to connect to oscilloscope!")
        ps.disconnect()
        load.disconnect()
        fg.disconnect()
        return None
    print("  OK Oscilloscope connected")
    instruments['scope'] = scope

    print("\n" + "=" * 70)
    print("OK All four instruments connected successfully!")
    print("=" * 70)

    return instruments


def setup_instruments(instruments):
    """Configure initial settings for all instruments"""
    ps = instruments['ps']
    load = instruments['load']
    fg = instruments['fg']
    scope = instruments['scope']

    print("\n" + "=" * 70)
    print("Setting up instruments...")
    print("=" * 70)

    # Power Supply setup
    print("\nPower Supply setup:")
    ps.set_current(channel=1, current=2.0)  # 2A current limit
    print("  - Current limit: 2.0A")
    print("  - Channel: 1")

    # Electronic Load setup
    print("\nElectronic Load setup:")
    load.set_mode_cr()  # Constant Resistance mode
    print("  - Mode: Constant Resistance (CR)")

    # Function Generator setup
    print("\nFunction Generator setup:")
    fg.set_square_wave(channel=1, frequency=95000, amplitude=2.0, offset=0, duty=50)
    print("  - Waveform: Square")
    print("  - Amplitude: 2V")
    print("  - Duty Cycle: 50%")
    print("  - Channel: 1")

    # Oscilloscope setup
    print("\nOscilloscope setup:")
    scope.enable_channel(1)
    scope.set_channel_coupling(channel=1, coupling='DC')
    scope.set_probe_attenuation(channel=1, attenuation=1)
    print("  - Channel: 1 enabled")
    print("  - Coupling: DC")
    print("  - Probe: 1X")

    # Run auto setup
    print("  - Running auto setup...")
    scope.auto_setup()
    time.sleep(1)

    print("\nOK All instruments configured!")


def turn_on_outputs(instruments):
    """Turn on outputs for all applicable instruments"""
    print("\nTurning on outputs...")

    instruments['ps'].turn_on_output(channel=1)
    print("  - Power supply output: ON")

    instruments['load'].turn_on_input()
    print("  - Electronic load input: ON")

    instruments['fg'].turn_on_output(channel=1)
    print("  - Function generator output: ON")


def turn_off_outputs(instruments):
    """Turn off outputs for all applicable instruments"""
    print("\nTurning off outputs...")

    instruments['fg'].turn_off_output(channel=1)
    print("  - Function generator output: OFF")

    instruments['load'].turn_off_input()
    print("  - Electronic load input: OFF")

    instruments['ps'].turn_off_output(channel=1)
    print("  - Power supply output: OFF")


def disconnect_all(instruments):
    """Disconnect all instruments"""
    print("\nDisconnecting all instruments...")

    for name, inst in instruments.items():
        try:
            inst.disconnect()
            print(f"  - {name}: disconnected")
        except Exception as e:
            print(f"  - {name}: error disconnecting - {e}")


def take_measurements(instruments):
    """Take measurements from all instruments"""
    ps = instruments['ps']
    load = instruments['load']
    fg = instruments['fg']
    scope = instruments['scope']

    measurements = {}

    # Power Supply measurements
    measurements['ps_voltage'] = ps.measure_voltage(channel=1)
    measurements['ps_current'] = ps.measure_current(channel=1)

    # Electronic Load measurements
    measurements['load_voltage'] = load.measure_voltage()
    measurements['load_current'] = load.measure_current()

    # Oscilloscope measurements
    measurements['scope_frequency'] = scope.measure_frequency(channel=1)
    measurements['scope_vpp'] = scope.measure_amplitude(channel=1)
    measurements['scope_vrms'] = scope.measure_vrms(channel=1)
    measurements['scope_vmean'] = scope.measure_mean(channel=1)
    measurements['scope_vmax'] = scope.measure_max(channel=1)
    measurements['scope_vmin'] = scope.measure_min(channel=1)
    measurements['scope_rise_time'] = scope.measure_rise_time(channel=1)
    measurements['scope_fall_time'] = scope.measure_fall_time(channel=1)

    return measurements


def full_matrix_sweep():
    """
    Perform full matrix sweep across all parameters:
    - Voltage: 5V, 10V, 15V
    - Resistance: 5, 10, 15, 20 Ohms
    - Frequency: 95, 97.5, 100, 102.5, 105 kHz
    Total: 60 test points
    """

    print("\n" + "=" * 70)
    print("FULL COMBINED AUTOMATION - ALL FOUR INSTRUMENTS")
    print("=" * 70)
    print()
    print("This automation controls:")
    print("  1. Power Supply (SPD 3303C) - Voltage sweep")
    print("  2. Electronic Load (DL3021) - Resistance sweep")
    print("  3. Function Generator (SDG) - Frequency sweep")
    print("  4. Oscilloscope (SDS) - Measurements")
    print()
    print("NOTE: Each instrument operates independently")
    print("      (not physically connected to each other)")
    print()

    # Define sweep parameters
    voltages = [5, 10, 15]  # Volts
    resistances = [5, 10, 15, 20]  # Ohms
    frequencies = [
        (95000, "95 kHz"),
        (97500, "97.5 kHz"),
        (100000, "100 kHz"),
        (102500, "102.5 kHz"),
        (105000, "105 kHz"),
    ]

    total_points = len(voltages) * len(resistances) * len(frequencies)
    print(f"Test matrix: {len(voltages)} voltages x {len(resistances)} resistances x {len(frequencies)} frequencies")
    print(f"Total test points: {total_points}")
    print("-" * 70)

    # Connect to all instruments
    instruments = connect_all_instruments()
    if instruments is None:
        print("\nX Failed to connect to all instruments. Aborting.")
        return

    # Setup instruments
    setup_instruments(instruments)

    # Prepare CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"full_sweep_results_{timestamp}.csv"
    results = []

    # Turn on all outputs
    turn_on_outputs(instruments)

    print("\n" + "=" * 70)
    print("STARTING MATRIX SWEEP")
    print("=" * 70)

    test_point = 0

    # Outer loop: Voltage
    for v_idx, voltage in enumerate(voltages):
        print(f"\n{'#' * 70}")
        print(f"VOLTAGE LEVEL {v_idx + 1}/{len(voltages)}: {voltage}V")
        print(f"{'#' * 70}")

        # Set power supply voltage
        instruments['ps'].set_voltage(channel=1, voltage=voltage)
        time.sleep(0.3)

        # Middle loop: Resistance
        for r_idx, resistance in enumerate(resistances):
            print(f"\n{'=' * 60}")
            print(f"  RESISTANCE LEVEL {r_idx + 1}/{len(resistances)}: {resistance} Ohm")
            print(f"{'=' * 60}")

            # Set electronic load resistance
            instruments['load'].set_resistance(resistance)
            time.sleep(0.3)

            # Inner loop: Frequency
            for f_idx, (freq_hz, freq_label) in enumerate(frequencies):
                test_point += 1

                print(f"\n  [{test_point}/{total_points}] V={voltage}V, R={resistance}Ohm, F={freq_label}")
                print(f"  {'-' * 50}")

                # Set function generator frequency
                instruments['fg'].set_frequency(channel=1, frequency=freq_hz)

                # Adjust oscilloscope timebase for frequency
                period = 1.0 / freq_hz
                timebase = period * 2.5
                if timebase >= 1e-6:
                    timebase = round(timebase * 1e6) / 1e6
                instruments['scope'].set_timebase(timebase)

                # Wait for stabilization
                time.sleep(0.5)

                # Take all measurements
                meas = take_measurements(instruments)

                # Display measurements
                print(f"    Power Supply:")
                if meas['ps_voltage'] is not None:
                    print(f"      Voltage: {meas['ps_voltage']:.3f} V")
                if meas['ps_current'] is not None:
                    print(f"      Current: {meas['ps_current']:.3f} A")

                print(f"    Electronic Load:")
                if meas['load_voltage'] is not None:
                    print(f"      Voltage: {meas['load_voltage']:.3f} V")
                if meas['load_current'] is not None:
                    print(f"      Current: {meas['load_current']:.3f} A")

                print(f"    Oscilloscope:")
                if meas['scope_frequency'] is not None:
                    print(f"      Frequency: {meas['scope_frequency']/1e3:.3f} kHz")
                if meas['scope_vpp'] is not None:
                    print(f"      Vpp: {meas['scope_vpp']:.4f} V")
                if meas['scope_vrms'] is not None:
                    print(f"      Vrms: {meas['scope_vrms']:.4f} V")

                # Store result
                result = {
                    'test_point': test_point,
                    'set_voltage_v': voltage,
                    'set_resistance_ohm': resistance,
                    'set_frequency_hz': freq_hz,
                    'set_frequency_label': freq_label,
                    'ps_voltage_v': meas['ps_voltage'],
                    'ps_current_a': meas['ps_current'],
                    'load_voltage_v': meas['load_voltage'],
                    'load_current_a': meas['load_current'],
                    'scope_frequency_hz': meas['scope_frequency'],
                    'scope_vpp_v': meas['scope_vpp'],
                    'scope_vrms_v': meas['scope_vrms'],
                    'scope_vmean_v': meas['scope_vmean'],
                    'scope_vmax_v': meas['scope_vmax'],
                    'scope_vmin_v': meas['scope_vmin'],
                    'scope_rise_time_s': meas['scope_rise_time'],
                    'scope_fall_time_s': meas['scope_fall_time'],
                }
                results.append(result)

                print(f"    OK Point {test_point} completed")

    # Save results to CSV
    print("\n" + "=" * 70)
    print("Saving results to CSV...")
    print("=" * 70)

    try:
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = list(results[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"OK Results saved to: {csv_filename}")
    except Exception as e:
        print(f"X Error saving CSV: {e}")

    # Print summary table
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Point':<6} {'V(V)':<6} {'R(Ohm)':<8} {'F(kHz)':<10} {'PS_V':<8} {'PS_I':<8} {'Scope_Vpp':<10}")
    print("-" * 70)

    for r in results:
        ps_v = f"{r['ps_voltage_v']:.2f}" if r['ps_voltage_v'] else "N/A"
        ps_i = f"{r['ps_current_a']:.3f}" if r['ps_current_a'] else "N/A"
        vpp = f"{r['scope_vpp_v']:.3f}" if r['scope_vpp_v'] else "N/A"
        freq = r['set_frequency_hz'] / 1000

        print(f"{r['test_point']:<6} {r['set_voltage_v']:<6} {r['set_resistance_ohm']:<8} {freq:<10.1f} {ps_v:<8} {ps_i:<8} {vpp:<10}")

    print("=" * 70)
    print(f"OK Full matrix sweep complete! {total_points} test points.")
    print("=" * 70)

    # Cleanup
    turn_off_outputs(instruments)
    disconnect_all(instruments)

    print("\nOK Done!")
    
    return results


if __name__ == "__main__":
    full_matrix_sweep()