### Normalization Forms and Database Schema Design (1NF–BCNF)

### 1. Introduction

Normalization is essential for maintaining data integrity and reducing redundancy in database management. It refers to organizing data into a tabular form, which simplifies storage, retrieval, and manipulation of information. There are different forms of normalization, each with its own rules and constraints. This lecture will discuss the three main forms of normalization and their relevance to database schema design: 1NF, 2NF, 3NF, BCNF, and 4NF.

### 2. 1st Normal Form (1NF)

1NF is the first step in the normalization process and is achieved by removing multi-valued attributes from the table. A multi-valued attribute is an attribute that can have multiple values, such as an address with multiple street names. 1NF requires that each value in an attribute must be unique and distinct.

#### Definition

1. A relation is in 1NF if and only if all its attributes are atomic.
2. An attribute is atomic if and only if it cannot be partitioned into two or more independent attributes.

#### Example

Consider the table:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|------------|
| 1          | John Smith   |           |            |
| 2          | Jane Doe     |           |            |
| 3          | Bob Johnson  |           |            |
```

In this example, the Address attribute is multi-valued, as it can have multiple street names. To make the table in 1NF, we can create a new table called Address, which will store the street names:

```
| AddressID | StreetName |
|-----------|------------|
| 1         | Main St    |
| 2         | 2nd St     |
| 3         | 3rd St     |
| 4         | 4th St     |
```

### 3. 2nd Normal Form (2NF)

2NF is the second step in the normalization process and is achieved by removing primary key-part attributes from tables that have multiple primary keys. This ensures that the table does not contain any transitive dependencies.

#### Definition

2NF is achieved when a table is in 1NF and all non-key attributes are fully dependent on the primary key. A non-key attribute is dependent on the primary key if it cannot be determined without the value of the primary key.

#### Example

Consider the table:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|---
[...truncated...]
```

To make this table in 2NF, we need to remove the AddressID attribute, which is a part of the primary key. This can be achieved by creating a new table called Address with the following attributes:

```
| AddressID | AddressName | AddressType |
|-----------|-------------|-------------|
| 1         | Main St     | Apartment   |
| 2         | 2nd St      | House       |
| 3         | 3rd St      | Condo       |
```

Then, we can join the Address table with the Customer table using the AddressID attribute to retrieve the street name:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|---
| 1          | John Smith   |           | Main St    |
| 2          | Jane Doe     |           | 2nd St     |
| 3          | Bob Johnson  |           | 3rd St     |
```

### 4. 3rd Normal Form (3NF)

3NF is the third step in the normalization process and is achieved by removing transitive dependencies. This ensures that the table does not contain any non-transitive dependencies.

#### Definition

3NF is achieved when a table is in 2NF and all non-key attributes are not dependent on any non-key attributes.

#### Example

Consider the table:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|---
[...truncated...]
```

To make this table in 3NF, we need to remove the StreetName attribute, which is dependent on the AddressID attribute. This can be achieved by creating a new table called Address with the following attributes:

```
| AddressID | AddressName | AddressType |
|-----------|-------------|-------------|
| 1         | Main St     | Apartment   |
| 2         | 2nd St      | House       |
| 3         | 3rd St      | Condo       |
```

Then, we can join the Address table with the Customer table using the AddressID attribute to retrieve the street name:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|---
| 1          | John Smith   |           | Main St    |
| 2          | Jane Doe     |           | 2nd St     |
| 3          | Bob Johnson  |           | 3rd St     |
```

### 5. 4th Normal Form (4NF)

4NF is the fourth step in the normalization process and is achieved by removing non-transitive and non-key attributes. This ensures that the table does not contain any non-transitive dependencies.

#### Definition

4NF is achieved when a table is in 3NF and all non-key attributes are not dependent on any non-key attributes.

#### Example

Consider the table:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|---
[...truncated...]
```

To make this table in 4NF, we need to remove the StreetName attribute, which is dependent on the AddressID attribute, and the AddressID attribute itself. This can be achieved by creating a new table called Address with the following attributes:

```
| AddressID | AddressName | AddressType |
|-----------|-------------|-------------|
| 1         | Main St     | Apartment   |
| 2         | 2nd St      | House       |
| 3         | 3rd St      | Condo       |
```

Then, we can join the Address table with the Customer table using the AddressID attribute to retrieve the street name:

```
| CustomerID | CustomerName | AddressID | StreetName |
|------------|--------------|-----------|---
| 1          | John Smith   |           | Main St    |
| 2          | Jane Doe     |           | 2nd St     |
| 3          | Bob Johnson  |           | 3rd St     |
```