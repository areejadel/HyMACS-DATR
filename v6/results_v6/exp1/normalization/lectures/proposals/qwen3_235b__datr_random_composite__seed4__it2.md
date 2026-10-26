- Apply 3NF and BCNF to a given relation schema by decomposing it to eliminate transitive and non-superkey functional dependencies.
- Analyze a database schema to identify violations of 3NF and BCNF using functional dependency diagrams.
- Evaluate the trade-offs between normalization levels, particularly regarding dependency preservation and update anomaly prevention.
- Design a normalized schema that balances data integrity with query usability.

---

## 3. Third Normal Form (3NF): Eliminating Indirect Dependencies

### Prerequisites

Before diving in, let’s make sure we’re aligned on key concepts:
- A **functional dependency** $X \rightarrow Y$ means the value of $X$ determines the value of $Y$.
- A **prime attribute** is part of *any* candidate key.
- A **non-prime attribute** is not part of any candidate key.
- **Transitive dependency**: If $A \rightarrow B$ and $B \rightarrow C$, then $A \rightarrow C$ through $B$, assuming $B$ does not determine $A$.

We’ll build on 2NF: recall that 2NF eliminates partial dependencies (where a non-prime attribute depends on only part of a composite key).

> 🔍 **Quick Check: 2NF Recap**  
> Given: `Enrollment(StudentID, CourseID, StudentName)` with $StudentID \rightarrow StudentName$ and key $\{StudentID, CourseID\}$.  
> Is this in 2NF? Why or why not?  
> 💡 *Answer: No — $StudentName$ depends only on $StudentID$, a partial key. Fix: split into `Student(StudentID, StudentName)` and `Enrollment(StudentID, CourseID)`.*

---

### Intuition First: The Problem of Indirect Control

Let’s start with a real-world scenario.

Imagine a company where each employee belongs to a department, and each department has one manager. So if you know the employee, you know their department, and from that, you know the manager.

But here’s the catch: **you can’t change the manager without changing the department**. The manager is tied to the *department*, not the employee. This creates a chain:  
**Employee → Department → Manager**

Now suppose the company restructures and wants to assign a new manager to a department. Every employee in that department now indirectly "has a new manager" — but what if some employees should report to someone else? The schema doesn’t allow it.

This is a **transitive dependency**:  
$EmpID \rightarrow Dept$, $Dept \rightarrow Manager$ → therefore $EmpID \rightarrow Manager$ via $Dept$.

But $Manager$ is not directly determined by $EmpID$ — it’s determined by $Dept$, which is not a key in the `Employee` table.

> ❗ **Common Misconception**: "If the data is correct now, it’s safe."  
> Reality: Even correct data can lead to **update anomalies** later. If you later try to assign a different manager to the same department for just one employee, you either violate consistency or need to split the department artificially.

---

### Formal Definition of 3NF

A relation is in **Third Normal Form (3NF)** if:
1. It is in 2NF, and  
2. No non-prime attribute is **transitively dependent** on any candidate key.

Equivalently: For every non-trivial functional dependency $X \rightarrow Y$:  
- $X$ is a superkey, **or**  
- $Y$ is a prime attribute.

> 💡 **Why this works**: 3NF stops chains like $A \rightarrow B \rightarrow C$ when $C$ is non-prime and $B$ is not a superkey. It ensures that non-key facts depend *directly* on a key.

---

### Worked Example: Applying 3NF

Given relation:  
```
Employee(EmpID, Dept, Manager)
```
With functional dependencies:  
- $EmpID \rightarrow Dept$  
- $Dept \rightarrow Manager$

Step 1: Identify candidate key  
- $EmpID \rightarrow Dept \rightarrow Manager$, so $EmpID$ determines all attributes → $EmpID$ is candidate key.

Step 2: Identify non-prime attributes  
- Prime: $EmpID$ (it’s the key)  
- Non-prime: $Dept$, $Manager$

Step 3: Check for transitive dependencies  
- $Dept \rightarrow Manager$: $Dept$ is not a superkey, $Manager$ is non-prime → **violates 3NF**

Step 4: Decompose  
We break the chain by promoting the determinant $Dept$ into its own relation.

New schema:  
```
Employee(EmpID, Dept)  
Department(Dept, Manager)
```

Now:
- In `Employee`: $EmpID \rightarrow Dept$ — valid, $EmpID$ is key.
- In `Department`: $Dept \rightarrow Manager$ — valid, $Dept$ is key.

No transitive dependency remains. Both relations are in 3NF.

> ✅ **Test Yourself: Quick Check 4**  
> Given:  
> ```
> Student(StudentID, Advisor, AdvisorOffice)
> ```
> With:  
> - $StudentID \rightarrow Advisor$  
> - $Advisor \rightarrow AdvisorOffice$  
> 
> 1. Is this in 3NF?  
> 2. If not, how would you decompose it?  
> 
> 💡 *Hint: Draw the dependency chain. Is $AdvisorOffice$ transitively dependent on $StudentID$?*  
> 
> **Answer**:  
> 1. No — $Advisor \rightarrow AdvisorOffice$ creates a transitive dependency $StudentID \rightarrow AdvisorOffice$.  
> 2. Decompose into:  
>    ```
>    Student(StudentID, Advisor)  
>    AdvisorInfo(Advisor, AdvisorOffice)
>    ```

> 💡 **Design Prompt**: What if an advisor has multiple offices? Would $Advisor \rightarrow AdvisorOffice$ still hold?  
> → Then $AdvisorOffice$ is multi-valued → violates 1NF. You’d need to normalize further or model as a separate table.

---

## 4. Boyce-Codd Normal Form (BCNF): Ensuring Determinants Are Keys

### Prerequisites

We assume 3NF is understood. Remember: 3NF allows some functional dependencies where the determinant is not a superkey — as long as the dependent is prime.

BCNF removes this exception.

---

### Intuition First: The Problem of Dual Authority

Let’s consider a university course enrollment system.

```
Enrollment(StudentID, CourseID, Instructor)
```

With rules:
- Each course has one instructor: $CourseID \rightarrow Instructor$
- No student takes two sections of the same course: $\{StudentID, CourseID\}$ is candidate key.

Now suppose: each instructor teaches only one course → $Instructor \rightarrow CourseID$

So both $CourseID$ and $Instructor$ determine each other. That means:
- $CourseID \rightarrow Instructor$
- $Instructor \rightarrow CourseID$

Now, is $\{StudentID, Instructor\}$ a key? Yes — because $Instructor$ determines $CourseID$, so you can recover the full tuple.

But here’s the problem: **both $CourseID$ and $Instructor$ can determine $Instructor$** — but neither is necessarily the key in the original table.

So if someone adds a record where Dr. Smith teaches CS402, but we already have Dr. Smith teaching CS401, is that allowed?

The schema doesn’t prevent it — because `Instructor` isn’t a superkey. But the functional dependency $Instructor \rightarrow CourseID$ implies it *should*.

> ❗ **Common Misconception**: "If I document the rule, the database enforces it."  
> Reality: **Constraints must be enforced by keys or explicit constraints**. If $Instructor \rightarrow CourseID$ isn’t enforced via a key, the database allows violations.

This is a **governance failure**: the schema doesn’t reflect the business rule.

---

### Formal Definition of BCNF

A relation is in **Boyce-Codd Normal Form (BCNF)** if:  
For every non-trivial functional dependency $X \rightarrow Y$,  
- $X$ is a **superkey**.

This is stricter than 3NF. Every BCNF schema is in 3NF, but not every 3NF schema is in BCNF.

> 💡 **Key Insight**: BCNF ensures that **only keys can determine values**. It eliminates ambiguity about who "owns" a fact.

---

### Worked Example: Applying BCNF

Given:  
```
R(Professor, Course, Time)
```
With FDs:  
- $Professor \rightarrow Course$ (each professor teaches only one course)  
- $Course, Time \rightarrow Professor$ (only one professor teaches a course at a given time)

Step 1: Find candidate keys  
- $Professor \rightarrow Course$, so $\{Professor, Time\}$ determines all attributes → candidate key.  
- $Course, Time \rightarrow Professor$, so $\{Course, Time\}$ also determines all → another candidate key.

Step 2: Check BCNF  
- $Professor \rightarrow Course$: Is $Professor$ a superkey? No — it’s not a candidate key alone. → **Violates BCNF**

Step 3: Decompose  
We must eliminate $Professor \rightarrow Course$ by splitting.

Create:  
```
Teaches(Professor, Course)  -- enforces Professor → Course
Schedule(Course, Time, Professor) -- with key {Course, Time}
```

Now check determinants:
- In `Teaches`: $Professor \rightarrow Course$, $Professor$ is key → OK.
- In `Schedule`: $Course, Time \rightarrow Professor$, $Course, Time$ is key → OK.

Both relations are in BCNF.

> ✅ **Test Yourself: Spot the Hidden Conflict**  
> Given:  
> ```
> R(A, B, C)
> ```
> With FDs: $A \rightarrow B$, $B \rightarrow C$  
> Assume $A$ is the candidate key.

> 1. Is this in 3NF?  
> 2. Is it in BCNF?  
> 3. Decompose if needed.

> 💡 *Hint: Is $B$ a superkey? Is $C$ prime?*

> **Answer**:  
> 1. 3NF? No — $B \rightarrow C$, $B$ is not a superkey, $C$ is non-prime → violates 3NF.  
> 2. BCNF? Also no — same reason.  
> 3. Decompose into:  
>    ```
>    R1(A, B)  -- A → B
>    R2(B, C)  -- B → C
>    ```
>    - Lossless? Yes — $B$ is key in $R2$.  
>    - Dependency preserved? Yes — both FDs are captured.

> 💡 **Edge Case Alert**: What if $C \rightarrow B$ instead? Try decomposing.  
> → Then $C \rightarrow B$, $B \rightarrow C$: mutual determination. But $C$ is not a superkey → still violates BCNF. Decompose same way.

---

## Trade-Offs: When to Stop Normalizing

Normalization isn’t a race to BCNF. Sometimes, **preserving functional dependencies** is more important than eliminating all redundancy.

### The 3NF vs. BCNF Dilemma

| Feature | 3NF | BCNF |
|--------|-----|------|
| Lossless decomposition | ✅ Yes | ✅ Yes |
| Dependency preservation | ✅ Yes | ❌ Not guaranteed |
| Eliminates transitive dependencies | ✅ | ✅ |
| Requires all determinants to be superkeys | ❌ | ✅ |

> 💡 **Key Insight**: 3NF is **dependency-preserving** — it can always decompose without losing functional dependencies. BCNF cannot always do both.

---

### Worked Example: The Cost of BCNF

Given:  
```
R(A, B, C)
```
With FDs:  
- $A \rightarrow B$  
- $C \rightarrow B$  
Candidate key: $\{A, C\}$

Step 1: Check BCNF  
- $A \rightarrow B$: $A$ is not a superkey → violates BCNF  
- $C \rightarrow B$: $C$ is not a superkey → also violates

Step 2: Decompose to BCNF  
Try splitting on $A \rightarrow B$:  
```
R1(A, B)  -- A → B
R2(A, C)  -- from key
```

But now $C \rightarrow B$ is lost — no relation contains both $C$ and $B$.

Alternatively, split on $C \rightarrow B$:  
```
R1(C, B)
R2(A, C)
```

Then $A \rightarrow B$ is lost.

→ **No way to preserve both FDs in BCNF**.

> ✅ **Test Yourself: Final Challenge**  
> 1. Is the original in BCNF?  
> 2. Can you decompose it into BCNF while preserving all FDs?  
> 3. What would you do in practice?

> **Answer**:  
> 1. No — $C \rightarrow B$, $C$ is not a superkey.  
> 2. No — decomposition loses one FD.  
> 3. In practice:  
>    - Use 3NF instead — it can preserve both dependencies.  
>    - Or keep the redundancy and add a **materialized view** or **application-level check** to enforce $C \rightarrow B$.  
>    - Trade-off: BCNF gives purity; 3NF gives practicality.

---

## Summary: The Normalization Ladder

| Normal Form | Requirement | Prevents |
|-------------|-----------|---------|
| 1NF | Atomic values | Unstructured data |
| 2NF | No partial dependencies | Redundant data in composite keys |
| 3NF | No transitive dependencies (unless prime) | Indirect update anomalies |
| BCNF | Every determinant is a superkey | Key ambiguity and governance failure |

Normalization is not dogma — it’s **diagnosis and surgery**. You inspect the schema, identify the disease (redundancy, anomalies), and apply the right procedure.

But like medicine, over-treatment has side effects. Know when to stop.

> 🔄 **Final Prompt**: Revisit a schema you’ve worked on. Can you draw its FDs? Where are the middlemen? The dual authorities? Normalize it — then ask: did you gain clarity, or lose flexibility?