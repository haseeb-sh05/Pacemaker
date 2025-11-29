import serial

SYNC = 0x16
FN_SET = 0x55

print("Mock Pacemaker starting on COM4...")

pacemaker = serial.Serial("COM4", 115200, timeout=1)

buffer = []
ascii_buffer = ""

while True:
    if pacemaker.in_waiting > 0:
        byte = pacemaker.read(1)

        # ---------------------
        # ASCII COMMANDS
        # ---------------------
        if byte in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?0123456789":
            ascii_buffer += byte.decode()

            if ascii_buffer.endswith("\n") or ascii_buffer == "ID?":
                cmd = ascii_buffer.strip()

                if cmd == "ID?":
                    pacemaker.write(b"DEVICE_ID:PACEMAKER\n")
                    print("Sent device ID")

                ascii_buffer = ""

            continue

        # ---------------------
        # PACKET MODE (20 bytes)
        # ---------------------
        value = byte[0]

        if len(buffer) == 0:
            if value == SYNC:
                buffer.append(value)
            continue
        else:
            buffer.append(value)

        if len(buffer) == 20:
            print("\nReceived 20-byte packet:", buffer)

            if buffer[1] != FN_SET:
                print("Invalid FN CODE")
                buffer = []
                continue

            MODE             = buffer[2]
            LRL              = buffer[3]
            URL              = buffer[4]
            MSR              = buffer[5]   # <-- ADDED
            ARP              = buffer[6]
            VRP              = buffer[7]
            PVARP            = buffer[8]
            ATR_AMP          = buffer[9]
            VENT_AMP         = buffer[10]
            ATR_PW           = buffer[11]
            VENT_PW          = buffer[12]
            ATR_SENS         = buffer[13]
            VENT_SENS        = buffer[14]
            ReactionTime     = buffer[15]
            RecoveryTime     = buffer[16]
            ResponseFactor   = buffer[17]
            ActivityThresh   = buffer[18]
            EGRAM_FLAG       = buffer[19]

            # Print parsed values
            print("----- Parsed Packet -----")
            print("MODE:", MODE)
            print("LRL:", LRL)
            print("URL:", URL)
            print("MSR:", MSR)
            print("ARP:", ARP)
            print("VRP:", VRP)
            print("PVARP:", PVARP)
            print("Atrial Amp:", ATR_AMP)
            print("Ventricle Amp:", VENT_AMP)
            print("Atrial PW:", ATR_PW)
            print("Ventricular PW:", VENT_PW)
            print("Atrial Sensitivity:", ATR_SENS)
            print("Ventricular Sensitivity:", VENT_SENS)
            print("Reaction Time:", ReactionTime)
            print("Recovery Time:", RecoveryTime)
            print("Response Factor:", ResponseFactor)
            print("Activity Threshold:", ActivityThresh)
            print("EGRAM FLAG:", EGRAM_FLAG)
            print("-------------------------")

            # Respond OK
            pacemaker.write(b"PARAM OK\n")

            buffer = []
