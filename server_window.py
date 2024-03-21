import socket
import mido
from mido import Message

vol_current_value = {
    1: 0,
    2: 0
}

fader_current_value = {
    1: 63,
    2: 63
}

max_value = 127
MIDIport = 1
change_by_percent_volume = 20
change_by_const = 20
loopBool = False

def change_volume(port_index, channel, controller, change_by_percent, change_type):
    available_ports = mido.get_output_names()
    if port_index >= len(available_ports):
        print("Invalid port index. Exiting.")
        return

    port_name = available_ports[port_index]
    with mido.open_output(port_name) as outport:
        change_value = int((max_value * change_by_percent) / 100)
        if change_type == 'U':
            new_value = min(max_value, vol_current_value[channel] + change_value)
        elif change_type == 'D':
            new_value = max(0, vol_current_value[channel] - change_value)
        else:
            print("Invalid change type. Exiting.")
            return

        cc_message = Message('control_change', channel=channel, control=controller, value=new_value)
        outport.send(cc_message)
        print(f"Sent volume change to {port_name}: {cc_message}")

        vol_current_value[channel] = new_value

def change_fader(port_index, channel, controller, change_by_constant, change_type):
    available_ports = mido.get_output_names()
    if port_index >= len(available_ports):
        print("Invalid port index. Exiting.")
        return

    port_name = available_ports[port_index]
    with mido.open_output(port_name) as outport:
        current_value = fader_current_value[channel]
        if change_type == 'U':
            new_value = min(max_value, current_value + change_by_constant)
        elif change_type == 'D':
            new_value = max(0, current_value - change_by_constant)
        else:
            print("Invalid change type. Exiting.")
            return

        cc_message = Message('control_change', channel=channel, control=controller, value=new_value)
        outport.send(cc_message)
        print(f"Sent fader change to {port_name}: {cc_message}")

        fader_current_value[channel] = new_value

def loop(port_index, channel, controller, valuez):
    available_ports = mido.get_output_names()
    if port_index >= len(available_ports):
        print("Invalid port index. Exiting.")
        return

    port_name = available_ports[port_index]
    with mido.open_output(port_name) as outport:
        cc_message = Message('control_change', channel=channel, control=controller, value=valuez)
        outport.send(cc_message)
        print(f"Sent Looper change to {port_name}: {cc_message}")


def start_server():
    host = '0.0.0.0'  # Listen on all network interfaces
    port = 12345  # Port to listen on

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Server started. Listening on {host}:{port}")

        try:
            while True:
                conn, _ = s.accept()
                with conn:
                    while True:
                        data = conn.recv(1024).decode().strip()
                        if not data:
                            break  # Exit the inner loop if no data
                        
                        # Check if the data starts with '0' or '1' and is followed by an integer between 1 and 5
                        if len(data) >= 2 and data[0] in ('0', '1') and data[1] in '12345':

                            channel = int(data[0]) + 1
                            command = int(data[1])

                            print(channel)
                            print(command)
                            print("\n")

                            if command == 1:  # Vol U
                                controller = 20  # Assuming 20 for volume control
                                change_volume(MIDIport, channel, controller, change_by_percent_volume, 'U')
                            elif command == 2:  # Vol D
                                controller = 20  # Assuming 20 for volume control
                                change_volume(MIDIport, channel, controller, change_by_percent_volume, 'D')
                            elif command == 3:  # Fader U
                                controller = 21  # Assuming 21 for fader control
                                change_fader(MIDIport, channel, controller, change_by_const, 'U')
                            elif command == 4:  # Fader D
                                controller = 21  # Assuming 21 for fader control
                                change_fader(MIDIport, channel, controller, change_by_const, 'D')
                            elif command == 5:  # Loop
                                controller = 22
                                loop(MIDIport, channel, controller, 100)
                        
                # Connection is closed, ready to accept a new connection
        except KeyboardInterrupt:
            print("Server is shutting down.")

start_server()
