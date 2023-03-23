import re
import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import tempfile
import graphviz
import sys
import glob
import tqdm

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
    Returns the path to the cloned repository or None if the cloning fails.
    """
    tmp_dir = tempfile.mkdtemp(dir=temp_folder)

    cmd = ['git', 'clone', '--quiet', '-b', git_tag, '--depth', '1', git_ssh_url, tmp_dir]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return tmp_dir
    except subprocess.CalledProcessError:
        print(f"[ERROR] - Failed to clone repository: {git_ssh_url}")
        return None

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

def add_no_dependencies_node(file_name, graph):
    """
    Adds a 'no further dependencies' node to the graph.
    """
    graph.node("No further dependencies")
    graph.edge(file_name, "No further dependencies")


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
        
        if dependent_repo_path:
            dependent_folder_path = find_folder_path(dependent_repo_path, path)

            if dependent_folder_path:
                dependent_file_path = get_dependent_file_path(dependent_folder_path)
                if dependent_file_path:
                    sub_dependency_tree = display_dependency_tree(dependent_file_path)
                    if sub_dependency_tree:
                        dependency_tree[dependency] = sub_dependency_tree
                    else:
                        dependency_tree[dependency] = {}
                else:
                    dependency_tree[dependency] =  {"ERROR DOWNLOADING": ""}
        else:
            dependency_tree[dependency] = {"ERROR DOWNLOADING": ""}

    return dependency_tree


def browse_file_path():
    """
    Opens a file dialog and allows the user to select a Terraform file or a folder.
    Updates a StringVar variable with the file path or folder path.
    """
    file_path = filedialog.askopenfilename()
    if file_path:
        file_path_var.set(file_path)
        clear_log_output()
        analyze_file()


def analyze_directory():
    """
    Analyzes a directory and visualizes the dependency tree for each Terraform file in its subdirectories.
    """
    clear_log_output()

    directory_path = filedialog.askdirectory()
    if not directory_path:
        return

    tf_files = glob.glob(os.path.join(directory_path, '**', 'main.tf'), recursive=True)
    hcl_files = glob.glob(os.path.join(directory_path, '**', 'terragrunt.hcl'), recursive=True)
    all_files = tf_files + hcl_files

    if not all_files:
        print("No .tf or .hcl files found in the selected directory.")
        return

    # Create a single graph for all the files
    main_graph = graphviz.Digraph()

    for file_path in tqdm.tqdm(all_files, "Analyzing files ..."):
        print(f"Analyzing file: {file_path}")
        dependency_tree = display_dependency_tree(file_path)

        if dependency_tree is None:
            print(f"No dependencies found for file: {file_path}")
            continue

        dir_name = os.path.dirname(file_path).replace(":", "")

        dependency_tree_str = transform_dict_keys(dependency_tree)
        dependency_tree_str = {dir_name: dependency_tree_str}
        tree = dict_to_tree(dependency_tree_str)

        # Add the nodes and edges for the current file to the main graph
        visualize_tree(tree, main_graph)

        # Print dependency tree to console
        print()
        if dependency_tree:
            print_dependency_tree({dir_name: dependency_tree})
        else:
            print(f"{dir_name}\n  No dependencies found")

        print()
        print("=" * 80)

    # Render the main graph containing all the dependency trees
    main_graph.render("dependency_tree", format="png")

    print("FINISHED")


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
        if isinstance(children_dict, str):
            node['children'].append({'name': children_dict})
        else:
            for key, value in children_dict.items():
                child = {'name': key}
                if isinstance(value, dict):
                    child['children'] = []
                    add_children(child, value)
                else:
                    child['children'] = []
                    for sub_child in value:
                        if sub_child:
                            if isinstance(sub_child, str):
                                child['children'].append({'name': sub_child})
                            else:
                                add_children(child, sub_child)
                                if 'children' in sub_child and any(sub_child['children']):
                                    child['children'].append(sub_child['children'])
                if child['name'] != "children":
                    node['children'].append(child)

    tree = {'name': list(dictionary.keys())[0], 'children': []}
    add_children(tree, list(dictionary.values())[0])
    return tree



def visualize_tree(tree, graph=None):
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

    if graph is None:
        graph = graphviz.Digraph()

    add_node(tree, graph)
    return graph


def print_dependency_tree(tree, indent=0):
    """
    Recursively prints the dependency tree in a human-readable format.
    """
    if isinstance(tree, str):
        print('  ' * indent + tree)
    else:
        for key, value in tree.items():
            print('  ' * indent + str(key))
            if isinstance(value, dict):
                if not value:
                    print('  ' * (indent + 1) + "No further dependencies")
                else:
                    print_dependency_tree(value, indent + 1)
            elif isinstance(value, list):
                if not value:
                    print('  ' * (indent + 1) + "No further dependencies")
                else:
                    for item in value:
                        print_dependency_tree(item, indent + 1)


def analyze_file():
    """
    Analyzes a Terraform file and visualizes its dependency tree.
    """
    clear_log_output()

    print("COMPUTING ...")
    print()

    file_path = file_path_var.get()
    if not os.path.isfile(file_path):
        tk.messagebox.showerror("Error", "Invalid file path: '" + file_path + "'")
        return
    
    dependency_tree = display_dependency_tree(file_path)
    
    dir_name = os.path.dirname(file_path).replace(":", "")

    dependency_tree_str = transform_dict_keys(dependency_tree)
    dependency_tree_str = {dir_name: dependency_tree_str}
    tree = dict_to_tree(dependency_tree_str)
    graph = visualize_tree(tree)

    graph.render("dependency_tree", format="png")

    # Print dependency tree to console
    print()
    if dependency_tree:
        print_dependency_tree({dir_name: dependency_tree})
    else:
        print(f"{dir_name}\n  No dependencies found")

    print()
    print("FINISHED")

class TextRedirector(ScrolledText):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

    def write(self, text):
        self.insert(tk.END, text)
        self.see(tk.END)

    def flush(self):
        pass

def clear_log_output():
    """
    Clears the log output.
    """
    log_output.delete(1.0, tk.END)

if __name__ == '__main__':
    # Create the GUI interface
    root = tk.Tk()
    root.geometry("1000x700")  # Set the default window width and height
    root.title("Dependency Analyzer")

    # Create a frame for the file path selection widgets
    file_path_frame = tk.Frame(root)
    file_path_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)

    # Create the file path selection widgets
    file_path_label = tk.Label(file_path_frame, text="File path:")
    file_path_var = tk.StringVar()
    file_path_entry = tk.Entry(file_path_frame, textvariable=file_path_var, width=50)

    # Create the log output widget
    log_output = TextRedirector(root, wrap=tk.WORD)
    log_output.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Redirect standard output to the log_output widget
    sys.stdout = log_output

    # Button to analyze a single file or a folder
    analyze_file_button = tk.Button(root, text="Analyze File", command=browse_file_path)
    analyze_folder_button = tk.Button(root, text="Analyze Folder", command=analyze_directory)

    # Pack the widgets
    file_path_label.pack(side=tk.LEFT, padx=(10, 0), pady=10)
    file_path_entry.pack(side=tk.LEFT, padx=(0, 10), pady=10, fill=tk.X, expand=True)
    analyze_file_button.pack(side=tk.BOTTOM, padx=10, pady=(0, 10))
    analyze_folder_button.pack(side=tk.BOTTOM, padx=10, pady=(0, 10))
    # Run the GUI
    root.mainloop()