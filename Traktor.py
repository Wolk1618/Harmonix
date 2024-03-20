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


# List available MIDI ports
print("Available MIDI ports:")
available_ports = mido.get_output_names()
for i, port in enumerate(available_ports):
    print(f"{i}: {port}\n")

MIDIport = 1
change_by_percent_volume = 20
change_by_const = 10
loopBool = False

#while True:
#    userInp1st = input('Channel A or B: ')
#    if userInp1st in ['A', 'B']:
#        channel = 1 if userInp1st == 'A' else 2
#        userInp = input('Vol U, Vol D, Fader U, Fader D, Loop: ')
#
#        if 'Vol' in userInp:
#            controller = 20  # Assuming 20 for volume control
#            change_type = userInp[-1]
#            change_volume(MIDIport, channel, controller, change_by_percent_volume, change_type)
#        elif 'Fader' in userInp:
#            controller = 21  # Assuming 21 for fader control
#            change_type = userInp[-1]
#            change_fader(MIDIport, channel, controller, change_by_const, change_type)
#        elif 'Loop' in userInp:
#            controller = 22
#            loop(MIDIport, channel, controller, 100)
#                
#        else:
#            print("Invalid input. Please enter 'Vol U', 'Vol D', 'Fader U', or 'Fader D'.")
#    else:
#        print("Invalid input. Please enter 'A' for channel A or 'B' for channel B.")
        
while True:
    userInp1st = input('Channel 0 or 1: ')
    if userInp1st in ['0', '1']:
        channel = int(userInp1st) + 1  # Convert to integer and adjust channel number
        
        print('1: Vol U, 2: Vol D, 3: Fader U, 4: Fader D, 5: Loop')
        userInp = input('Enter action number: ')

        if userInp == '1':  # Vol U
            controller = 20  # Assuming 20 for volume control
            change_volume(MIDIport, channel, controller, change_by_percent_volume, 'U')
        elif userInp == '2':  # Vol D
            controller = 20  # Assuming 20 for volume control
            change_volume(MIDIport, channel, controller, change_by_percent_volume, 'D')
        elif userInp == '3':  # Fader U
            controller = 21  # Assuming 21 for fader control
            change_fader(MIDIport, channel, controller, change_by_const, 'U')
        elif userInp == '4':  # Fader D
            controller = 21  # Assuming 21 for fader control
            change_fader(MIDIport, channel, controller, change_by_const, 'D')
        elif userInp == '5':  # Loop
            controller = 22
            loop(MIDIport, channel, controller, 100)
        else:
            print("Invalid input. Please enter a number between 1 and 5.")
    else:
        print("Invalid input. Please enter '0' for channel 1 or '1' for channel 2.")
