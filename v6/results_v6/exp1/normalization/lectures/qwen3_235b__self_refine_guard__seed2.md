**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Recall** the definitions of 1NF, 2NF, 3NF, BCNF, 4NF, and 5NF using precise criteria involving atomicity, functional dependencies, multivalued dependencies, and join dependencies.  
2. **Identify** violations of normalization forms in a given schema by analyzing functional and multivalued dependencies, candidate keys, and prime/non-prime attributes.  
3. **Apply** decomposition techniques to convert a schema into 2NF, 3NF, BCNF, or 4NF, ensuring lossless join and checking for dependency preservation.  
4. **Explain** how partial, transitive, and multivalued dependencies cause insertion, deletion, and update anomalies with concrete examples from real-world domains.  
5. **Evaluate** trade-offs between normalization levels and practical design needs, justifying when to normalize or denormalize based on workload, integrity, and performance.

---

### Prerequisites: Functional Dependencies, Keys, and Data Anomalies

Imagine training a machine learning model to predict hospital readmissions. Your dataset includes patient records where each row lists “Adverse Events” as a comma-separated string: *Nausea, Headache, Fatigue*. You build features by counting keywords—but the model learns that “Headache” appears more often in patients from ZIP 90210. Is this a medical insight… or a data design flaw?

Spoiler: It’s both. The structure of your data shapes what patterns algorithms can—or *must*—find. This is why **database schema design isn’t just plumbing—it’s epistemology**: it determines what knowledge can be reliably extracted.

Normalization ensures that the truths encoded in a database reflect real-world constraints—not accidental redundancies. Let’s begin with the foundation.

#### Functional Dependencies: Business Rules in Disguise

A **functional dependency (FD)** $ X \rightarrow Y $ holds over a relation $ R $ if, for every valid instance of $ R $, any two tuples that agree on $ X $ must also agree on $ Y $. This is a *semantic constraint*, not an observation from sample data.

Think of it like a **causal rule in a knowledge graph**: if you know the cause, the effect is determined. In medicine, *Vaccination → AntibodyResponse* is a dependency—if two patients receive the same vaccine under controlled conditions, they should exhibit the same immune marker.

For example:  
- $ \text{AccountID} \rightarrow \text{BranchCode} $: Each account belongs to exactly one branch by policy.  
- $ \text{ZIP} \rightarrow \text{BranchCode} $ does *not* necessarily hold—even if all current ZIP 90210 accounts use Branch B1—unless the bank enforces that rule.

> 🔍 **Quick Check: Spot the Valid FD**  
> In a university:  
> - All CS students have advisor "Dr. Lee".  
> - Some non-CS students also have Dr. Lee.  
> Does $ \text{Advisor} \rightarrow \text{Department} $ hold?  
> **Answer**: No. Since Dr. Lee advises students from multiple departments, the same advisor maps to more than one department. An FD must hold universally across all valid data states.

> 💡 **Try This Yourself: Dependency Detective**  
> You’re auditing a clinical trial database. The field `Dosage` appears to always match `WeightGroup`. Is $ \text{WeightGroup} \rightarrow \text{Dosage} $ a valid FD? What would you ask the domain expert?

#### Keys and Attribute Classification

- A **candidate key** $ K $ is a minimal set of attributes such that $ K \rightarrow R $.  
- A **superkey** is any superset of a candidate key.  
- A **prime attribute** is part of *at least one* candidate key.  
- A **non-prime attribute** is not part of any candidate key.

These distinctions are essential for identifying dependency types in higher normal forms.

**Analogy**: Think of a candidate key as a **unique molecular fingerprint**. Just as no two people share the same DNA profile (in theory), no two tuples share the same key. Prime attributes are like the variable regions of DNA—they contribute to uniqueness. Non-prime attributes are the expressed traits (phenotype), determined by the genotype (key).

#### Data Anomalies: The Consequences of Poor Design

Redundant schemas lead to operational problems known as **anomalies**:

- **Insertion anomaly**: Cannot insert certain information without unrelated data.  
  *Example*: Cannot add a new department without hiring an employee.
- **Deletion anomaly**: Deleting data unintentionally removes other information.  
  *Example*: Deleting the last employee in a department erases the department itself.
- **Update anomaly**: A single logical change requires multiple row updates.  
  *Example*: Renaming a department forces updates across many employee records.

These aren’t just inefficiencies—they’re **data integrity risks**. In machine learning pipelines, such anomalies introduce **systematic bias**: if a department name appears inconsistently due to partial updates, any model using that feature learns noise as signal.

> 💡 **Cross-Domain Insight: Normalization as Data Preprocessing**  
> In ML, we remove multicollinearity to prevent model instability. In databases, we eliminate transitive dependencies to prevent update anomalies. Both are about **removing hidden couplings** that make systems brittle.

✅ **Worked Example: E-Commerce Orders**

Consider the schema:  
```
Orders(OrderID, CustomerID, CustomerEmail, ProductID, ProductName, Quantity)
```

Assume the following functional dependencies:  
- $ \text{OrderID} \rightarrow \text{CustomerID} $  
- $ \text{CustomerID} \rightarrow \text{CustomerEmail} $  
- $ \text{ProductID} \rightarrow \text{ProductName} $  
- $ \{\text{OrderID}, \text{ProductID}\} \rightarrow \text{Quantity} $

The candidate key is $ \{\text{OrderID}, \text{ProductID}\} $.  
Non-prime attributes: `CustomerEmail`, `ProductName`.  

Both are transitively dependent on the key:  
- $ \text{OrderID} \rightarrow \text{CustomerID} \rightarrow \text{CustomerEmail} $  
- $ \text{ProductID} \rightarrow \text{ProductName} $

This redundancy leads to update anomalies. For instance, changing a customer’s email requires modifying every order they placed.

> ❗ **Common Misconception Alert**  
> Functional dependencies are *semantic*, not statistical. Observing $ \text{City} \rightarrow \text{State} $ in your dataset does not prove it is a valid FD—Springfield exists in 34 U.S. states. Always validate FDs with domain experts.

> 💡 **Interactive Prompt**  
> Sketch a sample table with three orders from the same customer purchasing different products. How many times is `CustomerEmail` repeated? What happens if the email changes?

---

### 1. First Normal Form (1NF): Atomic Values Only

#### Motivation: The Problem of Composite Values

Consider a hospital database storing adverse events as a semicolon-separated list:  

| PatientID | AdverseEvents               |  
|----------|-----------------------------|  
| P001     | Nausea; Headache; Fatigue    |  

Now imagine building a predictive model for drug safety. You tokenize the `AdverseEvents` string and compute TF-IDF scores. The model flags “Headache” as a high-risk signal—but it’s overrepresented because one patient’s list was unusually long. Is the signal real… or an artifact of non-atomic storage?

This is not just a database issue—it’s a **data science validity crisis**.

Such a structure violates **First Normal Form (1NF)**.

#### What Does "Atomic" Mean?

An attribute is **atomic** if it cannot be subdivided *in the context of the application*. Atomicity is context-dependent:  
- A full name may be atomic if used only for display.  
- But if queries filter by last name, splitting into `FirstName`, `LastName` is necessary.

Atomic does not mean "single character"—it means "treated as indivisible".

**Analogy**: Think of atomic values like **pixels in an image**. A JPEG is made of indivisible pixels for display purposes. But if you want to analyze facial features, you need to decompose further—into eyes, nose, etc. Similarly, atomicity depends on the *task*: display vs. query.

#### Formal Definition

A relation is in **1NF** if and only if:  
- Every attribute contains only atomic (indivisible) values.  
- Each tuple has exactly one value per attribute (no repeating groups or arrays).

#### Worked Example: Fixing a 1NF Violation

Original schema:  
```
Patients(PatientID, Name, AdverseEvents)
```
With `AdverseEvents = 'Nausea; Headache'` → violates 1NF.

Decompose into:  
```
PatientEvents(PatientID, Event)
```

| PatientID | Event     |  
|----------|-----------|  
| P001     | Nausea    |  
| P001     | Headache  |  
| P001     | Fatigue   |  

Now:  
- Each value is atomic.  
- We can index `Event`.  
- Optionally, add a foreign key to a `ValidEvents(EventCode)` table.

✅ **Real Application: FDA FAERS**  
The FDA Adverse Event Reporting System (FAERS) stores each adverse event in a separate record, enabling statistical signal detection across millions of reports.

> ❗ **Common Pitfall**  
> Using JSON or array types (e.g., PostgreSQL `TEXT[]`) does **not** satisfy 1NF if queries extract elements. If you write `WHERE Event @> 'Headache'`, you are treating the attribute as non-atomic.

> 💡 **Interactive Prompt**  
> You are designing a messaging app. Should `Tags` (e.g., `["urgent", "billing"]`) be stored as a JSON array or in a separate table? When would each choice violate 1NF?

---

### 2. Second Normal Form (2NF): Eliminate Partial Dependencies

#### Motivation: The Warehouse Inventory Problem

Consider:  
```
Inventory(OrderID, ItemID, ItemName, Quantity)
```
Functional dependencies:  
- $ \text{ItemID} \rightarrow \text{ItemName} $  
- $ \{\text{OrderID}, \text{ItemID}\} \rightarrow \text{Quantity} $

Candidate key: $ \{\text{OrderID}, \text{ItemID}\} $.  
`ItemName` depends only on `ItemID`—a proper subset of the key. This is a **partial dependency**.

As a result, `ItemName` is repeated across all orders for the same item. Renaming "AA Battery" to "Alkaline AA" requires updating thousands of rows.

**Analogy**: This is like **storing metadata in log files**. Every time a server writes a log, it includes the full software version string. To update the version, you must rewrite every future log entry. Instead, reference a central `Versions` table.

#### Formal Definition

A relation is in **2NF** if:  
- It is in 1NF, and  
- Every non-prime attribute is **fully functionally dependent** on every candidate key.

That is, no non-prime attribute depends on a proper subset of a candidate key.

#### Worked Example: Decomposing to 2NF

Schema:  
```
Inventory(OrderID, ItemID, ItemName, Quantity)
```

**Step 1**: Candidate key = $ \{\text{OrderID}, \text{ItemID}\} $  
Prime attributes: `OrderID`, `ItemID`  
Non-prime attributes: `ItemName`, `Quantity`

**Step 2**: Identify $ \text{ItemID} \rightarrow \text{ItemName} $:  
- $ \text{ItemID} \subset \text{key} $,  
- `ItemName` is non-prime → violates 2NF

**Step 3**: Decompose using $ \text{ItemID} \rightarrow \text{ItemName} $:  
1. `Items(ItemID, ItemName)` — key: $ \{\text{ItemID}\} $  
2. `OrderItems(OrderID, ItemID, Quantity)` — key: $ \{\text{OrderID}, \text{ItemID}\} $

Now:  
- `ItemName` depends fully on its key.  
- Updates occur in one place.

✅ **Industry Example: Amazon Inventory**  
Amazon separates the product catalog (`Items`) from order lines (`OrderItems`), ensuring consistent naming and reducing update load.

> ❗ **Common Misconception Alert**  
> 2NF only applies when the candidate key is composite. If a relation has a single-attribute key, it cannot have partial dependencies and is automatically in 2NF (provided it is in 1NF).

> 💡 **Interactive Prompt**  
> You encounter a table `Enrollments(StudentID, CourseID, CourseName, Grade)` with key $ \{\text{StudentID}, \text{CourseID}\} $. Does `CourseName` violate 2NF? Why?

---

### 3. Third Normal Form (3NF): Eliminate Transitive Dependencies

#### Motivation: The University Advisor Problem

Consider:  
```
Students(StudentID, Advisor, Dept, DeptPhone)
```
Functional dependencies:  
- $ \text{StudentID} \rightarrow \text{Advisor} $  
- $ \text{Advisor} \rightarrow \text{Dept} $  
- $ \text{Dept} \rightarrow \text{DeptPhone} $

Then $ \text{StudentID} \rightarrow \text{DeptPhone} $ *transitively*—a **transitive dependency**.

Changing the Computer Science department’s phone number requires updating every CS student’s record.

**Analogy**: This is like **propagating configuration changes through microservices**. If Service A calls Service B, which reads from Config C, and you change C, you must notify B—but A has no idea. In databases, transitive dependencies create the same hidden coupling.

#### Formal Definition

A relation is in **3NF** if:  
- It is in 2NF, and  
- For every nontrivial FD $ X \rightarrow Y $, at least one of the following holds:  
  1. $ X $ is a superkey, or  
  2. $ Y $ is a prime attribute.

This prevents non-prime attributes from being determined by non-superkeys.

#### Worked Example: Achieving 3NF

Schema:  
```
Students(StudentID, Advisor, Dept, DeptPhone)
```
Key: $ \{\text{StudentID}\} $.  
Non-prime attributes: `Advisor`, `Dept`, `DeptPhone`.

Check $ \text{Dept} \rightarrow \text{DeptPhone} $:  
- $ \text{Dept} $ is not a superkey,  
- `DeptPhone` is non-prime → violates 3NF

Decompose:  
1. `DeptPhones(Dept, DeptPhone)` — key: $ \{\text{Dept}\} $  
2. `Students(StudentID, Advisor, Dept)` — key: $ \{\text{StudentID}\} $

Now $ \text{Dept} \rightarrow \text{DeptPhone} $ is in a relation where `Dept` is a superkey.

But $ \text{Advisor} \rightarrow \text{Dept} $? If `Advisor` is not a superkey, this still violates 3NF.

Decompose again:  
3. `AdvisorDept(Advisor, Dept)` — key: $ \{\text{Advisor}\} $  
4. `Students(StudentID, Advisor)` — key: $ \{\text{StudentID}\} $

Final schema:  
- `Students(StudentID, Advisor)`  
- `AdvisorDept(Advisor, Dept)`  
- `DeptPhones(Dept, DeptPhone)`  

No transitive dependencies remain.

✅ **Real Application: MIT Registrar**  
MIT uses 3NF to isolate departmental changes from student records, ensuring administrative updates do not require mass modifications.

> ❗ **Common Pitfall**  
> 3NF allows $ X \rightarrow Y $ if $ Y $ is prime, even if $ X $ is not a superkey. This can permit redundancy—resolved in BCNF.

> 💡 **Interactive Prompt**  
> In `Employees(EmpID, Manager, Dept, ManagerEmail)`, with $ \text{Manager} \rightarrow \text{ManagerEmail} $, which attribute violates 3NF? How would you fix it?

---

### 4. Boyce-Codd Normal Form (BCNF): Only Superkeys Determine Attributes

#### Motivation: The Airline Pilot Problem

Consider:  
```
FlightAssignments(FlightNo, Pilot, AircraftType)
```
Functional dependencies:  
- $ \text{FlightNo} \rightarrow \text{Pilot} $  
- $ \text{Pilot} \rightarrow \text{AircraftType} $

Each pilot is certified for one aircraft type.  
But `AircraftType` repeats per pilot.

Key: $ \{\text{FlightNo}\} $.  
$ \text{Pilot} \rightarrow \text{AircraftType} $:  
- $ \text{Pilot} $ is not a superkey,  
- `AircraftType` is non-prime → violates BCNF.

Even if this schema were in 3NF (it is not), BCNF demands stricter control.

**Analogy**: Think of BCNF as **type safety in programming**. In a dynamically typed language, you might allow `x = "5"` then `x + 3`—but it could fail at runtime. 3NF is like that: it allows some risky dependencies. BCNF is like static typing: only superkeys (types) can determine values—no implicit coercion.

#### Formal Definition

A relation is in **BCNF** if and only if:  
For every nontrivial FD $ X \rightarrow Y $, $ X $ is a **superkey**.

BCNF implies 3NF but is stricter: it removes the “$ Y $ is prime” exception.

#### Worked Example: BCNF Decomposition

Schema:  
```
FlightAssignments(FlightNo, Pilot, AircraftType)
```
FDs:  
- $ \text{FlightNo} \rightarrow \text{Pilot} $  
- $ \text{Pilot} \rightarrow \text{AircraftType} $

Key: $ \{\text{FlightNo}\} $.  
$ \text{Pilot} \rightarrow \text{AircraftType} $ violates BCNF.

Decompose using $ \text{Pilot} \rightarrow \text{AircraftType} $:  
1. `PilotCert(Pilot, AircraftType)` — key: $ \{\text{Pilot}\} $  
2. `FlightPilot(FlightNo, Pilot)` — key: $ \{\text{FlightNo}\} $

Now:  
- In `PilotCert`, $ \text{Pilot} $ is a superkey → satisfies BCNF.  
- In `FlightPilot`, $ \text{FlightNo} $ is a superkey → satisfies BCNF.  
- Join on `Pilot` reconstructs the original data → **lossless join**.

✅ **Industry Example: Delta Airlines**  
Delta uses BCNF to manage pilot certifications, ensuring changes propagate correctly without redundancy.

> ❗ **Critical Limitation**  
> BCNF decomposition does **not** guarantee dependency preservation. The implied FD $ \text{FlightNo} \rightarrow \text{AircraftType} $ (via transitivity) is lost. Applications must enforce such dependencies externally.

> 💡 **Interactive Prompt**  
> Can you reconstruct the original data from the two tables? Try joining them. Is any information lost?

---

### 5. Fourth Normal Form (4NF): Eliminate Multivalued Dependencies

#### Motivation: The Product Catalog Problem

Consider:  
```
Products(ProductID, Color, Feature)
```

| ProductID | Color  | Feature       |  
|----------|--------|---------------|  
| P1       | Red    | Waterproof    |  
| P1       | Red    | GPS           |  
| P1       | Blue   | Waterproof    |  
| P1       | Blue   | GPS           |  

Here, `Color` and `Feature` are independent: choosing a color does not affect available features.

But storing them together forces all combinations to be listed—redundancy.

This suggests a **multivalued dependency (MVD)**:  
- $ \text{ProductID} \twoheadrightarrow \text{Color} $  
- $ \text{ProductID} \twoheadrightarrow \text{Feature} $

An MVD $ X \twoheadrightarrow Y $ means that for