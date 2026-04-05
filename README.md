# NSGA-II Route Optimizer for Waste Collection

Python implementation of the **Non-dominated Sorting Genetic Algorithm II (NSGA-II)** for multi-objective vehicle routing optimization. This engine balances conflicting objectives: distance, time, and waste load.

## Project Structure
The repository is organized as follows to ensure correct execution:

* **src/**: Contains the source code, including the main execution script `alg_nsga2.py`.
* **output/ejemplares/**: Directory containing the problem instance files (.txt).
* **requirements.txt**: List of necessary Python libraries.

## Usage
To run the optimizer, use the following command structure from the root directory:

```bash
python .\src\alg_nsga2.py .\output\ejemplares\[Instance_File_Name].txt

## Execution Example
Test the program with the provided sample instance:

```bash
python .\src\alg_nsga2.py .\output\ejemplares\A-n32-k5.txt
