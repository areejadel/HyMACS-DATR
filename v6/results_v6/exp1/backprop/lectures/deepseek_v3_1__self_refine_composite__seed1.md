### Learning Objectives

By the end of this lecture, you will be able to:
1.  **Remember:** State the central computational problem that backpropagation solves and identify its algorithmic classification (dynamic programming).
2.  **Understand:** Explain why a naive gradient computation is intractable for deep networks and how backpropagation reduces the cost to the scale of a forward pass.
3.  **Apply:** Construct a computational graph for a given arithmetic expression and manually execute its forward and backward passes to compute gradients.
4.  **Analyze:** Derive the gradient update rules for a two-layer neural network with a non-linear activation and a mean squared error loss.
5.  **Create:** Given a novel network architecture (e.g., one with a skip connection), determine the correct gradient accumulation step in the backward pass.

---

### 1. Prerequisites: What You Need to Know

We assume a working knowledge of three concepts. A brief refresher is provided below.

*   **Derivatives as Slopes:** The derivative \( f'(x) \) measures how much the output of a function \( f \) changes in response to a tiny nudge in its input \( x \). For \( f(x) = x^2 \), \( f'(x) = 2x \). If \( x = 3 \), a tiny change of \( \Delta x \) causes an output change of approximately \( 6 \cdot \Delta x \).
*   **Gradient:** For a function with multiple inputs, such as \( f(x, y) \), the gradient is a vector of partial derivatives, \( \nabla f = [\partial f / \partial x, \partial f / \partial y] \). Each component indicates the function's sensitivity to one input, treating the others as constant.
*   **The Chain Rule:** If a variable’s influence flows through a chain of functions, the total derivative is the product of the local derivatives. If \( a \) affects \( b \), and \( b \) affects \( c \), then \( \frac{dc}{da} = \frac{dc}{db} \cdot \frac{db}{da} \).

---

### 2. The Problem: A Million-Knob Machine

**Learning Objective:** Understand the intractability of naive gradient computation and the core algorithmic insight of backpropagation.

Imagine you're tuning an old analog radio with a million dials, each one interacting with the others in complex ways. Your goal: adjust every dial to get the clearest signal. This is training a neural network. The "signal" is the network's error, \( J(\theta) \), on a task like recognizing handwritten digits, and the "dials" are its parameters, \( \theta \). To improve, you need to know which way to turn each dial—you need the gradient \( \partial J / \partial \theta_i \) for every parameter \( \theta_i \).

Consider a seemingly modest network: 3 hidden layers, 100 neurons each. Its parameters number in the millions. Here’s the core tension: **how do you assign credit to a single dial in the first layer for the final output error, when its signal is scrambled by a million others?**

#### The Intuitive (and Terrible) Approach: Tracing Every Path
Let us try to compute the gradient for a single weight in the first layer. Its influence flows forward: it affects a neuron in layer 1, which affects all 100 neurons in layer 2, which affects all 100 in layer 3, and finally the output.
*   From an input to the first hidden layer: 100 possible paths (one per neuron).
*   From the first hidden layer to the second: \( 100 \times 100 = 10,000 \) paths.
*   From the second to the third: \( 100 \times 100 \times 100 = 1,000,000 \) paths.

For just *one* parameter in the first layer, its tiny change ripples to the output through one million distinct paths. The chain rule tells us to sum the derivative along each path, and each path's derivative is a long product of local derivatives. Now, multiply this work by a million parameters. We would be computing and summing an astronomically large number of path-products. Worse, we would recompute the exact same sub-products millions of times. This approach is computationally intractable.

**Try this yourself:** For a 4-layer network (100 neurons each), how many paths would exist from a single first-layer weight to the output? The answer reveals why even slightly deeper networks were untrainable before backpropagation.

#### The Insight: Dynamic Programming
This is where the puzzle cracks. Backpropagation is not just a clever trick; it's an application of a classic algorithm design principle: dynamic programming. It recognizes that **shared sub-computations should be computed once and reused.** Instead of tracing millions of long, overlapping paths from the start, we compute gradients locally, layer by layer, from the output back to the input. Think of it as an efficient audit: you don't trace every dollar from a million bank accounts back to a single fraudulent transaction. You start at the fraud and work backward through the accounts, noting the percentage of blame each step of the way.

**Quantifying the Improvement:** For our 3-layer, 100-neuron network, the naive method traces roughly \( 10^{12} \) path-products. Backpropagation collapses this to approximately \( 2 \times 10^6 \) operations—a reduction by a factor of one million. This is the difference between a computation that takes until the heat death of the universe and one that finishes before your coffee gets cold.

---

### 3. The Computational Graph: Our Map for the Journey

**Learning Objective:** Construct a computational graph for a given function and identify its key components.

Before we can run the algorithm, we need a map of the computation. Any mathematical formula can be drawn as a **directed acyclic graph (DAG)**. Deep learning frameworks like PyTorch and TensorFlow literally build this graph in memory when you write code. Calling `.backward()` on a final value triggers a traversal of this graph. It's the scaffolding that makes the "automatic" in automatic differentiation.

Let us build a graph for a simple expression: \( z = (x \cdot y) + b \).

*   **Nodes** represent values (variables) or actions (operations).
*   **Edges** (arrows) represent the flow of data from inputs to the operation that consumes them.

The graph looks like this:
```
x --→ [×] --→ v --→ [+] --→ z
y --→      b --→
```
Here, \( x, y, b \) are input variable nodes. \( [\times] \) and \( [+] \) are operation nodes. \( v = x \cdot y \) is an intermediate variable node created by the multiplication, which then feeds into the addition. The final output is \( z \).

**Key Terminology:**
*   **Leaf Nodes:** Nodes with no incoming edges. These are our parameters and inputs—the targets for which we want gradients.
*   **Root Node:** The final scalar output, usually the cost \( J \). Our gradient computation starts here.
*   **Upstream Gradient:** The gradient of the root with respect to a node's output. This arrives from nodes "closer" to the root.
*   **Downstream Gradient:** The gradient we compute for a node's inputs and pass "backward."
*   **Local Jacobian:** The derivative of an operation's output with respect to its inputs, evaluated at the values stored during the forward pass.

**Quick Check:** Draw the computational graph for \( z = (x + y) \cdot \sigma(x) \). Identify the leaf nodes, the root node, and all intermediate variable nodes.
*   *Solution:* The leaves are \( x \) and \( y \). The root is \( z \). The intermediate variables are \( v_1 = x+y \) and \( v_2 = \sigma(x) \). The operations are \( [+] \), \( [\sigma] \), and \( [\times] \).

---

### 4. The Chain Rule: The Engine of Backpropagation

**Learning Objective:** Apply the multivariate chain rule to compute the total derivative of a scalar output with respect to a variable that influences it through multiple paths.

#### 4.1 Intuition: A Single Path
If a tiny change in \( a \) causes a change in \( b \), which causes a change in our cost \( J \), the total effect is the product of the individual effects: \( \frac{dJ}{da} = \frac{dJ}{db} \cdot \frac{db}{da} \). This is the basic chain rule.

#### 4.2 The Critical Case: Multiple Paths
A single variable can influence the final cost through multiple downstream operations. This is the norm, not the exception. The **multivariate chain rule** captures this perfectly:

\[
\frac{\partial J}{\partial u^{(i)}} = \sum_{j: u^{(i)} \text{ is input to } u^{(j)}} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

This is the most important equation in the lecture. It states: "The gradient of the cost with respect to my node is the sum, over every operation that uses my node as input, of (the gradient of the cost with respect to that operation's output) times (that operation's local derivative with respect to my node)."

**Worked Example: A Single Multiplication**
Suppose our cost is simply the output of a multiplication: \( J = u^{(3)} = u^{(1)} \cdot u^{(2)} \). Let \( u^{(1)} = 3 \) and \( u^{(2)} = 4 \).

1.  **Forward Pass:** \( J = 3 \cdot 4 = 12 \).
2.  **Local Jacobians:** For the multiplication operation \( [\times] \):
    *   The derivative with respect to its first input is the second input: \( \frac{\partial u^{(3)}}{\partial u^{(1)}} = u^{(2)} = 4 \).
    *   The derivative with respect to its second input is the first input: \( \frac{\partial u^{(3)}}{\partial u^{(2)}} = u^{(1)} = 3 \).
3.  **Backward Pass:** We start with the upstream gradient \( \frac{\partial J}{\partial J} = 1 \). Applying our summation rule (which here has one term for each input):
    *   \( \frac{\partial J}{\partial u^{(1)}} = \frac{\partial J}{\partial u^{(3)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(1)}} = 1 \cdot 4 = 4 \).
    *   \( \frac{\partial J}{\partial u^{(2)}} = \frac{\partial J}{\partial u^{(3)}} \cdot \frac{\partial u^{(3)}}{\partial u^{(2)}} = 1 \cdot 3 = 3 \).

**Critical Observation:** To compute the local Jacobian for the multiplication, we needed the *other* input's value. To get \( \partial J / \partial u^{(1)} \), we needed the value of \( u^{(2)} \). This is why the forward pass must store all intermediate values. The backward pass needs the actual numbers from the forward pass.

**Common Misconception:** "The sum in the multivariate chain rule is optional." It is not. In architectures with skip connections (like ResNets), a variable often feeds into both a main path and a skip path. The total gradient is the sum of contributions from both. Forgetting to sum is a classic and hard-to-find bug.

**Quick Check (Multivariate Chain Rule):** Suppose \( a = 2 \), \( b = a^2 \), \( c = a + b \), and the cost is \( J = c \). Compute \( \partial J / \partial a \).
*   *Solution:* The variable \( a \) influences \( J \) via two paths.
    *   Path 1 (direct): \( a \to c \). Contribution = \( \frac{\partial J}{\partial c} \cdot \frac{\partial c}{\partial a} = 1 \cdot 1 = 1 \).
    *   Path 2 (via \( b \)): \( a \to b \to c \). Contribution = \( \frac{\partial J}{\partial c} \cdot \frac{\partial c}{\partial b} \cdot \frac{\partial b}{\partial a} = 1 \cdot 1 \cdot 2a = 4 \).
    *   Total gradient: \( 1 + 4 = 5 \). We can verify this: \( c = a + a^2 = 6 \), so \( dc/da = 1 + 2a = 5 \).

---

### 5. The Backpropagation Algorithm: A Two-Pass Procedure

**Learning Objective:** Execute the forward and backward passes of the backpropagation algorithm on a given computational graph.

The algorithm is a two-phase process.

#### 5.1 The Forward Pass (Compute and Store)
We execute the graph in topological order, from inputs to the final cost. For every operation, we perform two steps:
1.  **Compute** the output value.
2.  **Store** any values needed later for the backward pass. This storage defines the memory cost of training.

**Storage Examples:**
*   **Multiplication \( z = x \cdot y \):** Store both \( x \) and \( y \), because \( \partial z / \partial x = y \) and \( \partial z / \partial y = x \).
*   **Sigmoid \( a = \sigma(z) \):** We can store the output \( a \) and use the fact that \( \sigma'(z) = a(1-a) \), or store \( z \) directly. Storing \( z \) is often preferred for numerical stability.

#### 5.2 The Backward Pass (Traverse and Accumulate)
We traverse the graph in reverse topological order, from the final cost back to the inputs. At the root node (the cost \( J \)), we initialize the upstream gradient to \( \frac{\partial J}{\partial J} = 1 \).

For each operation node we encounter:
1.  **Receive** the upstream gradient \( \frac{\partial J}{\partial \text{output}} \).
2.  **Retrieve** the stored input values from the forward pass.
3.  **Compute** the local Jacobians for each of its inputs.
4.  **Multiply** to get the gradient for each input: \( \frac{\partial J}{\partial \text{input}} = \frac{\partial J}{\partial \text{output}} \cdot \frac{\partial \text{output}}{\partial \text{input}} \).
5.  **Accumulate (Add)** this contribution to the input's gradient. If the input node already has a gradient from a different path, we add to it.
6.  **Pass** the newly computed gradient downstream to the next nodes.

**Worked Example: A Complete Backward Pass**
Let us trace the full algorithm for \( z = (x + y) \cdot \sigma(x) \) with \( x=1 \) and \( y=2 \).

**Forward Pass (Compute and Store):**
1.  \( v_1 = x + y = 1 + 2 = 3 \). Store \( v_1 \).
2.  \( v_2 = \sigma(x) = \sigma(1) \approx 0.7311 \). Store \( v_2 \) and \( x \).
3.  \( z = v_1 \cdot v_2 \approx 3 \cdot 0.7311 = 2.1933 \). Store \( v_1, v_2, z \).

**Backward Pass (Traverse and Accumulate):**
*   **Start at root \( z \):** Upstream gradient \( \frac{\partial J}{\partial z} = 1 \).
*   **Node \( [\times] \):** Inputs are \( v_1, v_2 \). Output is \( z \).
    *   Local Jacobians: \( \frac{\partial z}{\partial v_1} = v_2 \approx 0.7311 \), \( \frac{\partial z}{\partial v_2} = v_1 = 3 \).
    *   Compute gradients:
        *   \( \frac{\partial J}{\partial v_1} = 1 \cdot 0.7311 = 0.7311 \)
        *   \( \frac{\partial J}{\partial v_2} = 1 \cdot 3 = 3 \)
*   **Node \( [+] \):** Inputs are \( x, y \). Output is \( v_1 \). Upstream gradient is \( 0.7311 \).
    *   Local Jacobians: \( \frac{\partial v_1}{\partial x} = 1 \), \( \frac{\partial v_1}{\partial y} = 1 \).
    *   Compute gradients:
        *   \( \frac{\partial J}{\partial x} \leftarrow 0.7311 \cdot 1 = 0.7311 \) (First contribution)
        *   \( \frac{\partial J}{\partial y} = 0.7311 \cdot 1 = 0.7311 \)
*   **Node \( [\sigma] \):** Input is \( x \). Output is \( v_2 \). Upstream gradient is \( 3 \).
    *   Local Jacobian: \( \frac{\partial v_2}{\partial x} = \sigma'(x) = \sigma(x)(1-\sigma(x)) \approx 0.7311 \cdot 0.2689 \approx 0.1966 \).
    *   Compute gradient: \( \frac{\partial J}{\partial x} \leftarrow 3 \cdot 0.1966 = 0.5898 \) (Second contribution, added to the first).
*   **Accumulate Gradient for \( x \):** \( 0.7311 + 0.5898 = 1.3209 \).

**Final Gradients:** \( \frac{\partial J}{\partial x} \approx 1.3209 \), \( \frac{\partial J}{\partial y} \approx 0.7311 \).

---

### 6. Application: Backpropagation in a Two-Layer Network

**Learning Objective:** Derive the gradient formulas for a simple neural network by applying the backpropagation algorithm to its computational graph.

We now bridge the gap from abstract graphs to a real training step. Consider a network for a single data point.

**Architecture:**
*   **Input:** \( x \in \mathbb{R}^d \)
*   **Hidden Layer:** \( h = \sigma(z^{[1]}) \), where \( z^{[1]} = W^{[1]} x + b^{[1]} \)
*   **Output:** \( \hat{y} = W^{[2]} h + b^{[2]} \)
*   **Loss (Cost):** \( J = \frac{1}{2}\|\hat{y} - y\|_2^2 \)

**The Computational Graph:**
```
x --→ [W¹x+b¹] --→ z¹ --→ [σ] --→ h --→ [W²h+b²] --→ ŷ --→ [loss] --→ J
```

#### 6.1 Forward Pass
We store the values indicated in brackets.
1.  **Hidden Pre-activation:** \( z^{[1]} = W^{[1]} x + b^{[1]} \). [Store \( x, W^{[1]}, b^{[1]}, z^{[1]} \)]
2.  **Hidden Activation:** \( h = \sigma(z^{[1]}) \). [Store \( z^{[1]} \)]
3.  **Output Pre-activation:** \( \hat{y} = W^{[2]} h + b^{[2]} \). [Store \( h, W^{[2]}, b^{[2]}, \hat{y} \)]
4.  **Loss:** \( J = \frac{1}{2}\sum_{i=1}^k (\hat{y}_i - y_i)^2 \). [Store \( \hat{y}, y \)]

#### 6.2 Backward Pass
We start with the upstream gradient \( \frac{\partial J}{\partial J} = 1 \).

**Step 1: The Loss Node.** The operation is \( J = \frac{1}{2}\sum_{i=1}^k (\hat{y}_i - y_i)^2 \). The upstream gradient for the input \( \hat{y} \) is the error vector:
\[
\frac{\partial J}{\partial \hat{y}} = \hat{y} - y
\]

**Step 2: The Output Layer (\(