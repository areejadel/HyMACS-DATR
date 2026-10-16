Normalization Forms and Database Schema Design (1NF–BCNF)

**Learning Objectives:**

1. Define and explain the fundamental normal forms (1NF, 2NF, 3NF, BCNF, and 4NF) in database design, with a focus on their practical utility.
2. Identify and illustrate the key differences between each normal form, with a focus on their application in database design.
3. Apply the concept of normalization to a given database schema, ensuring data consistency and integrity.

**1NF: No Repeating Groups or Arrays - A digital library's records would be a mess without normalization!**

A relation is in 1NF if it has no repeating groups or arrays. This is the most basic level of normalization. For example, consider a digital library's database, where each book's information is stored in a single record. Without normalization, the library's records would be a mess, with repeating groups or arrays causing inconsistencies and data redundancy.

**2NF: Each Non-Key Attribute Must Depend on the Entire Primary Key - A student's grades report illustrates this concept.**

In 2NF, each non-key attribute must depend on the entire primary key. This ensures that each non-key attribute is dependent on the entire primary key, not just a part of it. For example, consider a student's grades report, where each subject's grade depends on the entire student ID. This ensures that each non-key attribute (like GPA or address) is dependent on the entire primary key, not just a part of it.

**Case Study: Normalizing a University's Student Information System**

To illustrate the practical relevance of 2NF, consider a university's student information system. The system's database is designed to store student information, including grades, GPA, and address. Without normalization, the database would have a large number of repeating groups or arrays, leading to inconsistencies and data redundancy. By applying 2NF, the database can be normalized, ensuring that each non-key attribute (like GPA or address) depends on the entire primary key (Student ID).

**3NF: Each Non-Key Attribute Must Depend on the Entire Primary Key, and for Each Non-Key Attribute, There Must be at Least One Candidate Key - A university's student information system illustrates this concept.**

3NF is a more stringent condition, where each non-key attribute must depend on the entire primary key, and for each non-key attribute, there must be at least one candidate key. This ensures that each non-key attribute is dependent on the entire primary key and has at least one candidate key. For example, consider a university's student information system, where each student's record depends on the entire primary key (Student ID), and each non-key attribute (like GPA or address) has at least one candidate key.

**BCNF: A Relation that is in 3NF and has no Transitive Functional Dependency - A bank's customer database illustrates this concept.**

BCNF is a relation that is in 3NF and has no transitive functional dependency. This ensures that each non-key attribute is dependent on the entire primary key and has no transitive functional dependency. For example, consider a bank's customer database, where each customer's information is dependent on the entire primary key (Customer ID), and there's no transitive functional dependency between attributes.

**Case Study: Normalizing a Bank's Customer Database**

To illustrate the practical relevance of BCNF, consider a bank's customer database. The database is designed to store customer information, including name, address, and account balance. Without normalization, the database would have a large number of repeating groups or arrays, leading to inconsistencies and data redundancy. By applying BCNF, the database can be normalized, ensuring that each non-key attribute is dependent on the entire primary key (Customer ID) and has no transitive functional dependency.

**4NF: A Relation that is in BCNF and has no Multidisciplinary Dependency - A university's employee database illustrates this concept.**

4NF is a relation that is in BCNF and has no multidisciplinary dependency. This ensures that each non-key attribute is dependent on the entire primary key and has no multidisciplinary dependency. For example, consider a university's employee database, where each employee's information is dependent on the entire primary key (Employee ID), and there's no multidisciplinary dependency between attributes.

**Illustrating Normalization: The TEACH Relation -**

Consider the relation TEACH, which has attributes Student, Instructor, and Course. Designating (Student, Instructor) as a primary key of the relation TEACH, the FD instructor → Course causes a partial (non-fully-functional) dependency of Course on a part of this key. This FD may be removed as part of second normalization (or by a direct application of the above procedure to achieve BCNF) yielding exactly the same two relations in the result.

**Algorithm 15.5: Producing BCNF Schemas by Decomposition of a Universal Schema -**

Algorithm 15.5 from Chapter 15 provides a systematic approach to normalization.

**Consideration of Multivalued Dependencies: The EMP Relation -**

Try to normalize the EMP relation, which has attributes Ename, Pname, and Dname. Can you identify the multivalued dependencies and apply the concept of normalization?

**Conclusion:**

Normalization is a crucial step in database design, ensuring data consistency and integrity. By applying the concepts of 1NF, 2NF, 3NF, BCNF, and 4NF, database designers can create efficient and scalable databases. This lecture has illustrated the practical relevance of normalization through case studies and examples, demonstrating how normalization can be applied to real-world database systems.