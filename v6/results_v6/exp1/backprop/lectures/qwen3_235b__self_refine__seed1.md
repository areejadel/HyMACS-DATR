**Learning Objectives**

By the end of this lecture, you will be able to:

1. **Remember** the prerequisites for backpropagation: compute partial derivatives, apply the multivariable chain rule, and describe forward propagation in a neural network.
2. **Understand** the intuition behind reverse-mode automatic differentiation by explaining why finite differences are inefficient and how gradients flow backward through a computational graph.
3. **Apply** the backpropagation algorithm to compute gradients in a two-layer MLP using step-by-step derivations and proper matrix dimensions.
4. **Analyze** common failure modes (e.g., vanishing gradients) by tracing their origin in activation functions and weight initialization.
5. **Create** a generalized backpropagation loop for an arbitrary feedforward network and adapt it to different activation functions and loss types.

---

### The Credit Assignment Problem: One Chord, Ten Million Knobs

Imagine standing before a pipe organ with 10 million knobs—each adjusting pitch, volume, or timbre. You play a chord. It sounds wrong. From that single dissonant sound, you must decide how to tweak every knob to make it harmonious.

Now imagine the organ is inside a black box. You can’t see which knob controls what. You only hear the final chord. And you must adjust all 10 million knobs *simultaneously*, based on that one sound.

This is the **credit assignment problem** in deep learning: a scalar loss tells us *how bad* a prediction is, but not *which weights* are responsible or *how to fix them*. Yet, we solve this efficiently—without testing each weight individually—by leveraging the network’s computational structure and the chain rule of calculus.

That’s the power of **backpropagation**: not a learning algorithm itself, but the engine that computes gradients so optimization methods like stochastic gradient descent (SGD) can update weights.

> 🔍 **Pause and Predict (Try This Yourself)**: Before seeing the solution, sketch your own idea. Given only the final error, how would you determine which weights contributed most? What information from the forward pass might help?

Now let’s see how calculus and network structure make this possible—with precision and speed.

---

### Prerequisites: What You Need to Know

Backpropagation builds on well-established mathematical tools. We review the essentials.

#### 1. Multivariable Chain Rule

Let $ f(g(x,y), h(x,y)) $. The derivative of $ f $ with respect to $ x $ sums contributions from all paths:
$$
\frac{\partial f}{\partial x} = \frac{\partial f}{\partial g} \frac{\partial g}{\partial x} + \frac{\partial f}{\partial h} \frac{\partial h}{\partial x}
$$
This **path-summing** behavior is central: every influence path from a parameter to the loss must be accounted for.

> ✅ **Worked Example**: Let $ f = (2x + 3y)^2 $. Define $ u = 2x + 3y $, so $ f = u^2 $. Then:
$$
\frac{\partial f}{\partial x} = \frac{df}{du} \cdot \frac{\partial u}{\partial x} = 2u \cdot 2 = 4(2x + 3y)
$$
We applied the chain rule along the single path from $ x $ to $ f $ via $ u $.

> 🔍 **Misconception Alert**: The chain rule applies only when functions are differentiable. Non-differentiable operations (e.g., hard argmax) break backpropagation unless approximated (e.g., via Gumbel-Softmax).

> ✅ **Quick Check (Remember)**: Compute $ \frac{\partial f}{\partial y} $ for $ f = \sin(xy) $.  
Answer: $ \frac{\partial f}{\partial y} = x \cos(xy) $. If you used the chain rule correctly, you’re ready.

#### 2. Forward Propagation in Neural Networks

In a neural network layer $ l $, we compute:
$$
\mathbf{z}^{(l)} = \mathbf{W}^{(l)} \mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}, \quad \mathbf{a}^{(l)} = \sigma(\mathbf{z}^{(l)})
$$
where $ \mathbf{a}^{(0)} = \mathbf{x} $ is the input, and $ \sigma $ is applied element-wise.

> ✅ **Worked Example**: Let $ \mathbf{x} = [1, 2]^\top $, $ \mathbf{W}^{(1)} = \begin{bmatrix} 1 & 0 \\ -1 & 1 \end{bmatrix} $, $ \mathbf{b}^{(1)} = [0, 1]^\top $, $ \sigma = \text{ReLU} $.  
Then:
- $ \mathbf{z}^{(1)} = \mathbf{W}^{(1)}\mathbf{x} + \mathbf{b}^{(1)} = [1, 2]^\top + [0,1]^\top = [1, 3]^\top $
- $ \mathbf{a}^{(1)} = \text{ReLU}([1, 3]) = [1, 3]^\top $

> 🔍 **Why Store $ \mathbf{z}^{(l)} $?** Because $ \sigma'(\mathbf{z}^{(l)}) $ is needed during backpropagation. For ReLU, $ \sigma'(z) = 1 $ if $ z > 0 $, else 0. You cannot recover $ z $ from $ a = \sigma(z) $—information is lost.

> ✅ **Quick Check (Analyze)**: Can you compute $ \sigma'(z) $ from $ \sigma(z) $ alone for sigmoid? For tanh?  
Answer: Yes for both—because $ \sigma'(z) = \sigma(z)(1 - \sigma(z)) $ for sigmoid, and $ 1 - \tanh^2(z) $ for tanh. But numerical instability or custom activations break this—so we store $ \mathbf{z}^{(l)} $ to be safe.

---

### Intuition: Why We Can’t Try Every Knob

Suppose your network has $ 10^7 $ parameters. To estimate the gradient via finite differences:
$$
\frac{\partial J}{\partial \theta_i} \approx \frac{J(\theta + \epsilon \mathbf{e}_i) - J(\theta)}{\epsilon}
$$
Each parameter requires a separate forward pass. Total cost: $ 10^7 $ forward passes per gradient.

That’s like tuning each organ knob one at a time—playing the full chord each time—just to adjust one.

But here’s the key insight: **the loss depends on all parameters through shared computations**. Why recompute everything when only one input changes?

Backpropagation uses **reverse-mode automatic differentiation**, which computes the full gradient in time comparable to *one* forward pass.

> 🔍 **Analogy: The Ripple Upstream**  
Drop a pebble into a river. Ripples spread upstream, revealing how each bend or rock shaped the water’s motion. Backpropagation is that reverse flow: starting from the loss, it traces influence backward through every operation.

This is not metaphor—it’s literal. The chain rule, applied in reverse topological order, ensures each intermediate gradient is computed once and reused.

> ✅ **Try This Yourself (Understand)**: Why can’t we compute $ \frac{\partial J}{\partial \mathbf{W}^{(1)}} $ before knowing $ \frac{\partial J}{\partial \mathbf{a}^{(1)}} $?  
Answer: Because $ \mathbf{W}^{(1)} $ affects $ J $ only through $ \mathbf{a}^{(1)} $. We need the “downstream influence” first—this is why we go backward.

> 🔍 **Cross-Domain Insight: Quantum Interference and Sensitivity Paths**  
In quantum mechanics, the path integral formulation sums over all possible histories to compute a particle’s amplitude. Similarly, backpropagation sums over all computational paths from a parameter to the loss. Each partial derivative is like a coherent contribution from a path—interference isn’t physical, but *cancellation or reinforcement of gradient signals* can occur in deep networks. This reframing helps anticipate gradient pathologies: just as destructive interference suppresses quantum amplitudes, saturated activations can cancel gradient flow across layers.

---

### Concrete Example: Backpropagation on a Small Graph

Let’s walk through a tiny network to see the mechanics.

Define:
$$
a = w_1 x, \quad b = a + w_2, \quad J = b^2
$$
We want $ \frac{\partial J}{\partial w_1} $ and $ \frac{\partial J}{\partial w_2} $.

#### Step 1: Forward Pass — Compute and Store

Given $ x = 2 $, $ w_1 = 3 $, $ w_2 = 1 $:
- $ a = 3 \cdot 2 = 6 $
- $ b = 6 + 1 = 7 $
- $ J = 7^2 = 49 $

Store $ a $, $ b $: these are the **waypoints** for backprop.

> ✅ **Connection to Theory**: This mirrors forward propagation—intermediate values are cached for backward use.

#### Step 2: Backward Pass — Chain Rule in Reverse

Start with $ \frac{\partial J}{\partial J} = 1 $: the **seed**.

1. $ \frac{\partial J}{\partial b} = 2b = 14 $
2. $ \frac{\partial J}{\partial a} = \frac{\partial J}{\partial b} \cdot \frac{\partial b}{\partial a} = 14 \cdot 1 = 14 $
3. $ \frac{\partial J}{\partial w_1} = \frac{\partial J}{\partial a} \cdot \frac{\partial a}{\partial w_1} = 14 \cdot x = 14 \cdot 2 = 28 $
4. $ \frac{\partial J}{\partial w_2} = \frac{\partial J}{\partial b} \cdot \frac{\partial b}{\partial w_2} = 14 \cdot 1 = 14 $

✅ Final gradients: $ \nabla_{w_1} J = 28 $, $ \nabla_{w_2} J = 14 $

> 🔍 **Why This Works**: Each node’s gradient $ \bar{u} = \frac{\partial J}{\partial u} $ summarizes how much $ u $ affects the loss. By going backward, we ensure we have all downstream information before computing upstream contributions.

> ✅ **Try This Yourself (Apply)**: Compute $ \frac{\partial J}{\partial x} $.  
Solution:
$$
\frac{\partial J}{\partial x} = \frac{\partial J}{\partial a} \cdot \frac{\partial a}{\partial x} = 14 \cdot w_1 = 14 \cdot 3 = 42
$$
This shows input sensitivity—useful for interpretability methods like saliency maps.

---

### General Rule: Reverse-Mode Automatic Differentiation

Let $ J $ be a scalar function over a computational graph. Define the **adjoint** of node $ u_i $ as:
$$
\bar{u}_i = \frac{\partial J}{\partial u_i}
$$

The **reverse-mode chain rule**:
$$
\bar{u}_i = \sum_{j \in \text{children}(u_i)} \bar{u}_j \cdot \frac{\partial u_j}{\partial u_i}
$$

We compute adjoints in **reverse topological order**.

> ✅ **Worked Example**: In our graph, $ a $ has child $ b $. So:
$$
\bar{a} = \bar{b} \cdot \frac{\partial b}{\partial a} = 14 \cdot 1 = 14
$$
This matches our earlier result.

> 🔍 **Cross-Domain Insight: Influence Accounting**  
In economics, a price change at the consumer level ripples upstream, affecting raw material orders. Similarly, backpropagation allocates “blame” backward through operations. Both compute sensitivities in DAGs using reverse accumulation.

> ✅ **Quick Check (Analyze)**: Why is forward-mode inefficient for neural networks?  
Answer: Forward-mode computes one partial derivative per pass. For $ n $ parameters, it takes $ n $ passes. Reverse mode computes all $ n $ gradients in *one* backward pass—optimal when output is scalar.

---

### Application: Backpropagation in a Two-Layer MLP

#### Network Definition

Let $ \mathbf{x} \in \mathbb{R}^d $ be the input, with hidden layer size $ h $ and output size $ o $. The network computes:

$$
\mathbf{z}^{(1)} = \mathbf{W}^{(1)} \mathbf{x} + \mathbf{b}^{(1)}, \quad
\mathbf{h} = \sigma(\mathbf{z}^{(1)}), \quad
\hat{\mathbf{y}} = \mathbf{W}^{(2)} \mathbf{h} + \mathbf{b}^{(2)}, \quad
J = \frac{1}{2} \| \mathbf{y} - \hat{\mathbf{y}} \|^2
$$

We assume MSE loss and element-wise activation $ \sigma $.

---

#### Step 1: Forward Pass — Compute and Store

We compute and store:
- $ \mathbf{z}^{(1)} $, $ \mathbf{h} $, $ \hat{\mathbf{y}} $, $ J $

> 🔍 **Why Store $ \mathbf{z}^{(1)} $?** Because $ \sigma'(\mathbf{z}^{(1)}) $ is needed during backpropagation. For ReLU, $ \sigma'(z) = \mathbb{I}(z > 0) $. You cannot recover $ z $ from $ h = \sigma(z) $—information is lost.

> ✅ **Try This Yourself (Analyze)**: Suppose $ \sigma = \tanh $, and $ z_i = 5 $. What is $ \sigma'(z_i) $?  
Answer: $ \tanh'(5) = 1 - \tanh^2(5) \approx 1 - 1^2 = 0 $. Gradient vanishes—neuron is saturated and learns slowly.

---

#### Step 2: Backward Pass — Output Layer

**Step 2.1: Compute $ \boldsymbol{\delta}^{(2)} = \frac{\partial J}{\partial \hat{\mathbf{y}}} $**

For mean squared error (MSE):
$$
\boldsymbol{\delta}^{(2)} = \hat{\mathbf{y}} - \mathbf{y}
$$
This is the **error signal**—how the output should change to reduce loss.

> ✅ **Worked Example**: Let $ \mathbf{y} = [1, 0]^\top $, $ \hat{\mathbf{y}} = [0.8, 0.3]^\top $. Then:
$$
\boldsymbol{\delta}^{(2)} = [0.8 - 1, 0.3 - 0] = [-0.2, 0.3]
$$

**Step 2.2: Gradients for $ \mathbf{W}^{(2)} $, $ \mathbf{b}^{(2)} $**

From $ \hat{\mathbf{y}} = \mathbf{W}^{(2)} \mathbf{h} + \mathbf{b}^{(2)} $:
- $ \frac{\partial \hat{\mathbf{y}}}{\partial \mathbf{W}^{(2)}} = \mathbf{h}^\top $
- $ \frac{\partial \hat{\mathbf{y}}}{\partial \mathbf{b}^{(2)}} = \mathbf{I} $

Applying the chain rule:
$$
\frac{\partial J}{\partial \mathbf{W}^{(2)}} = \boldsymbol{\delta}^{(2)} \mathbf{h}^\top, \quad
\frac{\partial J}{\partial \mathbf{b}^{(2)}} = \boldsymbol{\delta}^{(2)}
$$

> ✅ **Worked Example**: Let $ \boldsymbol{\delta}^{(2)} \in \mathbb{R}^2 $, $ \mathbf{h} \in \mathbb{R}^3 $. Then $ \frac{\partial J}{\partial \mathbf{W}^{(2)}} $ is $ 2 \times 3 $, matching $ \mathbf{W}^{(2)} $. Gradient dimensions must match parameter dimensions for updates.

> ✅ **Try This Yourself (Apply)**: If $ \mathbf{h} = [1, 2, 3]^\top $, $ \boldsymbol{\delta}^{(2)} = [-0.2, 0.3]^\top $, compute $ \frac{\partial J}{\partial \mathbf{W}^{(2)}} $.  
Answer: Outer product:
$$
\begin{bmatrix} -0.2 \\ 0.3 \end{bmatrix}
\begin{bmatrix} 1 & 2 & 3 \end{bmatrix}
=
\begin{bmatrix}
-0.2 & -0.4 & -0.6 \\
0.3 & 0.6 & 0.9
\end{bmatrix}
$$

---

#### Step 3: Backward Pass — Hidden Layer

**Step 3.1: Compute $ \frac{\partial J}{\partial \mathbf{h}} $**

Error flows backward through $ \mathbf{W}^{(2)} $:
$$
\frac{\partial J}{\partial \mathbf{h}} = (\mathbf{W}^{(2)})^\top \boldsymbol{\delta}^{(2)}
$$
This tells us how the hidden layer’s output should change.

> ✅ **Worked Example**: Let $ \mathbf{W}^{(2)} = \begin{bmatrix} 1 & 2 \\ 3 & 4 \\ 5 & 6 \end{bmatrix} $, $ \boldsymbol{\delta}^{(2)} = [-0.2, 0.3]^\top $. Then:
$$
\frac{\partial J}{\partial \mathbf{h}} = 
\begin{bmatrix}
1 & 2 \\
3 & 4 \\
5 & 6
\end{bmatrix}^\top
\begin{bmatrix} -0.2 \\ 0.3 \end{bmatrix}
= 
\begin{bmatrix}
1(-0.2) + 3(0.3) \\
2(-0.2) + 4(0.3) \\
5(-0.2) + 6(0.3)
\end{bmatrix}
= 
\begin{bmatrix} 0.7 \\ 0.8 \\ 0.8 \end{bmatrix}
$$

**Step 3.2: Compute $ \boldsymbol{\delta}^{(1)} = \frac{\partial J}{\partial \mathbf{z}^{(1)}} $**

Apply activation derivative:
$$
\boldsymbol{\delta}^{(1)} = \frac{\partial J}{\partial \mathbf{h}} \odot \sigma'(\mathbf{z}^{(1)})
$$
The Hadamard product applies local sensitivity: neurons in saturated regions get zero gradient.

> ✅ **Worked Example**: Let $ \mathbf{z}^{(1)} = [5, -1, 0]^\top $, $ \sigma = \tanh $. Then:
- $ \sigma'(\mathbf{z}^{(1)}) = [1 - \tanh^2(5), 1 - \tanh^2(-1), 1 - \tanh^2(0)] \approx [0, 0.42, 1] $
- $ \frac{\partial J