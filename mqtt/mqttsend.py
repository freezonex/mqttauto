import csv
import paho.mqtt.client as mqtt
from mqttauto.mqtt.realdatatransfer import create_serialized_value_sequence
import time

# MQTT broker details
broker_address = "47.236.10.165"
port = 32566  # Default MQTT port

topic = "/239f67e0-0b85-11ef-b05c-7df9e9869244/mltest/mltest/rtdvalue/report"
qos = 0  # Quality of Service level 0
retain = True  # Retain flag

# CSV File path
csv_file_path =  'C:\\Users\\shimu\\Desktop\\朱佳楠\\AI\\train_data1.csv'

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_publish(client, userdata, mid):
    print("Message Published.")

def publish_message(client, topic, data, serialize_function):
    # Call the appropriate serialization function
    encoded_message = serialize_function(data)
    client.publish(topic, payload=encoded_message, qos=qos, retain=retain)

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish

    client.connect(broker_address, port, 60)
    client.loop_start()  # Start a non-blocking loop

    try:
        current_count = 1
        max_count_found = False
        while not max_count_found:
            with open(csv_file_path, mode='r') as file:
                reader = csv.DictReader(file)
                data_to_publish = []
                date_for_current_count = ""
                for row in reader:
                    if int(row['count']) == current_count:
                        data_to_publish.append({
                            'name': row['warehouse name'],
                            'dblVal': int(row['storage']),
                            'quality': int(row['count']),
                        })
                        date_for_current_count = row['date']  # Capture the date
                if data_to_publish:
                    # Append the common date for the current count
                    data_to_publish.append({'name': "date", 'strVal': date_for_current_count, 'quality': 8})
                    print(f"Publishing data for count: {current_count}")
                    publish_message(client, topic, data_to_publish, create_serialized_value_sequence)
                    current_count += 1  # Increment to the next count
                else:
                    max_count_found = True  # Exit the loop if no data for current count
            time.sleep(6)  # Wait for 5 seconds before the next publish
    finally:
        client.loop_stop()  # Stop the loop
        client.disconnect()  # Disconnect from the broker


if __name__ == "__main__":
    main()