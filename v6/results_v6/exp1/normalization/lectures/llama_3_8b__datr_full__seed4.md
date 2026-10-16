Normalization Forms and Database Schema Design (1NF–BCNF)

**Learning Objectives:**

1. Define and explain the fundamental normal forms (1NF, 2NF, 3NF, BCNF, and 4NF) in database design, with a focus on their practical utility.
2. Identify and illustrate the key differences between each normal form, with a focus on their application in database design.
3. Apply the concept of normalization to a given database schema, ensuring data consistency and integrity.

**Case Study: Online Shopping Database**

Imagine an online shopping database that stores customer information, order details, and product descriptions. Without normalization, this database would be prone to data inconsistencies and anomalies. Let's apply normalization to this database to ensure data consistency and integrity.

**1NF: No Repeating Groups or Arrays**

In 1NF, a relation has no repeating groups or arrays. For example, the online shopping database has a table for customer information, where each customer's name, address, and contact information are stored in separate columns. This ensures that each customer's information is unique and consistent.

**2NF: Each Non-Key Attribute Must Depend on the Entire Primary Key**

In 2NF, each non-key attribute must depend on the entire primary key. For example, the order details table has a primary key of (Order ID, Customer ID), and each non-key attribute (such as order date, product name, and quantity) depends on the entire primary key.

**3NF: Each Non-Key Attribute Must Depend on the Entire Primary Key, and for Each Non-Key Attribute, There Must be at Least One Candidate Key**

In 3NF, each non-key attribute must depend on the entire primary key, and for each non-key attribute, there must be at least one candidate key. For example, the product description table has a primary key of (Product ID), and each non-key attribute (such as product name, description, and price) depends on the entire primary key and has at least one candidate key.

**BCNF: A Relation that is in 3NF and has no Transitive Functional Dependency**

In BCNF, a relation is in 3NF and has no transitive functional dependency. For example, the customer information table has a primary key of (Customer ID), and each non-key attribute (such as name, address, and contact information) depends on the entire primary key and has no transitive functional dependency.

**4NF: A Relation that is in BCNF and has no Multidisciplinary Dependency**

In 4NF, a relation is in BCNF and has no multidisciplinary dependency. For example, the order details table has a primary key of (Order ID, Customer ID), and each non-key attribute (such as order date, product name, and quantity) depends on the entire primary key and has no multidisciplinary dependency.

**Illustrating Normalization: Online Shopping Database**

Let's apply normalization to the online shopping database. We can identify the repeating groups and arrays in the database and break them down into smaller, more manageable tables. For example, the customer information table can be broken down into separate tables for customer names, addresses, and contact information.

**Algorithm 15.5: Producing BCNF Schemas by Decomposition of a Universal Schema**

Algorithm 15.5 from Chapter 15 provides a systematic approach to normalization. By applying this algorithm, we can systematically normalize the online shopping database and ensure data consistency and integrity.

**Consideration of Multivalued Dependencies: Online Shopping Database**

In addition to normalization, we must also consider multivalued dependencies in the online shopping database. For example, the order details table has a multivalued dependency between the order date and product name. To normalize this table, we can break down the multivalued dependency into separate tables for order dates and product names.

By applying normalization and considering multivalued dependencies, we can ensure that the online shopping database is consistent, intuitive, and easy to maintain.