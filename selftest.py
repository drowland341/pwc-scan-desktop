#!/usr/bin/env python3
"""Checks the protocol code against the simulated ECU. Run: python selftest.py  (no ski or cable needed)"""
import os
import queue
import time

import kline as kl


def check_codes():
    """Reading codes: the fixed read-only request, the reply parser, the code table, and the demo ECU end to end."""
    assert kl.hexs(kl.READ_CODES_REQUEST) == "13 01"
    table = kl.load_service_codes(os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_codes.json"))
    assert table["P0340"]["code"] == 23 and table["P0340"]["obd_code_seen"]       # seen from a real Ultra LX
    assert table["P1112"]["code"] == 73 and table["P0115"]["dash"] == "AqUt"
    assert kl.obd_code(0x03, 0x40) == "P0340" and kl.obd_code(0x11, 0x12) == "P1112"
    assert kl.obd_code(0x41, 0x23) == "C0123" and kl.obd_code(0xC0, 0x01) == "U0001"

    r = kl.parse_codes_reply(bytes.fromhex("53 02 03 40 01 99"), table)      # 53 01 03 40 is a real Ultra LX reply
    assert [c["obd"] for c in r["codes"]] == ["P0340", "P0199"] and not r["warning"]
    assert r["codes"][0]["info"]["code"] == 23 and r["codes"][1]["info"] is None
    assert kl.parse_codes_reply(bytes.fromhex("53 00"), table) == {"codes": [], "count": 0, "warning": ""}
    assert "extra byte" in kl.parse_codes_reply(bytes.fromhex("53 01 03 40 00"), table)["warning"]
    assert "said 2" in kl.parse_codes_reply(bytes.fromhex("53 02 03 40"), table)["warning"]

    events = queue.Queue()
    engine = kl.Engine(events)
    engine.start()

    def wait_for(kind, deadline=10.0):
        end = time.time() + deadline
        while time.time() < end:
            try:
                ev = events.get(timeout=0.5)
            except queue.Empty:
                continue
            if ev[0] == kind[0] and (len(kind) == 1 or ev[1] == kind[1]):
                return ev
        raise AssertionError(f"no {kind} event")

    try:
        engine.send("read_codes", table)
        early = wait_for(("codes",))[1]
        assert not early["ok"] and early["frames"] == [], early           # nothing is sent until connected
        engine.send("connect", dict(kl.DEFAULT_SETTINGS, port=kl.DEMO_PORT), [p.copy() for p in kl.DEFAULT_PIDS])
        ecu = wait_for(("ecu",))[1]
        assert ecu["reply"] == "80 F1 11 03 C1 EA 8F BF" and ecu["key_bytes"] == "EA 8F", ecu
        wait_for(("state", "connected"))
        engine.send("read_codes", table)
        result = wait_for(("codes",))[1]
    finally:
        engine.send("quit")
        engine.join(timeout=3)
    assert result["ok"], result
    assert [c["obd"] for c in result["codes"]] == ["P0115", "P0340"], result
    assert [c["info"]["code"] for c in result["codes"]] == [14, 23]
    assert result["frames"][0] == ("TX", "80 11 F1 02 13 01 98"), result["frames"]


def check_dashboard():
    tach = kl.DASHBOARD_TACH
    assert tach.level(6999) == ("normal", "") and tach.level(7000) == ("warn", "HIGH")
    assert tach.level(7600) == ("crit", "HIGH") and tach.level(None) == ("normal", "")
    assert tach.readout(7512) == "7,510" and tach.readout(None) == "--"
    assert tach.fraction(-50) == 0.0 and tach.fraction(9000) == 1.0
    battery = next(g for g in kl.DASHBOARD_CARDS if g.pid == 0x0A)
    assert battery.level(12.2) == ("warn", "LOW") and battery.level(11.5) == ("crit", "LOW")
    assert battery.level(13.8) == ("normal", "") and battery.readout(13.84) == "13.8"
    temp = next(g for g in kl.DASHBOARD_CARDS if g.pid == 0x06)
    assert temp.level(104.9) == ("warn", "HIGH") and temp.level(105) == ("crit", "HIGH")   # limits are in C
    defaults = {p.pid for p in kl.DEFAULT_PIDS}
    assert all(g.pid in defaults for g in [tach] + kl.DASHBOARD_CARDS)


def main():
    # Frames must match what Kawasaki ECUs expect byte for byte.
    assert kl.hexs(kl.build_frame(0x11, 0xF1, [0x81], length_in_fmt=True)) == "81 11 F1 81 04"
    assert kl.hexs(kl.build_frame(0x11, 0xF1, [0x10, 0x80])) == "80 11 F1 02 10 80 14"
    assert kl.hexs(kl.build_frame(0x11, 0xF1, [0x21, 0x09])) == "80 11 F1 02 21 09 AE"
    print("Frame building ........ ok")

    # Every channel list in channels/ must load.
    for name in sorted(os.listdir(kl.CHANNELS_DIR)):
        if name.endswith(".json"):
            pids, rev, note = kl.load_channel_defaults(os.path.join(kl.CHANNELS_DIR, name))
            assert pids and rev > 0 and note, f"{name}: needs channels, defaults_revision and defaults_note"
            assert len({p.pid for p in pids}) == len(pids), f"{name}: duplicate PIDs"
    print("Channel lists ......... ok")

    for method in ("break", "360baud"):
        link = kl.KLine(dict(kl.DEFAULT_SETTINGS, port=kl.DEMO_PORT, init_method=method))
        link.open()
        info = link.start_session()
        assert info["key_bytes"] == "EA 8F" and info["diag"] == "accepted", info
        rpm = kl.DEFAULT_PIDS[0].decode(link.read_local_id(0x09))
        assert 0 < rpm < 9000
        link.stop()
        link.close()
        print(f"Handshake ({method:7s}) ... ok, demo RPM {rpm:.0f}")

    check_codes()
    print("Service codes ......... ok")

    check_dashboard()
    print("Dashboard limits ...... ok")

    link = kl.KLine(dict(kl.DEFAULT_SETTINGS, port=kl.DEMO_PORT))
    link.open()
    link.start_session()
    for p in kl.DEFAULT_PIDS:          # the demo ECU speaks the same scalings as the built-in channels
        v = p.decode(link.read_local_id(p.pid))
        assert (p.gauge_min or 0) <= v <= (p.gauge_max or v), f"{p.name}: demo reads {v:.1f} {p.units}"
    print("Demo vs defaults ...... ok")
    t0, n = time.perf_counter(), 0
    while time.perf_counter() - t0 < 1.5:
        link.read_local_id(0x09)
        n += 1
    link.close()
    print(f"Request rate .......... {n / 1.5:.1f} per second (demo ECU)")
    print("\nAll good. Start the app with: python pwc_scan.py")


if __name__ == "__main__":
    main()
