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

| AddressID | StreetName |
|-----------|------------|
| 1         | Main St    |
| 1         | 2nd St     |
| 1         | 3rd St     |
| 2         | 4th St     |

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

In this example, the primary key is "CustomerID", and the attributes "CustomerName" and "AddressID" are part of the primary key. To make the table in 2NF, we can create a new table called AddressDetails, which will store the street names and customer details separately:

| CustomerID | CustomerName | AddressID | AddressDetailsID | StreetName |
|------------|---------------|-----------|-----------------|------------|
| 1          | John Smith    |           |                 | Main St    |
| 2          | Jane Doe      |           |                 | 4th St     |
| 3          | Bob Johnson   |           |                 | 2nd St     |

## 3. 3rd Normal Form (3NF)

3NF is the third step in the normalization process and is achieved by removing non-transitive dependencies. A non-transitive dependency is a dependency that is not fully determined by the primary key.

### Definition

1. A relation is in 3NF if and only if all its non-transitive dependencies are removed.

### Example

Consider the table:

| CustomerID | CustomerName | AddressID | AddressDetailsID | StreetName |
|------------|---------------|-----------|-----------------|------------|
| 1          | John Smith    |           |                 | Main St    |
| 2          | Jane Doe      |           |                 | 4th St     |
| 3          | Bob Johnson   |           |                 | 2nd St     |

In this example, the non-transitive dependency is the relationship between "CustomerName" and "AddressID". To make the table in 3NF, we can create a new table called AddressDetails, which will store the street names and customer details separately:

| CustomerID | CustomerName | AddressID | AddressDetailsID | StreetName |
|------------|---------------|-----------|-----------------|------------|
| 1          | John Smith    |           |                 | Main St    |
| 2          | Jane Doe      |           |                 | 4th St     |
| 3          | Bob Johnson   |           |                 | 2nd St     |

## 4. Boyce-Codd Normal Form (BCNF)

BCNF is the fourth step in the normalization process and is achieved by removing partial dependencies. A partial dependency is a dependency that is not fully determined by the primary key and is not transitive.

### Definition

1. A relation is in BCNF if and only if all partial dependencies are removed.

### Example

Consider the table:

| CustomerID | CustomerName | AddressID | StreetName |
|------------|---------------|-----------|------------|
| 1          | John Smith    |           | Main St    |
| 2          | Jane Doe      |           | 4th St     |
| 3          | Bob Johnson   |           | 2nd St     |

In this example, the partial dependency is the relationship between "CustomerName" and "AddressID". To make the table in BCNF, we can create a new table called AddressDetails, which will store the street names and customer details separately:

| CustomerID | CustomerName | AddressID | AddressDetailsID | StreetName |
|------------|---------------|-----------|-----------------|------------|
| 1          | John Smith    |           |                 | Main St    |
| 2          | Jane Doe      |           |                 | 4th St     |
| 3          | Bob Johnson   |           |                 | 2nd St     |

## 5. Full Second Normal Form (FSNF)

FSNF is the fifth step in the normalization process and is achieved by removing non-prime attributes. A