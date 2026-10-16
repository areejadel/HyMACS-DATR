**Normalization Forms and Database Schema Design (1NF–BCNF)**

**Learning Objectives:**

* Define and explain the concept of normalization in database design.
* Identify and describe the different normal forms (1NF, 2NF, 3NF, BCNF, 4NF, 5NF) and their importance.
* Apply the concept of normalization to real-world scenarios and practical database design.

**First Normal Form (1NF)**

Imagine a chessboard: each square has a single piece, just like each customer has a single name, address, and order history in a normalized database. To ensure data consistency and integrity, the customer name attribute must have a single value for each customer, meeting the 1NF requirement.

Formally, a relation R is in 1NF if, for every attribute A in R, the set {t | t is a tuple in R and t[A] is not null} is not empty.

**Try This Yourself:**

Design a database for a popular social media platform. Would a single value for each attribute be sufficient for storing user information? (Answer: No, a social media platform would require more complex relationships between attributes, necessitating higher normal forms.)

**Second Normal Form (2NF)**

Consider a database designed for a university that tracks student course enrollment. Each student can take multiple courses, and each course has multiple students enrolled. To ensure data consistency and integrity, the course title attribute must depend on the entire primary key, which consists of the student ID and course ID, meeting the 2NF requirement.

Formally, a relation R is in 2NF if, for every attribute A in R, if A is a non-key attribute, then for every tuple t in R, t[A] depends on the entire primary key.

**Tension Before Resolution:**

Why is it crucial to ensure that each non-key attribute depends on the entire primary key in a relation? Consider a scenario where a database tracks student course enrollment and course prerequisites. If the course title depends on the student ID, which in turn depends on the instructor's name, how would you handle this transitive dependency?

**Quick Check:**

1. What is the primary key in the relation TEACH?
2. Is the relation TEACH in 2NF?
3. Is the relation TEACH in 3NF?
4. Is the relation TEACH in BCNF?

**Third Normal Form (3NF)**

Imagine a city's public transportation system: each bus route has a single schedule, just like each account has a single transaction history in a normalized database. To ensure data consistency and integrity, there are no transitive dependencies between attributes, meeting the 3NF requirement.

Formally, a relation R is in 3NF if, for every attribute A in R, if A is a non-key attribute, then for every tuple t in R, t[A] does not depend on any other attribute.

**Try This Yourself:**

Can you think of a scenario where a database with transitive dependencies would be problematic? Consider a database designed for a hospital that tracks patient medical records. If a patient's medical history depends on the doctor's name, which in turn depends on the patient's name, how would you handle this transitive dependency?

**Boyce-Codd Normal Form (BCNF)**

Consider a database designed for a hotel management system that tracks room reservations. Each room can have multiple reservations, and each reservation can have multiple guests. To ensure data consistency and integrity, the relation is in 3NF and there are no transitive dependencies, meeting the BCNF requirement.

Formally, a relation R is in BCNF if, for every attribute A in R, if A is a non-key attribute, then for every tuple t in R, t[A] does not depend on any other attribute.

**Fourth and Fifth Normal Forms (4NF and 5NF)**

Imagine a complex supply chain management system: each supplier can have multiple products, and each product can have multiple suppliers. To ensure data consistency and integrity, the relation is in 4NF and 5NF, which ensure that there are no multi-level dependencies and no join dependencies, respectively.

Formally, a relation R is in 4NF if, for every attribute A in R, if A is a non-key attribute, then for every tuple t in R, t[A] does not depend on any other non-key attribute.

Formally, a relation R is in 5NF if, for every attribute A in R, if A is a non-key attribute, then for every tuple t in R, t[A] does not depend on any other attribute.