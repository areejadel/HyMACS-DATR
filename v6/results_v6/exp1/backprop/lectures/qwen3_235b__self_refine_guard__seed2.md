**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Remember** the key components of forward and backward passes, including stored intermediate values and error signals.  
2. **Understand** how the multivariable chain rule applies across a computational graph using a concrete example.  
3. **Apply** the backpropagation algorithm to compute gradients for weights and biases in a two-layer network with ReLU and linear activations.  
4. **Analyze** a network’s structure to determine the correct order and dependencies for gradient computation.  
5. **Create** a complete implementation of forward and backward passes given inputs, parameters, and a cost function.

---

### 1. Prerequisites: Foundational Concepts

Imagine you're debugging a malfunctioning robot arm that learns from trial and error. It adjusts millions of internal settings, but only gets *one* signal: “You were off by 3 cm.” How should it decide which settings to tweak?

This is the **credit assignment problem**—and backpropagation is our best answer. But to understand it, we need three tools.

#### Matrix and Vector Operations  
We use matrix-vector multiplication to compute layer outputs. For a weight matrix $ W \in \mathbb{R}^{m \times n} $, input $ x \in \mathbb{R}^n $, the output is $ Wx \in \mathbb{R}^m $.  
We also use transposes (e.g., $ x^\top $) and outer products (e.g., $ ab^\top $). The gradient of a scalar with respect to a vector has the same shape as the vector.

> **Analogy: Wiring Diagrams**  
Think of $ Wx $ as a wiring diagram: each row of $ W $ connects inputs to one neuron, like electrical traces on a circuit board. The gradient tells us how to rewire each trace to reduce error.

#### Multivariable Chain Rule  
Backpropagation applies the chain rule to composite functions. Consider:  
Let $ f(u) = \sin(u) $, $ u = w^\top x $. Then:  
$$
\frac{d f}{d w} = \frac{d f}{d u} \cdot \frac{d u}{d w} = \cos(w^\top x) \cdot x
$$  
The result is a vector matching the shape of $ w $, as expected for a gradient.

> ✅ **Misconception Alert**  
> The derivative of $ w^\top x $ with respect to $ w $ is $ x $, not $ x^\top $. Gradient vectors inherit the shape of the variable being differentiated.

> **Try This Yourself: Chain Rule in Action**  
Compute $ \frac{d}{dw} \left( (w^2 + 1)^3 \right) $, where $ w \in \mathbb{R} $.  

**Solution**:  
Let $ u = w^2 + 1 $, so $ f = u^3 $. Then:  
$$
\frac{df}{dw} = \frac{df}{du} \cdot \frac{du}{dw} = 3u^2 \cdot 2w = 6w(w^2 + 1)^2
$$  
This illustrates the univariate chain rule—backpropagation extends this to vector-valued functions.

#### Neural Network Building Blocks  
Each layer computes:  
- Pre-activation: $ z^{(l)} = W^{(l)} h^{(l-1)} + b^{(l)} $  
- Activation: $ h^{(l)} = f^{(l)}(z^{(l)}) $  
The cost $ J $ measures prediction error, e.g., $ J = \frac{1}{2}(\hat{y} - y)^2 $.

> **Cross-Domain Link: Thermodynamics**  
Just as heat flows from hot to cold, gradients flow from high cost to low cost. But unlike heat, gradients carry *directional memory*—they remember the path through the network, like a hiker retracing steps down a mountain.

---

### 2. Forward Pass: Computation and Storage

Let’s return to the robot arm. Before it can learn, it must *act*. The forward pass is that action.

We now walk through a concrete network to illustrate the forward pass and emphasize the importance of storing intermediate values.

#### Network Setup  
- Input: $ x = 2 $  
- True label: $ y = 1 $  
- Layer 1:  
  $ W^{(1)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix},\ b^{(1)} = \begin{bmatrix} 0 \\ 1 \end{bmatrix},\ f^{(1)} = \text{ReLU} $  
- Layer 2:  
  $ W^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix},\ b^{(2)} = 0,\ f^{(2)}(z) = z $ (linear)  
- Cost: $ J = \frac{1}{2}(\hat{y} - y)^2 $

#### Step 1: First Pre-activation  
$$
z^{(1)} = W^{(1)}x + b^{(1)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix} \cdot 2 + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}
$$

#### Step 2: First Activation  
$$
h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} \max(0, 2) \\ \max(0, -1) \end{bmatrix} = \begin{bmatrix} 2 \\ 0 \end{bmatrix}
$$

#### Step 3: Second Pre-activation  
$$
z^{(2)} = W^{(2)} h^{(1)} + b^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix} \begin{bmatrix} 2 \\ 0 \end{bmatrix} + 0 = 4
$$

#### Step 4: Output and Cost  
$$
\hat{y} = z^{(2)} = 4,\quad J = \frac{1}{2}(4 - 1)^2 = 4.5
$$

We store all intermediate values: $ x, z^{(1)}, h^{(1)}, z^{(2)}, \hat{y}, J $. These are required during backpropagation because gradients depend on them. For example, $ \frac{\partial J}{\partial W^{(1)}} $ depends on $ x $, $ h^{(1)} $, and $ z^{(1)} $. Without storage, gradient computation is impossible.

> ✅ **Misconception Alert**  
> The forward pass does **not** compute gradients. It **prepares** for them by storing values needed in the backward pass.

> **Try This Yourself: Forward Pass Variation**  
If $ x = -1 $, what is $ h^{(1)} $?  

**Solution**:  
$ z^{(1)} = W^{(1)}(-1) + b^{(1)} = \begin{bmatrix} -1 \\ 1 \end{bmatrix} + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} -1 \\ 2 \end{bmatrix} $, so  
$ h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} 0 \\ 2 \end{bmatrix} $

> **Analogy: Theater Rehearsal**  
The forward pass is like a dress rehearsal. Every actor (neuron) takes their position, props (activations) are placed stage-left. Only then can the director (backprop) assign blame or praise.

---

### 3. Computational Graph and the Chain Rule

Now the robot arm gets its feedback: “You were off by 3 cm.” But which joint moved too far? Which motor turned too fast?

We model the network as a **computational graph**—a directed acyclic graph representing functional dependencies.

#### Graph Structure  
Nodes: $ x, W^{(1)}, b^{(1)}, z^{(1)}, h^{(1)}, W^{(2)}, b^{(2)}, z^{(2)}, \hat{y}, J $  
Edges: functional dependencies, e.g., $ z^{(1)} \leftarrow W^{(1)} $, $ h^{(1)} \leftarrow z^{(1)} $

To compute $ \frac{\partial J}{\partial W^{(1)}} $, we follow the path:  
$$
W^{(1)} \to z^{(1)} \to h^{(1)} \to z^{(2)} \to \hat{y} \to J
$$  
By the chain rule:  
$$
\frac{\partial J}{\partial W^{(1)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} \cdot \frac{\partial z^{(2)}}{\partial h^{(1)}} \cdot \frac{\partial h^{(1)}}{\partial z^{(1)}} \cdot \frac{\partial z^{(1)}}{\partial W^{(1)}}
$$

Computing such paths individually would be inefficient. Instead, **backpropagation reuses intermediate gradients** via reverse-mode automatic differentiation.

> **Analogy: Water Flow in Pipes**  
Imagine the cost $ J $ as water pressure. We open a valve at $ J $, and pressure flows backward through pipes (edges). At each junction (node), pressure splits or combines according to local rules. The force on each valve (parameter) is its gradient.

But here’s the **tension**: if we computed gradients forward, we’d have to repeat this for every parameter—like testing each pipe one at a time. Reverse mode does it all at once.

#### Key Insight: Reverse-Mode Efficiency  
Gradients are computed **backward**, starting from $ \frac{\partial J}{\partial J} = 1 $, and propagating backward through the graph. At each layer, we store the **error signal** $ \delta^{(l)} = \frac{\partial J}{\partial z^{(l)}} $, which captures sensitivity of the cost to pre-activations.

> ✅ **Misconception Alert**  
> Backpropagation is **not** “reverse chain rule.” It is **reverse-mode automatic differentiation with memoization**, a dynamic programming method that computes all gradients in $ O(n) $ time.

> **Try This Yourself: Graph Intuition**  
Sketch the graph for $ f(w) = \sin(w^\top x)^2 $. How many times is $ \frac{\partial f}{\partial \sin(w^\top x)} $ computed in reverse mode?  

**Answer**: Once. It is computed and reused to find $ \frac{\partial f}{\partial w} $.

---

### 4. Backward Pass: Gradient Computation via Error Signals

We now compute gradients using the error signal $ \delta^{(l)} = \frac{\partial J}{\partial z^{(l)}} $. This enables efficient, reusable gradient propagation.

#### Step 1: Output Layer Error  
We have $ \hat{y} = z^{(2)} $, so:  
$$
\frac{\partial J}{\partial \hat{y}} = \hat{y} - y = 4 - 1 = 3
$$  
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = 3 \cdot 1 = 3
$$  
This $ \delta^{(2)} $ seeds all upstream gradients.

#### Step 2: Gradients for $ W^{(2)} $ and $ b^{(2)} $  
From $ z^{(2)} = W^{(2)} h^{(1)} + b^{(2)} $:  
- $ \frac{\partial z^{(2)}}{\partial W^{(2)}} = h^{(1)} $, so:  
  $$
  \frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} \cdot \frac{\partial z^{(2)}}{\partial W^{(2)}} = \delta^{(2)} (h^{(1)})^\top = 3 \cdot \begin{bmatrix} 2 \\ 0 \end{bmatrix}^\top = \begin{bmatrix} 6 & 0 \end{bmatrix}
  $$  
- $ \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 3 $

> **Insight**: The bias gradient is always $ \delta^{(l)} $, because $ b^{(l)} $ is added directly to $ z^{(l)} $.

#### Step 3: Propagate Error to Hidden Layer  
First, compute how cost changes with $ h^{(1)} $:  
$$
\frac{\partial J}{\partial h^{(1)}} = \left( \frac{\partial z^{(2)}}{\partial h^{(1)}} \right)^\top \delta^{(2)} = (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix} \cdot 3 = \begin{bmatrix} 6 \\ -3 \end{bmatrix}
$$

Now apply the ReLU derivative:  
$$
\frac{\partial h^{(1)}}{\partial z^{(1)}} = \text{diag}(\mathbb{I}(z^{(1)}_i > 0)) = \begin{bmatrix} 1 & 0 \\ 0 & 0 \end{bmatrix}
$$  
$$
\delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial h^{(1)}} \odot \frac{\partial h^{(1)}}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ -3 \end{bmatrix} \odot \begin{bmatrix} 1 \\ 0 \end{bmatrix} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> **Analogy: Neural Diodes**  
> ReLU acts like a switch. Gradient flows only if $ z^{(1)}_i > 0 $. Here, the second neuron is inactive—no gradient passes through.

> **Cross-Domain Link: Traffic Control**  
Imagine a city where streets are neurons. During forward pass, cars (activations) move forward. During backprop, repair crews (gradients) move backward, but only on streets that were open. Closed streets (inactive ReLUs) block traffic—no crew can pass.

#### Step 4: Gradients for $ W^{(1)} $ and $ b^{(1)} $  
From $ z^{(1)} = W^{(1)} x + b^{(1)} $:  
- $ \frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix} 6 \\ 0 \end{bmatrix} \cdot 2 = \begin{bmatrix} 12 \\ 0 \end{bmatrix} $  
- $ \frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} = \begin{bmatrix} 6 \\ 0 \end{bmatrix} $

> ✅ **Misconception Alert**  
> The weight gradient is $ \delta^{(l)} (h^{(l-1)})^\top $, an outer product. This ensures correct dimensions and captures the interaction between input and error.

> **Try This Yourself: Backward Pass Variation**  
Suppose $ x = -1 $, so $ h^{(1)} = \begin{bmatrix} 0 \\ 2 \end{bmatrix} $. Recompute $ \delta^{(1)} $ and $ \frac{\partial J}{\partial W^{(1)}} $. Which neuron receives gradient?  

**Solution**:  
$ z^{(1)} = \begin{bmatrix} -1 \\ 2 \end{bmatrix} $, so ReLU derivative is $ \begin{bmatrix} 0 \\ 1 \end{bmatrix} $.  
$ \frac{\partial J}{\partial h^{(1)}} = (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix} \cdot 3 = \begin{bmatrix} 6 \\ -3 \end{bmatrix} $  
$ \delta^{(1)} = \begin{bmatrix} 6 \\ -3 \end{bmatrix} \odot \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 0 \\ -3 \end{bmatrix} $  
$ \frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix} 0 \\ -3 \end{bmatrix} \cdot (-1) = \begin{bmatrix} 0 \\ 3 \end{bmatrix} $  
Only the second neuron receives gradient—because it was active during the forward pass.

---

### 5. Practical Considerations in Real-World Training

Backpropagation isn’t just theory—it’s engineered.

#### Example 1: Convolutional Neural Networks (CNNs)  
In ResNet, the forward pass computes activations across 50+ layers, storing $ z^{(l)} $ and $ h^{(l)} $. The backward pass uses these to compute gradients. Optimizers like **Adam** use gradients to update weights with adaptive learning rates.

> **Analogy: Postal System**  
Gradients are like letters from customers (loss) to engineers (parameters). ResNet’s skip connections are express lanes—bypassing traffic jams in deep layers.

#### Example 2: Memory Optimization  
Storing all activations consumes significant GPU memory. **Gradient checkpointing** stores only a subset of layers; others are recomputed during backprop. This trades computation time for reduced memory usage.

> **Cross-Domain Link: Archaeology**  
Checkpointing is like preserving only key artifacts. Later, you reconstruct the site (activations) from notes and fragments—costly, but necessary when space is limited.

#### Example 3: Distributed Training  
In models like GPT-3, gradients are computed across thousands of GPUs. Each processes a batch subset, computes local gradients, then synchronizes via **all-reduce** to average gradients.

#### Key Challenges  
- **Vanishing gradients**: Gradients diminish over many layers. Fix: residual connections (ResNet), better initialization.  
- **Dead neurons**: ReLU units stuck at zero. Fix: Leaky ReLU ($ f(z) = \max(0.01z, z) $).  
- **Non-differentiability**: ReLU is not differentiable at 0. Frameworks use subgradient (typically 0).  
- **Gradient explosion**: Fix: gradient clipping (cap gradient norm).

> **Try This Yourself: Efficiency Trade-off**  
Why is forward-mode automatic differentiation impractical for training deep networks?  

**Answer**: Forward mode computes gradients for one input parameter at a time. In deep learning, we have **one scalar cost** and **millions of parameters**—reverse mode (backpropagation) computes all gradients in a single backward pass, making it exponentially more efficient.

---

### 6. Generalization: Beyond Feedforward Networks

Backpropagation is a general principle applicable beyond standard neural networks.

#### Graph Neural Networks (GNNs)  
Messages pass between nodes in a graph. Backpropagation flows through message-passing steps, updating edge and node functions.

> **Analogy: Rumor Spreading**  
Forward pass: a rumor spreads through a social network. Backward pass: someone says, “That rumor was wrong.” The correction spreads backward, assigning blame to who distorted it.

#### Neural ODEs  
The forward pass solves $ \frac{dh}{dt} = f(h(t), t, \theta) $. The backward pass uses the **adjoint method**: solving a second ODE backward in time to compute $ \frac{dJ}{d\theta} $.

> **Cross-Domain Link: Time Reversal in Physics**  
Just as Newton