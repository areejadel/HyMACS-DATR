# Lecture: Normalization Forms and Database Schema Design (1NF-BCNF)

## Introduction

Normalization is a process of designing database schema to minimize redundancy and improve data integrity. Normalization forms are a set of rules that database designers follow to design a database schema that meets the requirements of normalization. In this lecture, we will discuss the normalization forms and database schema design, specifically focusing on 1NF, 2NF, 3NF, 4NF, and BCNF.

## 1NF (First Normal Form)

1NF is the first normalization form and it requires that each column in a table has a single data type and that each row contains only one value for each column. This means that there should be no repeating groups in a table, and each column should contain only atomic values.

### Example

Consider the following table:

```
| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |
```

This table is in 1NF because each column has a single data type, and each row contains only one value for each column.

## 2NF (Second Normal Form)

2NF is the second normalization form and it requires that the table be in 1NF, and that every non-key attribute (attribute that is not part of the primary key) is functionally dependent on the primary key. This means that there should be no partial dependencies in the table.

### Example

Consider the following table:

```
| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |
```

This table is in 2NF because each non-key attribute (Sales and Marketing) is functionally dependent on the primary key (Department).

## 3NF (Third Normal Form)

3NF is the third normalization form and it requires that the table be in 2NF, and that there be no transitive dependencies in the table. This means that there should be no non-key attributes that are functionally dependent on other non-key attributes, and the table should be in a transitive dependency-free form.

### Example

Consider the following table:

```
| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |
```

This table is in 3NF because there are no non-key attributes that are functionally dependent on other non-key attributes.

## 4NF (Fourth Normal Form)

4NF is the fourth normalization form and it requires that the table be in 3NF, and that there be no multi-valued dependencies in the table. This means that there should be no non-key attributes that have more than one value that is functionally dependent on a single key value.

### Example

Consider the following table:

```
| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |
```

This table is in 4NF because there are no non-key attributes that have more than one value that is functionally dependent on a single key value.

## BCNF (Boyce-Codd Normal Form)

BCNF is the fifth normalization form and it requires that the table be in 4NF, and that every candidate key be a functional dependency of the primary key. This means that there should be no non-key attributes that are not functionally dependent on the primary key.

### Example

Consider the following table:

```
| Department | Department Head | Sales | Marketing |
| ---------- | ---------------- | ----- | ---------- |
| Sales      | Mary Johnson     | 100   | 50         |
| Marketing  | John Smith       | 75    | 30         |
```

This table is in BCNF because every candidate key (Department) is a functional dependency of the primary key (Department).

## Practical Relevance

Normalization is a crucial concept in database design because it helps to minimize redundancy and improve data integrity. By applying the normalization forms, database designers can ensure that their database schema is efficient, consistent, and easy to maintain.

For example, consider an online retail store that sells various products. The database schema for the store should be designed in a normalized form to ensure that the data is consistent and easy to maintain. By applying the normalization forms, the database schema can be designed to minimize redundancy and improve data integrity.

For instance, consider the following database schema for a retail store:

```
| Product | Description | Price | Quantity |
| ------- | ----------- | ----- | -------- |
| 1       | iPhone X    | 999.99 | 20       |
| 2       | Samsung Galaxy | 799.99 | 30       |
| 3       | MacBook Pro  | 1,799.99 | 10       |
| 4       | iPad Pro     | 999.99 | 5        |
```

This schema is in 1NF because each column has a single data type, and each row contains only one value for each column. It is also in 2NF because the non-key attributes (Description, Price, Quantity) are functionally dependent on the primary key (Product).

In this example, the database schema is designed in a normalized form, which helps to minimize redundancy and improve data integrity. The schema is easy to maintain and can be easily updated to reflect changes in product information. This is important because maintaining accurate and up-to-date information is crucial for an online retail store.

In summary, normalization is a crucial concept in database design because it helps to minimize redundancy and improve data integrity. By applying the normalization forms, database designers can ensure that their database schema is efficient, consistent, and easy to maintain. The practical relevance of normalization forms is important because it helps to ensure that the database schema is designed in a way that meets the requirements of normalization and helps to ensure that the data is consistent and easy to maintain.