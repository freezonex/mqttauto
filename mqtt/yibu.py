import csv
import time
import os
from datetime import datetime
from mqttauto.mqtt.akskg import SignRequest
import concurrent.futures
from functools import partial

attribute_names = ['SC01', 'SC10', 'SC12', 'SC14', 'SC15', 'SC16', 'SC17', 'SC18', 'SC19', 'SC02', 'SC20', 'SC21', 'SC22',
                   'SC23', 'SC24', 'SC25', 'SC26', 'SC27', 'SC28', 'SC29', 'SC03', 'SC30', 'SC31', 'SC32', 'SC34', 'SC35',
                   'SC36', 'SC37', 'SC38', 'SC39', 'SC04', 'SC40', 'SC41', 'SC43', 'SC44', 'SC46', 'SC47', 'SC48', 'SC49',
                   'SC05', 'SC51', 'SC52', 'SC53', 'SC54', 'SC55', 'SC56', 'SC57', 'SC58', 'SC06', 'SC60', 'SC61', 'SC63',
                   'SC66', 'SC68', 'SC07', 'SC08', 'SC09']


values_store = {}
last_known_date = None

def fetch_data(attribute_name, date, retries=3):
    sign_request = SignRequest()
    data = {"inputs": [f"system.Collect Template.mltest.system.{attribute_name}"]}
    endpoint = "/open-api/supos/oodm/v2/attribute/current"
    for attempt in range(retries):
        try:
            response = sign_request.post(endpoint, data)
            response.encoding = 'utf-8'
            response_data = response.json()
            value = response_data['data'].get(f'system.Collect Template.mltest.system.{attribute_name}', {}).get('value', 'No Storage Data')
            return [attribute_name, date, value]
        except Exception as e:
            print(f"Error on attempt {attempt + 1} for {attribute_name}: {e}")
            if attempt == retries - 1:
                return [attribute_name, date, 'Error']

def write_to_csv(attribute, data):
    """ Write to CSV immediately after fetching data """
    file_path = 'output_data.csv'
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not os.path.exists(file_path):
            writer.writerow(['warehouse_name', 'date', 'storage', 'next_day_storage'])
        writer.writerow(data)

def update_values_store(results_array, date):
    """ Update the stored values with new data and write to CSV. """
    global values_store
    for result in results_array:
        attribute, _, value = result
        if attribute in values_store:
            # Write previous day's data with current day as next_day_storage
            write_to_csv(attribute, values_store[attribute] + [value])
            values_store[attribute] = result  # Update the current day's data
        else:
            # Store the data initially without next_day_storage
            values_store[attribute] = result

def fetch_date():
    global last_known_date
    sign_request = SignRequest()
    data = {"inputs": ["system.Collect Template.mltest.system.date"]}
    endpoint = "/open-api/supos/oodm/v2/attribute/current"
    try:
        response = sign_request.post(endpoint, data)
        response.encoding = 'utf-8'
        response_data = response.json()
        date_value = response_data['data'].get('system.Collect Template.mltest.system.date', {}).get('value', '1111-11-11')
        current_date = datetime.strptime(date_value, "%Y-%m-%d")
        last_known_date = current_date
        return date_value
    except Exception as e:
        print(f"Failed to fetch date: {e}")
        return '1111-11-11'

def main():
    while True:
        current_date_str = fetch_date()
        results_array = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fetch_with_date = partial(fetch_data, date=current_date_str)
            results = executor.map(fetch_with_date, attribute_names)
            results_array.extend(results)

        update_values_store(results_array, current_date_str)
        time.sleep(30)

if __name__ == '__main__':
    main()
