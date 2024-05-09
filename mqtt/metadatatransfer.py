# import binascii
# import metatag_pb2
#
# # Create a MetaTagSequence
# metatag = metatag_pb2.MetaTagSequence()
#
# # Create and add the first MetaTag
# metatag1 = metatag.tags.add()
# metatag1.version = 1
# metatag1.name = "SC01"
# metatag1.showName = "SC01"
# metatag1.description = "SC01"
# metatag1.type = metatag_pb2.ValueType.Integer
#
# # Create and add the second MetaTag
# metatag2 = metatag.tags.add()
# metatag2.version = 1
# metatag2.name = "SC02"
# metatag2.showName = "SC02"
# metatag2.description = "SC02"
# metatag2.type = metatag_pb2.ValueType.Integer
#
# # Serialize the MetaTagSequence
# serialized_data = metatag.SerializeToString()
#
# # Print the entire MetaTagSequence and the serialized data in hexadecimal format
# print(metatag)
# print(binascii.hexlify(serialized_data))



import binascii
import metatag_pb2

def create_serialized_metatag(tags):
    # Create a MetaTagSequence
    metatag = metatag_pb2.MetaTagSequence()

    # Iterate over each tag data in the list
    for tag_data in tags:
        # Add a MetaTag based on provided inputs
        metatag_tag = metatag.tags.add()
        metatag_tag.version = 1  # Assuming version is fixed
        metatag_tag.name = tag_data['name']
        metatag_tag.showName = tag_data['showName']
        metatag_tag.description = tag_data['description']
        metatag_tag.type = tag_data['type']

    # Serialize the MetaTagSequence
    serialized_data = metatag.SerializeToString()

    # Optional: Print the entire MetaTagSequence and the serialized data in hexadecimal format
    print("Serialized MetaTagSequence:")
    print(metatag)
    print("Hexadecimal representation of serialized data:")
    print(binascii.hexlify(serialized_data))
    hex_data = binascii.hexlify(serialized_data).decode('utf-8')

    # Print the hexadecimal data
    print("Hexadecimal representation of serialized data:")
    print(hex_data)

    return hex_data
