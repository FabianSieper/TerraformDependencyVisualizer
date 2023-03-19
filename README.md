# Terraform Dependency Analyzer

## General Description
The Terraform Dependency Analyzer is a GUI-based Python tool designed to analyze and visualize the dependency tree of Terraform files. It allows users to easily understand the dependencies between modules and resources within a Terraform project. By visualizing the dependency tree, developers can quickly identify the relationships between resources and modules and make more informed decisions during development and maintenance.

## Requirements
To use the Terraform Dependency Analyzer, you need to have the following installed:
- Python 3.7 or higher
- The graphviz Python package (for generating dependency tree visualizations)
- The tkinter package (for the GUI interface)
- Graphviz software (required by the graphviz Python package)
- Git (for cloning Git repositories to analyze dependencies)

### Installing Python Packages
To install the required Python packages, run the following command:
```bash
pip install -r requirements.txt
```

### Installing Graphviz

In addition to the Python graphviz package, you need to install the Graphviz software on your system. The Python package serves as a wrapper around the Graphviz software and requires the software to be installed on the system to function correctly. Here's how you can install Graphviz on different platforms:

#### Windows

1. Download the Graphviz installer for Windows from the [official](https://graphviz.org/download/) website.
2. Run the installer and follow the prompts to install Graphviz.
3. Add the Graphviz `bin` directory (e.g., C:\Program Files (x86)\GraphvizX.XX\bin) to your system's `PATH` environment variable.

#### macOS

You can install Graphviz using Homebrew:

1. If you don't have Homebrew installed, follow the instructions on the Homebrew website to install it.
2. Run the following command in your terminal:

```bash
brew install graphviz
```

#### Linux (Debian/Ubuntu-based distributions)

Run the following command in your terminal:

```bash
sudo apt-get install graphviz
```

#### Linux (Fedora-based distributions)

Run the following command in your terminal:

```bash
sudo dnf install graphviz
```

After installing Graphviz on your system, the Python graphviz package should work as expected.


### File and Git Repository Format
For the Terraform Dependency Analyzer to work correctly, your files and Git repositories should adhere to the following formats:

#### Terraform Files

1. The tool expects Terraform files to be named `main.tf` or `terragrunt.hcl`.
2. The dependencies should be defined using the source attribute in the Terraform module block or the terraform.source attribute in the Terragrunt configuration block.
3. The source attribute should be formatted as follows: `git::<git_ssh_url>//<path>?ref=<tag>`. The tool currently supports only SSH URLs for Git repositories.

#### Git Repository Structure
1. The Git repositories should contain Terraform modules or resources, and the folder structure should be consistent with the paths provided in the source attribute.
2. The repository should have Git tags corresponding to the tags specified in the source attribute. The tool will use these tags to clone the appropriate version of the repository.

#### Example 
Here's an example of a valid Terraform file and Git repository structure:
- Terraform file main.tf:

    ```bash
    module "example" {
        source = "git::git@github.com:organization/terraform-modules//module-a?ref=v1.0.0"
    }
    ```

- Git Repository:
    ```bash
    github.com/organization/terraform-modules/
    ├── module-a/
    │   ├── main.tf
    │   └── variables.tf
    └── module-b/
        ├── main.tf
        └── variables.tf
    ```

In this example, the `main.tf` file depends on `module-a`, which is located in the `terraform-modules` repository. The repository has two modules, `module-a` and `module-b`, and the dependency is specified using the `source` attribute with an SSH URL, path, and Git tag.

## How to Use

1. Run the script using Python:

    ```bash
    python main.py
    ```

2. The GUI interface will open. Click on the "Browse..." button to select the Terraform file (main.tf or terragrunt.hcl) you want to analyze.

3. After selecting the file, click the "Analyze" button. The tool will analyze the selected file and generate a visualization of the dependency tree as a PNG file named dependency_tree.png in the same directory as the script.

4. If the tool encounters any issues or cannot find any dependencies, an error or informational message will be displayed. Make sure to provide a valid Terraform file and ensure that your Git repositories are accessible.

5. To analyze another file, repeat steps 2-4.

### Generated Images

When the Terraform Dependency Analyzer successfully generates a dependency tree, it will create an image of the tree using Graphviz. This image will be stored in the same directory as the script with the filename `dependency_tree.png`.

You can open the image using any image viewer or editor that supports PNG files to view the visual representation of your Terraform project's dependency tree.

#### Example terraform-dependency images

This image represents a whole dependency tree of a file `terragrunt.hcl`.

![Dependency tree without errors](/example_images/dependency_tree.png)

In this case, a dependency could not be downloaded. This is indicated with an error from the resource, which could not be loaded.

![Dependency tree without errors](/example_images/error_downloading.png)
