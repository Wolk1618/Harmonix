import mido

print("Available MIDI ports:")
available_ports = mido.get_output_names()
for i, port in enumerate(available_ports):
    print(f"{i}: {port}\n")