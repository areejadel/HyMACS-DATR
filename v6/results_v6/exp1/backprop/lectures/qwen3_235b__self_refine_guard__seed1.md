**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Remember**: Identify the components of a computational graph and the role of each in forward and backward passes.  
2. **Understand**: Explain how the chain rule applies recursively in backpropagation and why reverse-mode automatic differentiation is efficient for scalar losses.  
3. **Apply**: Compute gradients step by step in a two-layer MLP using backpropagation, including activation derivatives and matrix operations.  
4. **Analyze**: Diagnose common failure modes (e.g., vanishing gradients) and match them to architectural solutions (e.g., ReLU, skip connections).  
5. **Create**: Design a minimal PyTorch-like computational graph for a scalar function, implementing automatic gradient computation.

---

### Prerequisites: Required Background

Before proceeding, confirm familiarity with the following concepts:

- **Partial derivatives**: For a scalar function $ J = f(a, b) $, the partial derivative $ \frac{\partial J}{\partial a} $ measures the rate of change of $ J $ with respect to $ a $, holding $ b $ constant.
- **Multivariable chain rule**: If $ J = f(g(x)) $, then $ \frac{\partial J}{\partial x} = \frac{\partial J}{\partial g} \cdot \frac{\partial g}{\partial x} $. In vector form, for intermediate variables $ \mathbf{u}_j $,  
  $$
  \frac{\partial J}{\partial \mathbf{x}} = \sum_j \frac{\partial J}{\partial \mathbf{u}_j} \cdot \frac{\partial \mathbf{u}_j}{\partial \mathbf{x}}.
  $$
- **Matrix calculus**: Given $ \mathbf{z} = \mathbf{W}\mathbf{x} $, the gradient of $ J $ with respect to $ \mathbf{x} $ is $ \frac{\partial J}{\partial \mathbf{x}} = \mathbf{W}^\top \frac{\partial J}{\partial \mathbf{z}} $. Gradient dimensions must match those of the corresponding parameter.
- **Forward pass**: For layer $ l $, compute pre-activation $ \mathbf{z}^{(l)} = \mathbf{W}^{(l)}\mathbf{a}^{(l-1)} + \mathbf{b}^{(l)} $, then activation $ \mathbf{a}^{(l)} = \sigma(\mathbf{z}^{(l)}) $. The loss $ J $ compares output $ \hat{\mathbf{y}} $ to target $ \mathbf{y} $.

> 🔍 **Quick Check**: Suppose $ \mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b} $ and $ \frac{\partial J}{\partial \mathbf{z}} = \boldsymbol{\delta} $. What is $ \frac{\partial J}{\partial \mathbf{x}} $?  
> *Answer*: $ \frac{\partial J}{\partial \mathbf{x}} = \mathbf{W}^\top \boldsymbol{\delta} $. This relationship is central to gradient propagation.

**Common Misconception**: “Gradients flow forward like activations.”  
No—activations propagate forward during the forward pass; gradients propagate backward during the backward pass. The two passes traverse the same computational graph in opposite directions.

---

### Intuition: The Need for Backpropagation — A Paradox in Efficiency

Imagine tuning a telescope to focus on a distant star. You can nudge each of its 10,000 mechanical joints one at a time, measuring how each affects image sharpness—a brute-force method. Or, you could analyze the optical path in reverse, tracing how light *arrives* at your eye, and deduce all adjustments at once.

Neural networks face the same paradox: millions of parameters, one loss. How can we compute all gradients efficiently?

Finite differences would require one forward pass per parameter—impossible at scale. Yet, **backpropagation computes all gradients in just one backward pass**, regardless of parameter count.

This isn't magic—it's **reverse-time causality in computation**. Just as a detective reconstructs a crime from its aftermath, backpropagation reconstructs parameter influences from the final loss.

> 🧩 **Concrete Example**: You bake cookies using flour ($ f $), sugar ($ s $), and eggs ($ e $). Tastiness $ T $ depends on batter $ b = f + 2s $, then $ c = b \cdot e $, and finally $ T = c^2 $.  
> You want $ \frac{\partial T}{\partial f} $. Instead of baking many batches, work backward:  
> - $ \frac{\partial T}{\partial c} = 2c $  
> - $ \frac{\partial T}{\partial b} = \frac{\partial T}{\partial c} \cdot \frac{\partial c}{\partial b} = 2c \cdot e $  
> - $ \frac{\partial T}{\partial f} = \frac{\partial T}{\partial b} \cdot \frac{\partial b}{\partial f} = 2c \cdot e \cdot 1 $  
> A single backward pass yields the gradient—this is the essence of backpropagation.

Now, try this:

> 💡 **Try This Yourself**: Let $ J = \sin(a + b) $, $ a = x^2 $, $ b = 2y $. Compute $ \frac{\partial J}{\partial x} $ and $ \frac{\partial J}{\partial y} $ using a backward pass.  
> *Hint*: Start from $ \frac{\partial J}{\partial J} = 1 $, propagate backward through $ a $ and $ b $.  
> *Answer*: $ \frac{\partial J}{\partial x} = \cos(x^2 + 2y) \cdot 2x $, $ \frac{\partial J}{\partial y} = \cos(x^2 + 2y) \cdot 2 $

Having built intuition, we now formalize the process.

---

### Formalism: Computational Graphs and Reverse-Mode Differentiation

A **computational graph** represents a function as nodes (variables) and edges (operations). In neural networks, nodes include inputs, weights, pre-activations, activations, and loss.

Let $ J $ be the scalar loss. The goal is to compute $ \frac{\partial J}{\partial u_i} $ for every node $ u_i $. Using the **generalized chain rule**:
$$
\frac{\partial J}{\partial u_i} = \sum_{j \in \text{children}(u_i)} \frac{\partial J}{\partial u_j} \cdot \frac{\partial u_j}{\partial u_i}.
$$
The gradient at $ u_i $ is the sum over all direct dependents $ u_j $, weighted by their local Jacobians.

We compute gradients in **reverse topological order**, starting from $ J $, where $ \frac{\partial J}{\partial J} = 1 $. This ensures that when computing $ \frac{\partial J}{\partial u_i} $, all $ \frac{\partial J}{\partial u_j} $ for $ j \in \text{children}(u_i) $ are already known.

> 💡 **Why reverse order?** Only $ J $ has a known gradient (equal to 1). All other gradients depend on it and must be propagated backward.

This method uses **dynamic programming**: each gradient is computed once and reused. Total cost is one backward pass, compared to $ O(n) $ for finite differences.

> 📘 **Worked Example**: Let $ J = (w_1 x + w_2)^2 $, with $ x = 3 $, $ w_1 = 2 $, $ w_2 = 1 $.  
> Define intermediate variables:  
> - $ a = w_1 x $  
> - $ b = a + w_2 $  
> - $ J = b^2 $  
>  
> **Forward pass**:  
> - $ a = 2 \cdot 3 = 6 $  
> - $ b = 6 + 1 = 7 $  
> - $ J = 7^2 = 49 $  
>  
> **Backward pass** (start from $ J $):  
> - $ \frac{\partial J}{\partial b} = 2b = 14 $  
> - $ \frac{\partial J}{\partial a} = \frac{\partial J}{\partial b} \cdot \frac{\partial b}{\partial a} = 14 \cdot 1 = 14 $  
> - $ \frac{\partial J}{\partial w_1} = \frac{\partial J}{\partial a} \cdot \frac{\partial a}{\partial w_1} = 14 \cdot x = 14 \cdot 3 = 42 $  
>  
> Result: $ \frac{\partial J}{\partial w_1} = 42 $.  
> Verification: $ J = (2 \cdot 3 + 1)^2 = 49 $, $ \frac{dJ}{dw_1} = 2(6 + 1) \cdot 3 = 42 $. ✔️

> 🔍 **Quick Check**: What is $ \frac{\partial J}{\partial w_2} $?  
> *Answer*: $ \frac{\partial J}{\partial w_2} = \frac{\partial J}{\partial b} \cdot \frac{\partial b}{\partial w_2} = 14 \cdot 1 = 14 $.  
> Confirm by direct differentiation.

**Common Misconception**: “We can compute gradients during the forward pass.”  
No—gradients depend on the final loss. The influence of an early parameter on $ J $ cannot be known until $ J $ is computed. Hence, forward pass *then* backward pass.

---

### Backpropagation in a Two-Layer MLP: Full Derivation

We now apply backpropagation to a two-layer multilayer perceptron (MLP).

#### Network Definition

- Input: $ \mathbf{x} \in \mathbb{R}^d $
- Hidden layer:  
  $$
  \mathbf{z}^{(1)} = \mathbf{W}^{(1)}\mathbf{x} + \mathbf{b}^{(1)}, \quad \mathbf{h} = \sigma(\mathbf{z}^{(1)})
  $$
- Output:  
  $$
  \hat{\mathbf{y}} = \mathbf{W}^{(2)}\mathbf{h} + \mathbf{b}^{(2)}
  $$
- Loss:  
  $$
  J = \frac{1}{2} \| \mathbf{y} - \hat{\mathbf{y}} \|^2
  $$

We compute gradients with respect to $ \mathbf{W}^{(1)}, \mathbf{W}^{(2)}, \mathbf{b}^{(1)}, \mathbf{b}^{(2)} $.

> 💡 **Key idea**: Define the error signal $ \boldsymbol{\delta}^{(l)} = \frac{\partial J}{\partial \mathbf{z}^{(l)}} $, the gradient of $ J $ with respect to pre-activations. These signals propagate backward through the network.

#### Step-by-Step Backward Pass

**1. Output layer ($ l=2 $)**  
- $ \frac{\partial J}{\partial \hat{\mathbf{y}}} = \hat{\mathbf{y}} - \mathbf{y} =: \boldsymbol{\delta}^{(2)} $
- Since $ \hat{\mathbf{y}} = \mathbf{W}^{(2)}\mathbf{h} + \mathbf{b}^{(2)} $:  
  - $ \frac{\partial J}{\partial \mathbf{W}^{(2)}} = \boldsymbol{\delta}^{(2)} \mathbf{h}^\top $ (outer product)  
  - $ \frac{\partial J}{\partial \mathbf{b}^{(2)}} = \boldsymbol{\delta}^{(2)} $
- Gradient with respect to hidden activations:  
  $$
  \frac{\partial J}{\partial \mathbf{h}} = (\mathbf{W}^{(2)})^\top \boldsymbol{\delta}^{(2)}
  $$

**2. Hidden layer ($ l=1 $)**  
- $ \mathbf{h} = \sigma(\mathbf{z}^{(1)}) $, so by the chain rule:  
  $$
  \boldsymbol{\delta}^{(1)} = \frac{\partial J}{\partial \mathbf{z}^{(1)}} = \frac{\partial J}{\partial \mathbf{h}} \odot \sigma'(\mathbf{z}^{(1)})
  $$
  where $ \odot $ denotes element-wise multiplication.
- Then:  
  - $ \frac{\partial J}{\partial \mathbf{W}^{(1)}} = \boldsymbol{\delta}^{(1)} \mathbf{x}^\top $  
  - $ \frac{\partial J}{\partial \mathbf{b}^{(1)}} = \boldsymbol{\delta}^{(1)} $

> 📘 **Worked Example**:  
> Parameters:  
> - $ \mathbf{x} = [1, 2]^\top $  
> - $ \mathbf{W}^{(1)} = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}, \quad \mathbf{b}^{(1)} = [0, 0]^\top $  
> - $ \sigma = \text{ReLU} $  
> - $ \mathbf{W}^{(2)} = [1, -1], \quad \mathbf{b}^{(2)} = 0 $  
> - $ \mathbf{y} = 3 $  
>  
> **Forward pass**:  
> - $ \mathbf{z}^{(1)} = \mathbf{W}^{(1)}\mathbf{x} = [1, 2]^\top $  
> - $ \mathbf{h} = \text{ReLU}(\mathbf{z}^{(1)}) = [1, 2]^\top $  
> - $ \hat{\mathbf{y}} = [1, -1] \cdot [1, 2] = -1 $  
> - $ J = \frac{1}{2}(3 - (-1))^2 = 8 $  
>  
> **Backward pass**:  
> - $ \boldsymbol{\delta}^{(2)} = \hat{\mathbf{y}} - \mathbf{y} = -4 $  
> - $ \frac{\partial J}{\partial \mathbf{W}^{(2)}} = \boldsymbol{\delta}^{(2)} \mathbf{h}^\top = -4 \cdot [1, 2] = [-4, -8] $  
> - $ \frac{\partial J}{\partial \mathbf{b}^{(2)}} = -4 $  
> - $ \frac{\partial J}{\partial \mathbf{h}} = (\mathbf{W}^{(2)})^\top \boldsymbol{\delta}^{(2)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix} \cdot (-4) = [-4, 4]^\top $  
> - $ \sigma'(\mathbf{z}^{(1)}) = [1, 1]^\top $ (since $ z_i > 0 $)  
> - $ \boldsymbol{\delta}^{(1)} = [-4, 4]^\top \odot [1, 1]^\top = [-4, 4]^\top $  
> - $ \frac{\partial J}{\partial \mathbf{W}^{(1)}} = \boldsymbol{\delta}^{(1)} \mathbf{x}^\top = \begin{bmatrix} -4 \\ 4 \end{bmatrix} \begin{bmatrix} 1 & 2 \end{bmatrix} = \begin{bmatrix} -4 & -8 \\ 4 & 8 \end{bmatrix} $  
> - $ \frac{\partial J}{\partial \mathbf{b}^{(1)}} = [-4, 4]^\top $  
>  
> All gradients are computed in one backward pass.

> 🔍 **Quick Check**: Why is $ \frac{\partial J}{\partial \mathbf{W}^{(1)}} $ a $ 2 \times 2 $ matrix?  
> *Answer*: $ \mathbf{W}^{(1)} \in \mathbb{R}^{2 \times 2} $, so its gradient must have the same shape. The outer product $ \boldsymbol{\delta}^{(1)} \mathbf{x}^\top $ ensures dimensional consistency.

**Common Misconception**: “We backpropagate the loss value.”  
No—we propagate gradients. The loss $ J $ is a scalar; gradients are vectors or matrices that inform parameter updates.

---

### Symmetry with Forward Propagation: The Adjoint Principle

A key insight: the backward pass applies the **adjoint** (transpose) of each forward operation.

- Forward: $ \mathbf{z} = \mathbf{W} \mathbf{a} $ → Backward: $ \frac{\partial J}{\partial \mathbf{a}} = \mathbf{W}^\top \frac{\partial J}{\partial \mathbf{z}} $
- Forward: Convolution → Backward: Transposed convolution
- Forward: Reshape → Backward: Reshape (same shape)

This symmetry arises because the gradient transformation is the **adjoint of the linearized forward operation**.

> 🌍 **Real-World Case Study**: In **U-Net** for medical image segmentation, the encoder applies convolutions and downsampling. The decoder uses transposed convolutions to upsample, mirroring the forward path. This ensures precise gradient alignment, enabling accurate pixel-level predictions. Without this symmetry, fine spatial details would degrade during backpropagation.

> 🔍 **Quick Check**: If $ \mathbf{y} = \mathbf{A} \mathbf{x} $, what is $ \frac{\partial J}{\partial \mathbf{x}} $ given $ \frac{\partial J}{\partial \mathbf{y}} $?  
> *Answer*: $ \frac{\partial J}{\partial \mathbf{x}} = \mathbf{A}^\top \frac{\partial J}{\partial \mathbf{y}} $

**Common Misconception**: “Backpropagation is just calculus.”  
It is more—it is a computational pattern. The adjoint principle allows deep learning frameworks to define backward rules automatically for any differentiable operation.

> 💡 **Cross-Domain Analogy**: Think of backpropagation like **feedback control in aerospace systems**. In a rocket guidance loop, sensors measure deviation from trajectory (analogous to loss), and a controller computes corrective forces. But instead of adjusting thrusters in real time, backpropagation computes *which initial design parameters* (e.g., fin shape, fuel curve) would reduce future error—by running the flight dynamics model *in reverse*. This is **adjoint-based optimization**, used in real aircraft design. Neural networks do the same: they optimize parameters by simulating error propagation backward through the computational "dynamics."

> 🧩 **Try This Yourself**: Consider a simple RNN cell: $ h_t = \tanh(W h_{t-1} + U x_t) $. Sketch the computational graph over two time steps. Where would gradients "accumulate" over time? Why might this cause vanishing or exploding gradients?

---

### Automatic Differentiation: Implementation in PyTorch

Backpropagation is a special case of **reverse-mode automatic differentiation (autodiff)**.

Two modes exist:
- **Forward mode**: Efficient when inputs are few and outputs many.
- **Reverse mode**: Efficient when inputs are many and output is scalar—ideal for deep learning (millions of weights, one loss).

**PyTorch’s autograd mechanism**:
1. **Forward pass**: Each operation (e.g., `+`, `*`, `ReLU`) records its inputs and function on a