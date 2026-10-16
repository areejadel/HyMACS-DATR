# Normalization Forms and Database Schema Design (1NF-BCNF)

## Learning Objectives:
- Explain the purpose of normalization in database schema design.
- Describe the five normal forms used in database schema design, including 1NF, 2NF, 3NF, 4NF, and BCNF.
- Explain the requirements of each normal form.
- Describe the benefits of each normal form.

## Normalization Forms
Normalization is the process of organizing data in a database to minimize redundancy and dependency. It is essential to ensure the data is stored in an efficient manner and can be easily accessed, modified, and queried.

### 1NF (First Normal Form)
1NF requires that each column in a table contains atomic values, meaning that each value in the column is an individual piece of data. This means that each value in the column is a separate record or row. For example, in a table of customers, each customer's name would be a separate record.

$$ \text{CustomerID} \rightarrow \text{Customer Name} $$

### 2NF (Second Normal Form)
2NF requires that a table is in 1NF and all non-key attributes are fully functionally dependent on the primary key. This means that each non-key attribute depends on the primary key to determine its value. For example, in the above customer table, the customer's address would depend on the customer's ID.

$$ \text{CustomerID} \rightarrow \text{Customer Name} \rightarrow \text{Customer Address} $$

### 3NF (Third Normal Form)
3NF requires that a table is in 2NF and all non-key attributes are not transitive, meaning that they do not depend on each other to determine their values. In other words, the non-key attributes do not have a dependency on the non-key attributes. For example, in the customer table, the customer's ID and address are not dependent on each other.

$$ \text{CustomerID} \rightarrow \text{Customer Name} \rightarrow \text{Customer Address} $$

### 4NF (Fourth Normal Form)
4NF requires that a table is in 3NF and all non-key attributes are not only not transitive, but also do not depend on each other. This means that the non-key attributes have no dependencies on each other. For example, in the customer table, the customer's ID and address are not dependent on each other.

$$ \text{CustomerID} \rightarrow \text{Customer Name} \rightarrow \text{Customer Address} $$

### BCNF (Boyce-Codd Normal Form)
BCNF is a higher normal form than 4NF, which is used in the design of hierarchical databases, where data is organized in a tree structure.

$$ \text{CustomerID} \rightarrow \text{Customer Name} \rightarrow \text{Customer Address} $$

### Benefits of Each Normal Form
- 1NF: Eliminates redundancy and improves data consistency.
- 2NF: Eliminates data anomalies and improves data integration.
- 3NF: Eliminates data inconsistencies and improves data redundancy.
- 4NF: Eliminates data anomalies and improves data redundancy.
- BCNF: Eliminates data inconsistencies and improves data redundancy.

By understanding these normal forms, database designers can create more efficient and reliable database schemas.