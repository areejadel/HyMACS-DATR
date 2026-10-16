# Normalization Forms and Database Schema Design (1NF–BCNF)

By the end of this lecture, you will be able to:

1. **Define** functional dependencies, candidate keys, prime and non-prime attributes, and use them to **identify** normal form violations in a given schema.
2. **Explain** the purpose and requirements of 1NF, 2NF, 3NF, and BCNF using intuitive examples and formal definitions.
3. **Apply** decomposition techniques to transform a schema from lower to higher normal forms, ensuring lossless joins.
4. **Analyze** a database schema for redundancy and anomalies, and **justify** whether 3NF or BCNF is more appropriate given dependency preservation constraints.
5. **Evaluate** trade-offs in normalization, particularly between eliminating redundancy and preserving functional dependencies.

---

## Prerequisites: Functional Dependencies and Keys

Imagine you're debugging a production database and discover that after an update, two users suddenly share the same phone number — one of whom never entered it. How could this happen?

The culprit: **uncontrolled functional dependencies** hiding in poorly structured data.

In relational databases, a **functional dependency (FD)** $X \rightarrow Y$ means that the value of attribute set $X$ uniquely determines the value of attribute set $Y$. For example, if $StudentID \rightarrow Email$, then each student ID corresponds to exactly one email address — like a deterministic function in code.

A **superkey** is a set of attributes that uniquely identifies every tuple in a relation. A **candidate key** is a minimal superkey: no proper subset of its attributes is also a superkey. An attribute is **prime** if it is part of *any* candidate key; otherwise, it is **non-prime**.

> **Why minimality matters**: Think of a candidate key as the smallest possible "address" for a row. Just as your home address doesn't need both your street name and GPS coordinates, a key shouldn't carry redundant identifying information.

> **Critical insight**: Normal forms are defined by how non-prime attributes depend on keys. Misidentifying keys or functional dependencies leads to incorrect normalization analysis — like misdiagnosing a disease because you misread the symptoms.

### Try This Yourself: Quick Check 1

Given relation $R(A,B,C)$ with functional dependencies $A \rightarrow B$, $B \rightarrow C$, $A \rightarrow C$, and assuming $A$ is a candidate key:

- Is $B$ a prime attribute?  
- Does $B \rightarrow C$ represent a partial or transitive dependency?

Pause here. Write down your answers before reading on.

**Answer**:  
- No, $B$ is not prime because it is not part of the candidate key $A$.  
- The dependency $B \rightarrow C$ is a **transitive dependency**: $A \rightarrow B$, $B \rightarrow C$, and $C$ is non-prime, but $B$ is not a superkey.

> **Common Misconception Alert**: “An attribute involved in a functional dependency must be part of a key.”  
False. Participation in an FD does not imply primeness. Only membership in a candidate key defines a prime attribute. Just because $B \rightarrow C$ doesn't mean $B$ gets promoted to key status — authority must be earned, not assumed.

---

## Motivating Example: The Domino Effect of Poor Design

Consider a bookstore database with a single table:

```
Orders(OrderID, CustomerName, CustomerPhone, Product, Price, SalesRep, Region)
```

Sample data:

| OrderID | CustomerName | CustomerPhone | Product   | Price | SalesRep | Region  |
|---------|--------------|---------------|-----------|-------|----------|---------|
| 101     | Alice        | 555-1234      | Book A    | $20  | John     | North   |
| 102     | Bob          | 555-5678      | Book B    | $25  | John     | North   |
| 103     | Alice        | 555-1234      | Book C    | $18  | Mary     | South   |

Now imagine the business grows. John gets promoted and moves from North to Central region. You run:

```sql
UPDATE Orders SET Region = 'Central' WHERE SalesRep = 'John';
```

But what if John had 10,000 orders? What if the query times out? What if someone forgets to run it?

This isn’t just inefficiency — it’s **data fragility**. One logical fact (John works in Central) is scattered across thousands of rows. Change one, and you must change them all — or risk inconsistency.

And if Mary leaves and her last order is deleted? Poof — the fact that South has a sales rep vanishes.

This schema treats the database like a spreadsheet, not a **knowledge graph**. Normalization is the process of turning accidental structure into intentional design — replacing dominoes with independent supports.

But here’s a twist: suppose we *want* redundancy for performance. Is normalization always the answer?

Hold that thought. We’ll return to it — but first, let’s walk through the normal forms, each fixing a specific structural flaw.

---

## 1. First Normal Form (1NF): The Atomicity Foundation

### The Problem: Hidden Multiplicity

Suppose we allow this:

```
StudentCourses(StudentID, Name, Courses)
```

With a row:  
`(S01, "Alice", {CS101, MATH202})`

Here, `Courses` contains multiple values — a single cell holds a set. This seems convenient, but ask: *Can you query “Which students are taking CS101?” without parsing a list?*

In classical SQL, no. You’d need string operations or JSON traversal — slow, error-prone, and not relationally sound.

### Analogy: The Spreadsheet vs. The Ledger

Think of a non-1NF table like a handwritten ledger where one line says:  
"March 5: bought apples, bread, milk."

To analyze individual items, you must split the entry manually — every time. In contrast, a proper ledger lists each item on its own line. That’s 1NF: **one fact per cell**.

Now imagine you’re building a search engine for receipts. Would you index "bread" from a blob of text? Or would you prefer a clean column where every row is a single purchase?

Normalization is not about purity — it’s about **enabling computation**.

### Formal Definition

A relation is in **First Normal Form (1NF)** if:
- Every attribute is single-valued.
- All values in a column are drawn from the same domain.
- The order of rows and columns is irrelevant.

### Fix: Unpack Repeating Groups

Replace:

```
StudentCourses(StudentID, Name, Courses)
```

With:

```
Student(StudentID, Name)
Enrollment(StudentID, CourseCode)
```

Now each course is a separate fact. Querying, indexing, and constraining become possible.

> **Why This Matters**: 1NF isn’t about data types — it’s about **queryable structure**. Even if PostgreSQL lets you store arrays, doing so hides the relational model’s power. Normalization forces you to model relationships explicitly.

> **Myth Busting**: “Modern databases make 1NF obsolete.”  
No — they expand options, but not wisdom. Using JSON or arrays to avoid decomposition is like using duct tape to fix a cracked foundation. The building stands, but the stress remains.

### Practical Relevance: Real-World Case — E-commerce Product Attributes

Consider an online fashion retailer storing product features in a single column:

```
Products(ProductID, Name, Attributes)
```

With `Attributes` containing: `"{'color': 'blue', 'size': 'M', 'material': 'cotton'}"`

Initially, this seems flexible — but queries like “Find all blue shirts” require JSON parsing or LIKE operations, which cannot use standard B-tree indexes efficiently. Performance degrades as data grows.

In 2018, **Zalando**, Europe’s largest online fashion platform, reported [publicly](https://engineering.zalando.com/posts/2018/09/scaling-product-data.html) that denormalized storage of product attributes led to inconsistent filtering and slow search performance. Their solution? Decompose into atomic attributes or use a normalized `ProductAttribute(ProductID, AttributeName, Value)` table — effectively enforcing 1NF.

This change enabled efficient indexing, consistent validation, and scalable faceted search — a direct business impact from respecting atomicity.

### Try This Yourself: Quick Check 2

Given:

```
Employees(EmpID, Name, Skills)
```

With a row: `(E01, "Sam", ["Python", "SQL"])`

- If `Skills` is stored as an array, is the table in 1NF?
- How would you fix it to support queries like “Find all employees with Python skills”?

Now, before checking the answer, sketch a SQL query that would find all employees with Python skills *under the current design*. What operators would you need? How would performance scale?

**Answer**:  
- No — multiple values per cell violate 1NF.  
- Fix: Create `EmployeeSkills(EmpID, Skill)` with one row per skill. Now you can index, constrain, and join cleanly.

---

## 2. Second Normal Form (2NF): The Perils of Partial Knowledge

### The Problem: Half a Key, Full of Trouble

Consider:

```
Registration(StudentID, CourseID, CourseName)
```

Assume:
- Candidate key: $\{StudentID, CourseID\}$ (a student can enroll in multiple courses)
- Functional dependency: $CourseID \rightarrow CourseName$

Here, `CourseName` depends only on `CourseID` — half the key. This is a **partial dependency**.

### Analogy: The Incomplete Receipt

Imagine a receipt where the item name is written only once, but the price appears next to each quantity. If the item name depends only on the product code, why repeat it with every transaction? You wouldn’t print “iPhone” on every line of a sales log — you’d reference it once.

Similarly, `CourseName` belongs to the course, not the enrollment. Storing it in `Registration` ties it to a composite key it doesn’t need.

But here’s a deeper question: what if we *don’t* extract `CourseName`? What happens when a course is renamed?

Let’s simulate it.

### Consequences

- **Redundancy**: `CourseName` repeats for every student in the course.
- **Insertion anomaly**: Can’t add a new course until someone enrolls.
- **Update anomaly**: Renaming a course requires updating many rows.

Now, imagine you're responsible for this update. The system is live. Thousands of rows. The transaction locks the table.

What could go wrong?

A timeout? A partial update? A replication lag?

This isn’t theoretical — it’s operational risk.

### Fix: Promote the Determinant

Split into:

```
Enrollment(StudentID, CourseID)
Course(CourseID, CourseName)
```

Now `CourseName` depends fully on its own key, `CourseID`.

### Formal Definition

A relation is in **Second Normal Form (2NF)** if:
- It is in 1NF.
- Every non-prime attribute is **fully functionally dependent** on every candidate key.

> **Key Insight**: 2NF only matters when the candidate key is composite. If all keys are single-attribute, 1NF implies 2NF. It’s not about eliminating composite keys — it’s about ensuring that non-key data waits for the *whole* key, not just part of it.

> **Myth Busting**: “2NF requires a single-attribute primary key.”  
False. Composite keys are perfectly fine — as long as non-prime attributes don’t depend on a subset.

### Practical Relevance: Real-World Case — Inventory Management at Walmart

Walmart’s inventory tracking system historically used composite keys in item-location tables. A simplified version:

```
Inventory(ItemID, StoreID, ItemName, Quantity)
```

With FD: $ItemID \rightarrow ItemName$, key: $\{ItemID, StoreID\}$

This design caused massive redundancy: `ItemName` repeated across thousands of stores. When rebranding a product (e.g., “Coke” → “Coca-Cola Zero Sugar”), updates had to propagate across all stores — a slow, error-prone batch process.

By decomposing into:

```
Inventory(ItemID, StoreID, Quantity)
Item(ItemID, ItemName)
```

Walmart reduced update load, improved consistency, and enabled real-time synchronization across supply chain systems. This 2NF normalization became foundational in their distributed inventory architecture [as noted in Walmart Labs engineering blogs].

The lesson: even global enterprises suffer from partial dependencies — and fix them the same way we do in textbooks.

### Try This Yourself: Quick Check 3

Given:

```
OrderItems(OrderID, ProductID, ProductName, Quantity)
```

With:
- Candidate key: $\{OrderID, ProductID\}$
- Functional dependency: $ProductID \rightarrow ProductName$

- Is this in 2NF?
- If not, how do you fix it?

Now, go one step further: write the SQL `UPDATE` statement that renames a product under the current design. Then, write the same operation after decomposition. Compare complexity, risk, and performance.

**Answer**:  
- No — partial dependency on `ProductID`.  
- Fix:  
  ```
  OrderItems(OrderID, ProductID, Quantity)
  Products(ProductID, ProductName)
  ```

---

## 3. Third Normal Form (3NF): Cutting the Middleman

### The Problem: Indirect Control

Consider:

```
Employee(EmpID, Dept, Manager)
```

With:
- $EmpID \rightarrow Dept$
- $Dept \rightarrow Manager$

Then $EmpID \rightarrow Manager$ by transitivity.

But here’s the catch: **you can’t change the manager without changing the department**. The manager is indirectly tied to the employee through an intermediate attribute.

### Analogy: The Corporate Reporting Chain

In a company, if Alice reports to Bob, and Bob reports to Carol, then Alice indirectly reports to Carol. But if Bob leaves, Alice’s reporting line breaks — unless you explicitly reassign her.

Similarly, if `Dept → Manager`, then every employee in that department carries an implicit dependency on the manager. Change the manager? Update every employee. Delete the last employee? Lose the manager assignment.

This is **transitive dependency**: a non-prime attribute (`Manager`) depends on another non-prime attribute (`Dept`), not directly on the key.

Now, imagine a reorganization: the company eliminates middle management. You need to assign managers directly to employees.

How would the schema need to change?

### Fix: Promote the Source

Decompose into:

```
Employee(EmpID, Dept)
Department(Dept, Manager)
```

Now `Manager` depends directly on `Dept`, and `Dept` on `EmpID`. No middleman.

### Formal Definition

A relation is in **Third Normal Form (3NF)** if:
- It is in 2NF.
- No non-prime attribute is transitively dependent on any candidate key.
- Equivalently: For every non-trivial FD $X \rightarrow Y$, either:
  - $X$ is a superkey, or
  - $Y$ is a prime attribute.

> **Why This Works**: 3NF ensures that all non-key facts are either **key-determined** or **key-participating**. It stops chains of dependency before they create redundancy.

> **Non-Obvious Insight**: 3NF allows some redundancy — but only when necessary to preserve functional dependencies. It’s a **pragmatic compromise** between purity and usability.

### Practical Relevance: Real-World Case — Hospital Patient Records

A hospital database once stored:

```
Patient(PatientID, DoctorName, DoctorDept, Diagnosis)
```

With:
- $DoctorName \rightarrow DoctorDept$
- $PatientID \rightarrow DoctorName$

Thus, $PatientID \rightarrow DoctorDept$ via transitivity.

When a doctor changed departments, all their patients’ records had to be updated — a dangerous operation in a clinical setting. Worse, if no patients were registered under a doctor, their department was unknown (insertion anomaly).

After normalization:

```
Patient(PatientID, DoctorName, Diagnosis)
Doctor(DoctorName, DoctorDept)
```

The hospital eliminated update anomalies and ensured accurate reporting for staffing and billing. This 3NF redesign was part of a HIPAA compliance audit in a U.S. healthcare provider (reported in *Journal of Healthcare Information Management*, 2020), where data integrity directly affected regulatory outcomes.

Normalization wasn’t just academic — it prevented medical administrative errors.

### Try This Yourself: Quick Check 4

Given:

```
Student(StudentID, Advisor, AdvisorOffice)
```

With:
- $StudentID \rightarrow Advisor$
- $Advisor \rightarrow AdvisorOffice$

- Is this in 3NF?
- If not, how would you decompose it?

Now, simulate an update: the advisor moves offices. Write the `UPDATE` statement under the current schema. How many rows might be affected? What if the transaction fails halfway?

Then sketch the normalized version. Can you still express “Find all students whose advisor is in Room 305”?

**Answer**:  
- No — transitive dependency $StudentID \rightarrow AdvisorOffice$ via `Advisor`.  
- Fix:  
  ```
  Student(StudentID, Advisor)
  AdvisorInfo(Advisor, AdvisorOffice)
  ```

---

## 4. Boyce-Codd Normal Form (BCNF): The Gold Standard

### The Problem: Keys Calling the Shots

Consider:

```
Enrollment(StudentID, CourseID, Instructor)
```

With:
- Each course has one instructor: $CourseID \rightarrow Instructor$
- No student takes two sections of the same course: $\{StudentID, CourseID\}$ is candidate key.

But now suppose $Instructor \rightarrow CourseID$ — each instructor teaches only one course.

We have two FDs:
- $CourseID \rightarrow Instructor$
- $Instructor \rightarrow CourseID$

So both are candidate keys? Wait — then $\{StudentID, Instructor\}$ is also a key.

But here’s the catch: **what if an instructor teaches two courses?** The FD breaks. But if the FD holds, we’re okay — but only if we know all keys.

Now, imagine a new business rule: a course can have co-instructors. The FD $CourseID \rightarrow Instructor$ no longer holds — but the schema assumes it does.

The database starts storing conflicting data: two rows with the same `CourseID` but different `Instructor` values. Queries return inconsistent results.

This isn't a data entry error — it's a **schema-level lie**. The structure claims a fact (one course → one instructor) that the business no longer accepts.

### Analogy: The Two-Headed Manager

Imagine a department with two managers who always agree. Everything works — until one changes their mind. If both claim authority, who wins?

In BCNF, **only superkeys get to make decisions**. If `Instructor → CourseID`, then `Instructor` must be a superkey — otherwise, it’s an unauthorized determinant.

This isn’t about redundancy — it’s about **governance**. Who owns the truth?

Now, imagine a course reassignment: a new instructor is hired to co-teach a course. The FD $CourseID \rightarrow Instructor$ breaks — but the schema assumed it was immutable.

The schema encoded a business rule — and when the rule changed, the database lied.

### Tension Point: When 3NF Isn’t Enough

3NF allows a non-superkey to determine a prime attribute. But BCNF says: **every determinant must be a superkey**.

Why? Because even prime attributes shouldn’t be determined by non-superkeys — it creates ambiguity in who controls the data.

Let’s test your intuition.

### Try This Yourself: Case Study – University Course Assignment

You're designing a university schema:

```
Teaches(Professor, Course, Semester)
```

With functional dependencies:
- $Professor, Semester \rightarrow Course$ (a professor teaches one course per semester)
- $Course, Semester \rightarrow Professor$ (a course is taught by one professor per semester)

Candidate keys: $\{Professor, Semester\}$ and $\{Course, Semester\}$

- Is this in 3NF?  
- Is it in BCNF?  
- If not, which FD violates BCNF?

Now, simulate an insertion: Professor Alice and Professor Bob both want to co-teach CS404 in Fall 2025.

Can you insert both rows?

What happens to the FDs?

What does the schema *think* is true — versus what the business now allows?

This is the moment normalization meets reality.

**Answer**:  
- Yes, it’s in 3NF: every non-prime attribute is either superkey-determined or prime.  
- No, it’s not in BCNF: neither $Professor