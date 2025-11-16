### Interactive Supermarket Simulation with Association Rule Mining

#### Author Information

- **Name**: Gabriela del Cristo Sanchez
- **Student ID**: 6417618
- **Course**: CAI 4002 - Artificial Intelligence
- **Semester**: Fall 2025

#### Direct Link
```
https://supermarketsimulation.streamlit.app/
```

#### System Overview

This application lets users upload or create their own supermarket transaction data and automatically analyzes it using association rule mining. It helps identify which products are commonly bought together, generates useful recommendations, and displays the results clearly.

#### Technical Stack

- **Language**: Python 3.13
- **Key Libraries**: Streamlit, Pandas, NumPy, itertools, Pathlib
- **UI Framework**: I used Streamlit, a Python based web framework that makes it easy to build interactive dashboards and data applications.

#### Installation

##### Prerequisites
- Python 3.10+
- Streamlit

##### Setup

# Clone or extract project
```
https://github.com/gdelcsan/AssociationRuleDataMining.git
```
# Install dependencies
```
pip install -r requirements.txt
```
# Run application
```
streamlit run src/main.py
```

#### Usage

##### 1. Load Data
- **Manual Entry**: Click items to create transactions
- **Import CSV**: sample_transactions.csv is default file, click "browse files" to import custom csv file

##### 2. Preprocess Data
- Click "Preprocess"
- Review cleaning report (empty transactions, duplicates, etc.)

##### 3. Run Mining
- Set minimum support and confidence thresholds
- Click "Analyze" to execute all three algorithms
- Wait for completion (~1-3 seconds)

##### 4. Query Results
- Select product from dropdown
- View associated items and recommendation strength
- Optional: View technical details (raw rules, performance metrics)

#### Algorithm Implementation

##### Apriori
For my project, I implemented the Apriori algorithm using a step-by-step, level-based approach. I started by finding all the frequent single
items and then gradually built larger itemsets as long as they met the minimum support threshold. At each stage, I reused the results from the
previous level to keep the process efficient.
- Data structure: I stored the frequent itemsets in a dictionary where each level maps to another dictionary of frozenset(itemset): support.
This made it easy to look up supports and organize results.
- Candidate generation: I used a level-wise/breadth-first approach, where I joined frequent (k–1)-itemsets with each other to produce new 
item candidates.
- Pruning strategy: Before accepting a candidate, I checked whether all of its subsets were already frequent, and then I filtered out anything
that didn’t meet the minimum support. This helped reduce unnecessary calculations.

##### Eclat
For the Eclat algorithm, I took a different approach by using a vertical data format instead of scanning full transactions each time. I converted the dataset into item transaction ID sets, which let me compute support using simple set intersections. This made it faster to explore combinations of items compared to Apriori.
- Data structure: I kept the data in a dictionary where each key is a frozenset([item]) and each value contains all the transaction IDs that include that item.
- Search strategy: I followed a depth-first search approach. The algorithm drills down into one itemset at a time, expanding it as far as possible before backtracking.
- Intersection method: I used Python’s set operations to intersect TID sets. This allows me to quickly check how many transactions two itemsets share and whether they meet minimum support.


#### Performance Results

Tested on provided dataset (80-100 transactions after cleaning):

| Algorithm | Runtime (ms) | Rules Generated |
|-----------|--------------|-----------------|
| Apriori   | 0.1 ms       | 11              |
| Eclat     | 0.2 ms       | 11              |

**Parameters**: min_support = 0.2, min_confidence = 0.5

**Analysis**: In my tests, Apriori surprisingly ran faster than Eclat. Since the dataset wasn’t very large, Apriori’s repeated scans didn’t slow it down much, while Eclat’s vertical data format and set-intersection steps seemed to add extra overhead. So, for this project’s data size, Apriori ended up being the quicker option.


#### Project Structure

```
project-root/
├── devcontainer/
│   └── json
├── data/
│   ├── products.csv
│   └── sample_transactions.csv
├── src/
│   ├── algorithms/
│   │   ├── apriori.py
│   │   └── eclat.py
│   ├── preprocessing/
│   │   └── cleaner.py
│   ├── ui/
│   │   └── app.py 
│   └── main.py
├── LICENSE
├── README.md
└── requirements.txt
```

#### Data Preprocessing

Issues handled:
- Empty transactions: [count] removed
- Single-item transactions: [count] removed
- Duplicate items: [count] instances cleaned
- Case inconsistencies: [count] standardized
- Invalid items: [count] removed
- Extra whitespace: trimmed from all items



#### Testing

Verified functionality:
- [✓] CSV import and parsing
- [✓] All preprocessing operations
- [✓] Three algorithm implementations
- [✓] Interactive query system
- [✓] Performance measurement

Test cases:

First test case was using the default csv file. No transactions added, preprocessing and then analyzing.

Second test case was using the default csv file. Adding a couple transactions and then preprocessing and analyzing to see what changes.

Third test case was using an imported csv file, just the default which I edited so I could test the import feature. I tested it by itself and with adding transactions to see the changes.

#### Known Limitations

- Results depend on clean input data so messy or inconsistent entries may still affect accuracy.
- Apriori can be slow on larger datasets due to heavy candidate generation.
- Eclat may struggle when there are too many unique items since intersections get expensive.
- The system is designed for small/medium datasets, not large production use. Also only 200 entries will show at a time in the table.
- Uploaded CSVs with unusual formatting may require manual cleanup.

#### AI Tool Usage

For this project, I used AI tools such as ChatGPT to help generate more detailed comments on my code that I didn't know how to phrase and for debugging certain sections that I couldn't figure out what was wrong.

#### References

- Course lecture materials
- Google
- Github (previous projects for reference)

