## Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** functional dependencies and candidate keys within a given relation.
2. **Detect** violations of 1NF, 2NF, 3NF, and BCNF in a database schema.
3. **Decompose** a non-normalized relation into a set of normalized relations to eliminate redundancy and anomalies.
4. **Evaluate** the trade-off between normalization (data integrity) and denormalization (query performance) for specific use cases.

---

## 0. Prerequisites and Intuition

### The Hook: The Cost of "Just Adding a Column"
Imagine you are designing a system for a global logistics company. You decide to store everything in one large `Shipments` table: `ShipmentID`, `CustomerName`, `CustomerAddress`, `WarehouseID`, and `WarehouseLocation`. It seems efficient—one query gets all the data. 

But then, a warehouse moves to a new city. To reflect this, you must update 10,000 shipment records. If the system crashes halfway through, your database now claims the same warehouse is in two different cities simultaneously. You haven't just encountered a bug; you've encountered a structural failure of the schema. This "data corruption by design" is exactly what normalization prevents.

### The Core Problem: Anomalies
Redundancy occurs when the same fact is stored in multiple rows. This creates three structural traps:

*   **Update Anomaly:** Changing a single fact (e.g., an instructor's office) requires updating every row where that fact appears. Partial updates lead to "schizophrenic" data.
*   **Insertion Anomaly:** You cannot record a fact about an entity (e.g., a new instructor's office) until that entity is linked to another entity (e.g., a student) because the primary key requires both.
*   **Deletion Anomaly:** Deleting a relationship (e.g., the last student in a course) accidentally wipes out a fundamental fact (e.g., the existence of the instructor and their office).

**Normalization** is the process of decomposing relations to ensure that every single fact is stored in exactly one place.

### The Tool: Functional Dependency (FD)
To normalize, we need a mathematical way to describe "what determines what."

**Intuition:** Think of a Functional Dependency as a **lookup function**. If $X \to Y$, then $X$ is the input and $Y$ is the output. If I give you a specific `StudentID`, the "function" of the database should return exactly one `StudentEmail`. If it could return two different emails for the same ID, the dependency is broken.

**Formal Definition:** A functional dependency $X \to Y$ exists in relation $R$ if, for every pair of tuples $t_1$ and $t_2$ in $R$, whenever $t_1[X] = t_2[X]$, then $t_1[Y] = t_2[Y]$.

### Key Terminology
*   **Candidate Key:** A minimal set of attributes that functionally determines all other attributes in the relation. (The "Unique Identifier").
*   **Prime Attribute:** An attribute that is a member of at least one candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

---

## 1. First Normal Form (1NF): Atomicity

### The Tension: The "List" Temptation
It is tempting to store a list of values in a single cell (e.g., `Courses: "CS101, CS102, MATH201"`). While this looks clean to a human, it is a nightmare for a machine. How do you write a SQL query to find all students taking "CS101" without using slow, error-prone string searching (like `LIKE '%CS101%'`)?

**Cross-Domain Connection:** This is effectively the difference between a **Scalar** and a **Collection**. In programming, you wouldn't store a list of objects as a single comma-separated string if you intended to iterate or filter them; you would use an Array or a List. 1NF forces the database to treat data as scalars, enabling the engine to use B-Tree indexing for lightning-fast lookups rather than scanning every character of every string.

### Formal Definition
A relation is in **1NF** if every attribute in every tuple contains only **atomic** (indivisible) values from its domain.

### Worked Example
**Scenario:** $\text{STUDENT\_COURSES}(\text{StudentID, CourseName})$

| StudentID | CourseName |
| :--- | :--- |
| 101 | {Physics, Calculus} |

**The Problem:** The $\text{CourseName}$ cell contains a set. This forces the application layer to parse strings rather than allowing the database engine to use its relational algebra.

**The Solution:** Decompose the multi-valued attribute into separate rows.

| StudentID | CourseName |
| :--- | :--- |
| 101 | Physics |
| 101 | Calculus |

**Real-World Case Study: E-commerce Order Items.** 
A common mistake in early-stage MVP development is storing order items as a JSON blob or comma-separated string in an `Orders` table (e.g., `Items: "SKU123:2, SKU456:1"`). This violates 1NF. While it makes the initial "Get Order" query fast, it makes "Calculate total sales for SKU123" an $O(N)$ operation requiring a full table scan and string parsing. By moving to 1NF (creating an `OrderItems` table), the database can use an index on `SKU`, turning the query into an $O(\log N)$ operation.

**Real-World Case Study: Fintech Transaction Tags.**
In a banking app, a transaction might have multiple tags (e.g., `#Travel`, `#Food`, `#Business`). Storing these as a string `"Travel, Food"` prevents the bank from efficiently running a query like "Sum all spending for #Food across 1 million users." By normalizing to 1NF, the bank creates a `TransactionTags` table, allowing for a high-performance join between the `Tags` and `Transactions` tables.

**Try this yourself:** Look at a CSV file or a JSON response from a public API (like GitHub or Twitter). Identify one field that is a "list" (e.g., `tags` or `followers`). If you were to move this into a relational database, how would you split it to satisfy 1NF? What is the new Primary Key of the resulting table?

---

## 2. Second Normal Form (2NF): No Partial Dependencies

### The Tension: The "Half-Key" Problem
Once we have 1NF, we often use **composite keys** (keys made of multiple columns). But what happens if a column only cares about *part* of that key? 

**Analogy:** Imagine a badge that grants access to a building. The badge ID is the key. If the badge also lists the "Building Color," the color depends on the building, not the specific badge. Storing the building color on every single badge is redundant.

**Innovation Insight:** 2NF is essentially a check for **entity confusion**. A partial dependency is a signal that you are trying to describe two different "things" (entities) in one table. In the badge example, the "Badge" and the "Building" are different entities. 2NF forces you to separate the "Badge-to-Building" relationship from the "Building Properties."

### Formal Definition
A relation is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key.

A violation occurs if a non-prime attribute depends on a proper subset of a candidate key (a **Partial Dependency**).

### Worked Example
**Scenario:** $\text{TEACH}(\text{Student, Course, Instructor, InstructorOffice})$
*   **Candidate Key:** $\{\text{Student, Course}\}$
*   **Functional Dependencies:**
    1. $\{\text{Student, Course}\} \to \text{Instructor}$
    2. $\text{Instructor} \to \text{InstructorOffice}$

**The Problem:** $\text{InstructorOffice}$ is determined by $\text{Instructor}$. But $\text{Instructor}$ is only *part* of the logic that identifies the row. We don't need to know which $\text{Student}$ is in the class to know where the $\text{Instructor}$'s office is. This is a partial dependency.

**The Solution:** Split the table so that the "Office" fact lives only with the "Instructor" fact.
1. $R_1(\underline{\text{Instructor}}, \text{InstructorOffice})$
2. $R_2(\underline{\text{Student, Course}}, \text{Instructor})$

**Real-World Case Study: Inventory Management.**
Consider a table $\text{Inventory}(\text{WarehouseID, ProductID, Quantity, WarehouseAddress})$. The primary key is $\{\text{WarehouseID, ProductID}\}$. However, $\text{WarehouseAddress}$ depends only on $\text{WarehouseID}$. If a warehouse has 5,000 products, the address is repeated 5,000 times. If the warehouse moves, you must update 5,000 rows (Update Anomaly). If you open a new warehouse but haven't stocked it yet, you cannot record its address because you lack a `ProductID` to complete the key (Insertion Anomaly). 2NF resolves this by splitting into $\text{Warehouses}(\underline{\text{WarehouseID}}, \text{Address})$ and $\text{Stock}(\underline{\text{WarehouseID, ProductID}}, \text{Quantity})$.

**Real-World Case Study: Aviation Flight Schedules.**
In a flight database, a table $\text{FlightLegs}(\text{FlightNumber, LegNumber, DepartureAirport, DepartureCity})$ has a composite key $\{\text{FlightNumber, LegNumber}\}$. However, $\text{DepartureCity}$ is functionally dependent only on $\text{DepartureAirport}$. Storing the city name for every single flight leg is redundant. 2NF mandates separating this into $\text{Airports}(\underline{\text{AirportCode}}, \text{City})$ and $\text{FlightLegs}(\underline{\text{FlightNumber, LegNumber}}, \text{DepartureAirport})$.

---

## 3. Third Normal Form (3NF): No Transitive Dependencies

### The Tension: The "Middleman" Dependency
Even if every column depends on the *whole* key, they might be depending on it through a "middleman." 

**Analogy:** Think of a chain of command. The CEO $\to$ Manager $\to$ Employee. If you store the Manager's phone number in the Employee's record, the phone number depends on the Employee *only because* the Employee depends on the Manager. If the employee quits, you lose the manager's phone number.

**Cross-Domain Connection:** This is analogous to **Tight Coupling** in software architecture. If Module A depends on Module B, and Module B depends on Module C, Module A is transitively coupled to C. If C changes, A might break. In 3NF, we "decouple" the attributes so that each non-key attribute depends *only* on the key, and nothing else.

### Formal Definition
A relation is in **3NF** if:
1. It is in 2NF.
2. No non-prime attribute is **transitively dependent** on a candidate key.

**Formal Condition:** For every non-trivial FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

### Worked Example
**Scenario:** $\text{EMPLOYEE}(\text{EmpID, DeptID, DeptName})$
*   **Candidate Key:** $\{\text{EmpID}\}$
*   **Functional Dependencies:**
    1. $\text{EmpID} \to \text{DeptID}$
    2. $\text{DeptID} \to \text{DeptName}$

**The Problem:** $\text{EmpID} \to \text{DeptID} \to \text{DeptName}$. The $\text{DeptName}$ is a "passenger" riding on $\text{DeptID}$. This creates a deletion anomaly: if you fire the only employee in "Research," the "Research" department itself vanishes from your database.

**The Solution:** Remove the middleman.
1. $R_1(\underline{\text{EmpID}}, \text{DeptID})$
2. $R_2(\underline{\text{DeptID}}, \text{DeptName})$

**Real-World Case Study: Healthcare Patient Records.**
Imagine a table $\text{PatientVisit}(\text{VisitID, PatientID, DoctorID, DoctorSpecialty})$. The key is $\text{VisitID}$. We have $\text{VisitID} \to \text{DoctorID}$ and $\text{DoctorID} \to \text{DoctorSpecialty}$. The specialty is transitively dependent on the visit. If a doctor changes their specialty (e.g., from General Practitioner to Cardiologist), you must update every visit record that doctor ever handled. If you fail to do so, the same doctor will appear to have different specialties across different visits. 3NF separates this into $\text{Visits}(\underline{\text{VisitID}}, \text{PatientID}, \text{DoctorID})$ and $\text{Doctors}(\underline{\text{DoctorID}}, \text{Specialty})$.

**Real-World Case Study: Logistics Tracking.**
In a shipment tracking system, a table $\text{Shipment}(\text{ShipmentID, CarrierID, CarrierContactPhone})$ has a key $\text{ShipmentID}$. Here, $\text{ShipmentID} \to \text{CarrierID}$ and $\text{CarrierID} \to \text{CarrierContactPhone}$. If you delete the only shipment associated with a specific carrier, you lose that carrier's contact information. 3NF separates this into $\text{Shipments}(\underline{\text{ShipmentID}}, \text{CarrierID})$ and $\text{Carriers}(\underline{\text{CarrierID}}, \text{ContactPhone})$.

---

## 4. Boyce-Codd Normal Form (BCNF): The Strictest Standard

### The Tension: The "Prime" Loophole
3NF has a loophole: it allows a dependency if the dependent attribute is "prime" (part of a key). This is rare, but it allows redundancy to sneak back in when you have overlapping candidate keys. BCNF closes this loophole.

**Innovation Insight:** BCNF is the "Zero Trust" policy of database design. While 3NF says "I'll trust this dependency if it's part of a key," BCNF says "I don't care if it's prime or not; if you are determining something, you MUST be a superkey." It eliminates the possibility of a non-key determining a part of a key.

### Formal Definition
A relation is in **BCNF** if, for every non-trivial functional dependency $X \to A$, $X$ is a superkey. 
*Simplified: "Every determinant must be a candidate key."*

### Worked Example
**Scenario:** $\text{TEACH}(\text{Student, Course, Instructor})$
*   **Constraints:** Each instructor teaches only one course; multiple instructors may teach the same course.
*   **Functional Dependencies:**
    1. $\{\text{Student, Course}\} \to \text{Instructor}$
    2. $\text{Instructor} \to \text{Course}$
*   **Candidate Keys:** $\{\text{Student, Course}\}$ and $\{\text{Student, Instructor}\}$

**Analysis:**
*   **3NF Check:** It *is* in 3NF. In $\text{Instructor} \to \text{Course}$, $\text{Course}$ is a prime attribute. 3NF says "That's fine."
*   **BCNF Check:** It is **not** in BCNF. In $\text{Instructor} \to \text{Course}$, the determinant ($\text{Instructor}$) is **not** a superkey (it can't tell us which student is in the class).

**The Solution:** Decompose to ensure the determinant is the key.
1. $R_1(\underline{\text{Instructor}}, \text{Course})$
2. $R_2(\underline{\text{Student, Instructor}})$

**Real-World Case Study: Specialized Consultant Assignments.**
Consider a project management system where $\text{Assignment}(\text{Project, Consultant, Skill})$. Assume:
1. A project requires a specific skill (e.g., Project A requires "Cloud Architecture").
2. A consultant has only one primary skill they provide to projects.
3. A project can have multiple consultants, but they must all possess the required skill for that project.

The candidate keys are $\{\text{Project, Consultant}\}$. However, we have the FD: $\text{Consultant} \to \text{Skill}$. Since $\text{Consultant}$ is not a superkey, this violates BCNF. If we store this in one table, we repeat the consultant's skill for every project they are assigned to. If a consultant is updated to a new skill, we face an update anomaly. BCNF forces the split into $\text{ConsultantSkills}(\underline{\text{Consultant}}, \text{Skill})$ and $\text{ProjectAssignments}(\underline{\text{Project, Consultant}})$.

**Real-World Case Study: Legal Case Management.**
In a law firm database, $\text{CaseAssignment}(\text{CaseID, Lawyer, Specialization})$. Assume each lawyer has one specialization, but a case can have multiple lawyers. The key is $\{\text{CaseID, Lawyer}\}$. However, $\text{Lawyer} \to \text{Specialization}$. Because the lawyer is not a superkey (they can be on many cases), this violates BCNF. Normalizing this prevents the firm from accidentally listing a lawyer as a "Tax Specialist" on Case A and a "Criminal Specialist" on Case B.

---

## 5. Practical Application and Trade-offs

**The Normalization Paradox:** As you move from 1NF $\to$ BCNF, you increase **Data Integrity** (no anomalies) but you increase **Join Complexity**. 

To retrieve a student's instructor's office in a BCNF schema, you might need to join three tables. In a non-normalized table, it's one row. In high-read environments (like a product catalog), engineers often **denormalize**—intentionally introducing redundancy to trade write-integrity for read-speed. 

**Try this yourself:** Imagine you are building a "User Profile" page for a social media app. The page needs to show the user's name, their current city, and the name of their city's mayor. If you use a BCNF schema, you might need to join `Users` $\to$ `Cities` $\to$ `Mayors`. If the app has 100 million users, how does this join affect latency? At what point would you decide to store the `MayorName` directly in the `Users` table?

**Architectural Pattern: OLTP vs. OLAP**
This is the fundamental divide between **OLTP (Online Transaction Processing)** and **OLAP (Online Analytical Processing)**. 
- **OLTP (The Source of Truth):** Highly normalized (BCNF) to ensure that a single update to a warehouse location is reflected everywhere instantly. This minimizes the "write penalty" and ensures ACID compliance.
- **OLAP (The Data Warehouse):** Intentionally denormalized (Star/Snowflake schemas) to avoid expensive joins when aggregating millions of rows for a business report. In a data warehouse, we often duplicate data (e.g., storing the `CustomerName` directly in the `Sales` table) because the data is "frozen" (read-only), meaning update anomalies are no longer a risk.

**Rule of Thumb:** Normalize for the "Source of Truth" (OLTP); denormalize for the "Analysis/View" (OLAP).