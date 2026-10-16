Here is the revised lecture body:

Normalization Forms and Database Schema Design (1NF–BCNF)

**Learning Objectives:**

1. Recall the definition of each normalization form (1NF, 2NF, BCNF) and explain its purpose in database design.
2. Identify and eliminate repeating groups or arrays in a given database schema (1NF).
3. Recognize and eliminate partial dependencies in a relation (2NF).
4. Eliminate transitive dependencies in a relation (BCNF).
5. Apply normalization techniques to a given database schema.

**1NF: Eliminating Repeating Groups or Arrays**

Imagine a social media platform where users can create multiple posts with varying details. How would you design the database schema to efficiently store and retrieve this information? Try to create a simple schema for this scenario, paying attention to repeating groups or arrays.

Formal Definition: A relation is in 1NF if it does not contain repeating groups or arrays.

**Example:** Normalize a given database schema by identifying and eliminating repeating groups or arrays.

**2NF: Eliminating Partial Dependencies**

Think of a healthcare system where patient medical records contain test results from various labs. Each test result depends on the patient's unique identifier. How would you design the database schema to ensure data consistency and integrity? Try to normalize the relation by creating separate tables for patient information and test results.

Formal Definition: A relation is in 2NF if each non-key attribute depends on the entire primary key.

**Example:** Normalize a given database schema by identifying and eliminating partial dependencies.

**BCNF: Eliminating Transitive Dependencies**

Consider a company's HR system, where employee job titles depend on their department and manager. If the manager's job title is determined by their department, the system is not in BCNF. How would you normalize the relation to ensure data consistency and integrity? Try to create a separate table for job titles and dependencies.

Formal Definition: A relation is in BCNF if it has no transitive dependencies.

**Example:** Normalize a given database schema by identifying and eliminating transitive dependencies.

**Higher Normal Forms**

[...truncated...]