### Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** update, insertion, and deletion anomalies in a schema and **explain** how they compromise data integrity.
2. **Calculate** attribute closures to **determine** candidate keys and distinguish between prime and non-prime attributes.
3. **Analyze** a relation to **determine** its highest Normal Form (1NF through BCNF) by detecting specific functional dependency violations.
4. **Decompose** a non-normalized relation into a set of normalized relations that preserve data integrity and functional dependencies.
5. **Evaluate** the trade-offs between normalization and system performance to decide when to apply denormalization.

---

### 1. The Problem: Data Redundancy and Anomalies

**The Paradox of "Cheap Storage"**
In modern engineering, we are told that storage is virtually free. If disk space is cheap, why do we spend hours meticulously decomposing tables? Because the cost of storage is not the problem—the cost of **inconsistency** is. When the same fact is stored in five different places, you no longer have one piece of data; you have five candidates for the "truth." The moment one is updated and the others are not, your database is no longer a source of truth, but a source of conflict.

#### The Three Operational Anomalies
Consistency failures are categorized into three types:
*   **Update Anomaly:** A value is updated in one record but not in others, creating conflicting data.
*   **Insertion Anomaly:** A record cannot be added because a required attribute (usually a primary key) is missing, even though other valid information is available.
*   **Deletion Anomaly:** Deleting a record to remove one piece of information inadvertently destroys unrelated, necessary data.

**Worked Example: Healthcare Management**
Consider the relation $\text{PatientVisits}(\underline{\text{VisitID}}, \text{PatientID, PatientPhone, DoctorID, ClinicAddress})$.

1.  **Update Anomaly:** If a clinic moves, the $\text{ClinicAddress}$ must be updated for every visit record associated with that clinic. If any row is missed, the database contains contradictory addresses for the same clinic.
2.  **Insertion Anomaly:** If a new clinic is opened, its address cannot be stored until a patient visits, because $\text{VisitID}$ (the primary key) cannot be $\text{NULL}$.
3.  **Deletion Anomaly:** If "Patient Smith" is the only person who visited "North Clinic," deleting Smith's record removes the only instance of the "North Clinic" address from the system.

**Try This Yourself:** Imagine a table $\text{ProjectAssignment}(\underline{\text{EmployeeID, ProjectID}}, \text{ProjectDeadline, EmployeeDepartment})$. If a project's deadline changes, but you only update the row for one employee assigned to it, which anomaly have you triggered? What happens if the last employee assigned to a project leaves the company?

---

### 2. Mathematical Foundation: Functional Dependencies and Keys

To fix anomalies, we need a formal way to describe how data "belongs" together. We use Functional Dependencies (FDs) to map the internal logic of the data.

#### Functional Dependencies (FDs)
A functional dependency $X \to Y$ holds if, for any two tuples $t_1, t_2$ in a relation, whenever $t_1[X] = t_2[X]$, then $t_1[Y] = t_2[Y]$. 

**The Analogy:** Think of an FD as a **mathematical function** $f(x) = y$. In a function, for every single input $x$, there is exactly one output $y$. If you provide the "input" (the value of $X$), the database must be able to return a single, unambiguous "output" (the value of $Y$). If one $X$ could lead to two different $Y$s, the dependency is broken.

#### Attribute Closure and Key Identification
To identify the candidate keys of a relation, we use the **Attribute Closure ($X^+$)**. 

**The Analogy:** Attribute closure is like a **domino effect**. You push over the first attribute ($X$), and it knocks down every other attribute it functionally determines. Those new attributes then knock down others, and so on, until no more attributes can be added to the set.

*   **Superkey:** A set of attributes $S$ such that $S^+$ contains every attribute in the relation.
*   **Candidate Key:** A minimal superkey; no proper subset of a candidate key is itself a superkey.
*   **Prime Attribute:** An attribute that is a member of at least one candidate key.

**Worked Example: Logistics Tracking**
Consider the relation $\text{Shipment}(\text{ShipID, RouteID, VehicleID, DriverName, RouteDistance})$ with the following FDs:
1. $\text{ShipID} \to \{\text{RouteID, VehicleID}\}$
2. $\text{VehicleID} \to \text{DriverName}$
3. $\text{RouteID} \to \text{RouteDistance}$

To calculate $\{\text{ShipID}\}^+$:
1.  **Initialization:** $\{\text{ShipID}\}$
2.  **Apply FD1:** $\text{ShipID}$ determines $\text{RouteID}$ and $\text{VehicleID} \to \{\text{ShipID, RouteID, VehicleID}\}$
3.  **Apply FD2:** $\text{VehicleID}$ determines $\text{DriverName} \to \{\text{ShipID, RouteID, VehicleID, DriverName}\}$
4.  **Apply FD3:** $\text{RouteID}$ determines $\text{RouteDistance} \to \{\text{ShipID, RouteID, VehicleID, DriverName, RouteDistance}\}$

Since $\{\text{ShipID}\}^+$ contains all attributes, $\text{ShipID}$ is a candidate key.

---

### 3. The Normalization Hierarchy (1NF to BCNF)

Normalization is the process of decomposing relations to eliminate redundancy. We move through the hierarchy, each level adding a stricter constraint to ensure "one fact in one place."

#### First Normal Form (1NF): Atomicity
A relation is in 1NF if every attribute contains only atomic (indivisible) values.
*   **Violation:** A `Tags` column containing a comma-separated list such as `"Urgent, Technical, Bug"`.
*   **The Fix:** Decompose the list into a separate relation where each tag is stored in its own row.

#### Second Normal Form (2NF): Full Functional Dependency
A relation is in 2NF if it is in 1NF and no non-prime attribute is functionally dependent on a proper subset of any candidate key. 

**The Tension:** If your key is composite (e.g., $\{\text{PartID, AssemblyID}\}$), but a piece of information (e.g., $\text{PartDescription}$) only requires the $\text{PartID}$ to be identified, you have a "partial dependency." This means you are storing the part's description every single time that part appears in *any* assembly.

*   **Violation:** In $\text{PartAssembly}(\underline{\text{PartID, AssemblyID}}, \text{Quantity, PartDescription})$, the candidate key is $\{\text{PartID, AssemblyID}\}$. However, $\text{PartID} \to \text{PartDescription}$.
*   **The Fix:** Decompose into two relations:
    1. $\text{Assembly}(\underline{\text{PartID, AssemblyID}}, \text{Quantity})$
    2. $\text{Parts}(\underline{\text{PartID}}, \text{PartDescription})$

#### Third Normal Form (3NF): No Transitive Dependencies
A relation is in 3NF if it is in 2NF and no non-prime attribute is transitively dependent on a candidate key. 

**The Analogy:** Transitive dependency is like a **game of telephone**. The Key tells Attribute A, and Attribute A tells Attribute B. While the Key technically determines B, it does so *through* A. 3NF insists that attributes must depend "on the key, the whole key, and nothing but the key."

*   **Violation:** In $\text{Store}(\underline{\text{StoreID}}, \text{City, ZipCode})$, we have $\text{StoreID} \to \text{ZipCode}$ and $\text{ZipCode} \to \text{City}$. $\text{City}$ depends on the key via $\text{ZipCode}$.
*   **The Fix:** Decompose the transitive chain:
    1. $\text{Store}(\underline{\text{StoreID}}, \text{ZipCode})$
    2. $\text{Locations}(\underline{\text{ZipCode}}, \text{City})$

#### Boyce-Codd Normal Form (BCNF): The Determinant Rule
BCNF is a stricter version of 3NF that addresses cases where a non-key determines a prime attribute. 
**The Rule:** Every determinant must be a superkey. If something is acting as a "boss" (determining other values), it must be the unique identifier for the whole table.

*   **Violation:** In $\text{ConsultantProject}(\underline{\text{Client, Project}}, \text{Consultant})$, we have $\{\text{Client, Project}\} \to \text{Consultant}$ and $\text{Consultant} \to \text{Project}$.
    *   Candidate Keys: $\{\text{Client, Project}\}$ and $\{\text{Client, Consultant}\}$.
    *   The FD $\text{Consultant} \to \text{Project}$ violates BCNF because $\text{Consultant}$ is not a superkey.
*   **The Fix:**
    1. $\text{ConsultantSpecialty}(\underline{\text{Consultant}}, \text{Project})$
    2. $\text{ClientAssignment}(\underline{\text{Client, Consultant}})$

---

### 4. Advanced Normalization: 4NF and 5NF

#### Fourth Normal Form (4NF): Multi-valued Dependencies (MVDs)
A relation is in 4NF if it is in BCNF and contains no non-trivial multi-valued dependencies. 

**The Analogy:** 4NF prevents **"The Cartesian Product Trap."** An MVD occurs when you try to store two independent one-to-many relationships in one table. If a Professor has multiple Courses AND multiple Research Projects, and those two things have nothing to do with each other, forcing them into one table creates a combinatorial explosion of rows.

*   **Violation:** $\text{Professor}(\underline{\text{ProfID, Course, Project}})$. If Prof. Jones teaches {CS101, CS102} and manages {AI, Robotics}, you need 4 rows to represent these independent facts.
*   **The Fix:** $\text{ProfCourses}(\underline{\text{ProfID, Course}})$ and $\text{ProfProjects}(\underline{\text{ProfID, Project}})$.

#### Fifth Normal Form (5NF): Join Dependency
5NF deals with ternary (3-way) relationships that cannot be reduced to binary relationships without losing semantic meaning. It ensures that if you decompose a table into three smaller tables, joining them back together doesn't create "phantom" data (spurious tuples) that wasn't there originally.

---

### 5. Limitations, Pitfalls, and Trade-offs

#### The Normalization Paradox
Normalization is a trade-off between **Write Integrity** and **Read Latency**.

1.  **Join Overhead:** Every time you decompose a table to reach BCNF, you add a `JOIN` operation to your read queries. In a high-traffic system, 10 joins can turn a millisecond query into a second-long bottleneck.
2.  **Dependency Loss:** Decomposing to BCNF can occasionally destroy functional dependencies, meaning some business rules can no longer be enforced by the database schema and must be handled by application code.

#### Strategic Denormalization: The Data Science Connection
In the world of Big Data and Machine Learning, we often intentionally violate these rules.
*   **OLAP (Analytical) Systems:** Use "Star Schemas" (denormalized) because they prioritize scan speed over update integrity.
*   **NoSQL Document Stores:** In MongoDB, we embed addresses inside user documents. This violates 2NF, but it transforms a complex join into a single disk seek ($\mathcal{O}(1)$), which is critical for web-scale performance.

#### Summary Reference Table
| Normal Form | Requirement | Primary Violation | Intuition |
| :--- | :--- | :--- | :--- |
| **1NF** | Atomic values | Multi-valued attributes | "No lists in cells" |
| **2NF** | 1NF + No partial deps | Non-prime depends on part of key | "Whole key or nothing" |
| **3NF** | 2NF + No transitive deps | Non-prime depends on non-prime | "No middle-men" |
| **BCNF**| Every determinant is superkey | Prime depends on non-superkey | "Determinants must be keys" |
| **4NF** | BCNF + No MVDs | Independent multi-valued facts | "Separate unrelated lists" |
| **5NF** | No Join Dependencies | Redundant ternary relationships | "Perfect reconstruction" |