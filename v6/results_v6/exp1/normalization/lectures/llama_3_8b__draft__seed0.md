**Normalization Forms and Database Schema Design (1NF–BCNF)**

**Learning Objectives:**

To understand the fundamental normal forms (1NF-BCNF) and their characteristics, apply the normal forms to ensure data consistency and integrity in database design, and analyze the trade-offs between normalization and denormalization in database design.

**The data chaos: a hook**

Imagine a database with multiple tables, each filled with data. Now, imagine trying to query this data to get a simple answer. You'd need to join multiple tables, dealing with anomalies, and hoping for the best. This is the reality of working with unnormalized data. But, what if we could normalize it? Let's dive into the world of normal forms and see how they can save us from this chaos.

**First Normal Form (1NF)**

The first normal form (1NF) requires that each table cell contains a single value, eliminating repeating groups. This is achieved by decomposing a relation into smaller, independent relations. For instance, an Employee table with attributes Employee ID, Name, and Department. In 1NF, each cell would contain a single value, ensuring that each employee is associated with a single department. Let's try it ourselves: can you think of a scenario where having multiple phone numbers for an employee would lead to data inconsistencies?

**Example 1: Employee Table in 1NF**

An Employee table with attributes Employee ID, Name, and Department, in 1NF, would contain a single value in each cell, ensuring that each employee is associated with a single department.

**Second Normal Form (2NF)**

The second normal form (2NF) is a refinement of 1NF, ensuring that each non-key attribute is fully functionally dependent on the primary key. This means that each non-key attribute is dependent on the primary key and cannot be modified independently. For example, a Department table with attributes Department ID, Name, and Location. In 2NF, the Location attribute is fully functionally dependent on the Department ID, ensuring that each department is associated with a single location.

**Example 2: Department Table in 2NF**

A Department table with attributes Department ID, Name, and Location, in 2NF, would have the Location attribute fully functionally dependent on the Department ID, ensuring that each department is associated with a single location.

**Third Normal Form (3NF)**

The third normal form (3NF) is a further refinement of 2NF, ensuring that each non-key attribute is not transitive dependent on another non-key attribute. This eliminates the possibility of indirect relationships between non-key attributes. For instance, a Course table with attributes Course ID, Name, and Instructor. In 3NF, the Instructor attribute is not transitive dependent on another non-key attribute, ensuring that each course is associated with a single instructor.

**Example 3: Course Table in 3NF**

A Course table with attributes Course ID, Name, and Instructor, in 3NF, would have the Instructor attribute not transitive dependent on another non-key attribute, ensuring that each course is associated with a single instructor.

**Boyce-Codd Normal Form (BCNF)**

The Boyce-Codd normal form (BCNF) is a stronger normal form, ensuring that each table is in 3NF and that there are no transitive dependencies between non-key attributes. For example, a Student-Teaching table with attributes Student ID, Teacher ID, and Course. In BCNF, the table is in 3NF, and there are no transitive dependencies between non-key attributes.

**Example 4: Student-Teaching Table in BCNF**

A Student-Teaching table with attributes Student ID, Teacher ID, and Course, in BCNF, would be in 3NF, and there would be no transitive dependencies between non-key attributes.

**Practical Use of Normal Forms**

In practical design projects, normal forms are often used to ensure data consistency and integrity. However, as noted in [1], the practical utility of these normal forms becomes questionable due to the rarity of the constraints on which they are based. As a result, database design often pays particular attention to normalization only up to 3NF, BCNF, or at most 4NF.

**Denormalization**

Denormalization is the process of storing the join of higher normal form relations as a base relation, which is in a lower normal form. This incurs the corresponding penalties of dealing with anomalies.

**Conclusion**

In this lecture, we have explored the fundamental normal forms, their characteristics, and practical applications. Normalization is a crucial step in database design, ensuring data consistency and integrity. By understanding the different normal forms, database designers can create efficient and effective database designs.

References:
[1] Elmasri & Navathe (2016), Fundamentals of Database Systems, Ch. 14-15.
[2]