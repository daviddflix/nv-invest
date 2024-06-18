import os 
import json
import requests
from monday import MondayClient
from dotenv import load_dotenv
load_dotenv() 

MONDAY_API_KEY_NOVATIDE = os.getenv("MONDAY_API_KEY_NOVATIDE")

monday_client = MondayClient(MONDAY_API_KEY_NOVATIDE)
monday_url = "https://api.monday.com/v2"

headers = {
    "Content-Type": "application/json",
    "Authorization": MONDAY_API_KEY_NOVATIDE
}      

def SUM(*args):
    return sum(args)

def resolve_formula(formula, columns_data, recursion_depth=0):
    """
    Recursively resolves formulas by replacing placeholders with actual values
    from column data, running up to three recursive levels.
    
    Args:
    - formula (str): The formula string to resolve.
    - columns_data (dict): Dictionary containing column data where keys are column ids.
    - recursion_depth (int): Current recursion depth (default is 0).
    
    Returns:
    - str: Resolved formula with actual values substituted.
    """
    if not formula or not columns_data or recursion_depth > 3:
        return ""

    # Find placeholders in the formula (e.g., {column123})
    placeholders = set()
    start = 0
    while True:
        start = formula.find('{', start)
        if start == -1:
            break
        end = formula.find('}', start)
        if end == -1:
            break
        placeholders.add(formula[start + 1:end])
        start = end + 1

    # Replace each placeholder with its actual value
    for placeholder in placeholders:
        column_id = placeholder
        if column_id in columns_data:
            column_value = columns_data[column_id]['text']
            print("column_id: ", column_id)
            print("column_value: ", column_value)
            if column_value == '':
                formula = formula.replace(f'{{{placeholder}}}', column_value if column_value else '0')


    # Evaluate the formula
    try:
        result = eval(formula, {"SUM": SUM, "__builtins__": {}})
        print(" result: ", result)
        print(" result: ", type(result))
    except Exception as e:
        print(f"Error evaluating formula '{formula}': {e}")
        return ""

    # If the result is a string, it might still contain unresolved placeholders
    if isinstance(result, str):
        return resolve_formula(result, columns_data, recursion_depth + 1)
    else:
        return str(result)




# Get column id, name and value of each column and row in the boards
def get_board_item_general_test(board_ids, limit=500):
    result = {'error': None, 'data': [], 'success': False}
    
    if not board_ids or not isinstance(board_ids, list):
        result['error'] = 'Invalid board_ids parameter. It should be a non-empty list.'
        return result
    
    if not isinstance(limit, int) or limit <= 0:
        result['error'] = 'Invalid limit parameter. It should be a positive integer.'
        return result

    board_ids_str = ', '.join(map(str, board_ids))
    
    query = f'''
    query {{
        boards(ids: [{board_ids_str}]) {{
            id
            name
            columns {{
                id
                title
                settings_str
            }}
            items_page(limit: {limit}) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                    
                    }}
                }}
            }}
        }}
    }}
    '''
    
    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()

        if 'errors' in data:
            result['error'] = f"GraphQL query error: {data['errors']}"
            return result

        boards = data.get('data', {}).get('boards', [])

        for board in boards:
            board_name = board.get('name')
            board_id = board.get('id')
            items = board.get('items_page', {}).get('items', [])

            # Prepare board dictionary with items
            board_dict = {
                'board_name': board_name,
                'id': board_id,
                'items': []
            }

            columns = {column['id']: {'title': column['title'], 'settings_str': column['settings_str']} for column in board['columns']}

            for item in items:
                item_id = item.get('id')
                item_name = item.get('name')
                column_values = item.get('column_values', [])

                # Prepare item dictionary
                item_dict = {
                    'id': item_id,
                    'name': item_name,
                    'column_values': []
                }

                for column_value in column_values:
                    column_id = column_value.get('id')
                    text = column_value.get('text')

                    # Determine if column is a formula column
                    is_formula = False
                    raw_formula = None
                    parsed_formula = None
                    value = None

                    if column_id in columns:
                        settings_str = columns[column_id]['settings_str']
                        formatted_formula = json.loads(settings_str)
                        if 'formula' in settings_str.lower():
                            is_formula = True
                            raw_formula = settings_str
                            parsed_formula = formatted_formula.get('formula', None)
                            # print("\nparsed_formula: ", parsed_formula)
                            # print("column_name: ", columns[column_id]['title'])

                            # # Resolve formula
                            # if is_formula:
                            #     # parsed_formula = resolve_formulas(columns, columns_data)
                            #     value = resolve_formula(parsed_formula, columns_data)

                    # Add column details to column_values
                    column_details = {
                        'id': column_id,
                        'text': text,
                        'name': columns[column_id]['title'],
                        'is_formula': is_formula,
                        'raw_formula': raw_formula,
                        'parsed_formula': parsed_formula,
                        'result_formula': value
                    }

                    item_dict['column_values'].append(column_details)

                board_dict['items'].append(item_dict)

            result['data'].append(board_dict)

        result['success'] = True

        # Write result to a JSON file
        with open('board_items.json', 'w') as json_file:
            json.dump(result, json_file, indent=4)

    except requests.exceptions.RequestException as e:
        result['error'] = f"Request error: {str(e)}"
    
    return result



# get_board_item_general_test(board_ids=[1397034863])