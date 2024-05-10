import csv
import time
import os
from datetime import datetime
from mqttauto.mqtt.akskg import SignRequest
import concurrent.futures
from functools import partial

# List of instance names excluding 'date'
attribute_names = ['SC01', 'SC10', 'SC12', 'SC14', 'SC15', 'SC16', 'SC17', 'SC18', 'SC19', 'SC02', 'SC20', 'SC21', 'SC22',
                   'SC23', 'SC24', 'SC25', 'SC26', 'SC27', 'SC28', 'SC29', 'SC03', 'SC30', 'SC31', 'SC32', 'SC34', 'SC35',
                   'SC36', 'SC37', 'SC38', 'SC39', 'SC04', 'SC40', 'SC41', 'SC43', 'SC44', 'SC46', 'SC47', 'SC48', 'SC49',
                   'SC05', 'SC51', 'SC52', 'SC53', 'SC54', 'SC55', 'SC56', 'SC57', 'SC58', 'SC06', 'SC60', 'SC61', 'SC63',
                   'SC66', 'SC68', 'SC07', 'SC08', 'SC09']

# Dictionary to store the previous day's values
previous_values = {}
values_store = {}
def fetch_data(attribute_name, date, retries=3):
    """Function to fetch data for a given instance with retry logic."""
    sign_request = SignRequest()
    data = {
        "inputs": [f"system.Collect Template.mltest.system.{attribute_name}"],
    }
    endpoint = "/open-api/supos/oodm/v2/attribute/current"
    for attempt in range(retries):
        try:
            response = sign_request.post(endpoint, data)
            response.encoding = 'utf-8'
            response_data = response.json()

            value_entry = response_data['data'].get(f'system.Collect Template.mltest.system.{attribute_name}', {})
            value = value_entry.get('value', 'No Storage Data')
            return [attribute_name, date, value]
        except Exception as e:
            print(f"Error on attempt {attempt + 1} for {attribute_name}: {e}")
            if attempt == retries - 1:
                return [attribute_name, date, 'Error']

def write_to_csv():
    """ Write the stored data to CSV, including next day values. """
    file_path = 'output_data.csv'
    file_exists = os.path.exists(file_path)
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['warehouse_name', 'date', 'storage', 'next_day_storage'])

        for attribute, data in values_store.items():
            if len(data) > 1:
                # Write previous day data with next day value
                writer.writerow(data[0] + [data[1][2]])  # Previous day row with next day storage
                values_store[attribute] = data[1:]  # Remove the written day

def update_values_store(results_array, date):
    """ Update the stored values with new data. """
    for result in results_array:
        if result[0] in values_store:
            # Append new data for next day processing
            values_store[result[0]].append(result)
        else:
            # Initialize with today's data
            values_store[result[0]] = [result]

def fetch_date():
    """Function to fetch the current date."""
    sign_request = SignRequest()
    data = {"inputs": ["system.Collect Template.mltest.system.date"]}
    endpoint = "/open-api/supos/oodm/v2/attribute/current"
    try:
        response = sign_request.post(endpoint, data)
        response.encoding = 'utf-8'
        response_data = response.json()
        date_value = response_data['data'].get('system.Collect Template.mltest.system.date', {}).get('value', '1111/11/11')
        return date_value
    except Exception as e:
        print(f"Failed to fetch date: {e}")
        return '1111/11/11'

def main():
    stop_date = datetime.strptime("2023/11/30", "%Y/%m/%d")
    while True:
        current_date_str = fetch_date()
        current_date = datetime.strptime(current_date_str, "%Y/%m/%d")
        flag = 0
        if current_date == stop_date:
            if flag != 0:
                break
            flag += 1
        results_array = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fetch_with_date = partial(fetch_data, date=current_date_str)
            results = executor.map(fetch_with_date, attribute_names)
            results_array.extend(results)

        update_values_store(results_array, current_date_str)
        write_to_csv()  # Write the previous day's data with today's values
        time.sleep(6)

if __name__ == '__main__':
    main()