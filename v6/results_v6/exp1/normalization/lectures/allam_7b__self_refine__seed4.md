# Normalization Forms and Database Schema Design (1NF-BCNF)

## 1. First Normal Form (1NF)

1NF is achieved when a table contains only atomic values, meaning each attribute in a table is a single value without any sub-attributes.

### Examples

* A table with a single attribute (e.g., "employee_id") is in 1NF.
* A table with multiple attributes (e.g., "employee_id", "employee_name") is not in 1NF because it contains sub-attributes (e.g., "employee_name").

### Misconception
* A table with multiple attributes (e.g., "employee_id", "employee_name") is in 1NF because all attributes are atomic.
* Anticipated Correction: Introduce the concept of "atomic value" and explain why the table is not in 1NF.

### Limitations

* 1NF only eliminates data redundancy in a single table.
* It does not address dependencies between attributes.

### Formative Check
* Can you identify a table that is in 1NF?
* Can you explain why a table with multiple attributes is not in 1NF?

## 2. Second Normal Form (2NF)

2NF is achieved when a table contains only primary keys and all non-key attributes are fully dependent on the primary key.

### Examples

* A table with a single attribute (e.g., "employee_id") is not in 2NF because not all non-key attributes are dependent on the primary key.

### Misconception
* A table with multiple attributes (e.g., "employee_id", "employee_name") is in 2NF because all non-key attributes are dependent on the primary key.
* Anticipated Correction: Explain the difference between "dependent" and "fully dependent" and why a table with multiple attributes is not in 2NF.

### Limitations

* 2NF only addresses dependencies between attributes and does not eliminate data redundancy in multiple tables.

### Formative Check
* Can you explain the difference between "dependent" and "fully dependent"?
* Can you identify a table that is not in 2NF?

## 3. Third Normal Form (3NF)

3NF is achieved when a table is in 2NF and all non-key attributes are not dependent on each other.

### Examples

* A table with a single attribute (e.g., "employee_id") and a non-key attribute (e.g., "employee_name") is in 3NF.

### Misconception
* A table with multiple attributes (e.g., "employee_id", "employee_name") is in 3NF because all non-key attributes are not dependent on each other.
* Anticipated Correction: Define "not dependent on each other" and explain why a table with multiple attributes is not in 3NF.

### Limitations

* 3NF only ensures independence of non-key attributes, not elimination of redundancy in multiple tables.

### Formative Check
* Can you define "not dependent on each other"?
* Can you identify a table that is not in 3NF?