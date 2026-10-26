# Normalization Forms and Database Schema Design (1NF-BCNF)

## Engagement Potential

Normalization is the process of structuring a relational database to eliminate data redundancy and dependencies, thus improving data integrity and performance. The process involves dividing a large relational table into smaller tables, each containing only a single piece of information related to the original table. The normal forms (1NF, 2NF, 3NF, BCNF, and 5NF) serve as guidelines for achieving this optimization.

## Practical Relevance

Understanding normalization is crucial for database designers, as it ensures that the database is efficient and reliable. It helps in avoiding data anomalies, which can lead to incorrect data or loss of data. For example, a table with a primary key (PK) can be normalized into multiple tables, each having a separate table for different attributes. This approach ensures that the data is not redundant and can be easily updated, making it easier to maintain a consistent database.

## Completeness

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

* A table with a single attribute (e.g., "employee_id", "employee_name") is in 3NF.
* A table with multiple attributes (e.g., "employee_id", "employee_name", "department_id") is in 3NF.

### Limitations

* 3NF only eliminates data redundancy in multiple tables.
* It does not eliminate data anomalies.

## 4. Fourth Normal Form (4NF)

4NF is achieved when a table is in 3NF and all non-key attributes are not dependent on each other.

### Examples

* A table with a single attribute (e.g., "employee_id", "employee_name") is in 4NF.
* A table with multiple attributes (e.g., "employee_id", "employee_name", "department_id") is in 4NF.

### Limitations

* 4NF only eliminates data redundancy in multiple tables.
* It does not eliminate data anomalies.

## 5. Fifth Normal Form (5NF)

5NF is achieved when a table is in 4NF and all non-key attributes are not dependent on each other.

### Examples

* A table with a single attribute (e.g., "employee_id", "employee_name") is in 5NF.
* A table with multiple attributes (e.g., "employee_id", "employee_name", "department_id") is in 5NF.

### Limitations

* 5NF only eliminates data redundancy in multiple tables.
* It does not eliminate data anomalies.
* It is difficult to achieve 5NF because it requires a deep understanding of the relationships between tables.

## Conclusion

Normalization is a crucial process in database design that ensures data is not redundant and can be easily updated. In this lecture, we have discussed the five normal forms and their applications in database schema design. We have also discussed the limitations and common pitfalls associated with normalization.