# Display dependencies of terraform modules
This project has the purpose to visualize dependencies between terraform files, lying in different repositories.

## Requirements
- Install graphiviz https://graphviz.org/download/
- Install required pip dependencies
    ```
    pip install regex
    pip install tkinter
    pip install graphviz
    ```

## Execution
```
python main.py
```

## Graph
After selecting a .hcl file, all dependent repos will be cloned into folder `temp`. A graph is computed and stored in the file `tree.png` right next to the file `main.py`.