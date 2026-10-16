# Lecture: Normalization Forms and Database Schema Design (1NF-BCNF)

## Introduction

Normalization is a process of designing database schema to minimize redundancy and improve data integrity. Normalization forms are a set of rules that database designers follow to design a database schema that meets the requirements of normalization. In this lecture, we will discuss the normalization forms and database schema design, specifically focusing on 1NF, 2NF, 3NF, 4NF, and BCNF.

## 1NF (First Normal Form)

1NF is the first normalization form and it requires that each column in a table has a single data type and that each row contains only one value for each column. This means that there should be no repeating groups in a table, and each column should contain only atomic values.

### Example

Consider the following table:

| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |

This table is in 1NF because each column has a single data type, and each row contains only one value for each column.

## 2NF (Second Normal Form)

2NF is the second normalization form and it requires that the table be in 1NF, and that every non-key attribute (attribute that is not part of the primary key) is functionally dependent on the primary key. This means that there should be no partial dependencies in the table.

### Example

Consider the following table:

| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |

This table is in 2NF because each non-key attribute (Sales and Marketing) is functionally dependent on the primary key (Department).

## 3NF (Third Normal Form)

3NF is the third normalization form and it requires that the table be in 2NF, and that there be no transitive dependencies in the table. This means that there should be no non-key attributes that are functionally dependent on other non-key attributes, and the table should be in a transitive dependency-free form.

### Example

Consider the following table:

| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |

This table is in 3NF because there are no non-key attributes that are functionally dependent on other non-key attributes, and the table is in a transitive dependency-free form.

## 4NF (Fourth Normal Form)

4NF is the fourth normalization form and it requires that the table be in 3NF, and that there be no multi-valued dependencies in the table. This means that there should be no non-key attributes that have more than one value for each key value.

### Example

Consider the following table:

| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |

This table is in 4NF because there are no non-key attributes that have more than one value for each key value, and the table is in a multi-valued dependency-free form.

## BCNF (Boyce-Codd Normal Form)

BCNF is the fifth and final normalization form and it requires that the table be in 4NF, and that there be no functional dependencies between non-key attributes. This means that there should be no non-key attributes that are determined by other non-key attributes.

### Example

Consider the following table:

| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |

This table is in BCNF because there are no functional dependencies between non-key attributes, and the table is in a functional dependency-free form.