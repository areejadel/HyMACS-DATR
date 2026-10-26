## 1. Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember:** State the central computational problem that backpropagation solves and why naive gradient computation fails.
2.  **Understand:** Explain how a computational graph represents a function and trace the flow of data in forward and backward passes.
3.  **Apply:** Compute gradients for a given scalar function and computational graph by hand, using the multivariate chain rule.
4.  **Analyze:** Deconstruct the backpropagation algorithm into its forward and backward passes, explaining the purpose of each and why intermediate values must be stored.
5.  **Create:** Diagnose and explain the cause of the vanishing gradient problem in a deep network and propose a potential mitigation.

---

## 2. The Problem That Backpropagation Solves

### 2.1 The Exponential Wall

Imagine you've just trained a neural network on a massive dataset. The training loop reports a loss, but now you need to update one million parameters. Each parameter demands its own partial derivative of the cost function \(J\). If you compute each derivative independently — tracing every path from that parameter to the output — the computation becomes intractable.

The number of computational paths from a parameter to the output grows exponentially with network depth. A network with \(n\) nodes per layer and \(L\) layers has on the order of \(n^{L-1}\) distinct paths. Computing each path's product independently means you repeat the same sub-chain products millions of times. This is the computational equivalent of recalculating \(3 \times 4\) every time you need it, instead of remembering the answer.

**The central tension:** We need one million derivatives, each a sum over potentially millions of paths. Yet training happens in minutes, not millennia. Something must give.

**Pause and predict:** Before reading further, can you think of any computational trick — from another domain you've studied — that avoids recomputing the same subproblem over and over? What would it require you to store? Hold that thought.

### 2.2 The Dynamic Programming Insight

Backpropagation resolves this tension by computing all one million derivatives in roughly the same time as *two* forward passes. It achieves this by recognizing that if two parameters share a subexpression, that subexpression's derivative is computed once and shared. This is dynamic programming applied to gradient computation — and it's the same algorithmic insight that makes sequence alignment algorithms in bioinformatics efficient. Just as the Smith-Waterman algorithm reuses subproblem scores to avoid re-enumerating all possible alignments, backpropagation reuses intermediate gradients to avoid re-enumerating all possible paths.

### 2.3 Beyond Neural Networks: A Universal Pattern

This idea extends far beyond neural networks. Consider ray tracing in computer graphics: when light bounces through a scene, computing the exact radiance at every surface point by tracing every photon path independently would be absurdly expensive. Instead, rendering engines use bidirectional path tracing and photon mapping — algorithms that cache and reuse intermediate radiance estimates at surface intersections. The photon map is, in essence, a forward-pass cache; the eye-path traversal that gathers from it is a backward pass. The same "compute once, reuse everywhere" pattern appears in probabilistic inference (belief propagation in graphical models), in optimal control (the adjoint method for trajectory optimization), and in computational finance (the Longstaff-Schwartz algorithm for pricing American options via backward induction). Backpropagation is not an isolated neural network trick — it is a specific instance of a general principle: when a cost function decomposes over a directed acyclic graph, gradients can be computed in time proportional to the number of edges, not the number of paths.

### 2.4 Test Yourself: The Path Explosion

Before reading further, estimate how many distinct paths exist from an input to the output in a fully-connected network with 3 hidden layers of 100 neurons each. Now imagine computing a derivative for each path independently.

<details>
<summary>Answer</summary>
Each layer has 100 neurons, and each neuron in layer \(k\) connects to all 100 neurons in layer \(k+1\). A path from an input neuron to the output neuron must choose one neuron in each hidden layer: \(100 \times 100 \times 100 = 10^6\) paths for a single parameter. With one million parameters, naive computation would trace \(10^{12}\) path-products, each repeating the same intermediate computations millions of times. Backpropagation collapses this to roughly \(2 \times 10^6\) operations.
</details>

---

## 3. The Computational Graph: A Map of Computation

### 3.1 What is a Computational Graph?

Before deriving the algorithm, we need a way to visualize the flow of computation. Any differentiable function can be represented as a **directed acyclic graph (DAG)**. Formally, a computational graph is a finite DAG \(G = (V, E)\) where:

- **Nodes** \(v \in V\) represent either variables (data, parameters, intermediate results) or operations (addition, multiplication, activation functions).
- **Edges** \(e = (u^{(i)}, u^{(j)}) \in E\) point from inputs to the operation that consumes them. An edge \(u^{(i)} \to u^{(j)}\) means \(u^{(i)}\) is an input to the operation computing \(u^{(j)}\).

The graph must be acyclic to ensure a well-defined topological ordering, which is required for both forward and backward passes.

**Concrete example:** The expression \(z = x \cdot y + b\) becomes:

```
x --→ [×] --→ v --→ [+] --→ z
y --→      b --→
```

Here \(v = x \cdot y\) is an intermediate variable (node). The operation nodes are \([\times]\) and \([+]\).

### 3.2 Why This Matters: A Sensitivity Map

The graph makes dependencies explicit. During backpropagation, we traverse this graph in reverse order. Every edge becomes a conduit for a gradient signal. Think of it as a plumbing system: during the forward pass, water flows from inputs to output. During the backward pass, we inject dye at the output and trace it backward through every pipe, measuring how much each upstream valve contributed to the final color.

This plumbing metaphor has a deeper implication. The computational graph is also a **sensitivity map**: it tells you not just what depends on what, but how perturbations propagate. If you perturb a leaf node by \(\epsilon\), the root changes by \(\frac{\partial J}{\partial u^{(i)}} \cdot \epsilon\). The graph encodes the entire first-order perturbation structure of your model. This perspective connects backpropagation to adjoint sensitivity analysis in differential equations, where the same reverse-accumulation pattern computes how a solution depends on initial conditions or parameters. In climate modeling, for instance, adjoint methods trace how a change in ocean temperature at one location affects global temperature decades later — by propagating sensitivities backward through the time-stepped simulation, exactly as backpropagation propagates gradients backward through layers. The computational graph is not just a debugging tool; it is the skeleton of your model's causal structure.

### 3.3 Key Terminology

- **Leaf nodes:** Nodes with no incoming edges (parameters, inputs). These are what we differentiate *with respect to*.
- **Root node:** The final scalar output (the cost \(J\)). This is where gradient computation *starts*.
- **Upstream gradient:** The gradient arriving at a node's output, already computed from nodes closer to the root.
- **Downstream gradient:** The gradient we send to that node's inputs, which we compute next.
- **Local Jacobian:** The derivative of an operation's output with respect to its inputs, evaluated at the stored forward-pass values.

### 3.4 Misconception Alert: It's Not Just an Abstraction

"The graph is just a theoretical abstraction." No. Modern frameworks (TensorFlow, PyTorch) literally build this graph in memory. When you call `.backward()` on a tensor, the framework traverses this graph. Understanding the graph means understanding what your framework does. It's not a metaphor — it's the actual data structure.

### 3.5 Test Yourself: Build a Graph

In the expression \(z = (x + y) \cdot \sigma(x)\), identify all nodes, edges, and the root node.

<details>
<summary>Answer</summary>
Nodes: \(x\), \(y\), \([+]\), \(v_1 = x+y\), \([\sigma]\), \(v_2 = \sigma(x)\), \([\times]\), \(z\). Root: \(z\). Leaf: \(x, y\). Edges: \(x \to [+]\), \(y \to [+]\), \(x \to [\sigma]\), \(v_1 \to [\times]\), \(v_2 \to [\times]\).
</details>

---

## 4. The Chain Rule: The Engine of Backpropagation

### 4.1 Intuition First: The Single Path

Imagine a cascade of gears. Turning the first gear by a small amount \(\Delta u^{(1)}\) causes the second gear to turn by \(\Delta u^{(2)}\). The ratio \(\frac{\Delta u^{(2)}}{\Delta u^{(1)}}\) is the sensitivity. If you have a long chain of gears, the total change in the final gear is the product of all the intermediate ratios.

Formally, for a single path \(u^{(1)} \to u^{(2)} \to \dots \to u^{(n)}\), the derivative of the end with respect to the beginning is the product of the step-by-step derivatives:

\[
\frac{\partial u^{(n)}}{\partial u^{(1)}} = \frac{\partial u^{(n)}}{\partial u^{(n-1)}} \cdot \frac{\partial u^{(n-1)}}{\partial u^{(n-2)}} \cdot \dots \cdot \frac{\partial u^{(2)}}{\partial u^{(1)}}
\]

Each factor represents a "sensitivity": a small change in \(u^{(1)}\) propagates through each step to produce a change in \(u^{(n)}\).

### 4.2 The Multivariate Chain Rule: Summing Over Paths

Now imagine a river delta where a single stream splits into multiple channels before merging again at the final output. A pollutant introduced upstream will reach the final output through *every* channel. The total impact is the sum of the impact through each path.

When a node \(u^{(i)}\) influences multiple downstream nodes \(u^{(j_1)}, u^{(j_2)}, \dots\), the total gradient sums over all paths. Let \(\text{children}(u^{(i)})\) denote the set of nodes \(u^{(j)}\) that directly consume \(u^{(i)}\) as input. The multivariate chain rule states:

\[
\frac{\partial J}{\partial u^{(i)}} = \sum_{u^{(j)} \in \text{children}(u^{(i)})} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**This is the single most important equation in backpropagation.** Let's parse it:

- \(\frac{\partial J}{\partial u^{(j)}}\) is the **upstream gradient**: the gradient of the final cost with respect to the output of operation \(j\). We already computed this because we are working backwards.
- \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\) is the **local Jacobian**: how much does this operation's output change when its \(i\)-th input changes? We compute this using the values stored during the forward pass.
- The product is the contribution of this one path. The sum collects contributions from all paths where \(u^{(i)}\) feeds into something.

Note that the summation is taken over all immediate consumers of \(u^{(i)}\), not over all paths. This is the critical observation: by summing over *edges* rather than *paths*, we avoid the exponential blowup. The recursive structure of the chain rule collapses the sum over exponentially many paths into a sum over polynomially many edges.

### 4.3 Worked Example: A Simple Multiplication Gate

Let's make this concrete. Let \(J = u^{(3)} = u^{(1)} \cdot u^{(2)}\), with \(u^{(1)} = 3\) and \(u^{(2)} = 4\). Then \(u^{(3)} = 12\). The operation is multiplication.

1.  **Upstream gradient:** \(\frac{\partial J}{\partial u^{(3)}} = 1\) (the gradient of the output with respect to itself).
2.  **Local Jacobian for \(u^{(1)}\):** \(\frac{\partial u^{(3)}}{\partial u^{(1)}} = u^{(2)} = 4\).
3.  **Local Jacobian for \(u^{(2)}\):** \(\frac{\partial u^{(3)}}{\partial u^{(2)}} = u^{(1)} = 3\).

Applying the multivariate chain rule:

\[
\frac{\partial J}{\partial u^{(1)}} = \frac{\partial J}{\partial u^{(3)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(1)}} = 1 \cdot 4 = 4
\]

\[
\frac{\partial J}{\partial u^{(2)}} = \frac{\partial J}{\partial u^{(3)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(2)}} = 1 \cdot 3 = 3
\]

**Notice:** The local Jacobian for multiplication uses the *other* input's value. For \(u^{(1)}\), we needed \(u^{(2)}\). This is why we stored all intermediate values during the forward pass. It's not a design choice — it's a mathematical necessity.

### 4.4 Test Yourself: The Necessity of Stored Values

What happens if you don't store \(u^{(2)}\) during the forward pass? Can you still compute \(\frac{\partial J}{\partial u^{(1)}}\) exactly?

<details>
<summary>Answer</summary>
No. The local Jacobian \(\frac{\partial u^{(3)}}{\partial u^{(1)}} = u^{(2)}\) requires the *runtime value* of \(u^{(2)}\), not its symbolic form. If \(u^{(2)}\) was itself computed from earlier inputs (e.g., \(u^{(2)} = \tanh(w)\)), you cannot reconstruct its value from the downstream gradient alone. This is why frameworks store the entire forward activations in memory — and why training large models demands so much GPU RAM.
</details>

### 4.5 Misconception Alert: Don't Forget the Sum

"The chain rule is just multiplying derivatives." For scalar-valued functions with multiple inputs, it is a *sum* over incoming paths, each being a *product*. Students often forget the sum when a variable feeds into multiple operations (e.g., skip connections in ResNets). The sum is not optional — it's the mathematical consequence of a variable influencing the output through multiple independent channels.

### 4.6 Test Yourself: A Variable with Two Paths

Suppose \(a = 2\), \(b = a^2\), \(c = a + b\), and \(J = c\). Compute \(\frac{\partial J}{\partial a}\).

<details>
<summary>Answer</summary>
\(a\) influences both \(b\) and \(c\). Path 1: \(a \to c\) directly, \(\frac{\partial c}{\partial a} = 1\). Path 2: \(a \to b \to c\), \(\frac{\partial c}{\partial b} \cdot \frac{\partial b}{\partial a} = 1 \cdot 2a = 4\). Sum: \(\frac{\partial J}{\partial a} = 1 + 4 = 5\). Check: \(c = a + a^2 = 2 + 4 = 6\), \(\frac{dc}{da} = 1 + 2a = 5\). Correct.
</details>

---

## 5. The Backpropagation Algorithm: Two Passes

### 5.1 Forward Pass: Compute and Store

**Purpose:** Compute the output of the network and store every intermediate value that will be needed during the backward pass.

The forward pass executes the computational graph in topological order: every node is computed only after all its inputs are available. For each operation, we:

1.  Receive input values from upstream nodes.
2.  Compute the output value.
3.  **Store** the output value (and often the input values themselves) in memory.
4.  Pass the output to downstream nodes.

**What gets stored and why:** For a multiplication node \(z = x \cdot y\), we need both \(x\) and \(y\) during the backward pass because \(\frac{\partial z}{\partial x} = y\) and \(\frac{\partial z}{\partial y} = x\). For a sigmoid node \(a = \sigma(z)\), we could store \(a\) and reconstruct \(\sigma'(z) = a(1-a)\) during the backward pass — but many implementations store \(z\) directly for numerical stability. The rule: store whatever the local Jacobian needs to evaluate.

**The memory cost:** This is the forward pass's hidden burden. Training a deep network means storing activations for every layer, for every sample in a minibatch. A ResNet-50 with a batch size of 32 stores tens of millions of floating-point numbers. This is why GPU memory is the bottleneck in deep learning, not compute speed. The forward pass is a strategic trade of memory for time, storing values now to avoid recomputing them later. This is the same space-time tradeoff that makes dynamic programming work — and it's why techniques like gradient checkpointing (which recomputes activations on-the-fly to save memory) exist.

### 5.2 Backward Pass: Propagate and Accumulate

**Purpose:** Compute \(\frac{\partial J}{\partial \text{every leaf node}}\) by traversing the graph in reverse topological order.

The backward pass starts at the root node (the cost \(J\)) with an upstream gradient of \(\frac{\partial J}{\partial J} = 1\). It then proceeds backward:

**Algorithm (per operation node):**

1.  Receive the upstream gradient \(\frac{\partial J}{\partial u^{(j)}}\) (the gradient of the cost with respect to *this* node's output).
2.  Retrieve the stored input values from the forward pass.
3.  Compute the local Jacobian: for each input \(u^{(i)}\), compute \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\).
4.  Multiply: \(\frac{\partial J}{\partial u^{(i)}} \leftarrow \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}\).
5.  If \(u^{(i)}\) has multiple outgoing edges, *add* this contribution to any previously computed gradient for \(u^{(i)}\).
6.  Pass the result downstream (toward the inputs).

**Why reverse topological order matters:** When we reach a node, we must already have computed the upstream gradient — the gradient of the cost with respect to *its* output. Reverse topological order guarantees this: we process nodes from output to input, so every node's consumers have already been processed.

**The dynamic programming insight:** Step 5 is where the magic happens. When a node \(u^{(i)}\) feeds into multiple operations, we don't recompute its gradient from scratch. We accumulate contributions as we visit each consumer. By the time we finish processing all consumers, \(\frac{\partial J}{\partial u^{(i)}}\) is complete — and we computed it exactly once. This is the "reuse" that collapses exponential time to linear time.

### 5.3 A Broader Framing: Credit Assignment

Economists and game theorists have long studied the problem of attributing a joint outcome to individual contributors. The Shapley value from cooperative game theory assigns credit to each player by averaging their marginal contribution over all possible coalitions. Backpropagation does something analogous but far more efficient: it assigns credit (gradient) to each parameter by computing its marginal contribution to the loss, but it exploits the DAG structure to avoid enumerating coalitions. The chain rule is, in this light, a closed-form solution to a structured credit assignment problem. Every edge in the computational graph defines a local contribution function; backpropagation aggregates them in a single reverse sweep. This reframing makes it clear why backpropagation fails for non-differentiable operations: without a local linear approximation, credit cannot be decomposed multiplicatively.

### 5.4 Worked Example: Tracing a Full Backward Pass

Let's trace the backward pass for \(z = (x + y) \cdot \sigma(x)\) with \(x=1, y=2\). Assume \(J=z\).

**Forward Pass:**
- \(v_1 = x+y = 3\)
- \(v_2 = \sigma(1) \approx 0.731\)
- \(z = 3 \cdot 0.731 = 2.193\)

**Try this yourself:** Before reading the backward pass below, grab a piece of paper or open a text editor. Sketch the computational graph for this expression. Then