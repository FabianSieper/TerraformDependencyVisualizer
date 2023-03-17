import re
import os
import subprocess
import tkinter as tk
from tkinter import filedialog
import tempfile
import graphviz

TMP_FOLDER_NAME = "temp"

def extract_source_info(line):
    match = re.search(r'source\s*=\s*"(.+)"', line)
    if match:
        return match.group(1)
    else:
        return None

def extract_dependency_info(source_info):
    match = re.search(r'git::(.+)//(.+)\?ref=(.+)', source_info)
    if match:
        return match.group(1), match.group(2), match.group(3)
    else:
        return None, None, None

def get_dependencies(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    dependencies = []
    for line in lines:
        source_info = extract_source_info(line)
        if source_info:
            url, path, tag = extract_dependency_info(source_info)
            if url and path and tag:
                dependencies.append((url, path, tag))

    return dependencies

def create_tmp_folder_if_not_existent():
    # Create a temporary directory next to the current working directory
    temp_folder = os.path.join(os.getcwd(), TMP_FOLDER_NAME)
    if not os.path.isdir(temp_folder):
        os.mkdir(temp_folder)
    
    return temp_folder
def clone_git_repo(git_ssh_url, git_tag):

    temp_folder = create_tmp_folder_if_not_existent()
    tmp_dir = tempfile.mkdtemp(dir=temp_folder)

    # Clone the Git repo to the temporary directory
    cmd = ['git', 'clone', '--quiet', '-b', git_tag, '--depth', '1', git_ssh_url, tmp_dir]
    subprocess.run(cmd, check=True)

    return tmp_dir

def find_folder_path(directory, folder_name):
    for root, dirs, _ in os.walk(directory):
        if folder_name in dirs:
            return os.path.join(root, folder_name)

    return None

def get_dependent_file_path(dependent_folder_path):

    main_path = os.path.join(dependent_folder_path, "main.tf")
    terragrunt_path = os.path.join(dependent_folder_path, "terragrunt.hcl")

    if os.path.isfile(main_path):
        return main_path
    elif os.path.isfile(terragrunt_path):
        return terragrunt_path
    else:
        print("[WARNING] - No main.tf or terragrunt.hcl file was found")
        return None

def display_dependency_tree(file_path):

    dependencies = get_dependencies(file_path)
    
    # Create a dictionary from the depenencies list
    dependencies_dict = {tup : [] for tup in dependencies}

    for dependency in dependencies_dict.keys():

        url, path, tag = dependency

        tmp_dir = clone_git_repo(url, tag)

        # Go to file path of dependency to compute further depenencies
        dependent_folder_path = find_folder_path(tmp_dir, path)
        dependent_file_path = get_dependent_file_path(dependent_folder_path)

        # Get depenencies of file
        sub_dependencies = display_dependency_tree(dependent_file_path)

        dependencies_dict[dependency].append(sub_dependencies)

    if len(dependencies_dict.keys()) == 0:
        return None
    
    return dependencies_dict


def browse_file_path():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_path_var.set(file_path)

def transform_dict_keys(data):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if isinstance(key, tuple):
                new_key = ' // '.join(str(x) for x in key)
                new_key = new_key.replace(":", "/")
            else:
                new_key = key
            new_dict[new_key] = transform_dict_keys(value)
        return new_dict
    elif isinstance(data, list):
        new_list = []
        for item in data:
            new_list.append(transform_dict_keys(item))
        return new_list
    else:
        return data
    

def analyze_file():
    file_path = file_path_var.get()
    if not os.path.isfile(file_path):
        tk.messagebox.showerror("Error", "Invalid file path")
        return

    dependency_dict = display_dependency_tree(file_path)
        
    # transform all keys from tuples to strings
    dependency_dict_str = transform_dict_keys(dependency_dict)


    # Add file_path folder, to the top of the depenency_dict
    dependency_dict_str = {file_path.split("/")[-2]: dependency_dict_str}

    tree = dict_to_tree(dependency_dict_str)
    graph = visualize_tree(tree)
    graph.render("tree", format="png")
    

def dict_to_tree(dictionary):
    """
    Converts a dictionary of dictionaries to a tree structure.
    """
    def add_children(node, children_dict):
        for key, value in children_dict.items():
            child = {'name': key}
            if isinstance(value, dict):
                child['children'] = []
                add_children(child, value)

            else:

                child['children'] = []

                for sub_child in value:

                    if sub_child:
                        
                        sub_child['children'] = []
                        add_children(child, sub_child)
                        if any(sub_child['children']):
                            child['children'].append(sub_child['children'])



            if child['name'] != "children":
                node['children'].append(child)

    tree = {'name': list(dictionary.keys())[0], 'children': []}
    add_children(tree, list(dictionary.values())[0])
    return tree

def visualize_tree(tree):

    def add_node(node, graph):
        if 'name' in node:
            name = node['name']

            graph.node(name)
            if 'children' in node:
                for child in node['children']:
                    
                    if child:
                        child_name = child['name']
                        graph.edge(name, child_name)
                        add_node(child, graph)

    graph = graphviz.Digraph()
    add_node(tree, graph)
    return graph

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Dependency Analyzer")

    # Create the file path selection widgets
    file_path_label = tk.Label(root, text="File path:")
    file_path_var = tk.StringVar()
    file_path_entry = tk.Entry(root, textvariable=file_path_var, width=50)
    file_path_browse_button = tk.Button(root, text="Browse...", command=browse_file_path)

    # Create the analyze button
    analyze_button = tk.Button(root, text="Analyze", command=analyze_file)

    # Pack the widgets
    file_path_label.pack(side=tk.LEFT, padx=(10, 0), pady=10)
    file_path_entry.pack(side=tk.LEFT, padx=(0, 10), pady=10, fill=tk.X, expand=True)
    file_path_browse_button.pack(side=tk.LEFT, pady=10)
    analyze_button.pack(side=tk.BOTTOM, padx=10, pady=10)

    root.mainloop()
