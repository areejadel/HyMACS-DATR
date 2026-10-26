## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember:** State the time complexity of computing the full gradient \(\nabla_{\boldsymbol{\theta}} J\) for a network with \(P\) parameters and \(L\) layers using back-propagation, and define the adjoint \(\bar{v}_i\).
2.  **Understand:** Explain why back-propagation is an instance of dynamic programming, and justify why the adjoint of a node is the sum over its children's contributions.
3.  **Apply:** Given a scalar computational graph and its forward-pass values, compute all adjoints by hand using the back-propagation algorithm.
4.  **Analyze:** Derive the back-propagation rules for a matrix multiplication and an element-wise activation function, and identify the memory-computation trade-off.
5.  **Create:** Assemble local gradient rules into a full backward pass for a two-layer MLP and compute the parameter gradients for a specific input.
6.  **Evaluate:** Diagnose the vanishing and exploding gradient problems in deep networks from the perspective of the backward pass, and compare back-propagation to forward-mode automatic differentiation and numerical differentiation.

---

## 1. Prerequisites and Problem Setting

### The Core Problem

Imagine you are tuning a massive pipe organ with 100 million pipes. Each pipe's length affects the final sound, but the sound emerges from air flowing through all of them in sequence. If the chord is off, you need to know exactly how much to adjust every single pipe. Testing each pipe individually—changing one, listening, resetting it, moving to the next—would take years. Yet organ builders of the 18th century could tune an instrument by working backward from the sound they wanted, propagating the desired adjustment through the mechanism. Neural network training faces the same structural challenge, and it solves it with the same insight.

A network with 100 million parameters has just produced a wrong prediction. Every one of those 100 million parameters must be adjusted in the correct direction to improve performance. A naive approach—testing each parameter individually—would take years. Yet frameworks like PyTorch compute the required gradient in milliseconds.

This speed is an algorithmic achievement, not a software engineering trick. The algorithm is back-propagation, a direct application of the multivariate chain rule. But the chain rule itself is just algebra; what makes back-propagation fast is the *order* in which we multiply the terms—an order that avoids redundant computation by recognizing shared subexpressions.

Consider a feedforward network with parameters \(\boldsymbol{\theta} \in \mathbb{R}^P\). For a single training example \((\mathbf{x}, \mathbf{y})\), the network computes a prediction \(\hat{\mathbf{y}} = f(\mathbf{x}; \boldsymbol{\theta})\) and a scalar loss \(J(\boldsymbol{\theta}) = \mathcal{L}(\hat{\mathbf{y}}, \mathbf{y})\). The gradient \(\nabla_{\boldsymbol{\theta}} J \in \mathbb{R}^P\) is the vector of partial derivatives:

\[
\nabla_{\boldsymbol{\theta}} J = \left[ \frac{\partial J}{\partial \theta_1}, \frac{\partial J}{\partial \theta_2}, \dots, \frac{\partial J}{\partial \theta_P} \right]^\top.
\]

**Why naive computation is expensive.** Computing \(\frac{\partial J}{\partial \theta_k}\) for a single parameter \(\theta_k\) requires evaluating the chain rule along all paths from \(\theta_k\) to \(J\). Because the network composes \(L\) layers, each evaluation costs \(\mathcal{O}(L)\) work. Repeating this for all \(P\) parameters yields \(\mathcal{O}(LP)\) total work. In modern networks, \(P\) ranges from \(10^6\) to \(10^{11}\), making this approach prohibitive.

**The back-propagation insight.** Reversing the order of computation—accumulating gradients from the output backward through the computational graph—computes the full gradient \(\nabla_{\boldsymbol{\theta}} J\) in \(\mathcal{O}(L + P)\) time. This cost is proportional to one forward pass plus one backward pass, with a constant factor of approximately 2–3× the forward pass cost. Instead of asking every parameter "what was your impact?" individually, we propagate an error signal once and let each parameter compute its contribution from local information.

But here is a question worth sitting with before we proceed: *why should reversing the order of multiplication save any work at all?* Multiplication is associative—\((ab)c = a(bc)\)—so the total number of scalar multiplications is the same regardless of parenthesization. The savings come from a different source: shared intermediate results. When many parameters influence the loss through common pathways, computing each gradient independently repeats the same sub-chain multiplications. Back-propagation computes each sub-chain once and reuses it. This is the dynamic programming insight, and it is the same principle that makes the Viterbi algorithm for hidden Markov models and Dijkstra's shortest-path algorithm efficient. Back-propagation is not a neural network algorithm; it is a *graph traversal* algorithm that happens to be perfectly suited to neural networks.

### Required Background

We assume working knowledge of:

- **Linear algebra:** matrix multiplication \(\mathbf{A}\mathbf{B}\), transposes \(\mathbf{A}^\top\), element-wise operations \(\odot\), and broadcasting semantics.
- **Multivariate calculus:** partial derivatives, the chain rule for scalar-valued functions of vector arguments, and the Jacobian matrix \(\frac{\partial \mathbf{y}}{\partial \mathbf{x}}\) for \(\mathbf{y} \in \mathbb{R}^m, \mathbf{x} \in \mathbb{R}^n\).
- **Feedforward neural networks:** the compositional structure \(\mathbf{x} \to \mathbf{h}^{(1)} \to \mathbf{h}^{(2)} \to \dots \to \hat{\mathbf{y}} \to J\), where each layer applies an affine transformation followed by an element-wise nonlinearity.
- **Gradient-based optimization:** the parameter update rule \(\boldsymbol{\theta} \leftarrow \boldsymbol{\theta} - \eta \nabla_{\boldsymbol{\theta}} J(\boldsymbol{\theta})\), with learning rate \(\eta > 0\).

Back-propagation applies the chain rule to a specific data structure. Without fluency in the chain rule, the algorithm will appear as magic rather than mechanism.

### Quick Check 1

*Question:* A network with \(P = 10^8\) parameters has a forward pass that takes 50 ms. Estimate the time for one gradient step using (a) naive per-parameter computation and (b) back-propagation.

*Answer:* (a) Naive: \(10^8 \times 50\text{ ms} = 5 \times 10^9\text{ ms} \approx 58\) days. (b) Back-propagation: roughly \(2 \times 50\text{ ms} = 100\text{ ms}\).

---

## 2. Computational Graphs

### Motivation: Representing Arbitrary Computations

A neural network composes primitive operations: matrix multiplies, element-wise nonlinearities, convolutions, pooling, and normalization. To reason about gradient computation uniformly, we represent the entire computation as a **computational graph**—a directed acyclic graph (DAG) where nodes are operations and edges carry data.

This abstraction is not merely pedagogical. All major automatic differentiation frameworks (PyTorch's autograd, TensorFlow's GradientTape, JAX's trace) construct computational graphs and execute back-propagation by traversing them. The graph is the data structure that makes the dynamic programming memoization explicit: each node stores its value during the forward pass, and its adjoint during the backward pass. The edges encode exactly which intermediate results are shared.

### Formal Definition

A **computational graph** \(\mathcal{G} = (\mathcal{V}, \mathcal{E})\) for a scalar output \(J\) is defined by:

- **Nodes** \(\mathcal{V} = \{u^{(1)}, u^{(2)}, \dots, u^{(n)}\}\). Each node \(u^{(i)}\) holds:
  - A value \(v_i\) (computed during the forward pass).
  - An operation \(f_i\) that produced \(v_i\) from its inputs.
- **Edges** \(\mathcal{E}\): a directed edge \(u^{(i)} \to u^{(j)}\) indicates that \(v_i\) is an input to operation \(f_j\).
- **Topological ordering:** nodes are indexed such that if \(u^{(i)} \to u^{(j)}\), then \(i < j\). The root \(u^{(n)} = J\) has out-degree zero. Leaf nodes (in-degree zero) are inputs or parameters.

For each node \(u^{(i)}\), we define:

- \(\text{parents}(i) = \{k : u^{(k)} \to u^{(i)}\}\) — the inputs to operation \(f_i\).
- \(\text{children}(i) = \{j : u^{(i)} \to u^{(j)}\}\) — the operations that consume \(v_i\).

### Building a Graph: Concrete Example

We build the graph for \(J = (a \cdot b) + c^2\) with \(a=3, b=4, c=2\).

**Step 1 — Identify the operations.** The expression contains a multiply (\(a \cdot b\)), a square (\(c^2\)), and an addition.

**Step 2 — Assign nodes.** We create a node for every input and intermediate result:
- \(u^{(1)} = a\) (leaf, value 3)
- \(u^{(2)} = b\) (leaf, value 4)
- \(u^{(3)} = c\) (leaf, value 2)
- \(u^{(4)} = u_1 = a \cdot b\) (multiply, value 12)
- \(u^{(5)} = u_2 = c^2\) (power, value 4)
- \(u^{(6)} = u_3 = u_1 + u_2\) (add, value 16)
- \(u^{(7)} = J\) (output, value 16)

**Step 3 — Add edges.** Draw an arrow from each input to the operation that consumes it:
- \(1 \to 4, 2 \to 4\)
- \(3 \to 5\)
- \(4 \to 6, 5 \to 6\)
- \(6 \to 7\)

**Step 4 — Verify the DAG.** Every edge goes from a lower index to a higher index, so the topological ordering is satisfied. We can now read off relationships: \(\text{children}(1) = \{4\}\), \(\text{children}(4) = \{6\}\), and so on. This graph structure is exactly what the backward pass will traverse in reverse.

**Try this yourself:** Sketch the computational graph for \(J = (x \cdot y) + \sin(z)\). Identify all nodes, their operations, and the children of the node holding \(x \cdot y\).

### What We Need to Compute

For every node \(u^{(i)}\), we define the **adjoint** (or **sensitivity**):

\[
\bar{v}_i = \frac{\partial J}{\partial v_i}.
\]

For leaf nodes representing parameters, \(\bar{v}_i\) is the gradient component needed for optimization. For intermediate nodes, the adjoints are intermediate results that enable efficient computation of parameter gradients.

**An analogy from electrical engineering:** Consider a network of resistors where the output is a voltage measured at one terminal. The adjoint of a node is analogous to the sensitivity of that output voltage to a small change in the current at that node. In circuit analysis, the adjoint network method computes all these sensitivities simultaneously by exciting the network with a single test source at the output and measuring the response at every internal node—exactly the same reversal trick. Back-propagation is the adjoint sensitivity method applied to computational graphs rather than electrical networks. This connection is not just a curiosity; it means that decades of research on adjoint methods for partial differential equations and circuit simulation directly inform how we implement and optimize back-propagation.

### Quick Check 2

*Question:* Draw the computational graph for \(J = (x + y) \cdot z\). Label all nodes and edges. Identify the children of the node representing \(x + y\).

*Answer:* Nodes: \(u^{(1)} = x\), \(u^{(2)} = y\), \(u^{(3)} = z\), \(u^{(4)} = x + y\), \(u^{(5)} = (x+y) \cdot z\), \(u^{(6)} = J\). Edges: \(1 \to 4, 2 \to 4, 4 \to 5, 3 \to 5, 5 \to 6\). The children of \(u^{(4)}\) are \(\{5\}\).

---

## 3. The Chain Rule on Computational Graphs

### The Multivariate Chain Rule

Let \(u^{(i)}\) be a node whose value \(v_i\) influences a set of downstream nodes \(\text{children}(i)\). By the multivariate chain rule, the total derivative of \(J\) with respect to \(v_i\) is the sum over all children of the product of the child's adjoint and the local derivative:

\[
\bar{v}_i = \frac{\partial J}{\partial v_i} = \sum_{j \in \text{children}(i)} \frac{\partial J}{\partial v_j} \cdot \frac{\partial v_j}{\partial v_i} = \sum_{j \in \text{children}(i)} \bar{v}_j \cdot \frac{\partial v_j}{\partial v_i}. \tag{1}
\]

**Why the sum?** Suppose \(v_i\) feeds into two different children. A small perturbation \(\Delta v_i\) changes both children's outputs, and both changes independently affect the final loss \(J\). Because the effects propagate through separate branches, they sum (to first order). Equation (1) captures this accumulation.

A common mistake is to apply the single-variable chain rule \(\frac{dJ}{dv_i} = \frac{dJ}{dv_j} \cdot \frac{dv_j}{dv_i}\). That formula holds only when \(v_i\) has exactly one child. When a node's output fans out to multiple consumers, the sum over children is essential.

**Think of it as a watershed.** Imagine rain falling on a mountain range. A single ridge divides the flow: water falling on one side reaches the eastern river, water on the other side reaches the western river. The total contribution of that ridge to the ocean level is the sum of contributions through both paths. The adjoint \(\bar{v}_i\) is the total "downstream influence" of node \(i\), and when the flow splits, you must sum over all branches.

### The Back-Propagation Algorithm

Equation (1) is recursive: computing \(\bar{v}_i\) requires \(\bar{v}_j\) for all children \(j\). The base case is the root:

\[
\bar{v}_n = \frac{\partial J}{\partial J} = 1.
\]

Processing nodes in **reverse topological order** guarantees that when we compute \(\bar{v}_i\), all \(\bar{v}_j\) for \(j \in \text{children}(i)\) have already been computed (since \(j > i\)).

**Algorithm 1: Back-Propagation**

```
Input: Graph with nodes u^{(1)},...,u^{(n)} in topological order,
       values v_i from forward pass.
Output: adjoints \bar{v}_i for all i.

\bar{v}_n = 1
for i = n-1 down to 1:
    \bar{v}_i = 0
    for j in children(i):
        \bar{v}_i += \bar{v}_j * (∂v_j / ∂v_i)
return \bar{v}
```

**Intuition:** We start at the loss with \(\bar{v}_n = 1\). Moving one step backward, we multiply the incoming adjoint by the local derivative of that node's operation. We continue layer by layer, accumulating contributions whenever a node fans out.

### Worked Example: Scalar Computation

We apply the algorithm to \(J = (a \cdot b) + c^2\) with \(a=3, b=4, c=2\), using the graph from Section 2.

**Forward pass (record values):**
- \(v_4 = a \cdot b = 12\)
- \(v_5 = c^2 = 4\)
- \(v_6 = v_4 + v_5 = 16\)
- \(v_7 = J = 16\)

**Backward pass (process nodes \(7, 6, 5, 4, 3, 2, 1\)):**

*Node 7 (root):* \(\bar{v}_7 = 1\).

*Node 6 (\(v_6 = v_4 + v_5\)):* The local derivatives are \(\frac{\partial v_6}{\partial v_4} = 1\) and \(\frac{\partial v_6}{\partial v_5} = 1\). Node 6 has one child (node 7), so:
\[
\bar{v}_6 = \bar{v}_7 \cdot \frac{\partial v_7}{\partial v_6} = 1 \cdot 1 = 1.
\]

*Node 5 (\(v_5 = c^2\)):* The local derivative is \(\frac{\partial v_5}{\partial c} = 2c = 4\). Node 5 has one child (node 6), so:
\[
\bar{v}_5 = \bar{v}_6 \cdot \frac{\partial v_6}{\partial v_5} = 1 \cdot 1 = 1.
\]
Propagating to \(c\) (node 3):
\[
\bar{v}_3 = \bar{v}_5 \cdot \frac{\partial v_5}{\partial c} = 1 \cdot 4 = 4.
\]

*Node 4 (\(v_4 = a \cdot b\)):* The local derivatives are \(\frac{\partial v_4}{\partial a} = b = 4\) and \(\frac{\partial v_4}{\partial b} = a = 3\). Node 4 has one child (node 6), so:
\[
\bar{v}_4 = \bar{v}_6 \cdot \frac{\partial v_6}{\partial v_4} = 1 \cdot 1 = 1.
\]
Propagating to \(a\) and \(b\):
\[
\bar{v}_1 = \bar{v}_4 \cdot \frac{\partial v_4}{\partial a} = 1 \cdot 4 = 4, \quad
\bar{v}_2 = \bar{v}_4 \cdot \frac{\partial v_4}{\partial b} = 1 \cdot 3 = 3.
\]

**Result:** \(\frac{\partial J}{\partial a} = 4\), \(\frac{\partial J}{\partial b} = 3\), \(\frac{\partial J}{\partial c} = 4\).

**Sanity check:** Increasing \(a\) by \(\epsilon\) gives \(J = ((3+\epsilon) \cdot 4) + 4 = 16 + 4\epsilon\), so the derivative is indeed 4. The other values confirm similarly.

### Dynamic Programming Perspective

Each adjoint \(\bar{v}_i\) is computed exactly once and then reused for all its parents. For example, \(\bar{v}_6 = 1\) was used to compute both \(\bar{v}_4\) and \(\bar{v}_5\) without recomputation.

This is dynamic programming: the subproblem "compute \(\frac{\partial J}{\partial v_i}\)" is solved once and memoized. The reverse topological order ensures all dependencies are available when needed. The total number of operations is proportional to the number of edges in the graph, which is \(\mathcal{O}(n)\) for typical neural network graphs—a dramatic improvement over the naive \(\mathcal{O}(n^2)\) path-enumeration approach.

**A connection beyond neural networks:** This same dynamic programming pattern—solving a recursive problem on a DAG in reverse topological order—appears in project management (the critical path method), in compilers (liveness analysis for register allocation), and in probabilistic graphical models (belief propagation). In each case, a quantity defined at the "output" is propagated backward through a dependency graph, with each node combining information from its downstream neighbors. Recognizing back-propagation as an instance of this general pattern means that insights from any of these fields—such as techniques for handling graphs with cycles or for trading off memory against recomputation—can be imported directly into the design of automatic differentiation systems.

### Quick Check 3

*Question:*