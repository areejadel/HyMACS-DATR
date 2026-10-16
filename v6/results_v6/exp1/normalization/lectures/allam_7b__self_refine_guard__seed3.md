Normalization Forms and Database Schema Design (1NF–BCNF)

## 1. Introduction

Normalization is essential for maintaining data integrity and reducing redundancy in database management. It refers to organizing data into a tabular form, which simplifies storage, retrieval, and manipulation of information. There are different forms of normalization, each with its own rules and constraints. This lecture will discuss the three main forms of normalization and their relevance to database schema design: 1NF, 2NF, 3NF, BCNF, and 4NF.

## 2. 1st Normal Form (1NF)

1NF is the first step in the normalization process and is achieved by removing multi-valued attributes from the table. A multi-valued attribute is an attribute that can have multiple values, such as an address with multiple street names. 1NF requires that each value in an attribute must be unique and distinct.

### Definition

1. A relation is in 1NF if and only if all its attributes are atomic.
2. An attribute is atomic if and only if it cannot be partitioned into two or more independent attributes.

### Example

Consider the table:

| CustomerID | CustomerName | AddressID | StreetName |
|------------|---------------|-----------|------------|
| 1          | John Smith    |           |            |
| 2          | Jane Doe      |           |            |
| 3          | Bob Johnson   |           |            |

In this example, the Address attribute is multi-valued, as it can have multiple street names. To make the table in 1NF, we can create a new table called Address, which will store the street names:

| CustomerID | AddressID | StreetName |
|------------|-----------|------------|
| 1          | 1         | Main St    |
| 2          | 1         | 2nd St     |
| 3          | 1         | 3rd St     |
|            |           | 4th St     |

## 3. 2nd Normal Form (2NF)

2NF is the second step in the normalization process and is achieved by removing primary key-part attributes from the table. A primary key-part attribute is an attribute that is a part of the primary key and is not fully determined by the primary key.

### Definition

1. A relation is in 2NF if and only if all its attributes are functionally dependent on the primary key and are not part of the primary key.

### Example

Consider the table:

| CustomerID | CustomerName | AddressID | StreetName |
|------------|---------------|-----------|------------|
| 1          | John Smith    |           |            |
| 2          | Jane Doe      |           |            |
| 3          | Bob Johnson   |           |            |

In this example, the primary key is CustomerID, and the StreetName attribute is a part of the primary key. To make the table in 2NF, we can remove the StreetName attribute from the table:

| CustomerID | CustomerName |
|------------|---------------|
| 1          | John Smith    |
| 2          | Jane Doe      |
| 3          | Bob Johnson   |

## 4. 3rd Normal Form (3NF)

3NF is the third step in the normalization process and is achieved by removing transitive dependencies in the table. A transitive dependency is a relationship between two attributes where the value of one attribute determines the value of the other attribute, and the value of the first attribute is determined by the value of the second attribute.

### Definition

1. A relation is in 3NF if and only if all its non-key attributes are functionally dependent only on the primary key.

### Example

Consider the table:

| CustomerID | CustomerName | AddressID | StreetName |
|------------|---------------|-----------|------------|
| 1          | John Smith    |           |            |
| 2          | Jane Doe      |           |            |
| 3          | Bob Johnson   |           |            |

In this example, the StreetName attribute is functionally dependent on the CustomerID attribute, and the CustomerID attribute is not fully determined by the primary key (AddressID). To make the table in 3NF, we can create a new table called Address, which will store the street names:

| CustomerID | CustomerName | AddressID |
|------------|---------------|-----------|
| 1          | John Smith    |           |
| 2          | Jane Doe      |           |
| 3          | Bob Johnson   |           |

| AddressID | StreetName |
|-----------|------------|
| 1         | Main St    |
| 2         | 2nd St     |
| 3         | 3rd St     |
| 4         | 4th St     |

## 5. Boyce-Codd Normal Form (BCNF)

BCNF is the fifth and final step in the normalization process and is achieved by removing all multi-valued and partial multi-valued attributes from the table.

### Definition

1. A relation is in BCNF if and only if all its non-key attributes are multi-valued, and no attribute is in the form of (K - M), where M is a multi-valued attribute and K is a primary key.

### Example

Consider the table:

| CustomerID | CustomerName | AddressID | StreetName |
|------------|---------------|-----------|------------|
| 1          | John Smith    |           |            |
| 2          | Jane Doe      |           |            |
| 3          | Bob Johnson   |           |            |

In this example, the StreetName attribute is not in the form of (K - M). To make the table in BCNF, we can remove the StreetName attribute from the table:

| CustomerID | CustomerName |
|------------|---------------|
| 1          | John Smith    |
| 2          | Jane Doe      |
| 3          | Bob Johnson   |