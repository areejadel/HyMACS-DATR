# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the two-phase structure of training: the forward pass computes and stores intermediate values; the backward pass computes gradients.
2. **Understand** why naive gradient computation is exponentially expensive and how dynamic programming eliminates this redundancy via reverse topological ordering.
3. **Apply** the backpropagation algorithm by hand to a two-layer neural network, computing every partial derivative step-by-step for a given minibatch.
4. **Analyze** a computational graph to identify which intermediate results must be stored during the forward pass and why each is necessary for the backward pass.
5. **Create** the backward pass for a novel operation (e.g., batch normalization) by deriving its local Jacobian and integrating it into the gradient flow.

---

## 1. The Problem That Backpropagation Solves

**Opening challenge:** You have a neural network with 60 million parameters. You need to compute the derivative of the loss with respect to every single one. The naive approach — tracing every path from each parameter to the output — would take longer than the age of the universe. Yet AlexNet did exactly this computation in six days in 2012. How?

In 2012, AlexNet stunned the computer vision community by winning the ImageNet challenge with a network containing 60 million parameters. Training took six days on two GPUs. But here is what nobody discusses: if the researchers had computed each parameter’s gradient independently—tracing every path from that parameter to the output—those six days would have become longer than the age of the universe.

Why? Because the number of computational paths from a parameter to the output grows exponentially with network depth. A network with \(n\) nodes per layer and \(L\) layers has on the order of \(n^{L-1}\) distinct paths. Computing each path's product independently means repeating the same sub-chain products millions of times. This is the computational equivalent of recalculating \(3 \times 4\) every time you need it, instead of remembering the answer.

**Pause and predict:** Before reading the solution, take 30 seconds to guess how you might avoid this explosion. What principle could reduce computing millions of overlapping paths to something manageable? Write down your intuition — we’ll check it against the actual algorithm.

**The central tension:** We need one million derivatives, each a sum over potentially millions of paths. Yet training happens in minutes, not millennia. Something must give.

Backpropagation resolves this tension by computing all one million derivatives in roughly the same time as *two* forward passes. It achieves this by recognizing that if two parameters share a subexpression, that subexpression's derivative is computed once and shared. This is dynamic programming applied to gradient computation — and it is the same algorithmic insight that makes sequence alignment algorithms in bioinformatics efficient. Just as the Smith-Waterman algorithm reuses subproblem scores to avoid re-enumerating all possible alignments, backpropagation reuses intermediate gradients to avoid re-enumerating all possible paths.

**Real-world case study:** Consider Google’s 2017 Transformer model for machine translation. The original "Attention Is All You Need" paper trained a model with 65 million parameters on 4.5 million sentence pairs. Training took 3.5 days on 8 GPUs. Let us break down what backpropagation made possible: each training step required computing gradients for all 65 million parameters. If each gradient required tracing through the model's 6 encoder and 6 decoder layers independently, with each attention head creating a fan-out of paths, the computation would have required approximately \(10^{18}\) operations per training step. At 3.5 teraflops per GPU, that is roughly 100 years per step. Backpropagation reduced this to roughly \(10^9\) operations — a billion-fold speedup. This is not merely clever optimization; it is what made the entire deep learning revolution computationally feasible.

**Try this yourself:** Before reading further, estimate how many distinct paths exist from an input to the output in a fully-connected network with 3 hidden layers of 100 neurons each. Now imagine computing a derivative for each path independently.

<details>
<summary>Answer</summary>
Each layer has 100 neurons, and each neuron in layer \(k\) connects to all 100 neurons in layer \(k+1\). A path from an input neuron to the output neuron must choose one neuron in each hidden layer: \(100 \times 100 \times 100 = 10^6\) paths for a single parameter. With one million parameters, naive computation would trace \(10^{12}\) path-products, each repeating the same intermediate computations millions of times. Backpropagation collapses this to roughly \(2 \times 10^6\) operations.
</details>

**Summary:** The exponential path explosion makes naive gradient computation infeasible for any practical network. Backpropagation eliminates this redundancy through dynamic programming, reducing the cost to approximately two forward passes. This efficiency is not an optimization detail — it is the enabling condition for modern deep learning.

---

## 2. The Computational Graph

Having established why backpropagation is necessary, we now introduce the data structure that makes it possible. Any differentiable function can be represented as a **directed acyclic graph (DAG)**:

- **Nodes** represent either variables (data, parameters, intermediate results) or operations (addition, multiplication, activation functions).
- **Edges** point from inputs to the operation that consumes them. An edge \(u^{(i)} \to u^{(j)}\) means \(u^{(i)}\) is an input to the operation computing \(u^{(j)}\).

**Concrete example:** The expression \(z = x \cdot y + b\) becomes:

```
x --→ [×] --→ v --→ [+] --→ z
y --→      b --→
```

Here \(v = x \cdot y\) is an intermediate variable (node). The operation nodes are \([\times]\) and \([+]\).

**Why this matters:** The graph makes dependencies explicit. During backpropagation, we traverse this graph in reverse order. Every edge becomes a conduit for a gradient signal. Think of it as a plumbing system: during the forward pass, water flows from inputs to output. During the backward pass, we inject dye at the output and trace it backward through every pipe, measuring how much each upstream valve contributed to the final color.

**Analogy check:** In a real plumbing system, if you inject dye at the output, does it travel backward against the water flow? No — this is where the analogy deliberately breaks. The backward pass doesn’t reverse physical flow; it reverses *responsibility*. It asks: “Output changed by \(\epsilon\). Which upstream changes would have caused this?” The dye metaphor captures the tracing of contributions, not literal reverse flow. Keep this distinction as we proceed.

**Case study: PyTorch's dynamic graph.** Unlike static frameworks that build the entire graph before execution, PyTorch constructs the computational graph on-the-fly as operations execute. When you write `y = x * 2 + 3`, PyTorch does not just compute the result — it simultaneously builds a graph recording that `y` depends on `x` through a multiplication and addition. This is why you can use Python control flow (if statements, for loops) in your models and backpropagation still works: each forward pass dynamically creates a new graph matching exactly the operations that executed. When you call `y.backward()`, PyTorch traverses this graph in reverse, applying the chain rule at each node. Understanding the graph means understanding what your framework does. It is not a metaphor — it is the actual data structure stored in memory.

**Key terminology:**
- **Leaf nodes:** Nodes with no incoming edges (parameters, inputs). These are what we differentiate *with respect to*.
- **Root node:** The final scalar output (the cost \(J\)). This is where gradient computation *starts*.
- **Upstream gradient:** The gradient arriving at a node's output, already computed from nodes closer to the root.
- **Downstream gradient:** The gradient we send to that node's inputs, which we compute next.
- **Local Jacobian:** The derivative of an operation's output with respect to its inputs, evaluated at the stored forward-pass values.

**Quick check:** In the expression \(z = (x + y) \cdot \sigma(x)\), identify all nodes, edges, and the root node.

<details>
<summary>Answer</summary>
Nodes: \(x\), \(y\), \([+]\), \(v_1 = x+y\), \([\sigma]\), \(v_2 = \sigma(x)\), \([\times]\), \(z\). Root: \(z\). Leaf: \(x, y\). Edges: \(x \to [+]\), \(y \to [+]\), \(x \to [\sigma]\), \(v_1 \to [\times]\), \(v_2 \to [\times]\).
</details>

**Summary:** The computational graph is the central data structure for backpropagation. It records dependencies as a DAG, enabling systematic reverse traversal. Every framework — PyTorch, TensorFlow, JAX — builds some variant of this graph, whether statically or dynamically.

---

## 3. The Chain Rule: From Single Paths to Multiple Inputs

With the graph defined, we now derive the mathematical engine of backpropagation: the chain rule in its single-path and multivariate forms.

### 3.1 Single Path: The Basic Chain Rule

For a single path \(u^{(1)} \to u^{(2)} \to \dots \to u^{(n)}\), the derivative of the end with respect to the beginning is the product of the step-by-step derivatives:

\[
\frac{\partial u^{(n)}}{\partial u^{(1)}} = \frac{\partial u^{(n)}}{\partial u^{(n-1)}} \cdot \frac{\partial u^{(n-1)}}{\partial u^{(n-2)}} \cdot \dots \cdot \frac{\partial u^{(2)}}{\partial u^{(1)}}
\]

**Intuition:** Each factor represents a "sensitivity": how much does \(u^{(k)}\) change when \(u^{(k-1)}\) changes by a tiny amount? The product chains these sensitivities: a small change in \(u^{(1)}\) propagates through each step to produce a change in \(u^{(n)}\). This is like a cascade of gears: each gear ratio multiplies the effect of turning the first gear, and the total effect is the product of all ratios.

### 3.2 Multiple Paths: The Multivariate Chain Rule

When a node \(u^{(i)}\) influences multiple downstream nodes \(u^{(j_1)}, u^{(j_2)}, \dots\), the total gradient sums over all paths:

\[
\frac{\partial J}{\partial u^{(i)}} = \sum_{j: u^{(i)} \text{ is input to } u^{(j)}} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**This is the single most important equation in backpropagation.** Let us parse it:

- \(\frac{\partial J}{\partial u^{(j)}}\) is the **upstream gradient**: the gradient of the final cost with respect to the output of operation \(j\). We already computed this because we are working backwards.
- \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\) is the **local Jacobian**: how much does this operation's output change when its \(i\)-th input changes? We compute this using the values stored during the forward pass.
- The product is the contribution of this one path. The sum collects contributions from all paths where \(u^{(i)}\) feeds into something.

**Worked example:** Let \(J = u^{(3)} = u^{(1)} \cdot u^{(2)}\), with \(u^{(1)} = 3\) and \(u^{(2)} = 4\). Then \(u^{(3)} = 12\). The operation is multiplication.

- \(\frac{\partial J}{\partial u^{(3)}} = 1\) (the gradient of the output with respect to itself).
- \(\frac{\partial u^{(3)}}{\partial u^{(1)}} = u^{(2)} = 4\) (local Jacobian for first input).
- \(\frac{\partial u^{(3)}}{\partial u^{(2)}} = u^{(1)} = 3\) (local Jacobian for second input).

Applying the multivariate chain rule:

\[
\frac{\partial J}{\partial u^{(1)}} = \frac{\partial J}{\partial u^{(3)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(1)}} = 1 \cdot 4 = 4
\]

\[
\frac{\partial J}{\partial u^{(2)}} = \frac{\partial J}{\partial u^{(3)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(2)}} = 1 \cdot 3 = 3
\]

**Notice:** The local Jacobian for multiplication uses the *other* input's value. For \(u^{(1)}\), we needed \(u^{(2)}\). This is why we stored all intermediate values during the forward pass. It is not a design choice — it is a mathematical necessity. The gradient of multiplication with respect to one input *is* the other input. Without storing that value, backpropagation would be blind.

**Try this yourself:** What happens if you do not store \(u^{(2)}\) during the forward pass? Can you still compute \(\frac{\partial J}{\partial u^{(1)}}\) exactly?

<details>
<summary>Answer</summary>
No. The local Jacobian \(\frac{\partial u^{(3)}}{\partial u^{(1)}} = u^{(2)}\) requires the *runtime value* of \(u^{(2)}\), not its symbolic form. If \(u^{(2)}\) was itself computed from earlier inputs (e.g., \(u^{(2)} = \tanh(w)\)), you cannot reconstruct its value from the downstream gradient alone. This is why frameworks store the entire forward activations in memory — and why training large models demands so much GPU RAM.
</details>

**Misconception alert:** "The chain rule is just multiplying derivatives." For scalar-valued functions with multiple inputs, it is a *sum* over incoming paths, each being a *product*. Students often forget the sum when a variable feeds into multiple operations (e.g., skip connections in ResNets). The sum is not optional — it is the mathematical consequence of a variable influencing the output through multiple independent channels.

**Real-world case study: ResNet's skip connections.** The ResNet architecture — which won the 2015 ImageNet competition and enabled training of networks over 100 layers deep — relies fundamentally on the summing behavior you just learned. A ResNet block computes `output = F(x) + x`, where `F(x)` is a small subnetwork and `x` is the original input passed through a skip connection. During backpropagation, `x` receives gradient from two paths: through `F(x)` and directly from the output. The sum ensures that even if the gradient through `F(x)` becomes vanishingly small (the notorious vanishing gradient problem), the direct path still delivers gradient signal. Without this sum — without the multivariate chain rule working correctly — deep networks would be untrainable. The entire field of deep learning beyond 20 layers exists because backpropagation correctly sums gradient contributions.

**Quick check:** Suppose \(a = 2\), \(b = a^2\), \(c = a + b\), and \(J = c\). Compute \(\frac{\partial J}{\partial a}\).

<details>
<summary>Answer</summary>
\(a\) influences both \(b\) and \(c\). Path 1: \(a \to c\) directly, \(\frac{\partial c}{\partial a} = 1\). Path 2: \(a \to b \to c\), \(\frac{\partial c}{\partial b} \cdot \frac{\partial b}{\partial a} = 1 \cdot 2a = 4\). Sum: \(\frac{\partial J}{\partial a} = 1 + 4 = 5\). Check: \(c = a + a^2 = 2 + 4 = 6\), \(\frac{dc}{da} = 1 + 2a = 5\). Correct.
</details>

**Summary:** The chain rule is the mathematical foundation of backpropagation. For a single path, derivatives multiply. For multiple paths, contributions sum. This sum — often overlooked — is what enables architectures like ResNet to train effectively at extreme depths.

---

## 4. The Backpropagation Algorithm: Two Passes

Equipped with the chain rule and the computational graph, we now assemble the full backpropagation algorithm. It consists of two passes: a forward pass that computes and stores, and a backward pass that differentiates and accumulates.

### 4.1 Forward Pass

**Purpose:** Compute the output of the network and store every intermediate value that will be needed during the backward pass.

The forward pass executes the computational graph in topological order: every node is computed only after all its inputs are available. For each operation, we:

1. Receive input values from upstream nodes.
2. Compute the output value.
3. **Store** the output value (and often the input values themselves) in memory.
4. Pass the output to downstream nodes.

**What gets stored and why:** For a multiplication node \(z = x \cdot y\), we need both \(x\) and \(y\) during the backward pass because \(\frac{\partial z}{\partial x} = y\) and \(\frac{\partial z}{\partial y} = x\). For a sigmoid node \(a = \sigma(z)\), we could store \(a\) and reconstruct \(\sigma'(z) = a(1-a)\) during the backward pass — but many implementations store \(z\) directly for numerical stability. The rule: store whatever the local Jacobian needs to evaluate.

**The memory cost:** This is the forward pass's hidden burden. Training a deep network means storing activations for every layer, for every sample in a minibatch. A ResNet-50 with a batch size of 32 stores tens of millions of floating-point numbers. This is why GPU memory is the bottleneck in deep learning, not compute speed. The forward pass is a kind of strategic hoarding: we trade memory for time, storing values now to avoid recomputing them later. This is the same space-time tradeoff that makes dynamic programming work — and it is why techniques like gradient checkpointing (which recomputes activations on-the-fly to save memory) exist.

**Case study: GPT-3's memory requirements.** When OpenAI trained GPT-3 with 175 billion parameters, the forward pass activations alone required approximately 2.5 terabytes of memory for a batch size of 32 with sequence length 2048. This is why the model was trained across hundreds of GPUs — not because the computation was too slow on a single machine, but because the memory required to store forward pass values would not fit. Each GPU stored only a slice of the activations, and the backpropagation had to coordinate gradient flow across machines. The forward pass's "store everything" strategy is the primary reason large language model training requires distributed systems.

### 4.2 Backward Pass

**Purpose:** Compute \(\frac{\partial J}{\partial \text{every leaf node}}\) by traversing the graph in reverse topological order.

The backward pass starts at the root node (the cost \(J\)) with an upstream gradient of \(\frac{\partial J}{\partial J} = 1\). It then proceeds backward:

**Algorithm (per operation node):**

1. Receive the upstream gradient \(\frac{\partial J}{\partial u^{(j)}}\) (the gradient of the cost with respect to *this* node's output).
2. Retrieve the stored input values from the forward pass.
3. Compute the local Jacobian: for each input \(u^{(i)}\), compute \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\).
4. Multiply: \(\frac{\partial J}{\partial u^{(i)}} \leftarrow \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}\).
5. If \(u^{(i)}\) has multiple outgoing edges, *add* this contribution to any previously computed gradient for \(u^{(i)}\).
6. Pass the result downstream (toward the inputs).

**Why reverse topological order matters:** When we reach a node, we must already have computed the upstream gradient — the gradient of the cost with respect to *its* output. Reverse topological order guarantees this: we process nodes from output to input, so every node's consumers have already been processed.

**The dynamic programming insight:** Step 5 is where the magic happens. When a node \(u^{(i)}\) feeds into multiple operations, we do not recompute its gradient from scratch. We accumulate contributions as we visit each consumer. By the time we finish processing all consumers, \(\frac{\partial J}{\partial u^{(i)}}\) is complete — and we computed it exactly once. This is the "reuse" that collapses exponential time to linear time.

**Try this yourself:** Trace the backward pass for \(z = (x + y) \cdot \sigma(x)\) with \(x=1, y=2\). Compute all