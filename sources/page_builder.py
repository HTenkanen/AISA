
import os
import glob
import subprocess

_dir_path = os.path.dirname(os.path.realpath(__file__))


def get_notebooks():
    notebooks = [f for f in glob.glob(os.path.join(_dir_path, "**", "*.ipynb",), recursive=True)]
    return notebooks


def convert_notebooks_to_rst(notebook_list):
    for nb in notebook_list:
        cmd = ["jupyter", "nbconvert", "--ClearOutputPreprocessor.enabled=True",
               nb, "--to", "rst"]
        print(cmd)
        subprocess.run(cmd)

def add_hypothesis_block(writer):

    codes = ['\n\n.. raw:: html\n',
             '    <script src="https://hypothes.is/embed.js" async> </script>',
             '\n'
             ]
    for line in codes:
        writer.write(line)


def add_binder_block(writer):
    codes = ["\n.. image:: https://mybinder.org/badge_logo.svg\n",
             "    :target: https://mybinder.org/v2/gh/HTenkanen/AISA/master?urlpath=lab/tree/sources/notebooks/spatial_network_analysis.ipynb",
             "\n\n"
             ]
    for line in codes:
        writer.write(line)

def convert_notebooks_to_jupyter_sphinx_rst(notebook_list):
    for nb in notebook_list:
        cmd = ["jupyter", "nbconvert", "--ClearOutputPreprocessor.enabled=True",
               nb, "--to", "rst"]
        print(f"Processing {os.path.basename(nb)} ..")
        subprocess.run(cmd)

        # Read rst file and convert (allow Exceptions)
        with open(nb.replace('.ipynb', '.rst'), 'r') as rst:
            lines = rst.readlines()
            converted_lines = []
            for line in lines:
                if line.startswith(".. code:: ipython3"):
                    # Convert to jupyter-execute
                    line = line.replace(".. code:: ipython3",
                                        ".. jupyter-execute::\n    :raises:\n")

                converted_lines.append(line)

        # Write
        with open(nb.replace('.ipynb', '.rst'), 'w') as rst:

            for i, line in enumerate(converted_lines):
                rst.write(line)

                # Add binder button after the title
                if i == 1:
                    if "spatial_network" in nb:
                        # Add binder button on top
                        add_binder_block(rst)


            # Insert Hypothesis tag
            add_hypothesis_block(rst)

if __name__ == "__main__":

    notebooks = get_notebooks()
    if len(notebooks) > 0:
        convert_notebooks_to_jupyter_sphinx_rst(notebooks)
