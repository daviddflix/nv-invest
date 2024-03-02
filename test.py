
with open('coingecko_coins.txt', 'r', encoding='utf-8') as file:
    for line in file:
        # Evaluate the line as a dictionary
        data = eval(line.strip())
        
        # Print each item in the dictionary
        for key, value in data.items():
            print(f'{key}: {value}')
        print()
        