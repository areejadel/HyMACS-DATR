## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** the two-pass structure of backpropagation (forward and backward) and the role of the computational graph.
2.  **Understand** why naive gradient computation is exponentially expensive and how dynamic programming resolves this.
3.  **Apply** the multivariate chain rule to compute gradients in simple branching computational graphs by summing over paths.
4.  **Analyze** a given computational graph to identify which intermediate values must be stored during the forward pass and why.
5.  **Create** a step-by-step backward pass for a small multi-operation network, correctly accumulating gradients at nodes with multiple outgoing edges.
6.  **Evaluate** the limitations of standard backpropagation and identify scenarios where alternative credit assignment methods are necessary.

---

## 1. Prerequisites

We assume familiarity with the following concepts:

- **Derivatives of basic functions:** \(\frac{d}{dx}(x^2) = 2x\), \(\frac{d}{dx}(e^x) = e^x\), \(\frac{d}{dx}(\ln x) = 1/x\).
- **The single-variable chain rule:** If \(y = f(u)\) and \(u = g(x)\), then \(\frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx}\).
- **Neural network basics:** A network maps an input \(\mathbf{x}\) to an output \(\hat{\mathbf{y}}\) through a series of layers, each applying a linear transformation followed by a nonlinear activation. The network has parameters—weights \(W\) and biases \(b\)—that are adjusted to minimize a scalar cost function \(J(W, b)\), such as the mean squared error \(J = \frac{1}{2}\|\hat{\mathbf{y}} - \mathbf{y}\|^2\) or cross-entropy.
- **Gradient descent:** To minimize \(J\), we repeatedly update each parameter \(\theta\) by taking a small step in the direction of the negative gradient: \(\theta \leftarrow \theta - \alpha \frac{\partial J}{\partial \theta}\), where \(\alpha\) is the learning rate.

If any of these concepts feel shaky, pause and review them. Backpropagation is simply an efficient algorithm for computing all those \(\frac{\partial J}{\partial \theta}\) terms.

**Quick self-check:** What is \(\frac{d}{dx}(\ln(x^2))\)? Compute it two ways: first by simplifying \(\ln(x^2) = 2\ln x\), then by applying the chain rule directly. Do you get the same answer?

<details>
<summary>Answer</summary>
Method 1: \(\frac{d}{dx}(2\ln x) = 2 \cdot \frac{1}{x} = \frac{2}{x}\).

Method 2: Let \(u = x^2\), so \(\frac{d}{dx}(\ln u) = \frac{1}{u} \cdot \frac{du}{dx} = \frac{1}{x^2} \cdot 2x = \frac{2}{x}\).

Both yield \(\frac{2}{x}\). The chain rule works.
</details>

---

## 2. The Problem That Backpropagation Solves

### 2.1 The Hook: A Billion-Dollar Algorithm Hiding in Plain Sight

In 1986, Rumelhart, Hinton, and Williams published a paper that resurrected neural networks from a decade of neglect. Their contribution wasn't a new architecture or activation function—it was an algorithm for computing gradients efficiently. Before this, training multi-layer networks was considered impractical. Afterward, it became merely slow. Today, the same algorithmic idea trains every large language model, every image generator, and every AlphaGo.

But here's what's rarely discussed: the core insight of backpropagation wasn't new in 1986. It had been independently discovered at least three times before—in control theory (1960s), in circuit sensitivity analysis (1970s), and in economics for computing derivatives of nested production functions. Each field thought they'd found something domain-specific. They hadn't. They'd all stumbled onto the same combinatorial structure: a function built from smaller functions, composed in layers, where the naive gradient computation explodes exponentially with depth.

The question that should be burning in your mind: **What makes this particular computation so universally hard, and what makes the efficient solution so universally applicable?**

### 2.2 When a Million Paths Isn't Enough

Let's make the problem concrete. Consider a neural network with \(L\) layers and parameters \(\theta = \{W^{[1]}, b^{[1]}, \dots, W^{[L]}, b^{[L]}\}\). To train the network with gradient descent, we need the partial derivative \(\frac{\partial J}{\partial \theta_i}\) for every parameter. A modern network can have billions of parameters.

Imagine a fully-connected network with an input layer, three hidden layers of 3 neurons each, and a single output neuron producing a scalar cost \(J\). Focus on one weight \(w\) connecting the input to the first hidden layer. How does a small change in \(w\) affect \(J\)?

A perturbation in \(w\) changes the activation of one neuron in hidden layer 1. That neuron connects to all 3 neurons in hidden layer 2. Each of those connects to all 3 neurons in hidden layer 3. And each of *those* connects to the output. The influence of \(w\) fans out through the network like ripples through a pond—except each ripple splits into more ripples at every step. To compute \(\frac{\partial J}{\partial w}\) exactly, we must sum the contribution over every possible path from \(w\) to \(J\).

In this tiny \(3 \times 3 \times 3\) network, the number of distinct paths from our weight to the output is \(3 \times 3 \times 3 = 27\). A naive approach would trace each path, multiply the derivatives along it, and sum the results. Manageable, but already tedious.

Now scale up: a network with 3 hidden layers of 100 neurons each. The number of paths from a single weight in layer 1 to the output is \(100 \times 100 \times 100 = 10^6\) — one million paths. For *one* weight. The input-to-first-hidden-layer weight matrix has \(d \times 100\) weights, where \(d\) is the input dimension. If \(d = 1000\), that's \(10^5\) weights, each requiring a sum over \(10^6\) paths. The naive approach would compute \(10^{11}\) path-products just for the first layer. The computational cost scales as \(O(n^L)\), where \(n\) is the layer width.

**Pause and absorb this:** The naive method isn't just slow — it's combinatorially impossible. For a network with 10 layers of 100 neurons each, you'd be summing over \(100^9 = 10^{18}\) paths per weight in the first layer. If each path-product took one nanosecond, computing the gradient for a single weight would take over 30 years. And you have millions of weights.

**Try this yourself:** Before reading the next section, look at that \(3 \times 3 \times 3\) network again. Do you see the redundancy? How many times does the naive method recompute the derivative of the path from hidden-layer-2-neuron-1 to the output? (Hint: every path from the input weight that passes through that neuron.)

<details>
<summary>Answer</summary>
Hidden-layer-2-neuron-1 connects to all 3 neurons in hidden layer 3, each of which connects to the output. So there are 3 distinct sub-paths from hidden-layer-2-neuron-1 to the output. But the naive method recomputes these 3 sub-paths for *every* incoming path to hidden-layer-2-neuron-1. Since 3 neurons in hidden layer 1 each connect to hidden-layer-2-neuron-1, those 3 sub-paths are recomputed 3 times. This redundancy compounds at every layer.
</details>

### 2.3 The Key Insight: Optimal Substructure

Notice the redundancy. The million paths from \(w\) to \(J\) share enormous overlap. All paths from a neuron in hidden layer 2 to the output are identical regardless of how we reached that neuron. Yet the naive method recomputes the same sub-path derivatives millions of times.

This is a classic case of **optimal substructure**: the gradient of the cost with respect to an intermediate node can be computed once and reused wherever that node influences the output. This is the principle behind dynamic programming—the same idea that makes Dijkstra's algorithm efficient, that lets sequence alignment run in quadratic instead of exponential time, and that powers the Viterbi algorithm for hidden Markov models.

**Think of it like GPS navigation computing traffic-aware routes.** A naive approach would enumerate every possible path from your location to the destination, compute each path's total travel time, and pick the minimum — impossible for a city with millions of intersections. Instead, navigation algorithms exploit optimal substructure: the fastest route from intersection A to the destination doesn't depend on how you reached A. Compute it once, cache it, and reuse it for every route that passes through A. Backpropagation does the same thing, but for gradient accumulation instead of travel times.

**A deeper connection — optimal control and the maximum principle.** Backpropagation is a special case of Pontryagin's maximum principle from control theory. In optimal control, you have a dynamical system evolving forward in time and a cost evaluated at the final state. To compute how initial conditions or control parameters affect the cost, you introduce *adjoint variables* (also called costates) that propagate backward in time, carrying sensitivity information. The adjoint equations are derived identically to the backpropagation rules. When you train a neural network, you're solving an optimal control problem where the layers are discrete time steps and the weights are control parameters. This connection, first noted by LeCun and others in the late 1980s, reveals that backpropagation is not a machine learning trick—it's a manifestation of a deep principle that appears whenever you optimize a process that unfolds over stages.

**A second cross-domain echo — automatic differentiation in scientific computing.** Climate models, aerodynamic simulations, and financial pricing models all require gradients of complex functions with respect to thousands of parameters. The algorithmic differentiation community independently developed forward-mode and reverse-mode differentiation—the latter being mathematically identical to backpropagation. Reverse-mode automatic differentiation computes the gradient of a scalar output with respect to all inputs in time proportional to the number of operations, exactly the property that makes backpropagation feasible. When you hear "backpropagation," think "reverse-mode automatic differentiation applied to neural networks."

**Backpropagation resolves the combinatorial explosion by computing all required derivatives in time proportional to the number of edges in the computational graph—roughly twice the cost of the forward pass.** Each edge is traversed exactly once during the backward pass. For our \(3 \times 100\) network, the number of edges is on the order of \(10^5\), not \(10^{11}\).

**Quick check:** In a fully-connected network with 2 hidden layers of 50 neurons each, approximately how many distinct paths exist from a weight in the first layer to the output? How many edges exist in the graph (assuming an input of size 100 and a single output)?

<details>
<summary>Answer</summary>
Paths from one weight in layer 1 to the output: \(50 \times 50 = 2500\) (choose one neuron in hidden layer 1, then one in hidden layer 2, then to output).

Edges: Input (100) → Hidden 1 (50): \(100 \times 50 = 5000\) edges. Hidden 1 → Hidden 2: \(50 \times 50 = 2500\) edges. Hidden 2 → Output: \(50 \times 1 = 50\) edges. Total edges ≈ 7550. Backpropagation does work proportional to 7550, not the millions of path-products a naive method would compute for all weights.
</details>

---

## 3. The Computational Graph

### 3.1 What Is a Computational Graph?

Before we can apply backpropagation, we need a structured way to represent the network's computations. Any differentiable function composed of elementary operations can be drawn as a **directed acyclic graph (DAG)**. This is not just a theoretical picture—it is the actual data structure that frameworks like PyTorch, TensorFlow, and JAX build in memory when you write code such as `z = x * y + b`.

- **Nodes** represent either *variables* (inputs, parameters, intermediate results) or *operations* (addition, multiplication, activation functions).
- **Edges** point from the output of one node to the input of another. An edge \(a \to b\) means "the value of \(a\) is used to compute the value of \(b\)."

**Concrete example:** The expression \(z = (x \cdot y) + b\) decomposes as:

```
x ──→ [×] ──→ v ──→ [+] ──→ z
y ──→                ↑
                     b
```

Here, \(v = x \cdot y\) is an intermediate variable node. The operation nodes \([\times]\) and \([+]\) tell us what computation was performed. The graph makes explicit that \(z\) depends on \(v\) and \(b\), while \(v\) depends on \(x\) and \(y\). During backpropagation, we traverse this graph backward, and every directed edge becomes a conduit for a gradient signal.

**Cross-domain insight — computational graphs as electrical circuits:** If you've studied circuit analysis, this structure should feel familiar. In a resistive network, you compute node voltages by propagating forward from sources. But to determine how a change in one resistor affects the voltage at a distant node, you can use *adjoint sensitivity analysis* — injecting a unit current at the measurement node and propagating backward through the circuit to compute sensitivities at every component. This is mathematically identical to backpropagation. The "upstream gradient" is the adjoint variable, and the "local Jacobian" is the branch constitutive relation. Electrical engineers have been doing backpropagation since the 1960s without calling it that. The circuit simulator SPICE, developed in 1973, uses adjoint methods for sensitivity analysis that are algorithmically equivalent to what we're about to derive.

### 3.2 Key Vocabulary

Let's name the parts of the graph so we can reason precisely:

- **Leaf nodes:** Nodes with no incoming edges—the parameters (weights, biases) and the input data. These are the variables we want gradients *with respect to*.
- **Root node:** The single scalar node representing the cost \(J\). Gradient computation starts here with \(\frac{\partial J}{\partial J} = 1\).
- **Upstream gradient:** The gradient of the cost with respect to a node's *output*. When we process a node during the backward pass, its upstream gradient has already been computed by nodes closer to the root.
- **Downstream gradient:** The gradient of the cost with respect to a node's *inputs*, which we are about to compute.
- **Local Jacobian:** The partial derivative of an operation's output with respect to its inputs, evaluated at the specific values seen during the forward pass. For a scalar operation \(z = f(x, y)\), the local Jacobian is the set \(\{\frac{\partial z}{\partial x}, \frac{\partial z}{\partial y}\}\).

**Misconception alert:** "The computational graph is just a conceptual aid for understanding backpropagation." This is false. When you run `z = x * y + b` in PyTorch with `requires_grad=True`, the framework constructs a graph object in memory, storing pointers to each operation's backward method and the input tensors. Calling `z.backward()` traverses this concrete graph. The graph *is* the mechanism, not a metaphor.

### 3.3 Why the Graph Structure Matters

Understanding the graph is essential for reasoning about gradient flow. Consider two common scenarios:

- **Branching:** A variable feeds into multiple operations. In the graph, this variable has multiple outgoing edges. During backpropagation, it will receive gradient contributions from *all* its consumers, and we must sum them.
- **Skip connections:** In a residual network, a tensor is passed through both a convolutional block and a direct identity connection. The graph has two parallel paths that reconverge at an addition node. The gradient with respect to the input tensor is the sum of the gradients through both paths.

**Try this yourself:** For the expression \(z = \sigma(w_1 x_1 + w_2 x_2) + (w_1 x_1)^2\), draw the computational graph. Identify all leaf nodes, the root node, and any variable with multiple outgoing edges.

<details>
<summary>Answer</summary>
Variable nodes: \(x_1, x_2, w_1, w_2\) (leaves); \(v_1 = w_1 x_1\); \(v_2 = w_2 x_2\); \(v_3 = v_1 + v_2\); \(v_4 = \sigma(v_3)\); \(v_5 = (v_1)^2\); \(z = v_4 + v_5\) (root).

Operation nodes: \([\times]\) for \(w_1 x_1\); \([\times]\) for \(w_2 x_2\); \([+]\) for \(v_1 + v_2\); \([\sigma]\); \([\text{square}]\); \([+]\) for \(v_4 + v_5\).

Variable with multiple outgoing edges: \(v_1\) feeds into both \(v_3\) (via the addition) and \(v_5\) (via the square). During the backward pass, \(\frac{\partial J}{\partial v_1}\) will receive two contributions that must be summed.
</details>

---

## 4. The Chain Rule on Computational Graphs

### 4.1 The Scalar Chain Rule (Single Path)

You already know this: if \(y = f(u)\) and \(u = g(x)\), then \(\frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx}\). For a longer chain \(u^{(1)} \to u^{(2)} \to \dots \to u^{(n)}\), the derivative is the product of intermediate derivatives:

\[
\frac{\partial u^{(n)}}{\partial u^{(1)}} = \frac{\partial u^{(n)}}{\partial u^{(n-1)}} \cdot \frac{\partial u^{(n-1)}}{\partial u^{(n-2)}} \cdot \dots \cdot \frac{\partial u^{(2)}}{\partial u^{(1)}}
\]

Each factor represents the sensitivity of one step to its input. A small perturbation \(\delta\) in \(u^{(1)}\) ripples through: it becomes \(\delta \cdot \frac{\partial u^{(2)}}{\partial u^{(1)}}\) at \(u^{(2)}\), then \(\delta \cdot \frac{\partial u^{(2)}}{\partial u^{(1)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(2)}}\) at \(u^{(3)}\), and so on.

**Worked example — a three-step chain:** Let \(u^{(1)} = x\), \(u^{(2)} = (u^{(1)})^2 = x^2\), \(u^{(3)} = \ln(u^{(2)}) = \ln(x^2)\), and \(J = u^{(3)}\). Compute \(\frac{\partial J}{\partial x}\) at \(x = 3\).

**Step 1: Forward pass.** \(u^{(1)} = 3\), \(u^{(2)} = 9\), \(u^{(3)} = \ln 9 \approx 2.197\).

**Step 2: Local Jacobians.** \(\frac{\partial u^{(2)}}{\partial u^{(1)}} = 2u^{(1)} = 6\). \(\frac{\partial u^{(3)}}{\partial u^{(2)}} = \frac{1}{u^{(2)}} = \frac{1}{9}\).

**Step 3: Chain them.** \(\frac{\partial J}{\partial x} = \frac{\partial u^{(3)}}{\partial u^{(2)}} \cdot \frac{\partial u^{(2)}}{\partial u^{(1)}} = \frac{1}{9} \cdot 6 = \frac{2}{3}\).

**Step 4: Verify.** \(J = \ln(x^2) = 2\ln x\), so \(\frac{\partial J}{\partial x} = \frac{2}{x}\). At \(x = 3\), this is \(\frac{2}{3}\). The chain rule product matches the direct derivative.

### 4.2 The Multivariate Chain Rule (Summing Over Paths)

Now the critical extension. In a neural network, a variable rarely influences the cost through a single path. Consider a variable \(u^{(i)}\) that feeds