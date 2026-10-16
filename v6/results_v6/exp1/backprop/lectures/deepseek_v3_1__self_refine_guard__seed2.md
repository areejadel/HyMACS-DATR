# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definition of a computational graph and identify nodes, edges, and the roles of forward and backward passes in gradient computation.
2. **Understand** why naive gradient computation is computationally prohibitive and how dynamic programming solves this efficiency problem.
3. **Apply** the back-propagation chain rule to compute gradients for any node in a computational graph, given its children’s gradients and local derivatives.
4. **Analyze** the memory–time trade-off in back-propagation and identify when recomputation strategies become necessary.
5. **Create** a complete backward pass for a two-layer multilayer perceptron, computing all parameter gradients from a given loss gradient.

---

## 1. Prerequisites and the Problem Setting

### The Three-Hour Problem

You’re training a neural network to distinguish cats from dogs. It has one million parameters. A single forward pass takes 10 milliseconds. To take one optimization step, you need the gradient—the direction to nudge every one of those million parameters to reduce the loss.

Your first instinct: for each parameter, tweak it slightly, run the full forward pass, and measure how much the loss changed. That’s one million tweaks × 10 ms each = 10,000 seconds. Nearly three hours. For one gradient step. Training would take years.

This isn’t a toy scenario. Before backpropagation was widely understood, researchers hit exactly this wall. The solution—computing all million gradients in roughly 20 milliseconds total—is what made deep learning computationally viable, not just theoretically interesting. That 500,000× speedup is the difference between a research curiosity and a technology that powers your phone’s face recognition.

Here’s the puzzle we’ll solve: how do you compute one million derivatives in the time it takes to do two forward passes? The answer reveals something deep about the structure of computation itself.

### Required Background

We assume familiarity with:

- **Matrix multiplication and broadcasting:** products \(\mathbf{A}\mathbf{B}\), transposes, and sums over rows or columns.
- **Partial derivatives and the chain rule:** for scalar functions, \(\frac{\partial}{\partial x} f(g(x)) = f'(g(x))\, g'(x)\). We extend this to vectors and matrices.
- **Feedforward neural network structure:** input \(\rightarrow\) hidden layers \(\rightarrow\) output \(\rightarrow\) loss.
- **Gradient-based optimization:** the update rule \(\boldsymbol{\theta} \leftarrow \boldsymbol{\theta} - \eta \nabla_{\boldsymbol{\theta}} J\).

Review these topics if needed—they form the foundation on which back-propagation is built.

### The Core Problem

Consider a feedforward network mapping input \(\mathbf{x} \in \mathbb{R}^d\) to prediction \(\hat{\mathbf{y}}\) through a sequence of layers. During supervised training, a scalar cost function \(J(\boldsymbol{\theta})\) measures the discrepancy between predictions and true labels \(\mathbf{y}\). The parameters \(\boldsymbol{\theta}\) include all weights and biases.

The learning task is to adjust \(\boldsymbol{\theta}\) to minimize \(J\). Gradient-based optimizers require \(\nabla_{\boldsymbol{\theta}} J\)—the vector of partial derivatives of \(J\) with respect to every parameter.

The challenge is that a modern network can have millions of parameters. Computing each partial derivative independently by traversing the entire network for each parameter would require millions of forward passes per gradient step—infeasible.

The insight: we can compute all gradients in roughly the same time as one forward pass plus one backward pass. This is back-propagation.

<div style="background-color: #f0f8ff; border-left: 4px solid #4682b4; padding: 10px; margin: 15px 0;">

**Quick Check 1**

*Question:* If a network has \(10^6\) parameters and a forward pass takes 10 ms, roughly how long would naive gradient computation take (computing each \(\partial J/\partial \theta_k\) by a separate forward-like traversal)?

<details>
<summary>Click for answer</summary>

On the order of \(10^6 \times 10\text{ ms} = 10{,}000\) seconds (≈ 3 hours) per gradient step. Back-propagation reduces this to roughly 20 ms (forward + backward).
</details>
</div>

---

## 2. Computational Graphs: The Universal Language

### Intuition: A Recipe, Not a Formula

Think of a neural network not as a fixed equation but as a *recipe*—a sequence of operations. Each operation takes some inputs and produces an output, and some outputs become inputs to later operations. We can draw this as a directed graph.

Here’s why this reframing matters: if you can write any computation as a graph, and you can figure out how to push gradients backward through any graph, you’ve solved gradient computation for every architecture—past, present, and future. Convnets, transformers, your own custom activation function—all become instances of the same algorithm.

**Example:** Consider the expression \(J = (a \cdot b) + c^2\). We decompose it into operations:

1. \(u_1 = a \cdot b\) (multiply)
2. \(u_2 = c^2\) (square)
3. \(u_3 = u_1 + u_2\) (add)
4. \(J = u_3\) (identity for the root)

The graph has nodes \(\{a, b, c, u_1, u_2, u_3, J\}\). Edges: \(a \to u_1\), \(b \to u_1\), \(c \to u_2\), \(u_1 \to u_3\), \(u_2 \to u_3\), \(u_3 \to J\). The leaf nodes are \(a, b, c\) (inputs or parameters). The root is \(J\).

### Formal Definition

A **computational graph** is a directed acyclic graph (DAG) where:

- **Nodes** represent operations (variables or functions).
- **Edges** represent data flow: an edge from \(u^{(i)}\) to \(u^{(j)}\) means \(u^{(i)}\) is an input to the operation that produces \(u^{(j)}\).

We number nodes \(u^{(1)}, u^{(2)}, \dots, u^{(n)}\) in topological order (every node appears after its inputs). The root is \(u^{(n)} = J\), the scalar cost.

Every neural network architecture—feedforward, convolutional, recurrent, transformer—can be expressed as a computational graph. By developing back-propagation on the *graph*, we obtain an algorithm that works for all architectures uniformly. This is the same insight that makes automatic differentiation frameworks like PyTorch and JAX architecture-agnostic: they trace the graph you construct and apply the same backward-pass algorithm.

<div style="background-color: #fff8dc; border-left: 4px solid #daa520; padding: 10px; margin: 15px 0;">

**Try this yourself:** Before continuing, sketch the computational graph for \(z = (x + y) \cdot \max(x, 0)\). Label each node with its operation. Notice how the \(\max\) operation introduces a branch—this will matter for gradients.

<details>
<summary>Click for solution</summary>

Nodes: \(x, y, u_1 = x + y, u_2 = \max(x, 0), z = u_1 \cdot u_2\).

Edges: \(x \to u_1\), \(y \to u_1\), \(x \to u_2\), \(u_1 \to z\), \(u_2 \to z\).

Node \(x\) feeds into two different operations (add and max). In the backward pass, \(x\) will receive gradient contributions from both paths.
</details>
</div>

### What We Want to Compute

For any node \(u^{(i)}\), we want:

\[
\frac{\partial J}{\partial u^{(i)}}
\]

This is the gradient of the final cost with respect to that node’s output. For parameter nodes (leaves), this is exactly the gradient needed for optimization. For intermediate nodes, these gradients are stepping stones to reach the parameters.

<div style="background-color: #f0f8ff; border-left: 4px solid #4682b4; padding: 10px; margin: 15px 0;">

**Quick Check 2**

*Question:* In the graph for \(J = (a \cdot b) + c^2\), list the children of node \(a\).

<details>
<summary>Click for answer</summary>

Node \(a\) has one child: \(u_1\) (the multiplication node), because \(a\) is an input to the operation that computes \(u_1\).
</details>
</div>

---

## 3. The Chain Rule Decomposition

### Intuition: Messages Flowing Backward

Imagine each node receives a “message” from the cost \(J\): “How much does \(J\) change when I change slightly?” The root \(J\) sends itself a message of 1 (changing \(J\) by \(\Delta\) changes \(J\) by exactly \(\Delta\)).

A node \(u^{(i)}\) computes its message by looking at all nodes that *directly* used \(u^{(i)}\)—its **children**. Each child \(u^{(j)}\) already has its message \(\frac{\partial J}{\partial u^{(j)}}\) and knows its *local* sensitivity to \(u^{(i)}\): the partial derivative \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\).

The total effect of \(u^{(i)}\) on \(J\) is the sum over all paths through its children:

\[
\text{message}(u^{(i)}) = \sum_{\text{children } j} \text{message}(u^{(j)}) \times (\text{local sensitivity of } u^{(j)} \text{ to } u^{(i)})
\]

This is exactly the multivariate chain rule.

The sum arises because \(u^{(i)}\) can influence \(J\) through multiple downstream paths. If \(u^{(i)}\) feeds into two different children that both eventually reach \(J\), a small change in \(u^{(i)}\) perturbs both paths simultaneously. The total effect is the sum of the individual path effects—the same principle as a river splitting into two tributaries: the total downstream flow is the sum of the flows in each branch.

**An analogy worth sitting with:** Imagine a city’s water distribution network. The forward pass is water flowing from reservoirs (inputs) through pipes (operations) to every neighborhood (outputs). Now imagine you want to know: if I increase pressure at a particular junction by 1 psi, how much does the total flow at the city’s edge change? The backward pass answers this by injecting a unit of "demand signal" at the output and letting it propagate backward through the same pipe network, splitting at every junction in reverse proportion to how the forward flow was routed. The same topology, traversed in reverse, answers a fundamentally different question. This is exactly what backpropagation does: the forward pass computes values; the backward pass computes *sensitivities* through the same graph structure.

### Formal Statement

Let node \(u^{(i)}\) have children \(\{u^{(j)} : j \in \text{children}(i)\}\)—the nodes whose computation directly depends on \(u^{(i)}\). Then:

\[
\frac{\partial J}{\partial u^{(i)}} = \sum_{j \in \text{children}(i)} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}. \tag{1}
\]

This is the **back-propagation rule**. It is recursive: to compute the gradient at a node, we need the gradients at its children. The recursion terminates at the root \(J\), where \(\frac{\partial J}{\partial J} = 1\) (base case).

<div style="background-color: #fff8dc; border-left: 4px solid #daa520; padding: 10px; margin: 15px 0;">

**Try this yourself:** Before reading the worked example, attempt to trace the backward pass for \(J = (a \cdot b) + c^2\) by hand. Start at \(J\) with gradient 1, then work backwards through each operation. Where do you get stuck?

<details>
<summary>Click for hint</summary>

Start at \(J\): its gradient w.r.t. itself is 1. The operation that produced \(J\) was \(u_3\) (identity), so the gradient flows to \(u_3\) unchanged. Then \(u_3 = u_1 + u_2\): the add operation distributes the gradient equally to both inputs. Now you have the gradient at \(u_1\) and \(u_2\). Continue upstream.
</details>
</div>

### Worked Example: A Tiny Graph

Apply (1) to \(J = (a \cdot b) + c^2\) with concrete numbers: \(a = 3, b = 4, c = 2\).

**Forward pass (compute and store all node values):**
- \(u_1 = a \cdot b = 3 \cdot 4 = 12\)
- \(u_2 = c^2 = 2^2 = 4\)
- \(u_3 = u_1 + u_2 = 12 + 4 = 16\)
- \(J = u_3 = 16\)

**Backward pass (reverse topological order: \(J, u_3, u_2, u_1, c, b, a\)):**

*Step 1: Root.* \(\frac{\partial J}{\partial J} = 1\).

*Step 2: Node \(u_3\).* Operation: \(J = u_3\) (identity). Local derivative \(\frac{\partial J}{\partial u_3} = 1\). Its child is \(J\). So:
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

**Interpretation:** \(\frac{\partial J}{\partial a} = 4\) means increasing \(a\) by \(\epsilon\) increases \(J\) by roughly \(4\epsilon\). Similarly, \(\frac{\partial J}{\partial b} = 3\) and \(\frac{\partial J}{\partial c} = 4\).

### Why This Is Dynamic Programming

We computed each node’s gradient exactly once, reusing previously computed gradients from its children. No redundant computation. This is dynamic programming: solve each subproblem once, store the result, and combine solutions from the leaves upward (here, from the root downward). The computational graph provides the dependency structure; the backward pass is the DP algorithm that exploits it.

**A cross-domain connection worth noticing:** The backward pass is essentially the Viterbi algorithm in reverse. In the Viterbi algorithm for hidden Markov models, you propagate probabilities forward through a trellis, then trace back the most likely path. In backpropagation, you propagate values forward, then trace back sensitivities. Both exploit the same insight: a global quantity (most likely path or total gradient) decomposes into local computations when you traverse the graph in the right order. This dynamic programming principle appears in speech recognition, genomics, and neural network training—apparently different domains united by directed acyclic computation graphs. If you’ve ever implemented Viterbi for a bioinformatics problem, you already understand the computational skeleton of backpropagation.

**A non-obvious framing:** Think of the backward pass not as "running the network in reverse" but as *solving a credit assignment problem on a dependency graph*. Each node asks: "Given how much I'm being blamed for the final error, how much should I blame each of my inputs?" The answer depends only on the local operation and the blame arriving from downstream. This modularity—each node solving its own local credit assignment problem—is why you can implement backpropagation by defining a backward method for each operation type and composing them. The graph handles the global routing; the nodes handle the local calculus.

<div style="background-color: #f0f8ff; border-left: 4px solid #4682b4; padding: 10px; margin: 15px 0;">

**Quick Check 3**

*Question:* Why is the backward pass more efficient than computing each \(\partial J/\partial \theta_k\) independently from the forward graph?

<details>
<summary>Click for answer</summary>

Each independent computation would re-traverse shared sub-paths from \(\theta_k\) to \(J\). The backward pass computes the gradient at each intermediate node once and reuses it for all upstream nodes that depend on it—classic dynamic programming memoization.
</details>
</div>

<div style="background-color: #ffe4e1; border-left: 4px solid #dc143c; padding: 10px; margin: 15px 0;">

**Common Misconception #1**

*Misconception:* “The backward pass computes gradients by running the network in reverse—feeding the output back through the layers.”

*Reality:* The backward pass does **not** feed data backward through the network. It computes *derivatives* using the chain rule, multiplying local Jacobians with upstream gradients. The activations from the forward pass are reused (not recomputed) during this process. The direction is reversed in the *computation graph*, not in the *data flow*.
</div>

---

## 4. Local Gradients: The Building Blocks

### The Key Abstraction

Every node in the computational graph is a function. To implement back-propagation for any architecture, we only need to know two things about each node type:

1. **Forward:** Given inputs, compute the output.
2. **Backward:** Given the gradient of the loss with respect to the *output* (\(\frac{\partial J}{\partial \text{out}}\)), compute the gradient with respect to each *input*.

The backward computation uses only the node’s local derivative and the incoming gradient from above. It does not need to know anything about the rest of the graph. This modularity makes automatic differentiation frameworks (PyTorch, TensorFlow, JAX) possible: each operation defines its own `forward` and `backward` methods, and the framework composes them.

**A non-obvious framing:** Think of each operation’s backward method as a **miniature tax accountant**. The upstream gradient is the total tax liability that has arrived at this node from downstream. The node’s job is to distribute that tax liability