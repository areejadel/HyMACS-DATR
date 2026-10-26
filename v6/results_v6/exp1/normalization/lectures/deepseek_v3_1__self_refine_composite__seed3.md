# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF, and identify the key property each form enforces.
2. **Understand** – Explain why partial dependencies, transitive dependencies, and non-superkey determinants cause update, insertion, and deletion anomalies.
3. **Apply** – Given a relation schema and a set of functional dependencies, determine its normal form and decompose it losslessly to the next higher form.
4. **Analyze** – Diagnose a real-world schema for normalization violations and predict the specific anomalies that will occur in a given operational context.
5. **Evaluate** – Decide when to stop at 3NF versus BCNF based on dependency preservation, performance implications, and the specific integrity requirements of a business domain.

---

## Prerequisites

You should be able to:

- Read a relation schema written as $R(A_1, A_2, \dots, A_n)$ with a primary key underlined.
- Write a basic SQL `SELECT` statement and recognize that a table is a set of tuples (rows).
- Understand that a constraint is an inviolable rule limiting the set of valid database states.

---

## Intuition First: The Problem Normalization Solves

**Opening hook — a paradox of scale.** A database is the only kind of software where adding more true facts can make the system *less* truthful. Store the same fact in two places, update one and forget the other, and your database now asserts two contradictory claims about reality — and it has no mechanism to know which one is the lie. This is not a bug in the DBMS; it is a logical consequence of the schema design. Normalization is the discipline that prevents this paradox.

Consider a company spreadsheet tracking employees and their project assignments:

| EmpID | EmpName | Dept  | DeptPhone | ProjectID | ProjName |
| :---- | :------ | :---- | :-------- | :-------- | :------- |
| 101   | Alice   | Sales | 555-0100  | P1        | WidgetX  |
| 101   | Alice   | Sales | 555-0100  | P2        | WidgetY  |
| 102   | Bob     | Sales | 555-0100  | P1        | WidgetX  |
| 103   | Carol   | HR    | 555-0200  | P3        | Onboard  |

**Pause and think:** Before reading on, identify at least two ways this design could corrupt data during routine operations. Be specific — what exact operation causes the corruption, and what falsehood does the database end up believing?

**What can go wrong during daily operations?**

- **Update Anomaly:** If the Sales department gets a new phone number, every row with `Dept = 'Sales'` must be updated. If the `UPDATE` statement’s `WHERE` clause misses one row, Sales now has two phone numbers. The database simultaneously “knows” that Sales’s phone is 555-9999 and 555-0100. Which one is true? The database cannot tell you — it has lost the ability to distinguish fact from artifact.
- **Insertion Anomaly:** A new department (e.g., “Legal”) cannot be recorded with its phone number until an employee is assigned to it. Because `EmpID` is part of the primary key and cannot be `NULL`, storing a department fact requires inventing a ghost employee. You are forced to lie about one thing (an employee exists) to tell the truth about another (a department exists).
- **Deletion Anomaly:** If Carol, the only HR employee, leaves the company and her record is deleted, the fact that the HR department’s phone number is 555-0200 is lost. A fact about the department vanishes with the employee. The database forgets HR’s phone number as a side effect of Carol’s departure — two independent real-world events become entangled in the data.

**The core insight:** Each of these anomalies arises from the same root cause — a single relation trying to represent multiple independent facts. The department’s phone number is a fact about the *department*, not about the *employee-project assignment*. When independent facts share a table, operations on one fact can corrupt or constrain the other. Normalization is the systematic process of untangling these facts so that each lives in exactly one place, governed by its own key.

**Cross-domain analogy — the library catalog.** Before computerized catalogs, a library might record book information on index cards. If each card listed the book title, the author’s name, and the author’s birth year, then updating the author’s birth year required changing every card for every book by that author. The librarian who missed one card created a catalog that contradicted itself. The solution — separate author cards and book cards, cross-referenced by author ID — is exactly a 2NF decomposition, invented by librarians decades before Codd formalized it.

---

## 1. Foundational Concepts: Keys and Functional Dependencies

### 1.1 Learning Objective

Given a relation schema and a set of business rules, you will identify candidate keys, classify attributes as prime or nonprime, and express the rules as functional dependencies.

---

### 1.2 Functional Dependencies

**Intuition.** A functional dependency (FD) is a promise the business makes to the database: “If you know $X$, you can look up exactly one $Y$.” It is not a pattern you observe in today’s data; it is a rule that must hold in every possible future state. Think of it as a mathematical function from the domain of $X$ to the domain of $Y$ — each input maps to exactly one output, forever.

**Analogy: GPS coordinates to street address.** Given a specific latitude and longitude, there is exactly one physical location. But the reverse is not true — a street address like “123 Main Street” might exist in multiple cities. The FD is directional: $X \rightarrow Y$ means $X$ is the lookup key for $Y$, not the other way around.

**Formal Definition.** Given a relation schema $R$, an FD $X \rightarrow Y$ (where $X, Y \subseteq R$) holds if, for every allowable instance $r(R)$, whenever two tuples $t_1, t_2 \in r$ agree on all attributes in $X$, they must also agree on all attributes in $Y$. We read $X \rightarrow Y$ as “$X$ functionally determines $Y$.”

**Worked Example.** In a university’s information system, the business rule “each instructor is assigned to exactly one department” becomes the FD:

$$\text{InstructorID} \rightarrow \text{DeptName}$$

Consider these two rows in our `Instructor` table:

| InstructorID | Name     | DeptName |
| :----------- | :------- | :------- |
| 4523         | Dr. Chen | Physics  |
| 4523         | Dr. Chen | Music    |

If both rows exist, the database state violates the business rule. The same `InstructorID` maps to two different `DeptName` values. The DBMS should reject this state.

**Common Misconception:** An FD is a constraint on *all possible future states* of the database. You cannot verify an FD by looking at today’s snapshot alone; you must know the business rule. The FD $\text{City} \rightarrow \text{State}$ might hold for a dataset of US addresses but would fail if the business expanded to include cities in multiple states (e.g., Portland, Oregon and Portland, Maine). Always derive FDs from business rules, not from sample data.

---

### 1.3 Superkeys and Candidate Keys

**Superkey.** A superkey is a set of attributes that uniquely identifies every tuple in a relation.

**Formal Definition.** A set of attributes $SK \subseteq R$ is a superkey of relation schema $R$ if, for any two tuples $t_1, t_2$ in any valid instance $r(R)$, whenever $t_1[SK] = t_2[SK]$, then $t_1 = t_2$.

**Worked Example.** In `Employee(EmpID, SSN, Name, Dept)`:

- $\{\text{EmpID}\}$ is a superkey: no two employees share an EmpID.
- $\{\text{SSN}\}$ is a superkey: SSN is unique per person.
- $\{\text{EmpID}, \text{Name}\}$ is a superkey, but it is *redundant* — `Name` is not needed to guarantee uniqueness.

**Candidate Key.** A candidate key is a *minimal* superkey. If you remove any attribute from it, the remaining set ceases to be a superkey.

In the example above:

- $\{\text{EmpID}\}$ is a candidate key (minimal).
- $\{\text{SSN}\}$ is a candidate key (minimal).
- $\{\text{EmpID}, \text{Name}\}$ is *not* a candidate key because dropping `Name` leaves $\{\text{EmpID}\}$, which is still a superkey.

A schema may have multiple candidate keys. We designate one as the *primary key* for physical implementation; the others are *alternate keys*.

**Why minimality matters:** A superkey with extra attributes is like carrying a passport, driver’s license, and utility bill to prove your identity when the passport alone suffices. The extra attributes do not help identify you — they only create more columns that other tables must carry as foreign keys, bloating the design.

---

### 1.4 Prime vs. Nonprime Attributes

**Definition.** An attribute is **prime** if it belongs to at least one candidate key of the relation. Otherwise, it is **nonprime**.

**Worked Example.** Consider `Enrollment(StudentID, CourseID, Grade)`. The only candidate key is $\{\text{StudentID}, \text{CourseID}\}$.

- `StudentID` is prime (it is in the key).
- `CourseID` is prime (it is in the key).
- `Grade` is nonprime (it is not in any candidate key).

This distinction is central to 3NF. “Prime” means “part of some key”; “nonprime” means “not part of any key.”

---

### 1.5 Full vs. Partial Functional Dependencies

**Intuition.** A full dependency means the entire left-hand side is required to determine the right-hand side. A partial dependency means a proper subset of the left-hand side already does the job.

**Cross-domain analogy: Two-factor identification.** To access a bank vault, you might need both a key and a biometric scan — both are required; neither alone suffices. That is a full dependency: $\{\text{Key}, \text{Biometric}\} \rightarrow \text{Access}$. But if the biometric alone already identifies you and grants access, then $\{\text{Key}, \text{Biometric}\} \rightarrow \text{Access}$ is partial — the key adds nothing. Partial dependencies in databases are like carrying a second factor that is actually redundant: they create duplication without adding security.

**Formal Definition.** An FD $X \rightarrow Y$ is **full** if removing any attribute $A$ from $X$ causes the dependency to fail — that is, no proper subset $X' \subset X$ exists such that $X' \rightarrow Y$ holds. If such an $X'$ does exist, the dependency is **partial**.

**Worked Example.** In `EMP_PROJ(EmpID, ProjID, Hours, EmpName)` with candidate key $\{\text{EmpID}, \text{ProjID}\}$:

- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ is full: you need both the employee and the project to know the hours worked on that specific project.
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{EmpName}$ is partial: the FD $\text{EmpID} \rightarrow \text{EmpName}$ already holds. `EmpName` depends on only part of the key.

Partial dependencies are the defect that 2NF eliminates. Notice the pattern: a nonprime attribute depending on a proper subset of a candidate key.

---

### Quick Check 1

Given `Order(OrderID, ProductID, CustomerID, CustomerName)` with candidate key $\{\text{OrderID}, \text{ProductID}\}$ and the FD $\text{CustomerID} \rightarrow \text{CustomerName}$:

1. Is `CustomerName` prime or nonprime?
2. Is $\{\text{OrderID}, \text{ProductID}\} \rightarrow \text{CustomerName}$ full or partial?

*(Pause and work through this before checking the answer.)*

*(Answers: `CustomerName` is nonprime — it is not in the key. The FD is partial because `CustomerName` depends on `CustomerID` alone, a proper subset of the key.)*

---

## 2. First Normal Form (1NF)

### 2.1 Learning Objective

Determine whether a schema satisfies 1NF, and if not, transform it into 1NF by eliminating multi-valued attributes and nested relations.

---

### 2.2 Intuition

1NF is the starting line of the relational model. It states: “Every attribute value in every tuple must be atomic from the database’s perspective.” No lists, no sets, no tables inside a cell. The relational model’s fundamental operations — `WHERE` clause predicates, joins, aggregate functions — all assume atomicity.

**Why this matters:** A column containing a comma-separated list like `'Alice,Bob,Carol'` is not a single value; it is a mini-database crammed into a string. To answer “Is Bob assigned to this project?”, you cannot write `WHERE Assignee = 'Bob'` — you must write `WHERE Assignee LIKE '%Bob%'`, which is slow, error-prone (it matches “Bobby”), and prevents the database from using indexes. You surrender the relational model’s query power at the exact moment you violate 1NF.

**Try this yourself:** Write a SQL query to count how many projects each person is assigned to, using the comma-separated design above. Then write the same query for the normalized design (one row per person-project pair). Compare the complexity. The normalized query is a simple `GROUP BY`; the denormalized one requires string-splitting functions, subqueries, or procedural code.

**Non-obvious framing — atomicity is relative to the query language.** “Atomic” does not mean “indivisible in reality.” A date like `2024-11-15` contains year, month, and day — but if your queries never need to filter on month alone, treating a date as atomic is perfectly valid 1NF. If you *do* need to query by month, storing it as a separate column becomes necessary. Atomicity is a contract between the schema and the operations you intend to run. The same string `'Alice,Bob'` is atomic for a logging system that only ever displays it; it is non-atomic for a project-management system that needs to query by assignee. 1NF is violated not by the data format, but by the mismatch between the format and the queries you must support.

---

### 2.3 Formal Definition

A relation schema $R$ is in 1NF if the domain of each attribute contains only *atomic* (indivisible) values, and the value of each attribute in any tuple is a single element from that domain.

---

### 2.4 Violations and Remedies

**Typical Violation.** A column stores multiple values for a single entity, such as a comma-separated list of phone numbers or a nested table of line items within an order.

**Remedy.** Decompose the multi-valued attribute into a separate relation linked by a foreign key, or expand the list into multiple rows, one per value.

**Worked Example.** Transform `Employee(EmpID, Name, PhoneNumbers)` where `PhoneNumbers` holds a set of values, into:

```sql
Employee(EmpID, Name)
EmployeePhone(EmpID, PhoneNumber)
```

Each phone number now occupies its own row in `EmployeePhone`, with `EmpID` as a foreign key referencing `Employee`. The schema is in 1NF.

**Common Misconception:** A common pitfall is to create columns like `Phone1`, `Phone2`, `Phone3`. This only hides the repeating group and does not resolve the fundamental issue, making queries that search for a specific number across all columns unnecessarily complex. True 1NF requires one value per cell, not one value per column name. The repeating-group trick also imposes an arbitrary limit — what happens when someone has four phone numbers?

---

### Quick Check 2

Consider this table design for a library system:
`Book(ISBN, Title, AuthorNames)` where `AuthorNames` stores values like `'Smith, J.|Jones, K.'`.

Is this schema in 1NF? If not, how would you fix it?

*(Pause and design your solution before reading on.)*

*(Answer: No, it is not in 1NF because `AuthorNames` contains multiple values. Fix by creating `Book(ISBN, Title)` and `BookAuthor(ISBN, AuthorName)`.)*

---

## 3. Second Normal Form (2NF)

### 3.1 Learning Objective

Given a 1NF schema, identify partial dependencies on candidate keys and decompose the schema to eliminate them, achieving 2NF.

---

### 3.2 Intuition

2NF targets the problem: “A nonprime attribute describes only a part of the key, not the whole key.” When this happens, the attribute is duplicated for every combination of the key’s other parts, leading to update anomalies.

**The tension:** Why does this duplication happen? Because the table is trying to serve two masters — it records facts about the whole key (like hours worked on a specific project by a specific employee) and facts about just part of the key (like the employee’s name, which is true regardless of which project they are on). Every time that employee appears with a new project, their name is copied. Change the name in one row and miss another, and the database now believes the same employee has two different names.

**Cross-domain analogy — the hotel registration card.** When you check into a hotel, the registration card records your name, your room number, and the nightly rate. Your name depends on you, the person. The nightly rate depends on the room. The fact that *you* are in *this room* on *this night* is a separate fact — the assignment. If the hotel stored everything on one master ledger, changing the room’s nightly rate would require updating every past and present guest entry for that room. A normalized design separates the guest table (guest ID → name), the room table (room number → rate), and the stay table (guest ID, room number, date → check-in time). This is a 2NF decomposition applied to hospitality logistics.

---

### 3.3 Formal Definition

A relation schema $R$ is in 2NF if it is in 1NF and every nonprime attribute is fully functionally dependent on every candidate key of $R$.

---

### 3.4 Detection and Decomposition

**Detection.** Find a candidate key $K$ and a nonprime attribute $A$ such that a proper subset $K' \subset K$ functionally determines $A$ ($K' \rightarrow A$).

**Decomposition.** Split $R$ using a lossless-join decomposition into:

- $R_1(K', \text{all attributes that are fully dependent on } K')$
- $R_2(K, \text{remaining attributes})$

**Worked Example.** Consider `EMP_PROJ(EmpID, ProjID, Hours, EmpName, ProjName)` with candidate key $\{\text{EmpID}, \text{ProjID}\}$ and FDs:

- $\text{EmpID} \rightarrow \text{EmpName}$
- $\text{ProjID} \rightarrow \text{ProjName}$
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$

**Step 1: Identify the candidate key.** The only candidate key is $\{\text{EmpID}, \text{ProjID}\}$.

**Step 2: Classify attributes.** `EmpID` and `ProjID` are prime. `Hours`, `EmpName`, and `ProjName` are nonprime.

**Step 3: Check each nonprime attribute for full dependency on the candidate key.**

- `Hours` depends on the full key $\{\text{EmpID}, \text{ProjID}\}$. ✓
- `EmpName` depends only on `EmpID`, a proper subset of the key. ✗ (partial dependency)
- `ProjName` depends