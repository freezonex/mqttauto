import csv
import os
from datetime import datetime
from mqttauto.mqtt.akskg import SignRequest
import time
import csv
import paho.mqtt.client as mqtt
from mqttauto.mqtt.realdatatransfer import create_serialized_value_sequence
import time

attribute_names = [
    'SC01', 'SC10', 'SC12', 'SC14', 'SC15', 'SC16', 'SC17', 'SC18', 'SC19', 'SC02', 'SC20', 'SC21', 'SC22',
    'SC23', 'SC24', 'SC25', 'SC26', 'SC27', 'SC28', 'SC29', 'SC03', 'SC30', 'SC31', 'SC32', 'SC34', 'SC35',
    'SC36', 'SC37', 'SC38', 'SC39', 'SC04', 'SC40', 'SC41', 'SC43', 'SC44', 'SC46', 'SC47', 'SC48', 'SC49',
    'SC05', 'SC51', 'SC52', 'SC53', 'SC54', 'SC55', 'SC56', 'SC57', 'SC58', 'SC06', 'SC60', 'SC61', 'SC63',
    'SC66', 'SC68', 'SC07', 'SC08', 'SC09'
]

# Store for holding previous day's values
values_store = {}

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


def fetch_all_data(date):
    sign_request = SignRequest()
    endpoint = "/open-api/supos/oodm/v2/attribute/current"
    inputs = [f"system.Collect Template.mltest.system.{name}" for name in attribute_names]
    data = {"inputs": inputs}
    try:
        response = sign_request.post(endpoint, data)
        response.encoding = 'utf-8'
        response_data = response.json()
        return [(name, date, response_data['data'].get(f"system.Collect Template.mltest.system.{name}", {}).get('value', 'No Storage Data')) for name in attribute_names]
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return [(name, date, 'Error') for name in attribute_names]

def fetch_date_with_retry(max_retries=3):
    endpoint = "/open-api/supos/oodm/v2/attribute/current"
    retries = 0
    inputs = [f"system.Collect Template.mltest.system.date"]
    data = {"inputs": inputs}
    sign_request = SignRequest()
    while retries < max_retries:
        try:
            response = sign_request.post(endpoint, data)
            if response.status_code == 200:
                response_data = response.json()
                date_value = response_data['data'].get('system.Collect Template.mltest.system.date', {}).get('value', None)
                if date_value:
                    return datetime.strptime(date_value, "%Y-%m-%d").strftime("%Y-%m-%d")
            retries += 1
            time.sleep(10)  # wait 10 seconds before retrying
        except Exception as e:
            print(f"Attempt {retries + 1} failed: {e}")
            retries += 1
    return '1111-11-11'  # return this only if all retries fail

def write_to_csv(attribute, data):
    file_path = 'output_data.csv'
    write_header = not os.path.exists(file_path)
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(['Attribute', 'Date', 'Storage', 'Next Day Storage'])
        writer.writerow(data)

def update_values_store(results_array, date):
    global values_store
    for attribute, _, value in results_array:
        if attribute in values_store:
            # Write current and next day storage
            write_to_csv(attribute, values_store[attribute] + [value])
        # Update the store with current data
        values_store[attribute] = [attribute, date, value]


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish

    client.connect(broker_address, port, 60)
    client.loop_start()  # Start a non-blocking loop

    try:
        while True:
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

                    time.sleep(2)  # Wait for 5 seconds before the next publish
                    current_date = fetch_date_with_retry()
                    if current_date != '1111-11-11':
                        results_array = fetch_all_data(current_date)
                        update_values_store(results_array, current_date)
                    else:
                        print("Failed to fetch valid date, skipping this cycle.")
                    time.sleep(5)

    finally:
        client.loop_stop()  # Stop the loop
        client.disconnect()  # Disconnect from the broker






if __name__ == '__main__':
    main()

