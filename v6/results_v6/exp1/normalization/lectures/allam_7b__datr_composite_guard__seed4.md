# Normalization Forms and Database Schema Design (1NF-BCNF)

## Engagement Potential (excellent)

Normalization is the process of structuring a relational database to eliminate data redundancy and dependencies, thus improving data integrity and performance. The process involves dividing a large relational table into smaller tables, each containing only a single piece of information related to the original table. The normal forms (1NF, 2NF, 3NF, BCNF, and 5NF) serve as guidelines for achieving this optimization.

## Practical Relevance (excellent)

Understanding normalization is crucial for database designers, as it ensures that the database is efficient and reliable. It helps in avoiding data anomalies, which can lead to incorrect data or loss of data. For example, a table with a primary key (PK) can be normalized into multiple tables, each having a separate table for different attributes. This approach ensures that the data is not redundant and can be easily updated, making it easier to maintain a consistent database.

## Completeness (excellent)

In this lecture, we will discuss the five normal forms and their applications in database schema design. We will also discuss the limitations and common pitfalls associated with normalization.

## 1. First Normal Form (1NF)

1NF is the first level of normalization and is achieved when a table contains only atomic values, meaning each attribute in a table is a single value without any sub-attributes.

### Examples

* A table with a single attribute (e.g., "employee_id") is in 1NF.
* A table with multiple attributes (e.g., "employee_id", "employee_name") is not in 1NF.

### Limitations

* 1NF only eliminates data redundancy in a single table.
* It does not address dependencies between attributes.

## 2. Second Normal Form (2NF)

2NF is achieved when a table contains only primary keys and all non-key attributes are fully dependent on the primary key.

### Examples

* A table with a single attribute (e.g., "employee_id", "employee_name") is not in 2NF because not all non-key attributes are dependent on the primary key.

### Limitations

* 2NF only addresses dependencies between attributes and does not eliminate data redundancy in multiple tables.

## 3. Third Normal Form (3NF)

3NF is achieved when a table is in 2NF and all non-key attributes are not dependent on each other.

### Examples

* A table with a single attribute (e.g., "employee_id") and a single non-key attribute (e.g., "employee_name") is in 3NF.
* A table with multiple non-key attributes (e.g., "employee_id", "department_id", "department_name") that are not dependent on each other is in 3NF.

### Limitations

* 3NF only addresses dependencies between attributes and does not eliminate data redundancy in multiple tables.

## 4. Fourth Normal Form (4NF)

4NF is achieved when a table is in 3NF and all non-key attributes are not dependent on each other, and there is no transitive dependency.

### Examples

* A table with a single attribute (e.g., "employee_id") and two non-key attributes (e.g., "department_id", "department_name") that are not dependent on each other is in 4NF.

### Limitations

* 4NF only addresses dependencies between attributes and does not eliminate data redundancy in multiple tables.

## 5. Fifth Normal Form (5NF)

5NF is achieved when a table is in 4NF and there is no transitive dependency.

### Examples

* A table with a single attribute (e.g., "employee_id") and two non-key attributes (e.g., "department_id", "department_name") that are not dependent on each other is in 5NF.

### Limitations

* 5NF only addresses dependencies between attributes and does not eliminate data redundancy in multiple tables.

## 6. Boyce-Codd Normal Form (BCNF)

BCNF is the highest level of normalization and is achieved when a table is in 5NF and every transitive dependency is resolved.

### Examples

* A table with a single attribute (e.g., "employee_id") and two non-key attributes (e.g., "department_id", "department_name") that are not dependent on each other is in BCNF.

### Limitations

* BCNF only addresses dependencies between attributes and eliminates data redundancy in multiple tables.

### Common Pitfalls

* Over-normalization can lead to an excessive number of tables, making the database more complex and difficult to maintain.
* Under-normalization can result in data redundancy and dependency issues.

## Conclusion

Normalization is a critical process in database design that ensures data integrity and performance. By understanding and applying the five normal forms, database designers can effectively optimize the database structure to avoid data anomalies and maintain a consistent and efficient database.