import paho.mqtt.client as mqtt
import pandas as pd
import json

# Load your initial dataset from a file
file_path = './modified_file.csv'  # Specify the file path here
df = pd.read_csv(file_path)

# MQTT setup
broker_address = "121.7.36.93"  # Add your broker address here
port = 30884  # Default MQTT port
topic = "spBv2.0/wms/NDATA/server/stock"  # Specify the MQTT topic
mqtt_username = "admin"  # Add your MQTT username here
mqtt_password = "public"  # Add your MQTT password here


def on_message(client, userdata, message):
    print("Received message: ", str(message.payload.decode("utf-8")))
    incoming_data = json.loads(message.payload)
    update_needed = False

    for item in incoming_data:
        # Check if the material exists in the DataFrame and the date is 2024-06-05
        condition = (df['warehouse_name'] == item['material']) & (df['date'] == '6/5/2024')
        if condition.any():
            # Update the DataFrame
            df.loc[condition, 'storage'] = item['quantity']
            update_needed = True
            print(f"Updated {item['material']} storage on 2024-06-05 to {item['quantity']}")

    # Save the DataFrame to a file if there were any updates
    if update_needed:
        df.to_csv(file_path, index=False)
        print(f"DataFrame updated and saved to {file_path}")

# MQTT client setup
client = mqtt.Client("ClientName")  # Create new instance with a unique client name
client.username_pw_set(mqtt_username, mqtt_password)  # Set username and password
client.on_message = on_message  # Attach the message function
client.connect(broker_address, port, 60)
client.subscribe(topic)  # Subscribe to the topic
client.loop_start()  # Start the loop

input("Press Enter to stop the script...")  # Keeps the script running
client.loop_stop()  # Stops the loop
client.disconnect()  # Disconnect the client