**Normalization Forms and Database Schema Design (1NF–BCNF)**

By the end of this lecture, students will be able to:

1. Define the concept of normalization and its importance in database design, identifying the benefits of minimizing data redundancy and improving data retrieval efficiency.
2. Identify and explain the characteristics of each normal form (1NF, 2NF, 3NF, and BCNF), recognizing the role of primary and foreign keys in ensuring data consistency.
3. Apply the principles of normalization to design a database schema, leveraging intuition and worked examples to illustrate the application of each normal form.

**1NF (First Normal Form)**

We begin with 1NF, which ensures that each table cell contains a single value. Consider the `Students` table with columns `StudentID`, `Name`, and `Address`. Each row in this table represents a single student, and each column has a single value.

| **Table Cell Contents** | **Single Value?** |
| --- | --- |
| `StudentID` | Yes |
| `Name` | Yes |
| `Address` | Yes |

**Formal Definition:** In 1NF, each table cell must contain a single value, and each row in a table must have a single value for each column.

**Worked Example:** Normalize the `Courses` table with columns `CourseID`, `CourseName`, and `Instructor`. Identify the steps to break down the `Instructor` column into separate columns for `InstructorName` and `InstructorID`. (Answer: Split the `Instructor` column into separate columns for `InstructorName` and `InstructorID` to avoid data redundancy.)

**Common Misconception:** 1NF applies to all tables, regardless of the number of rows.

**Formative Check:** What is the main goal of 1NF? (Answer: Ensure each table cell contains a single value.)

**2NF (Second Normal Form)**

Next, we explore 2NF, which ensures that each non-key attribute in a table depends on the entire primary key. Revisiting the `Courses` example, the primary key is `CourseID`, and the non-key attribute `Instructor` depends on the entire primary key.

| **Primary Key** | **Non-Key Attribute** | **Dependence** |
| --- | --- | --- |
| `CourseID` | `Instructor` | Entire primary key |

**Formal Definition:** In 2NF, each non-key attribute in a table must depend on the entire primary key.

**Worked Example:** Normalize the `Teach` table with columns `StudentID`, `Instructor`, and `Course`. Identify the steps to break down the `Instructor` column into separate columns for `InstructorName` and `InstructorID`. (Answer: Split the `Instructor` column into separate columns for `InstructorName` and `InstructorID` to avoid data redundancy.)

**Common Misconception:** 2NF applies to all tables, regardless of the number of primary keys.

**Formative Check:** What is the main goal of 2NF? (Answer: Ensure each non-key attribute depends on the entire primary key.)

...and so on...