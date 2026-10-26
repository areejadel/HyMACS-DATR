# Lecture: Backpropagation in Neural Networks

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Understand** the Credit Assignment Problem and how backpropagation solves it.
2. **Apply** the chain rule to decompose a global cost gradient into local derivatives for a specific weight.
3. **Analyze** the computational complexity of reverse-mode differentiation compared to forward-mode.
4. **Calculate** weight updates for a multi-layer perceptron using generalized backpropagation equations.
5. **Evaluate** the impact of activation functions and initialization strategies on gradient stability.

---

## 1. The Intuition: The Credit Assignment Problem

Imagine you are the CEO of a company with 1,000 employees arranged in a strict hierarchy. At the end of the year, the company loses $10 million. You know the final outcome is a disaster, but you don't know *why*. Was it the salesperson who promised something the product couldn't do? Was it the engineer who wrote a bug in the core logic? Or was it the middle manager who misinterpreted your instructions?

This is the **Credit Assignment Problem**: in a system of sequential dependencies, how do you determine exactly how much "blame" (or credit) to assign to a specific component deep within the system based only on the final result?

- If you punish everyone equally, you destroy the parts of the organization that actually worked.
- If you only punish the person who delivered the final report, you ignore the systemic failure that caused the error.

In a neural network with millions of parameters, backpropagation is the mathematical solution to this problem. It allows a global error at the output to be precisely decomposed into local "blame" for every individual weight in the network.

---

## 2. Prerequisites: The Forward Pass

Before we can assign blame, we must track the flow of information. A neural network is a composite function: $f(x) = f_L(f_{L-1}(\dots f_1(x)\dots))$.

### 2.1 Formal Definition
In a feedforward network, the state of layer $l$ is defined by two sequential steps:

1. **Linear Combination**: The network computes the "evidence" for a feature:
   $$z^{(l)} = w^{(l)} a^{(l-1)} + b^{(l)}$$
   Where $w^{(l)}$ is the weight matrix, $b^{(l)}$ is the bias vector, and $a^{(l-1)}$ is the activation vector from the previous layer.

2. **Activation**: A non-linear function $\sigma$ determines if that evidence is passed forward:
   $$a^{(l)} = \sigma(z^{(l)})$$
   Common examples include the Rectified Linear Unit, $\text{ReLU}(z) = \max(0, z)$, and the Sigmoid function, $\text{Sigmoid}(z) = \frac{1}{1+e^{-z}}$.

3. **Cost Computation**: At the final layer $L$, a scalar cost $J$ measures the error between the prediction $\hat{y} = a^{(L)}$ and the ground truth $y$. Using Mean Squared Error (MSE):
   $$J = \frac{1}{2}(y - \hat{y})^2$$

### 2.2 Forward Pass Example
Consider a single neuron with input $x=1.0$, weight $w=0.5$, bias $b=0$, and a $\text{ReLU}$ activation function.
1. Compute linear sum: $z = (0.5 \times 1.0) + 0 = 0.5$
2. Apply activation: $a = \max(0, 0.5) = 0.5$
3. Compute cost (given target $y=1.0$): $J = \frac{1}{2}(1.0 - 0.5)^2 = 0.125$

> **Try this yourself**: If the linear sum $z$ becomes $-0.2$ using the $\text{ReLU}$ activation, what is the activation $a$? How does this affect the cost $J$ if the target $y$ is $1.0$?

**Summary: The Forward Pass**
The forward pass transforms an input $x$ into a cost $J$. Crucially, we must store the intermediate values ($z$ and $a$) because they act as the "breadcrumbs" we will follow backward to assign blame.

---

## 3. The Mechanism: The Chain Rule

To minimize the cost $J$, we must determine how $J$ changes relative to a specific weight $w$. This is the gradient $\frac{\partial J}{\partial w}$.

### 3.1 The Sensitivity Chain
Think of the network as a series of connected gears. If gear A turns, gear B turns slightly, which in turn moves gear C. To find the total effect of gear A on gear C, you don't need a global formula; you simply multiply the ratios of every intermediate gear.

**The Chain Rule**: If $z$ depends on $y$, and $y$ depends on $x$, then:
$$\frac{\partial z}{\partial x} = \frac{\partial z}{\partial y} \cdot \frac{\partial y}{\partial x}$$

### 3.2 Single Path Gradient Example
Consider the path: $x \xrightarrow{w_1} z \xrightarrow{\sigma} a \xrightarrow{w_2} J$, where:
- $z = w_1 x$
- $a = \sigma(z)$
- $J = \frac{1}{2}(y - w_2 a)^2$

**The Tension**: How do we calculate the effect of $w_1$ on $J$ without knowing the entire global equation? We decompose the problem into local "sensitivities."

1. **Output Sensitivity**: $\frac{\partial J}{\partial a} = -(y - w_2 a)w_2$ (How much does the cost change if the activation $a$ changes?)
2. **Local Gate Sensitivity**: $\frac{\partial a}{\partial z} = \sigma'(z)$ (How much does the activation change if the linear sum $z$ changes?)
3. **Input Sensitivity**: $\frac{\partial z}{\partial w_1} = x$ (How much does the linear sum change if the weight $w_1$ changes?)

The final gradient is the product:
$$\frac{\partial J}{\partial w_1} = \underbrace{-(y - w_2 a)w_2}_{\text{Downstream}} \cdot \underbrace{\sigma'(z)}_{\text{Local Gate}} \cdot \underbrace{x}_{\text{Upstream}}$$

**Technical Note**: This is the essence of modularity. A neuron does not need to know the architecture of the rest of the network; it only needs the "error signal" from the layer above and its own local derivative.

> **Try this yourself**: In the path above, if $\sigma'(z) = 0$ (e.g., a $\text{ReLU}$ neuron is "off"), what happens to the gradient $\frac{\partial J}{\partial w_1}$? Why does this lead to "dead neurons"?

---

## 4. Efficiency: Reverse-Mode Differentiation

Calculating the chain rule independently for millions of weights is computationally impossible. If you have 1 million weights, calculating 1 million separate chains would be like recalculating the entire corporate hierarchy for every single employee.

### 4.1 The Redundancy Problem
In deep networks, thousands of weights share the same downstream path to the output. Calculating $\frac{\partial J}{\partial w}$ for each weight independently would result in recalculating the same output derivatives millions of times.

### 4.2 The Solution: Dynamic Programming
Backpropagation is an implementation of **reverse-mode automatic differentiation**. It is conceptually similar to **optimal control** in engineering (like the Kalman filter or LQR), where we propagate a "cost-to-go" backward from the target state.

1. **Forward Pass**: Compute and store all $z^{(l)}$ and $a^{(l)}$.
2. **Backward Pass**: Compute the error $\delta$ for the output layer, then propagate that $\delta$ backward to compute the errors for preceding layers.

### 4.3 The Memory Trade-off
- **Runtime**: Complexity is reduced from $O(W^2)$ to $O(W)$, as each edge is visited exactly once.
- **Memory**: Because the gradient at layer $l$ depends on the activation $a^{(l-1)}$ from the forward pass, we must store every single activation in VRAM. This is why deep models require massive GPUs; we are trading memory (storage of activations) for time (avoiding redundant calculations).

---

## 5. Generalization: Multilayer Perceptrons (MLP)

We now scale the single-path logic to matrix operations.

### 5.1 The Backpropagation Algorithm
The generalized updates are computed as follows:

1. **Output Error ($\delta^{(L)}$)**: The error at the final layer $L$:
   $$\delta^{(L)} = \nabla_{a^{(L)}} J \odot \sigma'(z^{(L)})$$
   Where $\odot$ denotes the element-wise (Hadamard) product.

2. **Error Backpropagation**: The error $\delta$ is propagated backward to layer $l$:
   $$\delta^{(l)} = ((w^{(l+1)})^T \delta^{(l+1)}) \odot \sigma'(z^{(l)})$$

3. **Weight Update**: The gradient for the weight matrix is the outer product of the error at the destination and the activation at the source:
   $$\frac{\partial J}{\partial w^{(l)}} = \delta^{(l)} (a^{(l-1)})^T$$

### 5.2 Weight Update Logic
The weight update is governed by the interaction of two signals: the **error signal** ($\delta^{(l)}$) and the **input signal** ($a^{(l-1)}$). 
If $\delta^{(l)}$ is large (the neuron is highly responsible for the error) and $a^{(l-1)}$ is large (the neuron was highly active), the product $\delta^{(l)} (a^{(l-1)})^T$ will be large. This indicates the weight $w^{(l)}$ had a significant impact on the final error and requires a larger correction.

---

## 6. Stability and Pitfalls

The success of backpropagation depends on the magnitude of the gradients. Because the gradient is a product of many terms, it behaves like a geometric progression:
$$\frac{\partial J}{\partial w^{(1)}} \propto \prod_{l=2}^{L} \sigma'(z^{(l)})w^{(l)}$$

### 6.1 Vanishing and Exploding Gradients
- **Vanishing Gradients**: If the product $|\sigma'(z)w| < 1$, the gradient shrinks exponentially as it moves toward the early layers. The "blame" disappears before it reaches the start of the network.
  - *Solution*: Use **ReLU** (derivative is $1$ for $z>0$) or **Residual Connections** (which create "highways" for gradients to bypass layers).
- **Exploding Gradients**: If $|\sigma'(z)w| > 1$, the gradient grows exponentially, leading to `NaN` values.
  - *Solution*: **Gradient Clipping**, which caps the gradient norm at a threshold $\tau$.

### 6.2 Breaking Symmetry: Initialization
Weights cannot be initialized to zero. If all $w^{(l)} = 0$, then every neuron in a hidden layer receives the exact same gradient $\delta_i = \delta_j$. They will evolve identically, effectively collapsing the network into a single-neuron model. This is known as the **Symmetry Problem**.

**Recommended Initialization Strategies**:
- **Xavier/Glorot**: Maintains variance across layers for Sigmoid/Tanh.
- **He Initialization**: Adjusted for ReLU, accounting for the fact that half the neurons are typically inactive (zeroed out).

**Final Summary Check**
1. How does the chain rule enable "blame" assignment without a global equation?
2. Why does reverse-mode differentiation necessitate high VRAM usage?
3. Why does a weight of $0$ in the input layer prevent the connected weights from learning?