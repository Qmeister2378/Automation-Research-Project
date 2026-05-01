from flask import Flask, render_template, jsonify, request
import time

from power_supply_connection import SiglentSPD
from electronic_load_connection import RigolDL3021
from function_generator_connection import SiglentSDG
from oscilloscope_connection import SiglentSDS

app = Flask(__name__)

instruments = {
    "ps": None,
    "load": None,
    "fg": None,
    "scope": None,
}

connected = False
results_data = []


def safe_float(value, name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number")


def connect_all():
    global connected, instruments

    if connected:
        return True

    ps = SiglentSPD()
    load = RigolDL3021()
    fg = SiglentSDG()
    scope = SiglentSDS()

    if not ps.connect():
        return False
    time.sleep(0.5)

    if not load.connect():
        ps.disconnect()
        return False
    time.sleep(0.5)

    if not fg.connect():
        load.disconnect()
        ps.disconnect()
        return False
    time.sleep(0.5)

    if not scope.connect():
        fg.disconnect()
        load.disconnect()
        ps.disconnect()
        return False

    instruments = {
        "ps": ps,
        "load": load,
        "fg": fg,
        "scope": scope,
    }

    # One-time basic setup
    ps.set_current(channel=1, current=2.0)        # current limit for power supply
    load.set_mode_cr()                           # electronic load resistance mode
    scope.enable_channel(1)
    scope.set_channel_coupling(channel=1, coupling="DC")
    scope.set_probe_attenuation(channel=1, attenuation=1)
    scope.set_acquisition_mode(mode="AVERAGE", count=32)
    scope.run()

    connected = True
    return True


def disconnect_all():
    global connected, instruments

    for key in ["fg", "load", "ps", "scope"]:
        inst = instruments.get(key)
        if inst:
            try:
                if key == "fg":
                    inst.turn_off_output(channel=1)
                elif key == "load":
                    inst.turn_off_input()
                elif key == "ps":
                    inst.turn_off_output(channel=1)
                inst.disconnect()
            except Exception:
                pass

    instruments = {"ps": None, "load": None, "fg": None, "scope": None}
    connected = False


@app.route("/")
def index():
    return render_template("power.html")


@app.route("/api/connect", methods=["POST"])
def api_connect():
    ok = connect_all()
    if not ok:
        return jsonify({"status": "error", "message": "Could not connect to all instruments."}), 500
    return jsonify({"status": "ok", "message": "All instruments connected."})


@app.route("/api/disconnect", methods=["POST"])
def api_disconnect():
    disconnect_all()
    return jsonify({"status": "ok", "message": "All instruments disconnected."})


@app.route("/api/run", methods=["POST"])
def api_run():
    global results_data

    try:
        data = request.get_json(silent=True) or {}

        voltage = safe_float(data.get("voltage"), "Voltage")
        resistance = safe_float(data.get("resistance"), "Resistance")
        frequency = safe_float(data.get("frequency"), "Frequency")
        amplitude = safe_float(data.get("amplitude", 2.0), "Amplitude")
        offset = safe_float(data.get("offset", 0.0), "Offset")

        if voltage < 0:
            raise ValueError("Voltage cannot be negative")
        if resistance <= 0:
            raise ValueError("Resistance must be greater than 0")
        if frequency <= 0:
            raise ValueError("Frequency must be greater than 0")

        if not connect_all():
            return jsonify({"status": "error", "message": "Could not connect to all instruments."}), 500

        ps = instruments["ps"]
        load = instruments["load"]
        fg = instruments["fg"]
        scope = instruments["scope"]

        # Set the user-entered values into the machines
        ps.set_voltage(channel=1, voltage=voltage)
        ps.turn_on_output(channel=1)

        load.turn_off_input()
        time.sleep(0.2)

        load.set_mode_cr()
        time.sleep(0.3)

        load.set_resistance(resistance)
        time.sleep(0.3)

        actual_resistance = load.get_resistance_setting()
        print("Requested resistance:", resistance)
        print("Actual resistance:", actual_resistance)

        load.turn_on_input()
        time.sleep(1)

        print("Load voltage:", load.measure_voltage())
        print("Load current:", load.measure_current())
        print("Load power:", load.measure_power())

        fg.set_square_wave(channel=1, frequency=frequency, amplitude=amplitude, offset=offset)
        fg.turn_on_output(channel=1)

        # Set oscilloscope timing based on entered frequency
        period = 1.0 / frequency
        scope.set_timebase(period * 2.5)
        scope.clear_sweeps()
        scope.run()

        # Let everything settle, then read measurements
        time.sleep(1.0)

        result = {
            "set_voltage_v": voltage,
            "set_resistance_ohm": resistance,
            "set_frequency_hz": frequency,
            "set_amplitude_v": amplitude,
            "set_offset_v": offset,

            "ps_voltage_v": ps.measure_voltage(channel=1),
            "ps_current_a": ps.measure_current(channel=1),
            "load_voltage_v": load.measure_voltage(),
            "load_current_a": load.measure_current(),
            "load_power_w": load.measure_power(),

            "scope_frequency_hz": scope.measure_frequency(channel=1),
            "scope_vpp_v": scope.measure_vpp(channel=1),
            "scope_vrms_v": scope.measure_vrms(channel=1),
            "scope_vmean_v": scope.measure_mean(channel=1),
            "scope_vmax_v": scope.measure_max(channel=1),
            "scope_vmin_v": scope.measure_min(channel=1),
        }

        results_data.append(result)

        return jsonify({
            "status": "ok",
            "message": "Values sent to instruments and measurements captured.",
            "data": [result]
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/stop", methods=["POST"])
def api_stop():
    try:
        if instruments["fg"]:
            instruments["fg"].turn_off_output(channel=1)
        if instruments["load"]:
            instruments["load"].turn_off_input()
        if instruments["ps"]:
            instruments["ps"].turn_off_output(channel=1)
        return jsonify({"status": "ok", "message": "Outputs stopped."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/status")
def api_status():
    return jsonify({"status": "connected" if connected else "disconnected"})


@app.route("/api/data")
def api_data():
    return jsonify({"data": results_data})


if __name__ == "__main__":
    app.run(debug=True)
