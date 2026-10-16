**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Remember** the structure of a computational graph and distinguish forward and backward passes.  
2. **Understand** how the multivariable chain rule enables efficient gradient computation in reverse mode.  
3. **Apply** backpropagation to compute gradients in a multi-layer perceptron using ReLU, sigmoid, and softmax activations.  
4. **Analyze** failure modes such as vanishing gradients and dead neurons, and connect them to activation function properties.  
5. **Create** a complete training step by combining computed gradients with an optimizer update rule.

---

### 1. Prerequisites and Intuition: The Blind Climber and the Inverted Avalanche

Before we derive formulas, let’s confront a paradox:  
*How can a system with millions of parameters learn from a single scalar reward—like finding your way down a mountain in pitch darkness, guided only by the temperature of your skin?*

This is the reality of training neural networks. The loss is that single signal—the warmth. Backpropagation is the method by which we reconstruct direction.

We begin with two analogies—one mechanical, one geological—each revealing a hidden truth about reverse-mode differentiation.

#### Analogy 1: The Blind Climber (Gradient as Local Compass)

Imagine you're blindfolded on a mountain and must descend. You can't see the slope, but you can feel the ground under your feet. At each step, you nudge each limb forward slightly and sense whether the terrain drops or rises.

That’s **forward mode** differentiation: testing each parameter independently. With millions of weights, this would take millions of nudges per step—hopeless.

But what if, instead, you could throw a rock down the mountain and *watch how every part of the terrain shaped its fall*? Not literally watch—but feel vibrations in reverse. Each crevice, slope, and ledge leaves a trace in the final impact. From that, you reconstruct which path mattered.

This is **backpropagation**: a single forward pass (the rock’s fall), followed by a backward sweep (the echo of impact), assigning responsibility to every decision point. One pass. Full gradient.

> ✅ **Try This Yourself 1.1**:  
> Suppose you have 10,000 parameters and want to compute the gradient of a scalar loss.  
> How many forward-mode passes would you need? How many reverse-mode passes?  
> **Answer**: Forward mode: 10,000. Reverse mode: **1**. This 10,000× efficiency gain is why deep learning exists.

#### Analogy 2: The Inverted Avalanche (Backprop as Time-Reversed Physics)

Picture an avalanche triggered by a single snowflake. The final destruction covers acres, but you want to know: *Which snowflake, if stabilized, would have prevented the most damage?*

You could simulate 10,000 alternate worlds—each with one flake fixed. Or, you could **run the avalanche backward**, like rewinding a film, where energy flows uphill and shattered trees reassemble. At each branching point, you ask: *How much did this layer amplify or dampen the collapse?*

In this reversed world, the rules are local: each slab only interacts with its neighbors. Yet, the final reconstruction reveals global sensitivity.

Backpropagation is this **time-reversed causality**. The loss is the destruction. The gradients are the counterfactual forces that could have prevented it. And the chain rule? It's the physics of the rewind.

> 🔍 **Why this matters**:  
> Just as avalanches depend on friction and cohesion, backprop depends on **activation derivatives**. A dead ReLU (derivative = 0) is like a frozen layer—no force propagates through. This is the *vanishing gradient* in physical form.

> ❗ **Common Misconception**:  
> "We can recompute intermediate values during backpropagation to save memory."  
> **Correction**: Some operations, such as ReLU or dropout, are non-invertible or stochastic. Recomputing $ z = wx + b $ may yield different results. Therefore, **cache pre-activation values $ a^{(l)} $**—they are essential for correct gradient computation.

---

#### Prerequisites

To follow this lecture, you must understand:  
- **Matrix-vector multiplication**: For $ W \in \mathbb{R}^{m \times n} $ and $ x \in \mathbb{R}^n $, the product $ Wx \in \mathbb{R}^m $ is defined as $ (Wx)_i = \sum_j W_{ij} x_j $.  
- **Vector calculus**: The gradient of a scalar $ J $ with respect to a vector $ x \in \mathbb{R}^n $ is $ \nabla_x J = \left[ \frac{\partial J}{\partial x_1}, \dots, \frac{\partial J}{\partial x_n} \right]^\top $.  
- **Chain rule**: For $ J = f(g(x)) $, $ \frac{\partial J}{\partial x} = \frac{\partial J}{\partial g} \cdot \frac{\partial g}{\partial x} $. In multivariable form, if $ z = g(x) $ and $ J = f(z) $, then $ \nabla_x J = \left( \frac{\partial z}{\partial x} \right)^\top \nabla_z J $.  
- **Neural network basics**: Each layer has weights $ W^{(l)} $, biases $ b^{(l)} $, activation functions $ g^{(l)} $, pre-activations $ a^{(l)} $, and outputs $ h^{(l)} $, related by $ a^{(l)} = W^{(l)} h^{(l-1)} + b^{(l)} $, $ h^{(l)} = g^{(l)}(a^{(l)}) $.

If any concept feels unfamiliar, pause and review. These form the foundation.

---

### 2. Computational Graphs and the Relay Race of Gradients

We now ground the idea with a **simple numerical example**, before introducing general formalism.

#### Concrete Example: Tiny Network with ReLU

Define:  
- Input: $ x = 2 $  
- Parameters: $ w = 3 $, $ b = 1 $  
- Pre-activation: $ z = w x + b = 3 \cdot 2 + 1 = 7 $  
- Activation: $ h = \text{ReLU}(z) = \max(0, 7) = 7 $  
- Prediction: $ \hat{y} = 2h = 14 $  
- True label: $ y = 10 $  
- Loss: $ J = \frac{1}{2}(\hat{y} - y)^2 = \frac{1}{2}(14 - 10)^2 = 8 $

Computational graph:  
$$
x \to z \leftarrow w,b \to h \to \hat{y} \to J
$$

**Forward pass**: Compute and store all values:  
- $ z = 7 $, $ h = 7 $, $ \hat{y} = 14 $, $ J = 8 $

**Backward pass**: Propagate gradients from $ J $ to $ w $:

1. $ \frac{\partial J}{\partial \hat{y}} = \hat{y} - y = 14 - 10 = 4 $  
2. $ \frac{\partial \hat{y}}{\partial h} = 2 \Rightarrow \frac{\partial J}{\partial h} = 4 \cdot 2 = 8 $  
3. $ \frac{\partial h}{\partial z} = \mathbf{1}_{z > 0} = 1 \Rightarrow \frac{\partial J}{\partial z} = 8 \cdot 1 = 8 $  
4. $ \frac{\partial z}{\partial w} = x = 2 \Rightarrow \frac{\partial J}{\partial w} = 8 \cdot 2 = 16 $

Each step uses only **local derivatives** and **cached values**—like runners passing a baton in a relay.

> ✅ **Try This Yourself 2.1**:  
> Compute $ \frac{\partial J}{\partial b} $.  
> *Hint: $ \frac{\partial z}{\partial b} = 1 $*  
> **Answer**: $ \frac{\partial J}{\partial b} = \frac{\partial J}{\partial z} \cdot \frac{\partial z}{\partial b} = 8 \cdot 1 = 8 $

> 🔍 **Why this is modular**:  
> Each node acts like a **customs agent** at a border. It doesn’t care about the origin of the goods—only the value of what arrives and the local tax rate (derivative). It computes duty owed and passes the invoice backward. No global knowledge needed. This is why frameworks like PyTorch can differentiate arbitrary code.

---

### 3. Chain Rule in Reverse Mode: From Avalanche to Algebra

Having defined the computational graph and illustrated gradient propagation, we now formalize reverse-mode automatic differentiation.

#### Adjoint Variables: The Currency of Influence

Define the **adjoint** at any node $ u $ as:  
$$
\delta_u = \frac{\partial J}{\partial u}
$$

This is not just a derivative—it’s a **unit of influence**, like dollars in a corporate budget. The loss is the CEO. Every node asks: *How much does my input affect the bottom line?*

The **reverse-mode chain rule** states:  
If $ u $ influences $ J $ through children $ v_1, \dots, v_k $, then:  
$$
\delta_u = \sum_{j=1}^k \delta_{v_j} \cdot \frac{\partial v_j}{\partial u}
$$

We compute this **backward**, from output to input.

> 🔍 **Why reverse mode wins**:  
> Neural networks have **one scalar loss** and **millions of parameters**. Reverse mode computes the full gradient in **one backward pass**. Forward mode would require one pass per parameter—prohibitively expensive at scale.

#### Layer-Wise Backpropagation: The MLP Case

Consider a standard layer:  
- $ a^{(l)} = W^{(l)} h^{(l-1)} + b^{(l)} $  
- $ h^{(l)} = g^{(l)}(a^{(l)}) $

Define the layer error signal:  
$$
\delta^{(l)} = \frac{\partial J}{\partial a^{(l)}}
$$

This is the sensitivity of the loss to the pre-activation $ a^{(l)} $.

**Output layer**:  
- $ \delta^{(L)} = \frac{\partial J}{\partial a^{(L)}} $, derived from the loss and output activation.

**Hidden layers** ($ l = L-1 $ down to $ 1 $):  
$$
\delta^{(l)} = \left( (W^{(l+1)})^\top \delta^{(l+1)} \right) \odot g'^{(l)}(a^{(l)})
$$

We now unpack this equation.

> 🔍 **Why the transpose?**  
> From $ a^{(l+1)} = W^{(l+1)} h^{(l)} + b^{(l+1)} $, the Jacobian of $ a^{(l+1)} $ with respect to $ h^{(l)} $ is $ W^{(l+1)} $. To propagate sensitivity backward, we apply the transpose: $ \frac{\partial J}{\partial h^{(l)}} = (W^{(l+1)})^\top \delta^{(l+1)} $. This ensures dimension compatibility: if $ \delta^{(l+1)} \in \mathbb{R}^{m_{l+1}} $ and $ W^{(l+1)} \in \mathbb{R}^{m_{l+1} \times m_l} $, then $ (W^{(l+1)})^\top \delta^{(l+1)} \in \mathbb{R}^{m_l} $.

> ✅ **Try This Yourself 3.1**:  
> Suppose $ h^{(l)} \in \mathbb{R}^3 $, $ W^{(l+1)} \in \mathbb{R}^{4 \times 3} $, $ \delta^{(l+1)} \in \mathbb{R}^4 $.  
> What is the shape of $ (W^{(l+1)})^\top \delta^{(l+1)} $?  
> **Answer**: $ (3 \times 4)(4 \times 1) = 3 \times 1 $, matching $ h^{(l)} $. Correct.

> 🧠 **Cross-Domain Insight**:  
> The transpose $ W^\top $ in backprop is like **rewinding a loan**. In the forward pass, weights *lend* influence: $ h^{(l)} \to a^{(l+1)} $. In reverse, the system *collects interest*: each output error charges back to the inputs that caused it. The transpose is the accounting ledger—tracking who owes what.

> ❗ **Common Misconception**:  
> "Backpropagation is symbolic differentiation."  
> **Correction**: No. It is **automatic differentiation (autodiff)**—applying symbolic rules *numerically* at each node. Frameworks like PyTorch build computational graphs dynamically and execute autodiff on-the-fly.

---

### 4. Vectorized Forward and Backward Pass

We now generalize to full vectorized notation for an $ L $-layer multi-layer perceptron (MLP).

#### Notation  
- $ h^{(0)} = x \in \mathbb{R}^d $: input vector  
- $ a^{(l)} = W^{(l)} h^{(l-1)} + b^{(l)} \in \mathbb{R}^{m_l} $: pre-activation  
- $ h^{(l)} = g^{(l)}(a^{(l)}) \in \mathbb{R}^{m_l} $: post-activation  
- $ J \in \mathbb{R} $: scalar loss  

#### Forward Pass (for $ l = 1 $ to $ L $)  
1. $ a^{(l)} = W^{(l)} h^{(l-1)} + b^{(l)} $  
2. $ h^{(l)} = g^{(l)}(a^{(l)}) $  
3. **Store $ a^{(l)} $** (required to compute $ g'^{(l)}(a^{(l)}) $ during backpropagation)  

At output: compute $ J $ using a loss function (e.g., MSE, cross-entropy).

#### Backward Pass  
Initialize:  
- $ \delta^{(L)} = \frac{\partial J}{\partial a^{(L)}} $  

For $ l = L-1 $ down to $ 1 $:  
1. $ \delta^{(l)} = \left( (W^{(l+1)})^\top \delta^{(l+1)} \right) \odot g'^{(l)}(a^{(l)}) $  
2. $ \nabla_{W^{(l)}} J = \delta^{(l)} (h^{(l-1)})^\top $  
3. $ \nabla_{b^{(l)}} J = \delta^{(l)} $

> 🔍 **Why $ \delta^{(l)} (h^{(l-1)})^\top $?**  
> For a single weight $ W^{(l)}_{ij} $, $ \frac{\partial J}{\partial W^{(l)}_{ij}} = \delta^{(l)}_i \cdot h^{(l-1)}_j $.  
> Stacking all $ i,j $, this forms the **outer product** $ \delta^{(l)} (h^{(l-1)})^\top $, yielding $ \nabla_{W^{(l)}} J \in \mathbb{R}^{m_l \times m_{l-1}} $.

> ✅ **Try This Yourself 4.1**:  
> If $ \delta^{(l)} \in \mathbb{R}^5 $, $ h^{(l-1)} \in \mathbb{R}^3 $, what is the shape of $ \nabla_{W^{(l)}} J $?  
> **Answer**: $ 5 \times 3 $, matching $ W^{(l)} $. Correct.

> 🧠 **Cross-Domain Insight**:  
> The gradient $ \nabla_W J = \delta h^\top $ resembles **credit assignment in a startup**. The error $ \delta $ is customer feedback. The input $ h $ is employee effort. The weight update? Equity reallocation—those who contributed most (large $ h $) and were most responsible for failure (large $ \delta $) get the biggest adjustment. It’s performance-based learning.

---

### 5. Worked Example: Two-Layer MLP with Cross-Entropy

We now apply backpropagation to a complete numerical example.

#### Problem Setup

- Input: $ x = \begin{bmatrix} 1 \\ 2 \end{bmatrix} $  
- True label: $ y = \begin{bmatrix} 0 \\ 1 \end{bmatrix} $ (one-hot encoded)  
- Parameters:  
  $$
  W^{(1)} = \begin{bmatrix} 1 & -1 \\ 0 & 2 \end{bmatrix},\ 
  b^{(1)} = \begin{bmatrix} 1 \\ 0 \end{bmatrix},\ 
  W^{(2)} = \begin{bmatrix} 1 & 1 \\ -1 & 2 \end{bmatrix},\ 
  b^{(2)} = \begin{bmatrix} 0 \\ -1 \end{bmatrix}
  $$  
- Activation: ReLU for hidden layer  
- Output: Softmax  
- Loss: Cross-entropy $ J = -\sum_i y_i \log \hat{y}_i $

---

#### Step 1: Forward Pass

**Layer 1**:  
$$
a^{(1)} = W^{(1)}x + b^{(1)} = 
\begin{bmatrix} 1 & -1 \\ 0 & 2 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix} +
\begin{bmatrix} 1 \\ 0 \end{bmatrix} =
\begin{bmatrix} 1 - 2 + 1 \\ 0 + 4 + 0 \end{bmatrix} =
\begin{bmatrix} 0 \\ 4 \end{bmatrix}
$$  
$$
h^{(1)} = \text{ReLU}(a^{(1)}) = \begin{bmatrix} \max(0, 0) \\ \max(0, 4) \end{bmatrix} = \begin{bmatrix} 0 \\ 4 \end{bmatrix}
$$

**Layer 2**:  
$$
a^{(2)} = W^{(2)}h^{(1)} + b^{(2)} = 
\begin{bmatrix} 1 & 1 \\ -1 & 2 \end{bmatrix}
\begin{bmatrix} 0 \\ 4 \end{bmatrix} +
\begin{bmatrix} 0 \\ -1 \end{bmatrix} =
\begin{bmatrix} 0 + 4 \\ 0 + 8 \end{bmatrix} +
\begin{bmatrix} 0 \\ -1 \end{bmatrix} =
\begin{bmatrix} 4 \\ 7 \end{bmatrix}
$$  
$$
\hat{y} = \text{softmax}(a^{(2)}) = \frac{1}{e^4 + e^7} \begin{bmatrix} e^4 \\ e^7 \end{bmatrix} \approx \frac{1}{54.60 + 1096.63} \begin{bmatrix} 54.60 \\ 1096.63 \end{bmatrix} \approx \begin{bmatrix} 0.0474 \\ 0.9526 \