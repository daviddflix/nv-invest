# polylastic = '4.697e-05'
# sats = '6.07663e-07'
# value = format(float(sats), '.12f')
# print(value)
# print(type(value))
# import json

# Calculate the closest multiple of 5 less than or equal to the number
def closest_multiples_of_5(number):
    lower_multiple = (number // 5) * 5
    if lower_multiple == 0:
        return False
    return lower_multiple

# Calculate the closest multiple of 10 less than or equal to the number
def closest_multiples_of_10(number):
    lower_multiple = (number // 10) * 10
    if lower_multiple == 0:
        return False
    return lower_multiple

# Example usage
# given_number = 0
# result = closest_multiples_of_10(given_number)
# print(f"The closest multiples of 5 to {given_number} is {result}")
