# Normalization Forms and Database Schema Design (1NF-BCNF)

## Definition and Motivation
Normalization is the process of organizing data in a database to minimize data redundancy and dependency, and to improve the consistency of the data. It is based on the principle of Normal Form, which is a series of rules and requirements for database design. The process starts with the first normal form (1NF) and progresses to the third normal form (3NF), and beyond.

## Formula and Derivation
The first normal form (1NF) is defined as a database table that has one column with atomic values, meaning that each column contains a single value, and there are no repeating groups or partial values. To derive the formula, we define the table as $T$, and we assume that $T$ has attributes $A_1, A_2, \ldots, A_n$. The table must have a primary key $P$, which is a non-null, unique, and unordered set of attributes. For each attribute $A_i$ in $T$, we check if it has repeating values within the same row. If $A_i$ is not atomic, then $A_i$ violates 1NF.

## Concrete Worked Example
Suppose we have a table for employees in a company, with the following attributes: ID, Name, Department, Salary. We want to ensure that each employee has a unique ID and a unique name, and that each employee belongs to a unique department. We can define the primary key as the combination of ID and Name, which is a non-null, unique, and unordered set of attributes. We can then check if each attribute $A_i$ in the table is atomic or not. If $A_i$ is not atomic, then $A_i$ violates 1NF.

## Example: ID and Name are atomic
ID | Name | Department | Salary
---|------|------------|-------
1  | John | Sales      | 5000
2  | Jane| Marketing  | 6000

ID and Name are atomic, so we can apply 1NF.

## Limitations and Common Pitfalls
One limitation of 1NF is that it may require a large number of columns in the table, which can make the table difficult to read and maintain. Another common pitfall is that 1NF does not guarantee the normalization of the data, and it is up to the user to ensure that the data is normalized.

## Prerequisites and Variants
The second normal form (2NF) is defined as a table that is in 1NF and has all attributes that are functionally dependent on the primary key. In other words, all attributes in the table are dependent on the primary key, and there are no partial dependencies. The third normal form (3NF) is defined as a table that is in 2NF and has no transitive dependencies.

## Explanation of 1NF, 2NF, and 3NF
1NF ensures that each attribute is atomic and that there are no repeating groups or partial values within the same row. 2NF ensures that all attributes that are not in the primary key are functionally dependent on the primary key. 3NF ensures that all attributes are dependent on the primary key and that there are no transitive dependencies.

## Intellectual Tension and "Try This Yourself" Prompts
To maintain curiosity and engagement, we can introduce intellectual tension by asking the audience to think about the consequences of not following the normalization rules. For example, you can ask them to consider the consequences of having partial values or repeating groups in a table. You can also include "try this yourself" prompts that ask the audience to apply the concepts they learned to a real-world scenario, such as designing a database for a small business.

## Non-trivial Cross-Domain Connection
In this lecture, we explored the relationship between database design and computer science. Specifically, we looked at how normalization forms can be used to optimize the performance of database systems. We also explored the relationship between database design and business. We saw how normalization forms can be used to improve the consistency of data and reduce data redundancy, which can have a significant impact on the efficiency of business operations.