

import numpy as np

from collections import defaultdict

transactions = {
    'T1': [('a', 1), ('c', 1), ('d', 1)],
    'T2': [('a', 2), ('c', 2), ('e', 2), ('g', 5)],
    'T3': [('a', 1), ('b', 2), ('c', 1), ('d', 6), ('e', 1), ('f', 5)],
    'T4': [('b', 4), ('c', 3), ('d', 3), ('e', 1)],
    'T5': [('b', 2), ('c', 2), ('e', 3), ('g', 2)]
}


external_utilities = {
    'a': 5,
    'b': 2,
    'c': 1,
    'd': 2,
    'e': 3,
    'f': 1,
    'g': 1
}

local_utilities = {}

for transaction_id, items in transactions.items():
    for item, quantity in items:
        if item not in local_utilities:
            local_utilities[item] = []
        local_utilities[item].append(quantity)

# Output local utilities
print(local_utilities)

def item_utility_in_transaction(item, transaction):
    for i in transaction:
        if i[0] == item:
            return i[1] * external_utilities[item]
    return 0

# Calculate utility of all items in a transaction
def transaction_utility(transaction):
    return sum(item_utility_in_transaction(item, transaction) for item, _ in transaction)

# Calculate TWU for all items in all transactions
def calculate_twu(transactions):
    twu_values = {}
    for transaction_id, transaction_data in transactions.items():
        # Generate all possible itemsets in the current transaction
        itemsets = [frozenset([item]) for item, _ in transaction_data]
        for i in range(len(transaction_data)):
            for j in range(i+1, len(transaction_data)):
                itemsets.append(frozenset([transaction_data[i][0], transaction_data[j][0]]))

        # Accumulate utility for each itemset
        for itemset in itemsets:
            twu_values[itemset] = twu_values.get(itemset, 0) + transaction_utility(transaction_data)

    return twu_values

# Calculate TWU values
twu_values = calculate_twu(transactions)

# Print TWU values of each itemset
print("TWU Values of Each Itemset:")
for itemset, twu in twu_values.items():
    print(f"{itemset}: {twu}")

def is_closed_itemset(itemset, transactions):
    # Get the support of the current itemset
    itemset_support = transactions.get(itemset, 0)

    # Get all subsets of the current itemset
    subsets = [subset for subset in itemset if len(subset) < len(itemset)]

    # Check if there exists no itemset X0 such that X ⊂ X0
    for subset in subsets:
        if transactions.get(subset, 0) == itemset_support:
            return False

    return True

closed_itemsets = []
for itemset in transactions.keys():
    if is_closed_itemset(itemset, transactions):
        closed_itemsets.append(itemset)

print("Closed Itemsets:")
for itemset in closed_itemsets:
    print(itemset)

# Prune low-utility itemsets
def prune_low_utility_itemsets(twu_values, threshold):
    pruned_twu_values = {}
    for itemset, twu in twu_values.items():
        if twu >= threshold:
            pruned_twu_values[itemset] = twu
    return pruned_twu_values


def itemset_utility_in_database(itemset, transactions):
    total_utility = 0

    # Iterate through transactions in the database
    for transaction, transaction_utility in transactions.items():
        # Check if the itemset is a subset of the transaction
        if set(itemset).issubset(set(transaction)):
            # Calculate the utility of the itemset in the transaction and accumulate
            itemset_utility = sum(transaction_utility for item, quantity in itemset if (item, quantity) in transaction)
            total_utility += itemset_utility
    return total_utility

# Overestimation check: Ensure TWU >= Utility for all itemsets
def overestimation_check(twu_values):
    for itemset, twu in twu_values.items():
        if twu < itemset_utility_in_database(itemset, transactions):
            return False
    return True

# Anti-monotonicity check: If X ⊆ Y, then TWU(X) >= TWU(Y)
def anti_monotonicity_check(twu_values, itemset_x, itemset_y):
    twu_x = twu_values.get(itemset_x, 0)
    twu_y = twu_values.get(itemset_y, 0)
    return twu_x >= twu_y

twu_values = calculate_twu(transactions)

# Prune low-utility itemsets
threshold = 40
pruned_twu_values = prune_low_utility_itemsets(twu_values, threshold)
print("pruned_twu_values : ",pruned_twu_values)

# Order the pruned TWU values
ordered_pruned_twu_values = dict(sorted(pruned_twu_values.items(), key=lambda item: item[1]))

print("Ordered Pruned TWU Values:")
for itemset, twu in ordered_pruned_twu_values.items():
    print(f"{itemset}: {twu}")

# Overestimation check
overestimation_result = overestimation_check(pruned_twu_values)
print("Overestimation check result:", overestimation_result)

# Anti-monotonicity check
itemset_x = frozenset([('a', 1), ('c', 1)])
itemset_y = frozenset([('a', 1)])
anti_monotonicity_result = anti_monotonicity_check(pruned_twu_values, itemset_x, itemset_y)
print("Anti-monotonicity check result:", anti_monotonicity_result)

"""PHASE TWO

MAPPING TABLE
"""

mapping_table = {
    'd': 'A',
    'b': 'B',
    'e': 'C',
    'a': 'D',
    'c': 'E'
}

# Step 1: Reconstruct datasets using the mapping table
reconstructed_datasets = {}

for transaction_id, transaction_data in transactions.items():
    reconstructed_transaction = []

    for item, quantity in transaction_data:
        if item in mapping_table:
            reconstructed_transaction.append((mapping_table[item], quantity))

    reconstructed_datasets[transaction_id] = reconstructed_transaction

# Step 2: Prune absent data
pruned_datasets = {}

for transaction_id, transaction_data in reconstructed_datasets.items():
    pruned_transaction = [(item, quantity) for item, quantity in transaction_data if item]
    pruned_datasets[transaction_id] = pruned_transaction

# Step 3: Order the new datasets
ordered_datasets = {}

for transaction_id, transaction_data in pruned_datasets.items():
    ordered_transaction = sorted(transaction_data, key=lambda x: x[0])
    ordered_datasets[transaction_id] = ordered_transaction

# Output the ordered datasets in the desired format
for transaction_id, transaction_data in ordered_datasets.items():
    items_data = ' '.join([f"({item},{quantity})" for item, quantity in transaction_data])
    print(f"T{transaction_id[-1]} {items_data}")

"""MAP Algorithm"""

def map_algorithm(transaction_database):
    mapped_itemsets = []  # Initialize an empty list to store mapped itemsets

    # Iterate over each transaction in the database
    for transaction_id, transaction_data in transaction_database.items():
        # Iterate over each item in the transaction
        for i in range(len(transaction_data)):
            # Output pairs (transaction ID, substring of transaction starting from the current item)
            mapped_itemsets.append((transaction_id, transaction_data[i:]))

    return mapped_itemsets

mapped_itemsets = map_algorithm(transactions)

# Output the result
print("Itemsets after Map algorithm:")
for itemset in mapped_itemsets:
    print(itemset)

"""REDUCE Algorithm"""

def lu(transaction, item):
    if isinstance(transaction, list):
        for idx, (item_in_trans, _) in enumerate(transaction):
            if item_in_trans == item:
                # Check if the item exists in local_utilities and if the index is valid
                if item in local_utilities and idx < len(local_utilities[item]):
                    return local_utilities[item][idx]  # Return local utility if item exists and index is valid
                else:
                    return 0  # Return 0 if the item or index is not found
    return 0


def su(transaction, item):
    support_utility = 0
    for t_item, quantity in transaction:
        if t_item == item:
            support_utility += quantity
    return support_utility

def create_D_star(alpha, transaction_database):
    D_star = {}
    for tid, transaction in transaction_database.items():
        items = [item for item, _ in transaction]
        if set(alpha).issubset(set(items)):
            D_star[tid] = transaction
    return D_star

def Search(alpha, D_star, primary, secondary, min_util):
    HUIs = set()
    for tid, transaction in D_star.items():
        total_utility = sum(su(transaction, item) for item, _ in transaction)
        if total_utility >= min_util:
            HUIs.add(tid)
    return HUIs


# Test LU for item 'a' in transaction 'T1'
item_a_lu_T1 = lu(transactions['T1'], 'a')
print("Local utility of item 'a' in transaction 'T1':", item_a_lu_T1)

# Test LU for item 'b' in transaction 'T3'
item_b_lu_T3 = lu(transactions['T3'], 'b')
print("Local utility of item 'b' in transaction 'T3':", item_b_lu_T3)

# Test create_D_star function
alpha = {'a', 'b'}
D_star = create_D_star(alpha, transactions)
print("D* for alpha:", D_star)

# Test Search function
min_util = 2
primary = {'a', 'b', 'c'}
secondary = {'d', 'e', 'f', 'g'}
# HUIs = Search(alpha, D_star, primary, secondary, min_util)
# print("High Utility Itemsets:", HUIs)

def reduce_algorithm(transaction_database, key, min_util):
    # Initialize alpha with the key
    alpha = set(key)
    huis = set()  # Initialize set to store the High Utility Itemsets (HUIs)

    # Sort transactions in D according to some order (≻)
    sorted_transactions = sorted(transaction_database.items())

    # Create D* for the initial alpha
    D_star = create_D_star(alpha, transaction_database)

    # Search for High Utility Itemsets using the initial alpha and D*
    HUIs = Search(alpha, D_star, primary, secondary, min_util)

    # Add the initial HUIs to the final set
    huis.update(HUIs)

    # Iterate through remaining transactions
    for transaction_id, _ in sorted_transactions:
        # Skip if the transaction is already in alpha
        if transaction_id in alpha:
            continue

        # Add the transaction ID to alpha
        alpha.add(transaction_id)

        # Update D* according to the new alpha
        D_star = create_D_star(alpha, transaction_database)

        # Search for High Utility Itemsets using the updated alpha and D*
        HUIs = Search(alpha, D_star, primary, secondary, min_util)

        # Add the found HUIs to the final set
        huis.update(HUIs)

    return huis

# Example usage:
key = 'c'  # Example key
min_util = 1  # Example minimum utility threshold

# Call the reduce_algorithm function
huis = reduce_algorithm(transactions, key, min_util)

# Print the High Utility Itemsets
print("High Utility Itemsets:", huis)




key = 'a'  # Example key
min_util = 1 # Example minimum utility threshold

# Call the reduce_algorithm function
huis = reduce_algorithm(transactions, key, min_util)

# Print the High Utility Itemsets
print("High Utility Itemsets:", huis)
