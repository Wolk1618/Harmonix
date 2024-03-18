import mido
from mido import Message

global vol_current_value_A
global vol_current_value_B
vol_current_value_A = 0
vol_current_value_B = 0
max_value = 127

# Function to send MIDI control change to increase volume
def increase_volume(port_index, channel, controller, increase_by_percent):

    available_ports = mido.get_output_names()
    if port_index >= len(available_ports):
        print("Invalid port index. Exiting.")
        return

    port_name = available_ports[port_index]

    with mido.open_output(port_name) as outport:
        increase_value = int((max_value * increase_by_percent) / 100)
        new_value = min(max_value, vol_current_value_A + increase_value)  # Ensure the new value does not exceed the max

        # Construct the MIDI message
        cc_message = Message('control_change', channel=channel, control=controller, value=new_value)
        outport.send(cc_message)
        print(f"Sent volume increase to {port_name}: {cc_message}")

        vol_current_value_A = new_value  # Update the current value
        
def decrease_volume(port_index, channel, controller, decrease_by_percent):

    available_ports = mido.get_output_names()
    if port_index >= len(available_ports):
        print("Invalid port index. Exiting.")
        return

    port_name = available_ports[port_index]

    with mido.open_output(port_name) as outport:
        decrease_value = int((max_value * decrease_by_percent) / 100)
        new_value = max(0, vol_current_value_B - decrease_value)  # Ensure the new value does not go below 0

        # Construct the MIDI message
        cc_message = Message('control_change', channel=channel, control=controller, value=new_value)
        outport.send(cc_message)
        print(f"Sent volume decrease to {port_name}: {cc_message}")  # Corrected print statement

        vol_current_value_B = new_value  # Update the current value


# List available MIDI ports
print("Available MIDI ports:")
available_ports = mido.get_output_names()
for i, port in enumerate(available_ports):
    print(f"{i}: {port}\n")

# Ask the user to select the port by index




# Increase volume by 20%
increase_by_percent = 20

while (1):
    # Send the control change message
    userInp1st = input('Channel A or B: ')
    if userInp1st == 'A':
        # MIDI parameters
        channel = 1  
        controller = 20  # The controller number for volume
        userInp = input('Vol U or Vol D: ')
        
        if userInp == 'U':
            increase_volume(1, channel, controller, increase_by_percent)
        else:
            decrease_volume(1, channel, controller, increase_by_percent)
    else:
        # MIDI parameters
        channel = 2  
        controller = 20  # The controller number for volume
        userInp = input('Vol U or Vol D: ')
        
        if userInp == 'U':
            increase_volume(1, channel, controller, increase_by_percent)
        else:
            decrease_volume(1, channel, controller, increase_by_percent)

