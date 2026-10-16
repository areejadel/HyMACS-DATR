**Normalization Forms and Database Schema Design (1NF–BCNF)**

By the end of this lecture, students will be able to:

1. Define the concept of normalization and its importance in database design (apply).
2. Identify and explain the characteristics of each normal form (1NF, 2NF, 3NF, and BCNF) using concrete examples (analyze).
3. Apply the principles of normalization to design a database schema, avoiding data redundancy and anomalies (create).

**The Great Database Puzzle**

Imagine you're a detective trying to solve a mystery. You have a set of clues, but they're scattered across different locations. Each clue is a piece of information, and you need to gather them all to solve the case. But, what if the clues are duplicated or contradictory? That would make it impossible to solve the mystery! This is where normalization comes in – to ensure that each piece of information is unique and consistent, just like a detective needs to gather unique and accurate clues to solve the case.

**1NF (First Normal Form)**

Each table cell must contain a single value. To illustrate this, consider a table `Students` with columns `StudentID`, `Name`, and `Address`. Notice that each row represents a single student, and each column has a single value. To normalize this table, break down the `Address` column into separate columns for `Street`, `City`, and `Zipcode`, as shown in the figure below.

**Formal Definition:** A table is in 1NF if and only if each table cell contains a single value.

**2NF (Second Normal Form)**

Each non-key attribute in a table must depend on the entire primary key. Revisit the `Courses` example. The primary key is `CourseID`, and the non-key attribute `Instructor` depends on the entire primary key. Normalize this table by moving the `Instructor` column to a separate table, `Instructors`, with a primary key `InstructorID`, as shown in the figure below.

**Try This Yourself:** Can you think of a scenario where a database design would benefit from 2NF? Try to design a database schema for a library system, where students can borrow books. How would you normalize the tables to ensure data consistency and integrity?

**3NF (Third Normal Form)**

Each non-key attribute in a table must depend on the entire primary key, and there are no transitive dependencies. Revisit the `Courses` example. Normalize this table by moving the `Course` column to a separate table, `Courses`, with a primary key `CourseID`, as shown in the figure below.

**BCNF (Boyce-Codd Normal Form)**

BCNF is a normal form that is more restrictive than 3NF. It states that each table must be in 3NF, and there are no transitive dependencies.

**Denormalization**

Denormalization is the process of storing the join of higher normal form relations as a base relation, which is in a lower normal form. This can be done for performance reasons, but it can also lead to data redundancy and inconsistencies.

**Worked Examples**

Suppose we have a table `Courses` with columns `CourseID`, `CourseName`, and `Instructor`. The primary key is `CourseID`, and the non-key attribute `Instructor` depends on the entire primary key. Normalize this table by breaking down the `Instructor` column into separate columns for `InstructorName` and `InstructorID`, as shown in the figure below.

Consider a table `Teach` with columns `StudentID`, `Instructor`, and `Course`. The primary key is `StudentID`, and the non-key attribute `Instructor` depends on the entire primary key. Normalize this table by breaking down the `Instructor` column into separate columns for `InstructorName` and `InstructorID`, and move the `Instructor` values to the `Instructors` table, as shown in the figure below.

**Formative Check:** Can you identify the primary key and non-key attributes in the `Teach` table? Can you explain why 2NF is necessary in this case?

**Conclusion:** Normalization is a crucial step in database design, ensuring data consistency, integrity, and scalability. By applying the principles of normalization, we can design a database schema that avoids data redundancy and anomalies, making it more efficient and effective.