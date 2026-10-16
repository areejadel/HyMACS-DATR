# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** – State the definition of each normal form (1NF, 2NF, 3NF, BCNF) and identify the defect each one eliminates.
2.  **Understand** – Explain, using concrete examples from multiple domains, why partial dependencies, transitive dependencies, and non-superkey determinants cause update, insertion, and deletion anomalies.
3.  **Apply** – Given a relation schema and a set of functional dependencies, determine the highest normal form it satisfies and, if it falls short, decompose it losslessly into the next higher form.
4.  **Analyze** – Diagnose a real-world schema for normalization violations and predict the exact anomalies that will arise during routine operations.
5.  **Evaluate** – Decide when to stop at 3NF versus BCNF by weighing dependency preservation and performance trade-offs, and articulate when controlled denormalization is justified.

---

## Prerequisites

We assume you can:

- Read a relation schema written as `R(A_1, A_2, \dots, A_n)` with a primary key underlined.
- Write a basic SQL `SELECT` statement and recognize that a table is a set of tuples (rows).
- Understand the idea of a constraint: a rule that limits what data is valid.

We use "tuple" and "row" interchangeably throughout this lecture.

---

## 0. Intuition First: The Problem Normalization Solves

Here is a puzzle to start with. You are given a database and told it contains exactly one true fact: "The Sales department is on floor 4." You run a query to retrieve this fact, and the database returns two different answers: floor 4 and floor 7. The database now asserts a logical contradiction — Sales is simultaneously on two floors. How is this possible? The database did not malfunction. The schema itself made contradiction inevitable the moment anyone tried to update a single fact.

This is the problem normalization solves. It is not about tidy design or academic aesthetics. It is about preventing your database from becoming a machine that manufactures false statements.

Imagine you are running a small company. You open a single spreadsheet and start dumping in everything: employees, their departments, the department phone numbers, the projects they are on, the project names. It feels efficient—one place for everything. No joins, no complexity.

Six months later, the Sales department moves to a new floor and gets a new phone number. You search for "Sales" in the department column, find 47 rows, and start updating. You miss row 31. Now your database claims Sales has two different phone numbers. Which one is correct? The database no longer knows. You have just discovered that your "efficient" single-table design is a machine for manufacturing contradictions.

This is not a hypothetical edge case. It is the inevitable fate of any schema that entangles facts about different things in the same table. The root cause is structural, not procedural—no amount of careful data entry can fix a design that forces the same fact to be stored in multiple places.

Consider that company spreadsheet:

| EmpID | EmpName | Dept  | DeptPhone | ProjectID | ProjName |
| :---- | :------ | :---- | :-------- | :-------- | :------- |
| 101   | Alice   | Sales | 555-0100  | P1        | WidgetX  |
| 101   | Alice   | Sales | 555-0100  | P2        | WidgetY  |
| 102   | Bob     | Sales | 555-0100  | P1        | WidgetX  |
| 103   | Carol   | HR    | 555-0200  | P3        | Onboard  |

**Pause and think:** Scan the table above. What problems would arise if you had to maintain this data over months? Identify at least two issues before reading further.

Three types of anomalies afflict this design:

- **Update anomaly:** If the Sales department's phone number changes, you must update three rows. Miss one row, and Sales now has two phone numbers. The database contradicts itself. The same fact—a department's phone number—is stored multiple times, and each copy can diverge.
- **Insertion anomaly:** You cannot record a new department (e.g., "Legal") with its phone number until an employee is assigned to it. The `EmpID` component of the key forces you to invent an employee first. The database refuses to store a true fact about the world because it is entangled with an unrelated fact. This is like a library that will not let you catalog a new book until someone checks it out.
- **Deletion anomaly:** If you remove Carol (the only HR employee), you lose the fact that HR's phone number is 555-0200. Deleting an employee should not erase knowledge about a department, but here it does. The database accidentally forgets something true about the organization.

**The core insight:** This single table stores facts about three distinct entities—employees, departments, and projects. When facts about different entities are mixed together, anomalies arise. Normalization is the systematic untangling of these concerns.

Here is a cross-domain analogy: think of normalization as the database equivalent of refactoring a monolithic codebase into modules with single responsibilities. A function that calculates payroll, sends emails, and updates the UI is a nightmare to maintain—change the email format, and you risk breaking payroll. Similarly, a table that stores employees, departments, and projects is a nightmare to update—change a department phone number, and you risk corrupting project assignments. In both cases, the fix is the same: separate concerns so that each module (or table) has exactly one reason to change.

But here is a deeper analogy that standard treatments miss: normalization is the database analogue of eliminating redundancy in a geometric coordinate system. In a Cartesian plane, storing a point as $(x, y, r, \theta)$ is redundant because $r$ and $\theta$ are derivable from $x$ and $y$. If you update $x$ without recalculating $r$, your coordinate representation becomes internally inconsistent — it now describes two different points depending on which pair you trust. A normalized schema is like storing only $(x, y)$ and computing polar coordinates on demand. The database equivalent of "computing on demand" is a join.

**Application across domains:** This pattern is universal. Consider a hospital database storing `PatientVisit(PatientID, VisitDate, DoctorID, DoctorPhone, WardID, WardName)`. The same anomalies appear: updating a doctor's phone number requires changing every visit row for that doctor; a new ward cannot be recorded until a patient is admitted to it; deleting the last visit for a patient in Ward 3 silently erases the fact that Ward 3 exists. In e-commerce, an `Order(OrderID, ProductID, CustomerID, CustomerEmail, ProductPrice)` schema suffers identically. In a university's `CourseRegistration(StudentID, CourseID, ProfID, ProfOffice, RoomNumber, RoomCapacity)`, changing a professor's office requires updating every registration row for that professor. The underlying disease is invariant across domains: one relation encodes multiple independent facts.

> **Quick Check:** What is the fundamental cause of all three anomalies shown above?
> *Answer:* The table mixes facts about employees, departments, and projects. Each anomaly arises because a fact about one entity (e.g., a department's phone number) is stored redundantly alongside facts about another entity (e.g., an employee's project assignment). The structure forces duplication, and duplication creates inconsistency.

---

## 1. Foundational Concepts: Keys and Functional Dependencies

Before we can apply the normal forms, we need precise tools to describe the relationships among attributes. These tools are functional dependencies and keys. Think of them as the diagnostic instruments a doctor uses before prescribing treatment—you cannot fix what you cannot describe.

### 1.1 Functional Dependencies: The Detective's Tool

**Intuition.** A functional dependency (FD) is a statement of a deterministic relationship in the real world that the database must respect. It says: "If I know $X$, then I know exactly one $Y$—not just today, but always."

Here is an analogy from physics: an FD is like a state function in thermodynamics. The internal energy of a system depends only on its current state (temperature, pressure, volume)—not on how it got there. Given the state, the energy is determined. Similarly, given an employee ID, the employee's name is determined—regardless of what projects they are on or when they were hired. The relationship is invariant across all valid states of the database.

**Try this yourself:** Before reading the formal definition, try to express the following business rules as FDs. Write them as $X \to Y$:
1. Each course has exactly one instructor.
2. Each student has exactly one advisor.
3. Each order belongs to exactly one customer.

*Answers:* (1) $\text{CourseID} \to \text{InstructorID}$, (2) $\text{StudentID} \to \text{AdvisorID}$, (3) $\text{OrderID} \to \text{CustomerID}$. Notice the pattern: the left-hand side is the identifier of the thing you know, and the right-hand side is the single value that must follow.

**Formal Definition.** Given a relation schema $R$, an FD $X \to Y$ (read as "$X$ functionally determines $Y$") holds if, for every allowable instance $r(R)$, whenever two tuples agree on all attributes in $X$, they must also agree on all attributes in $Y$. Both $X$ and $Y$ are sets of attributes from $R$. The set $X$ is the *determinant*; $Y$ is the *dependent*.

**Worked Example.** In a university database, the rule "each instructor belongs to exactly one department" becomes:

$$\text{Instructor} \to \text{Department}$$

If two rows show $\text{Instructor} = \text{'Dr. Chen'}$, they must both show the same $\text{Department}$ value; otherwise, the business rule is violated.

**Cross-domain illustration.** An FD is not merely a relational database concept. In a hospital information system: $\text{PatientID} \to \text{DateOfBirth}$. In a logistics schema: $\text{ShipmentID} \to \text{OriginWarehouse}$. In a financial ledger: $\text{AccountNumber} \to \text{AccountType}$. In a music streaming platform: $\text{AlbumID} \to \text{ReleaseYear}$. The formalism is identical; only the domain vocabulary changes.

Here is a non-obvious framing worth internalizing: an FD is a promise the database makes to itself. When you declare $\text{EmpID} \to \text{Dept}$, you are instructing the DBMS: "If you ever see two rows with the same EmpID but different Dept values, sound the alarm — something has gone wrong." Normalization is the art of designing schemas where the DBMS can enforce all the important promises using only key constraints, without needing to check arbitrary FDs across the entire table on every update.

**Important:** An FD is a constraint on *all possible future states* of the database, not just the current snapshot. You cannot verify an FD by looking at today's data alone; you must know the business rule. A table might happen to have unique names today, but unless the business guarantees uniqueness forever, $\text{Name} \to \text{EmpID}$ is not a valid FD. Two designers looking at the same data can arrive at different FDs because they know different things about the business rules. Normalization requires domain knowledge.

> **Misconception Alert:** Students often think "if the data looks unique now, the FD holds." This is incorrect. FDs derive from business rules, not data snapshots. Always ask: "Does the business guarantee this relationship for all time?"

> **Test Yourself:** Consider a table $\text{Student}(\text{StudentID}, \text{Name}, \text{Email})$. Today, every student has a unique email. Is $\text{Email} \to \text{StudentID}$ a valid FD?
> *Answer:* Only if the university guarantees that email addresses will never be reused and that no two students will ever share an email. If the policy allows email reuse after graduation, the FD does not hold. You must ask the domain expert.

---

### 1.2 Superkeys and Candidate Keys

**Superkey (Intuition).** A set of attributes that, taken together, uniquely identifies every row. No two rows can share the same combination of values for a superkey.

**Formal Definition.** A set of attributes $\text{SK} \subseteq R$ is a superkey of relation schema $R$ if, for any two tuples $t_1, t_2$ in any valid instance $r(R)$, whenever $t_1[\text{SK}] = t_2[\text{SK}]$, then $t_1 = t_2$. Equivalently, $\text{SK}$ is a superkey if $\text{SK} \to R$ holds—that is, $\text{SK}$ functionally determines every attribute in the schema.

**Worked Example.** Consider $\text{Employee}(\text{EmpID}, \text{SSN}, \text{Name}, \text{Dept})$:
- $\{\text{EmpID}\}$ is a superkey: no two employees share the same EmpID.
- $\{\text{SSN}\}$ is a superkey: SSN is unique per person.
- $\{\text{EmpID}, \text{Name}\}$ is a superkey, but it is *redundant*—we do not need $\text{Name}$ to guarantee uniqueness. Adding attributes to a superkey always yields another superkey.

**Candidate Key.** A candidate key is a *minimal* superkey. Removing any attribute from it causes it to cease being a superkey. In the example above, $\{\text{EmpID}\}$ and $\{\text{SSN}\}$ are candidate keys, while $\{\text{EmpID}, \text{Name}\}$ is not. A schema may have multiple candidate keys. We designate one as the *primary key* for physical implementation; the others are *alternate keys*.

**Worked Example with Multiple Candidate Keys.** Consider a library schema $\text{Book}(\text{ISBN}, \text{LibraryCode}, \text{Title}, \text{AuthorID})$. Both $\{\text{ISBN}\}$ and $\{\text{LibraryCode}\}$ uniquely identify a book. Each is a candidate key. We might choose $\{\text{ISBN}\}$ as the primary key, making $\{\text{LibraryCode}\}$ an alternate key. Both ISBN and LibraryCode are prime attributes because each belongs to some candidate key.

**Try this yourself:** Consider a schema $\text{Citizen}(\text{NationalID}, \text{PassportNumber}, \text{Name}, \text{BirthDate})$. Assume both NationalID and PassportNumber are unique per person. List all superkeys and identify the candidate keys.

*Answer:* Candidate keys are $\{\text{NationalID}\}$ and $\{\text{PassportNumber}\}$. Superkeys include these two, plus any superset: $\{\text{NationalID}, \text{Name}\}$, $\{\text{PassportNumber}, \text{BirthDate}\}$, $\{\text{NationalID}, \text{PassportNumber}\}$, and all four attributes together. The candidate keys are the minimal ones.

> **Test Yourself:** Consider $\text{Book}(\text{ISBN}, \text{Title}, \text{Edition}, \text{PublisherID})$. What are the candidate keys? Assume ISBN is unique per edition.
> *Answer:* $\{\text{ISBN}\}$ is a candidate key. $\{\text{Title}, \text{Edition}\}$ might be a candidate key if no two books share the same title and edition—but this depends on the business rule, illustrating why you cannot infer keys from data alone.

---

### 1.3 Prime vs. Nonprime Attributes

**Definition.** An attribute is **prime** if it belongs to at least one candidate key. Otherwise it is **nonprime**. This distinction is central to 2NF and 3NF.

**Worked Example.** Consider $\text{Enrollment}(\text{StudentID}, \text{CourseID}, \text{Grade})$ with candidate key $\{\text{StudentID}, \text{CourseID}\}$:
- $\text{StudentID}$ is prime (it is in the key).
- $\text{CourseID}$ is prime (it is in the key).
- $\text{Grade}$ is nonprime (it is not in any candidate key).

**Worked Example with Multiple Keys.** In $\text{Employee}(\text{EmpID}, \text{SSN}, \text{Name})$, both $\{\text{EmpID}\}$ and $\{\text{SSN}\}$ are candidate keys. Therefore:
- $\text{EmpID}$ is prime (it belongs to the candidate key $\{\text{EmpID}\}$).
- $\text{SSN}$ is prime (it belongs to the candidate key $\{\text{SSN}\}$).
- $\text{Name}$ is nonprime (it belongs to no candidate key).

> **Quick Check:** In a schema $\text{Vehicle}(\text{VIN}, \text{LicensePlate}, \text{Make}, \text{Model})$ where both $\{\text{VIN}\}$ and $\{\text{LicensePlate}\}$ are candidate keys, which attributes are prime?
> *Answer:* Both $\text{VIN}$ and $\text{LicensePlate}$ are prime, since each is a candidate key. $\text{Make}$ and $\text{Model}$ are nonprime. An attribute can be prime even if it is not the primary key—it just needs to belong to *some* candidate key.

---

### 1.4 Full vs. Partial Functional Dependencies

**Intuition.** A full dependency means the entire left-hand side is needed to determine the right-hand side. A partial dependency means a proper subset of the left-hand side already determines the right-hand side—some of the left-hand side is dead weight.

Think of it like a combination lock: you need all the numbers in the correct sequence to open it. If the lock opened with just the first two numbers, the third would be dead weight. A partial dependency is exactly that—an attribute on the left-hand side that contributes nothing to determining the right-hand side.

Here is an even sharper analogy: partial dependency is like a function signature that takes more arguments than it actually uses. If you write `def get_employee_name(emp_id, project_id)` but the function body only ever reads `emp_id`, then `project_id` is dead weight in the parameter list. That is exactly what happens in a table where the key is `{EmpID, ProjectID}` but `EmpName` depends only on `EmpID`. The `ProjectID` is a parameter the dependency does not actually need.

**Formal Definition.** An FD $X \to Y$ is **full** if removing any attribute $A$ from $X$ causes the dependency to fail. That is, for every proper subset $X' \subset X$, the FD $X' \to Y$ does *not* hold. If such an $X'$ does exist for which $X' \to Y$ holds, the dependency is **partial**.

**Worked Example 1 — Employee Projects.** In $\text{EMP\_PROJ}(\text{EmpID}, \text{ProjID}, \text{Hours}, \text{EmpName})$ with candidate key $\{\text{EmpID}, \text{ProjID}\}$:
- $\{\text{EmpID}, \text{ProjID}\} \to \text{Hours}$ is full: you need both the employee and the project to know the hours worked. Hours is a fact about the *assignment*—the combination of employee and project.
- $\{\text{EmpID}, \text{ProjID}\} \to \text{EmpName}$ is partial: $\text{EmpID} \to \text{EmpName}$ already holds. $\text{EmpName}$ depends on only part of the key. The $\text{ProjID}$ is irrelevant for determining the name.

**Worked Example 2 — Hospital Prescriptions.** Consider a hospital schema $\text{Prescription}(\text{PatientID}, \text{DrugID}, \text{Dosage}, \text{PatientName})$ with candidate key $\{\text{PatientID}, \text{DrugID}\}$. We know $\text{PatientID} \to \text{PatientName}$:
- $\{\text{PatientID}, \text{DrugID}\} \to \text{Dosage}$ is full: you need both patient and drug to know the prescribed dosage. A patient might take 10mg of Drug A and 20mg of Drug B.
- $\{\text{PatientID}, \text{DrugID}\} \to \text{PatientName}$ is partial: $\text{