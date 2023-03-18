import re
import os
import subprocess
import tkinter as tk
from tkinter import filedialog
import tempfile
import graphviz

# Constant to name the temporary folder
TMP_FOLDER_NAME = "temp"

def extract_source_info(line):
    """
    Extracts the source information from a Terraform code line.
    Returns a tuple containing the URL, PATH, and TAG components, or None if no match is found.
    """
    match = re.search(r'source\s*=\s*"(.+)"', line)
    if match:
        source_info = match.group(1)
        match = re.search(r'git::(.+)//(.+)\?ref=(.+)', source_info)
        if match:
            return match.group(1), match.group(2), match.group(3)
    return None

def get_dependencies(file_path):
    """
    Extracts all dependencies from a Terraform code file.
    Returns a list of tuples containing the URL, PATH, and TAG components of each dependency.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    dependencies = []
    for line in lines:
        source_info = extract_source_info(line)
        if source_info:
            dependencies.append(source_info)

    return dependencies

def clone_git_repo(git_ssh_url, git_tag, temp_folder):
    """
    Clones a Git repository to a temporary folder.
    Returns the path to the cloned repository.
    """
    tmp_dir = tempfile.mkdtemp(dir=temp_folder)

    cmd = ['git', 'clone', '--quiet', '-b', git_tag, '--depth', '1', git_ssh_url, tmp_dir]
    subprocess.run(cmd, check=True)

    return tmp_dir

def find_folder_path(directory, folder_name):
    """
    Searches for a folder with a given name inside a directory and its subdirectories.
    Returns the path of the first matching folder found, or None if no folder is found.
    """
    for root, dirs, _ in os.walk(directory):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    return None

def get_dependent_file_path(dependent_folder_path):
    """
    Searches for a Terraform file (main.tf or terragrunt.hcl) inside a folder and returns its path.
    If no Terraform file is found, prints a warning message and returns None.
    """
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
    """
    Computes the dependency tree of a Terraform file.
    Returns a dictionary with a nested structure that represents the dependency tree.
    """
    temp_folder = os.path.join(os.getcwd(), TMP_FOLDER_NAME)
    if not os.path.isdir(temp_folder):
        os.mkdir(temp_folder)

    dependencies = get_dependencies(file_path)
    if not dependencies:
        return None

    dependency_tree = {}
    for dependency in dependencies:
        url, path, tag = dependency
        dependent_repo_path = clone_git_repo(url, tag, temp_folder)
        dependent_folder_path = find_folder_path(dependent_repo_path, path)
        if dependent_folder_path:
            dependent_file_path = get_dependent_file_path(dependent_folder_path)
            if dependent_file_path:
                sub_dependency_tree = display_dependency_tree(dependent_file_path)
                if sub_dependency_tree:
                    dependency_tree[dependency] = sub_dependency_tree

    return dependency_tree

def browse_file_path():
    """
    Opens a file dialog and allows the user to select a Terraform file.
    Updates a StringVar variable with the file path.
    """
    file_path = filedialog.askopenfilename()
    if file_path:
        file_path_var.set(file_path)

def transform_dict_keys(data):
    """
    Transforms all the keys of a nested dictionary from tuples to strings.
    Replaces colons with forward slashes to allow for better visualization of Git repository URLs.
    """
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

def dict_to_tree(dictionary):
    """
    Converts a nested dictionary into a tree structure.
    Returns a dictionary with a 'name' key and a 'children' key.
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
                        add_children(child, sub_child)
                        if any(sub_child['children']):
                            child['children'].append(sub_child['children'])
            if child['name'] != "children":
                node['children'].append(child)

    tree = {'name': list(dictionary.keys())[0], 'children': []}
    add_children(tree, list(dictionary.values())[0])
    return tree

def visualize_tree(tree):
    """
    Generates a visualization of a tree structure.
    Returns a graphviz object.
    """
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

def analyze_file():
    """
    Analyzes a Terraform file and visualizes its dependency tree.
    """
    file_path = file_path_var.get()
    if not os.path.isfile(file_path):
        tk.messagebox.showerror("Error", "Invalid file path")
        return

    dependency_tree = display_dependency_tree(file_path)
    if not dependency_tree:
        tk.messagebox.showinfo("Info", "No dependencies found")
        return

    dependency_tree_str = transform_dict_keys(dependency_tree)
    file_name = os.path.basename(file_path)
    dependency_tree_str = {file_name: dependency_tree_str}

    tree = dict_to_tree(dependency_tree_str)
    graph = visualize_tree(tree)
    graph.render("dependency_tree", format="png")

if __name__ == '__main__':
    # Create the GUI interface
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

    # Run the GUI
    root.mainloop()