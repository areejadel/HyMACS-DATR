### Normalization and Database Schema Design (1NF to BCNF)

#### Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** functional dependencies and determine candidate keys for a given relation.
2. **Apply** the rules of 1NF, 2NF, 3NF, and BCNF to detect anomalies in a database schema.
3. **Decompose** a non-normalized relation into a set of normalized relations while preserving data integrity.
4. **Evaluate** the trade-off between strict normalization (BCNF) and performance (denormalization) in real-world scenarios.

---

#### 1. Foundations: Dependencies and Redundancy

**The Hook: The Cost of a Single Typo**
Imagine a global logistics database where a warehouse address is stored alongside every single package record. If a warehouse moves across the street, you must update 10 million rows. If the system crashes after updating 5 million, your database is now "lying" to you: the warehouse is in two places at once. This is not a coding error; it is a structural failure. Normalization is the mathematical cure for this "lying" database.

**Terminology**
To ensure consistent notation, we define the following terms:
*   **Relation**: A table.
*   **Tuple**: A row within a relation.
*   **Attribute**: A column within a relation.

**Functional Dependency (FD)**
A functional dependency exists when an attribute $X$ uniquely determines an attribute $Y$, denoted as $X \to Y$. 
*   **Analogy**: Think of an FD as a **mathematical function** $f(x) = y$. If you provide the same input $x$, you must always get the same output $y$. If `StudentID` $\to$ `StudentName`, then every time the system sees ID `101`, it must see "Alice." If it sees "Bob" for ID `101` elsewhere, the dependency is violated.
*   **Determinant**: $X$ (the "input").
*   **Dependent**: $Y$ (the "result").

**Key Definitions**
*   **Superkey**: A set of attributes that uniquely identifies a tuple.
*   **Candidate Key**: A minimal superkey; no proper subset of a candidate key is also a superkey.
*   **Prime Attribute**: An attribute that is part of at least one candidate key.
*   **Non-prime Attribute**: An attribute that is not part of any candidate key.

**Worked Example: Determining the Candidate Key**
Consider the relation $\text{Enrollment}(\text{StudentID, CourseID, Grade, StudentName})$ with the following FDs:
1. $\text{StudentID} \to \text{StudentName}$
2. $\{\text{StudentID, CourseID}\} \to \text{Grade}$

*Analysis:*
*   $\text{StudentID}$ alone cannot be the key because a student may enroll in multiple courses, meaning $\text{Grade}$ would vary.
*   The set $\{\text{StudentID, CourseID}\}$ determines $\text{Grade}$ (via FD 2) and $\text{StudentName}$ (via FD 1).
*   Because $\{\text{StudentID, CourseID}\}$ determines all attributes and no smaller subset does, it is the **Candidate Key**.

**Try This Yourself**: Given $\text{Books}(\text{ISBN, Title, AuthorID, AuthorName})$ with FDs: $\text{ISBN} \to \text{Title}$ and $\text{AuthorID} \to \text{AuthorName}$. If we assume a book can have multiple authors, what is the candidate key? Why is it different from the "Quick Check" in the original draft?
*(Hint: If a book has multiple authors, ISBN alone cannot determine the AuthorID).*

---

#### 2. First Normal Form (1NF): Atomicity

**The Problem: The "Hidden" List**
Storing multiple values in a single cell (e.g., a `PhoneNumbers` column containing `"555-1234, 555-5678"`) creates a "black box" for the database. 
*   **The Tension**: You want to find all users with a "555" area code. Because the data isn't atomic, the database cannot use a B-Tree index to jump to the value. It must perform a **Full Table Scan**, reading every character of every row. As your data grows from 1,000 to 1 billion rows, your query time moves from milliseconds to hours.

**Formal Definition**
A relation is in **1NF** if the domain of every attribute contains only **atomic** (indivisible) values. 

**Worked Example: Normalizing to 1NF**
*Non-1NF Relation*: $\text{Student\_Courses}$
| StudentID | Courses |
| :--- | :--- |
| 101 | {CS101, MATH202} |

*Normalized Relation*: We decompose the multi-valued attribute into separate tuples.
| StudentID | CourseID |
| :--- | :--- |
| 101 | CS101 |
| 101 | MATH202 |

**Cross-Domain Connection**: 1NF is essentially the "Strong Typing" of database design. Just as you wouldn't store a list of integers inside a single `int` variable in C++, you don't store a list of values inside a single relational cell.

---

#### 3. Second Normal Form (2NF): Full Dependency

**The Problem: The "Identity Crisis"**
2NF is only relevant for relations with **composite keys**. A partial dependency occurs when a non-prime attribute depends on only *part* of the key.
*   **The Tension**: If a table has a composite key $\{\text{OrderID, ProductID}\}$ but also contains $\text{OrderDate}$, the $\text{OrderDate}$ only cares about the $\text{OrderID}$. The $\text{ProductID}$ is irrelevant. This means the table is trying to describe two different things: the *Order* and the *Line Item*.

**Formal Definition**
A relation is in **2NF** if it is in 1NF and every non-prime attribute is **fully functionally dependent** on every candidate key.

**Worked Example: Logistics**
Consider $\text{Shipment}(\underline{\text{ShipmentID, WarehouseID}}, \text{WarehouseCity, Weight})$.
*   **Candidate Key**: $\{\text{ShipmentID, WarehouseID}\}$
*   **Analysis**: $\text{Weight}$ depends on both (which package is at which warehouse). $\text{WarehouseCity}$ only depends on $\text{WarehouseID}$. This is a **Partial Dependency**.

*Decomposition*:
1. $\text{Warehouse}(\underline{\text{WarehouseID}}, \text{WarehouseCity})$
2. $\text{Shipment}(\underline{\text{ShipmentID, WarehouseID}}, \text{Weight})$

**Quick Check**: If a relation has a single-attribute candidate key, can it violate 2NF? 
*(Answer: No. You cannot have a "partial" dependency if there is only one attribute to depend on).*

---

#### 4. Third Normal Form (3NF): No Transitive Dependencies

**The Problem: The "Middleman" Dependency**
A transitive dependency occurs when a non-prime attribute is determined by another non-prime attribute: $\text{Key} \to \text{Attribute A} \to \text{Attribute B}$.
*   **Analogy**: This is like a "chain of command." If you want to know the $\text{DeptHead}$, you first find the $\text{DeptID}$ via the $\text{EmpID}$. The $\text{DeptHead}$ doesn't actually "know" the employee; they only know the department.
*   **The Tension (Deletion Anomaly)**: If you fire the last employee in a department and delete their row, you accidentally delete the fact that "Department 10 is led by Sarah." You've lost organizational knowledge because it was tied to a person rather than the department itself.

**Formal Definition**
A relation is in **3NF** if it is in 2NF and no non-prime attribute is transitively dependent on a candidate key. 
*Simplified Rule*: For every FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

**Worked Example: Corporate Hierarchy**
$\text{Employee}(\underline{\text{EmpID}}, \text{DeptID, DeptHead})$
*   $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \text{DeptHead}$.
*   **Decomposition**:
    1. $\text{Employee}(\underline{\text{EmpID}}, \text{DeptID})$
    2. $\text{Department}(\underline{\text{DeptID}}, \text{DeptHead})$

---

#### 5. Boyce-Codd Normal Form (BCNF): The Strict Rule

**The Problem: The "Prime" Loophole**
3NF allows $X \to A$ if $A$ is a prime attribute. BCNF says: "I don't care if $A$ is prime; $X$ must be a superkey." 

**The Tension: Overlapping Keys**
BCNF handles cases where candidate keys overlap. Consider $\text{CourseAssignment}(\text{Student, Course, Instructor})$.
*   **Constraints**: Each instructor teaches only one course; each course can have multiple instructors.
*   **Candidate Keys**: $\{\text{Student, Course}\}$ and $\{\text{Student, Instructor}\}$.
*   **FD**: $\text{Instructor} \to \text{Course}$.
*   **The Loophole**: This is 3NF because $\text{Course}$ is part of a candidate key (prime). But it is **not** BCNF because $\text{Instructor}$ is not a superkey. We can still have redundancy: if an instructor teaches a course, that fact is repeated for every student in the class.

**Decomposition**:
1. $\text{InstructorCourse}(\underline{\text{Instructor}}, \text{Course})$
2. $\text{StudentInstructor}(\underline{\text{Student, Instructor}})$

**Try This Yourself**: In the BCNF decomposition above, can we still easily enforce the rule that "A student cannot be enrolled in the same course under two different instructors"? 
*(Answer: No. The relationship between Student and Course is now split across two tables. This is the "Dependency Preservation" problem).*

---

#### 6. Practical Trade-offs: The "Real World"

**Dependency Preservation vs. BCNF**
As seen in the BCNF example, strict normalization can destroy functional dependencies. To enforce $\{\text{Student, Course}\} \to \text{Instructor}$, you now need a database trigger or application code, which is slower and more error-prone than a primary key constraint.

**The Denormalization Trade-off**
In OLAP (Data Warehousing), we prioritize **Read Speed** over **Write Integrity**.
*   **The Join Penalty**: Every time you normalize, you add a table. Every time you query, you add a `JOIN`. In a billion-row dataset, joining 10 tables is computationally ruinous.
*   **Strategic Redundancy**: We intentionally violate 3NF by adding `CustomerName` to the `Orders` table. We accept the risk of update anomalies to gain the speed of a single-table scan.

**Summary Matrix**

| Normal Form | Primary Requirement | Prevents | Trade-off |
| :--- | :--- | :--- | :--- |
| **1NF** | Atomic values | Full table scans / "Black box" data | Increased row count |
| **2NF** | No partial FDs | Redundancy in composite keys | Increased table count |
| **3NF** | No transitive FDs | Deletion anomalies (lost info) | Increased join complexity |
| **BCNF** | Determinant = Superkey | Redundancy in overlapping keys | Loss of FD preservation |