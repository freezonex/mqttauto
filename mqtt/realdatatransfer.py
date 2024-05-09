# import binascii
# import metatag_pb2
#
# # Create a MetaTagSequence
# namedvalue = metatag_pb2.ValueSequence()
#
# # Create and add the first MetaTag
# rtdvalue1 = namedvalue.values.add()
# rtdvalue1.name = "exampleTag1"
# rtdvalue1.value.dblVal = 89
# rtdvalue1.value.quality = 2
#
# rtdvalue2 = namedvalue.values.add()
# rtdvalue2.name = "exampleTag2"
# rtdvalue2.value.dblVal = 32.59
# rtdvalue1.value.quality = 8
#
# # Serialize the MetaTagSequence
# serialized_data = namedvalue.SerializeToString()
#
# # Print the entire MetaTagSequence and the serialized data in hexadecimal format
# print(namedvalue)
# print(binascii.hexlify(serialized_data))

import binascii
from mqttauto.mqtt import metatag_pb2


def create_serialized_value_sequence(values):
    # Create a ValueSequence
    namedvalue = metatag_pb2.ValueSequence()

    # Iterate over each value data in the list
    for value_data in values:
        # Add a Value to the sequence
        rtdvalue = namedvalue.values.add()
        rtdvalue.name = value_data['name']
        if 'strVal' in value_data and value_data['strVal'] != "":
            rtdvalue.value.strVal = value_data['strVal']
        else:
            rtdvalue.value.dblVal = value_data['dblVal']

        rtdvalue.value.quality = value_data['quality']

    # Serialize the ValueSequence
    serialized_data = namedvalue.SerializeToString()

    # Optional: Print the entire ValueSequence and the serialized data in hexadecimal format
    print("Serialized ValueSequence:")
    print(namedvalue)
    print("Hexadecimal representation of serialized data:")
    print(binascii.hexlify(serialized_data))

    return serialized_data


