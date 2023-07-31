import ruamel.yaml
from ruamel.yaml.comments import CommentedMap


def process_string(input_string):
    """
    Converts the input string to an integer or float if possible, or returns it as a string.

    Parameters:
    - input_string (str): The input string to process.

    Returns:
    - int or float or str: The processed value of the input string.
    """
    try:
        return float(input_string) if "." in input_string else int(input_string)
    except ValueError:
        return input_string


def construct_mapping_with_comments(loader, node):
    """
    Constructs a CommentedMap object with comments from the provided loader and node.

    Parameters:
    - loader (ruamel.yaml.Loader): The YAML loader object.
    - node (ruamel.yaml.nodes.MappingNode): The YAML mapping node.

    Returns:
    - ruamel.yaml.comments.CommentedMap: The constructed CommentedMap object.
    """
    mapping = CommentedMap()
    loader.construct_mapping(node, mapping)
    # mapping.yaml_add_eol_comment("This is a comment", key=list(mapping.keys())[0])
    return mapping


def update_yaml_value(yaml_file, key_path, new_value, overwrite=True):
    """
    Updates the value of a YAML file at the specified key path with a new value.

    Parameters:
    - yaml_file (str): The path to the YAML file to update.
    - key_path (str): The key path in the YAML file where the value should be updated.
    - new_value (str or int or float): The new value to set at the specified key path.
    - overwrite (bool): If True, then it overwrites the existing file. If False it creates a new one called updated.yaml

    Raises:
    - ValueError: If the key path is not found in the YAML file.

    Returns:
    - None
    """
    # Load the YAML file
    with open(yaml_file, "r") as file:
        yaml = ruamel.yaml.YAML()
        yaml.constructor.add_constructor("tag:yaml.org,2002:map", construct_mapping_with_comments)
        data = yaml.load(file)

    # Update the value
    keys = key_path.split(".")
    current_data = data
    for key in keys[:-1]:
        try:
            current_data = current_data[process_string(key)]
        except:
            print(current_data[0][1])
            # print(current_data)
            raise ValueError
    current_data[keys[-1]] = process_string(str(new_value))  # force a string to then ensure float or int

    # Preserve the comments
    comments = data.ca.items

    # Save the updated YAML file with preserved comments
    final_path = yaml_file if overwrite else "updated.yaml"
    with open(final_path, "w") as file:
        yaml.dump(data, file)
