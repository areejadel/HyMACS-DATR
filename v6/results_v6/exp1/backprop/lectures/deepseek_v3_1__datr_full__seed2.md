# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definition of a computational graph and identify nodes, edges, and the roles of forward and backward passes in gradient computation.
2. **Understand** why naive gradient computation is computationally prohibitive and how dynamic programming solves the efficiency problem.
3. **Apply** the back-propagation chain rule to compute gradients for any node in a computational graph, given its children's gradients and local derivatives.
4. **Analyze** the memory–time trade-off in back-propagation and identify when recomputation strategies become necessary.
5. **Create** a complete backward pass for a two-layer multilayer perceptron, computing all parameter gradients from a given loss gradient.

---

## 1. Prerequisites and the Problem Setting

### Required Background

We assume familiarity with:

- **Matrix multiplication and broadcasting:** products \(\mathbf{A}\mathbf{B}\), transposes, and sums over rows/columns.
- **Partial derivatives and the chain rule:** for scalar functions, \(\frac{\partial}{\partial x} f(g(x)) = f'(g(x))\, g'(x)\). We extend this to vectors and matrices.
- **Feedforward neural network structure:** input → hidden layers → output → loss.
- **Gradient-based optimization:** the idea that we update parameters via \(\boldsymbol{\theta} \leftarrow \boldsymbol{\theta} - \eta \nabla_{\boldsymbol{\theta}} J\).

If any of these feel shaky, pause and review them — they are the substrate on which back-propagation is built.

### The Core Problem

We have a feedforward network mapping input \(\mathbf{x} \in \mathbb{R}^d\) to prediction \(\hat{\mathbf{y}}\) through a sequence of layers. During supervised training, a scalar cost function \(J(\boldsymbol{\theta})\) measures the discrepancy between predictions and true labels \(\mathbf{y}\). The parameters \(\boldsymbol{\theta}\) include all weights and biases.

**The learning task:** adjust \(\boldsymbol{\theta}\) to minimize \(J\). Gradient-based optimizers require \(\nabla_{\boldsymbol{\theta}} J\) — the vector of partial derivatives of \(J\) with respect to every parameter.

**The challenge:** A modern network can have millions of parameters. Computing each partial derivative independently by evaluating the chain rule from scratch would require traversing the entire network for each parameter. That approach would mean millions of forward passes per gradient step — completely infeasible [1,5].

**The insight:** We can compute all gradients in roughly the same time as one forward pass plus one backward pass. This is back-propagation.

### Quick Check 1

*Question:* If a network has \(10^6\) parameters and a forward pass takes 10 ms, roughly how long would naive gradient computation take (computing each \(\partial J/\partial \theta_k\) by a separate forward-like traversal)?

*Answer:* On the order of \(10^6 \times 10\text{ ms} = 10{,}000\) seconds (≈ 3 hours) per gradient step. Back-propagation reduces this to roughly 20 ms (forward + backward).

---

## 2. Computational Graphs: the Universal Language

### Intuition: A Recipe, Not a Formula

Think of a neural network not as a fixed equation but as a *recipe* — a sequence of operations. Each operation takes some inputs and produces an output. Some outputs become inputs to later operations. We can draw this as a directed graph.

**Example (before formalism):** Consider the simple expression \(J = (a \cdot b) + c^2\). We decompose it into operations:

1. \(u_1 = a \cdot b\) (multiply)
2. \(u_2 = c^2\) (square)
3. \(u_3 = u_1 + u_2\) (add)
4. \(J = u_3\) (identity for the root)

The graph has nodes \(\{a, b, c, u_1, u_2, u_3, J\}\). Edges: \(a \to u_1\), \(b \to u_1\), \(c \to u_2\), \(u_1 \to u_3\), \(u_2 \to u_3\), \(u_3 \to J\). The leaf nodes are \(a, b, c\) (inputs/parameters). The root is \(J\).

### Formal Definition

A **computational graph** is a directed acyclic graph (DAG) where:

- **Nodes** represent operations (variables or functions).
- **Edges** represent data flow: an edge from \(u^{(i)}\) to \(u^{(j)}\) means \(u^{(i)}\) is an input to the operation that produces \(u^{(j)}\).

We number nodes \(u^{(1)}, u^{(2)}, \dots, u^{(n)}\) in topological order (every node appears after its inputs). The root is \(u^{(n)} = J\), the scalar cost.

**Why this matters:** Every neural network architecture — feedforward, convolutional, recurrent, transformer — can be expressed as a computational graph. By developing back-propagation on the *graph*, we obtain an algorithm that works for all architectures uniformly.

**Try this yourself:** Before continuing, sketch the computational graph for \(z = (x + y) \cdot \max(x, 0)\). Label each node with its operation. Notice how the \(\max\) operation introduces a branch — this will matter for gradients.

### What We Want to Compute

For any node \(u^{(i)}\), we want:

\[
\frac{\partial J}{\partial u^{(i)}}
\]

This is the gradient of the final cost with respect to that node's output. For parameter nodes (leaves), this is exactly the gradient we need for optimization. For intermediate nodes, these gradients are stepping stones to reach the parameters.

### Quick Check 2

*Question:* In the graph for \(J = (a \cdot b) + c^2\), list the children of node \(a\).

*Answer:* Node \(a\) has one child: \(u_1\) (the multiplication node), because \(a\) is an input to the operation that computes \(u_1\).

---

## 3. The Chain Rule Decomposition

### Intuition: "Messages Flowing Backward"

Imagine each node receives a "message" from the cost \(J\): "How much does \(J\) change when I change slightly?" The root \(J\) sends itself a message of 1 (changing \(J\) by \(\Delta\) changes \(J\) by exactly \(\Delta\)).

Now, how does a node \(u^{(i)}\) compute its message? It looks at all nodes that *directly* used \(u^{(i)}\) — its **children**. Each child \(u^{(j)}\) already has its message \(\frac{\partial J}{\partial u^{(j)}}\). The child also knows its *local* sensitivity to \(u^{(i)}\): the partial derivative \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\).

The total effect of \(u^{(i)}\) on \(J\) is the sum over all paths through its children:

\[
\text{message}(u^{(i)}) = \sum_{\text{children } j} \text{message}(u^{(j)}) \times (\text{local sensitivity of } u^{(j)} \text{ to } u^{(i)})
\]

This is exactly the multivariate chain rule.

**Why a sum?** Because \(u^{(i)}\) can influence \(J\) through multiple downstream paths. If \(u^{(i)}\) feeds into two different children that both eventually reach \(J\), a small change in \(u^{(i)}\) perturbs both paths simultaneously. The total effect is the sum of the individual path effects. This is the same principle as a river splitting into two tributaries: the total downstream flow is the sum of the flows in each branch.

### Formal Statement

Let node \(u^{(i)}\) have children \(\{u^{(j)} : j \in \text{children}(i)\}\) — the nodes whose computation directly depends on \(u^{(i)}\). Then:

\[
\frac{\partial J}{\partial u^{(i)}} = \sum_{j \in \text{children}(i)} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}. \tag{1}
\]

This is the **back-propagation rule**. It is recursive: to compute the gradient at a node, we need the gradients at its children. The recursion terminates at the root \(J\), where \(\frac{\partial J}{\partial J} = 1\) (base case).

**Try this yourself:** Before reading the worked example, attempt to trace the backward pass for \(J = (a \cdot b) + c^2\) by hand. Start at \(J\) with gradient 1, then work backwards through each operation. Where do you get stuck?

### Worked Example: A Tiny Graph

Let's apply (1) to \(J = (a \cdot b) + c^2\) with concrete numbers: \(a = 3, b = 4, c = 2\).

**Forward pass (compute and store all node values):**
- \(u_1 = a \cdot b = 3 \cdot 4 = 12\)
- \(u_2 = c^2 = 2^2 = 4\)
- \(u_3 = u_1 + u_2 = 12 + 4 = 16\)
- \(J = u_3 = 16\)

**Backward pass (reverse topological order: \(J, u_3, u_2, u_1, c, b, a\)):**

*Step 1: Root.* \(\frac{\partial J}{\partial J} = 1\).

*Step 2: Node \(u_3\).* Operation: \(J = u_3\) (identity). Local derivative \(\frac{\partial J}{\partial u_3} = 1\). Children of \(u_3\)? None (it's the root input). Actually, we apply the rule from the perspective of \(u_3\): its child is \(J\). So:
\[
\frac{\partial J}{\partial u_3} = \frac{\partial J}{\partial J} \cdot \frac{\partial J}{\partial u_3} = 1 \cdot 1 = 1.
\]

*Step 3: Node \(u_1\).* Operation: \(u_3 = u_1 + u_2\). Local derivative \(\frac{\partial u_3}{\partial u_1} = 1\). Child gradient \(\frac{\partial J}{\partial u_3} = 1\) (already computed).
\[
\frac{\partial J}{\partial u_1} = \frac{\partial J}{\partial u_3} \cdot \frac{\partial u_3}{\partial u_1} = 1 \cdot 1 = 1.
\]

*Step 4: Node \(u_2\).* Similarly, \(\frac{\partial u_3}{\partial u_2} = 1\).
\[
\frac{\partial J}{\partial u_2} = \frac{\partial J}{\partial u_3} \cdot \frac{\partial u_3}{\partial u_2} = 1 \cdot 1 = 1.
\]

*Step 5: Node \(a\).* Operation: \(u_1 = a \cdot b\). Local derivative \(\frac{\partial u_1}{\partial a} = b = 4\). Child gradient \(\frac{\partial J}{\partial u_1} = 1\).
\[
\frac{\partial J}{\partial a} = \frac{\partial J}{\partial u_1} \cdot \frac{\partial u_1}{\partial a} = 1 \cdot 4 = 4.
\]

*Step 6: Node \(b\).* Operation: \(u_1 = a \cdot b\). Local derivative \(\frac{\partial u_1}{\partial b} = a = 3\).
\[
\frac{\partial J}{\partial b} = \frac{\partial J}{\partial u_1} \cdot \frac{\partial u_1}{\partial b} = 1 \cdot 3 = 3.
\]

*Step 7: Node \(c\).* Operation: \(u_2 = c^2\). Local derivative \(\frac{\partial u_2}{\partial c} = 2c = 4\). Child gradient \(\frac{\partial J}{\partial u_2} = 1\).
\[
\frac{\partial J}{\partial c} = \frac{\partial J}{\partial u_2} \cdot \frac{\partial u_2}{\partial c} = 1 \cdot 4 = 4.
\]

**Interpretation:** \(\frac{\partial J}{\partial a} = 4\) means increasing \(a\) by \(\epsilon\) increases \(J\) by roughly \(4\epsilon\). \(\frac{\partial J}{\partial b} = 3\), \(\frac{\partial J}{\partial c} = 4\).

### Why This Is Dynamic Programming

Notice what happened: we computed each node's gradient exactly once, reusing previously computed gradients from its children. No redundant computation. This is the essence of dynamic programming: solve each subproblem once, store the result, and combine solutions from the leaves upward (in this case, from the root downward). The computational graph gives us the dependency structure; the backward pass is the DP algorithm that exploits it.

**An analogy from circuit analysis:** Think of the forward pass as applying a voltage at the input terminals and measuring the potential at every node in a resistor network. The backward pass is like injecting a unit current at the output terminal and measuring how much current flows through each branch back to the inputs. The superposition of these current measurements tells you exactly how sensitive the output voltage is to each input voltage. The forward pass computes function values; the backward pass computes *sensitivities* — and it does so by exploiting the same graph topology, just traversed in reverse.

### Quick Check 3

*Question:* Why is the backward pass more efficient than computing each \(\partial J/\partial \theta_k\) independently from the forward graph?

*Answer:* Because each independent computation would re-traverse shared sub-paths from \(\theta_k\) to \(J\). The backward pass computes the gradient at each intermediate node once and reuses it for all upstream nodes that depend on it — classic dynamic programming memoization.

---

## 4. Local Gradients: The Building Blocks

### The Key Abstraction

Every node in the computational graph is a function. To implement back-propagation for any architecture, we only need to know two things about each node type:

1. **Forward:** Given inputs, compute the output.
2. **Backward:** Given the gradient of the loss with respect to the *output* (\(\frac{\partial J}{\partial \text{out}}\)), compute the gradient with respect to each *input*.

The backward computation uses only the node's local derivative and the incoming gradient from above. It does not need to know anything about the rest of the graph. This modularity is what makes automatic differentiation frameworks (PyTorch, TensorFlow, JAX) possible: each operation defines its own `forward` and `backward` methods, and the framework composes them.

### Common Local Gradients

Here are the backward rules for operations you will encounter constantly. Commit these to memory — they are the atomic instructions of back-propagation.

| Operation | Forward | Backward (given \(\bar{g} = \frac{\partial J}{\partial \text{out}}\)) |
|----------|---------|----------------------------------------------------------------------|
| **Add:** \(z = x + y\) | \(z = x + y\) | \(\frac{\partial J}{\partial x} = \bar{g}\), \(\frac{\partial J}{\partial y} = \bar{g}\) |
| **Multiply:** \(z = x \cdot y\) | \(z = x \cdot y\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot y\), \(\frac{\partial J}{\partial y} = \bar{g} \cdot x\) |
| **Square:** \(z = x^2\) | \(z = x^2\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot 2x\) |
| **Exponential:** \(z = e^x\) | \(z = e^x\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot e^x = \bar{g} \cdot z\) |
| **Log:** \(z = \ln x\) | \(z = \ln x\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot \frac{1}{x}\) |
| **ReLU:** \(z = \max(0, x)\) | \(z = \max(0, x)\) | \(\frac{\partial J}{\partial x} = \begin{cases} \bar{g} & \text{if } x > 0 \\ 0 & \text{otherwise} \end{cases}}\) |
| **Sigmoid:** \(z = \sigma(x)\) | \(z = \frac{1}{1+e^{-x}}\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot z(1-z)\) |

**Why the ReLU gradient is 0 when \(x \leq 0\):** A neuron that didn't fire contributed nothing to the output, so small changes to its input don't change the output at all. The gradient signal stops dead at that node. This is the "dying ReLU" phenomenon — and also the reason ReLU is cheap to compute gradients for.

### The Add and Multiply Rules: A Deeper Look

The add rule is a *gradient distributor*: it passes the incoming gradient unchanged to both inputs. If \(J\) changes by \(\bar{g}\) when \(z\) changes, and \(z = x + y\), then changing \(x\) alone by \(\epsilon\) changes \(z\) by \(\epsilon\), which changes \(J\) by \(\bar{g} \cdot \epsilon\). Same for \(y\).

The multiply rule is a *gradient switcher*: the gradient with respect to \(x\) is \(\bar{g} \cdot y\). This is the value of the *other* input. Why? Because \(z = x \cdot y\), so \(\frac{\partial z}{\partial x} = y\). The incoming gradient \(\bar{g}\) gets scaled by \(y\). This means if \(y\) is large, \(x\) gets a proportionally larger gradient — a small change in \(x\) is amplified by \(y\).

**A physical analogy:** Think of \(z = x \cdot y\) as the area of a rectangle with sides \(x\) and \(y\). If you increase \(x\) by \(\Delta x\), the area increases by \(y \cdot \Delta x\). The longer side \(y\) is, the more a small change in \(x\) affects the area. The multiply rule captures exactly this: the gradient on one factor is proportional to the other factor.

### Quick Check 4

*Question:* In the expression \(J = (a \cdot b) + c^2\), why is \(\frac{\partial J}{\partial a} = b\) and not something involving \(c\)?

*Answer:* Because \(a\) only affects \(J\) through the multiplication \(u_1 = a \cdot b\). The addition with \(u_2 = c^2\) is a separate path. The local derivative \(\frac{\partial u_1}{\partial a} = b\). The gradient from \(u_3\) flows through \(u_1\) but \(u_1\)'s local derivative with respect to \(a\) is \(b\), independent of \(c\). The paths are independent; the chain rule multiplies along each path, and the add node sums them — but here \(a\) only has one path.

---

## 5. The Back-Propagation Algorithm

### Pseudocode

**Algorithm: Back-Propagation**

**Input:** Computational graph with nodes \(u^{(1)}, \dots, u^{(n)}\) in topological order, root \(u^{(n)} = J\). All node values computed in forward pass and stored.

**Output:** \(\frac{\partial J}{\partial u^{(i)}}\) for all nodes.

```
# Initialize gradient table
grad[u^{(n)}] = 1  # base case

# Traverse in reverse topological order
for i = n-1 down to 1:
    grad[u^{(i)}] = 0
    for each child j of u^{(i)}:
        # grad[u^{(j)}] already computed (j > i in topological order)
        # local_grad(u^{(j)}, u^{(i)}) = ∂u^{(j)} / ∂u^{(i)}
        grad[u^{(i)}] += grad[u^{(j)}] * local_grad(u^{(j)}, u^{(i)})

return grad
```

**Key invariant:** When we process node \(u^{(i)}\), all its children have already been processed. This is guaranteed by the reverse topological order.

### Why This Works: The Dynamic Programming Perspective

Consider the naive approach: for each leaf parameter \(\theta\), trace all paths from \(\theta\) to \(J\), multiply derivatives along each path, and sum. The