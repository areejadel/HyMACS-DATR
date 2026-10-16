**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Recall** the purpose of backpropagation and identify its role in training neural networks.  
2. **Explain** how the chain rule is applied during the backward pass to compute gradients efficiently.  
3. **Compute** gradients for weights and biases in a simple multilayer perceptron using backpropagation, step by step.  
4. **Analyze** common pitfalls (e.g., vanishing gradients) and describe practical strategies to mitigate them.  
5. **Apply** backpropagation logic to a minibatch setting using vectorized operations.

---

### Prerequisites

Before proceeding, ensure familiarity with the following concepts:  
- **Calculus**: derivatives, partial derivatives, and the chain rule.  
- **Linear algebra**: matrix-vector multiplication, transposition, and the element-wise (Hadamard) product.  
- **Neural network fundamentals**: layers, weights, biases, activation functions, and forward propagation.  
- **Loss functions**: mean squared error (MSE) and their role in parameter optimization.

We build exclusively on these foundations. No additional mathematical or algorithmic background is assumed.

---

### Step 1: A Concrete Example — Training a Small Network

Here’s a puzzle:  
You’re given a neural network that predicts house prices. After one forward pass, it outputs \$500K—but the true price is \$200K. You adjust *all* the weights slightly to reduce the error.  
But what if only *half* the network was responsible for the mistake?  
Should the quiet, well-behaved neurons be punished just like the loud, overconfident ones?

Now imagine you’re a detective investigating a blackout in a power grid. The lights went out at the far end—but was it a faulty transformer, a broken wire, or a misconfigured switch upstream? You can’t fix what you can’t trace.

Backpropagation is the **forensic accountant of neural networks**: it doesn’t just measure error—it traces the flow of responsibility backward through every connection, assigning precise blame using the chain rule. It answers: *Which parameter, if nudged slightly, would reduce the loss most?*

We begin with a fully worked example to ground abstract concepts. Consider a neural network with one hidden layer.

#### Network Architecture  
- Input: $ \mathbf{x} \in \mathbb{R}^2 $  
- Hidden layer: 2 neurons, ReLU activation $ f(z) = \max(0, z) $  
- Output: scalar $ \hat{y} \in \mathbb{R} $, linear (no activation)  
- Loss function: Mean Squared Error $ J = \frac{1}{2}(y - \hat{y})^2 $

#### Parameters  
- Weight matrix (input to hidden): $ \mathbf{W}^{(1)} \in \mathbb{R}^{2 \times 2} $, bias $ \mathbf{b}^{(1)} \in \mathbb{R}^2 $  
- Weight vector (hidden to output): $ \mathbf{w}^{(2)} \in \mathbb{R}^2 $, bias $ b^{(2)} \in \mathbb{R} $

#### Fixed Values for One Training Example  
- Input: $ \mathbf{x} = \begin{bmatrix} 1 \\ 2 \end{bmatrix} $, target: $ y = 1 $  
- $ \mathbf{W}^{(1)} = \begin{bmatrix} 1 & -1 \\ 0 & 2 \end{bmatrix},\quad \mathbf{b}^{(1)} = \begin{bmatrix} 0 \\ 1 \end{bmatrix} $  
- $ \mathbf{w}^{(2)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix},\quad b^{(2)} = 0 $

Our goal is to compute the gradients:  
$$
\frac{\partial J}{\partial \mathbf{W}^{(1)}},\quad
\frac{\partial J}{\partial \mathbf{b}^{(1)}},\quad
\frac{\partial J}{\partial \mathbf{w}^{(2)}},\quad
\frac{\partial J}{\partial b^{(2)}}
$$
These gradients will be used in gradient descent updates.

> 💡 **Why start with an example?**  
> A concrete case clarifies *what* backpropagation computes and *why*—before introducing general formulas. It reduces abstraction overload and anchors intuition.

> 🔍 **Try this yourself**:  
> Before we compute anything, take 60 seconds. Sketch the network: label neurons, weights, and activations. Then guess: which weight in $ \mathbf{W}^{(1)} $ do you think has the largest gradient magnitude? Why? Write it down—then check your intuition after Step 4.

---

### Step 2: Forward Pass — Compute and Store Intermediate Values

We compute activations layer by layer, storing pre-activations $ \mathbf{z}^{(l)} $ and outputs $ \mathbf{a}^{(l)} $ for use in the backward pass.

#### Layer 1 Pre-activation  
$$
\mathbf{z}^{(1)} = \mathbf{W}^{(1)} \mathbf{x} + \mathbf{b}^{(1)} = 
\begin{bmatrix} 1 & -1 \\ 0 & 2 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
+ \begin{bmatrix} 0 \\ 1 \end{bmatrix}
= \begin{bmatrix} -1 \\ 5 \end{bmatrix}
$$

#### Apply ReLU Activation  
$$
\mathbf{h} = \mathbf{a}^{(1)} = \max(0, \mathbf{z}^{(1)}) = \begin{bmatrix} 0 \\ 5 \end{bmatrix}
$$

#### Output Layer (Linear)  
$$
\hat{y} = \mathbf{w}^{(2)\top} \mathbf{h} + b^{(2)} = 
\begin{bmatrix} 2 & -1 \end{bmatrix}
\begin{bmatrix} 0 \\ 5 \end{bmatrix}
+ 0 = -5
$$

#### Compute Loss  
$$
J = \frac{1}{2}(y - \hat{y})^2 = \frac{1}{2}(1 - (-5))^2 = \frac{1}{2}(36) = 18
$$

We store $ \mathbf{z}^{(1)} $, $ \mathbf{h} $, and $ \hat{y} $—these are required during backpropagation.

> ✅ **Formative Check**  
> If $ \mathbf{z}^{(1)} = \begin{bmatrix} -2 \\ 3 \end{bmatrix} $, what is $ \mathbf{h} $?  
> **Answer**: $ \begin{bmatrix} 0 \\ 3 \end{bmatrix} $

> ❗ **Common Misconception**  
> *“We can recompute activations during backpropagation.”*  
> While mathematically valid, recomputation is inefficient. Storing activations trades memory for speed. For deep networks, this trade-off is essential—memory usage scales linearly with depth.

---

### Step 3: Intuition — How Backpropagation Works

Imagine a long chain of people passing buckets to put out a fire. The last person splashes water everywhere. Who’s responsible? The one who missed—or the one who passed a weak bucket?

Now consider a **supply chain**: a defective smartphone reaches a customer. Was it the screen supplier, the chip manufacturer, or the assembly robot? To fix the system, you need to trace the fault backward through each stage, weighted by contribution.

Backpropagation treats the network like a **responsibility pipeline**: each neuron passes not just data forward, but *blame* backward. The loss is the final report card, and backpropagation distributes credit and fault through the chain rule.

The key idea: propagate error gradients backward from the output to the input, reusing intermediate derivatives to avoid redundant computation.

Define the **error signal** (or local gradient) at layer $ l $:  
$$
\delta_i^{(l)} = \frac{\partial J}{\partial z_i^{(l)}}
$$
This measures how a small change in the pre-activation of neuron $ i $ affects the loss.

For a weight $ w_{ij}^{(l)} $ connecting neuron $ j $ in layer $ l-1 $ to neuron $ i $ in layer $ l $:  
$$
\frac{\partial J}{\partial w_{ij}^{(l)}} = \frac{\partial J}{\partial z_i^{(l)}} \cdot \frac{\partial z_i^{(l)}}{\partial w_{ij}^{(l)}} = \delta_i^{(l)} \cdot a_j^{(l-1)}
$$
Thus, the gradient is the product of the **sensitivity** $ \delta_i^{(l)} $ and the **input** $ a_j^{(l-1)} $.

> 💡 **Why “backward” propagation?**  
> We begin at the output where $ \partial J / \partial \hat{y} $ is known, then recursively compute $ \delta^{(l)} $ for earlier layers. This reverse traversal enables efficient reuse of gradients—achieving computational complexity linear in the number of parameters.

> 🔍 **Try this yourself**:  
> Suppose you could only measure the impact of one weight on the loss. Which would give you the most information: a weight near the input or near the output? Why? Write a one-sentence justification—then compare it to the gradient computation in Step 4.

---

### Step 4: Backward Pass — Step-by-Step Gradient Computation

We now compute gradients using the stored forward pass values.

#### Output Layer: Compute $ \delta^{(2)} $

Since $ \hat{y} = z^{(2)} $ (linear output),  
$$
\delta^{(2)} = \frac{\partial J}{\partial \hat{y}} = -(y - \hat{y}) = -(1 - (-5)) = -6
$$

Now compute gradients for output parameters:  
- $ \frac{\partial J}{\partial \mathbf{w}^{(2)}} = \delta^{(2)} \cdot \mathbf{h} = -6 \cdot \begin{bmatrix} 0 \\ 5 \end{bmatrix} = \begin{bmatrix} 0 \\ -30 \end{bmatrix} $  
- $ \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = -6 $

> ✅ **Formative Check**  
> If $ \hat{y} = 3 $, $ y = 5 $, what is $ \delta^{(2)} $?  
> **Answer**: $ -(5 - 3) = -2 $

---

#### Hidden Layer: Propagate $ \delta $ Backward

Here’s a tension: we know how the output affects the loss ($ \delta^{(2)} $), but how does the hidden layer affect the output? And how much of that blame should flow back?

Think of this as a **wiring diagram**: each hidden neuron contributes to the output through its outgoing weight. So the "upstream" gradient splits and scales by those weights.

But here’s a twist: not all neurons are listening. The first neuron in the hidden layer output $ h_1 = 0 $—it’s *asleep*. Should it be held accountable?

**Analogy**: Imagine a team presentation where only one member speaks. If the talk fails, should both members get equal feedback? No—only the speaker bears responsibility. Similarly, ReLU zeros out inactive neurons, and backpropagation respects that: no activation, no blame.

The general recurrence is:  
$$
\delta^{(l)} = \left( (\mathbf{W}^{(l+1)})^\top \delta^{(l+1)} \right) \odot f'^{(l)}(\mathbf{z}^{(l)})
$$

Here, $ \mathbf{W}^{(2)} $ is a column vector $ \mathbf{w}^{(2)} $, so:  
$$
(\mathbf{w}^{(2)})^\top \delta^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix} (-6) = -12 \quad \text{(scalar)}
$$
But this gives only one scalar. Instead, we interpret the contribution to each hidden unit as:  
$$
\text{upstream gradient} = \delta^{(2)} \cdot \mathbf{w}^{(2)} = -6 \cdot \begin{bmatrix} 2 \\ -1 \end{bmatrix} = \begin{bmatrix} -12 \\ 6 \end{bmatrix}
$$
This vector represents how changes in each hidden unit’s output affect $ J $.

Now apply the derivative of ReLU:  
- $ f'(z) = \begin{cases} 1 & z > 0 \\ 0 & z \leq 0 \end{cases} $  
- $ \mathbf{z}^{(1)} = \begin{bmatrix} -1 \\ 5 \end{bmatrix} \Rightarrow f'(\mathbf{z}^{(1)}) = \begin{bmatrix} 0 \\ 1 \end{bmatrix} $

Thus,  
$$
\delta^{(1)} = \begin{bmatrix} -12 \\ 6 \end{bmatrix} \odot \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 0 \\ 6 \end{bmatrix}
$$

> 💡 **Why is the first component zero?**  
> The first neuron is inactive ($ z_1^{(1)} = -1 < 0 $), so its output does not influence $ \hat{y} $. Therefore, its parameters receive zero gradient—this is **gradient sparsity** due to ReLU.

Now compute gradients for the first layer:  
- $ \frac{\partial J}{\partial \mathbf{W}^{(1)}} = \delta^{(1)} \mathbf{x}^\top = \begin{bmatrix} 0 \\ 6 \end{bmatrix} \begin{bmatrix} 1 & 2 \end{bmatrix} = \begin{bmatrix} 0 & 0 \\ 6 & 12 \end{bmatrix} $  
- $ \frac{\partial J}{\partial \mathbf{b}^{(1)}} = \delta^{(1)} = \begin{bmatrix} 0 \\ 6 \end{bmatrix} $

> ✅ **Formative Check**  
> Suppose $ \mathbf{z}^{(1)} = \begin{bmatrix} 3 \\ -4 \end{bmatrix} $, $ \delta^{(2)} = 4 $, $ \mathbf{w}^{(2)} = \begin{bmatrix} 1 \\ 3 \end{bmatrix} $. Compute $ \delta^{(1)} $.  
> **Answer**: $ (4) \cdot \begin{bmatrix} 1 \\ 3 \end{bmatrix} = \begin{bmatrix} 4 \\ 12 \end{bmatrix} $, $ f'(\mathbf{z}^{(1)}) = \begin{bmatrix} 1 \\ 0 \end{bmatrix} $, so $ \delta^{(1)} = \begin{bmatrix} 4 \\ 0 \end{bmatrix} $

> 🔍 **Try this yourself**:  
> What would happen to the gradients if we replaced ReLU with sigmoid? Would gradient sparsity still occur? Compute $ f'(z) $ for $ z = -1 $ and $ z = 5 $ using $ \sigma'(z) = \sigma(z)(1 - \sigma(z)) $, then recompute $ \delta^{(1)} $. Compare the results—what changes in the blame assignment?

---

### Step 5: General Algorithm and Vectorization

Backpropagation isn’t magic—it’s **structured calculus**. The full algorithm:

1. Perform forward pass, storing $ \mathbf{z}^{(l)} $, $ \mathbf{a}^{(l)} $.  
2. Compute $ \delta^{(L)} = \frac{\partial J}{\partial \mathbf{z}^{(L)}} $ at output.  
3. For each layer $ l = L-1 $ down to 1:  
   - $ \delta^{(l)} = \left( (\mathbf{W}^{(l+1)})^\top \delta^{(l+1)} \right) \odot f'^{(l)}(\mathbf{z}^{(l)}) $  
   - $ \frac{\partial J}{\partial \mathbf{W}^{(l)}} = \delta^{(l)} (\mathbf{a}^{(l-1)})^\top $  
   - $ \frac{\partial J}{\partial \mathbf{b}^{(l)}} = \delta^{(l)} $

In minibatch training, these operations become **matrix-matrix** instead of matrix-vector:  
- $ \mathbf{A}^{(l-1)} \in \mathbb{R}^{d_{l-1} \times B} $: activations for $ B $ examples  
- $ \Delta^{(l)} \in \mathbb{R}^{d_l \times B} $: error signals for $ B $ examples  
- Then: $ \frac{\partial J}{\partial \mathbf{W}^{(l)}} = \Delta^{(l)} (\mathbf{A}^{(l-1)})^\top $

This vectorization is not just faster—it reveals that backpropagation computes a **per-sample gradient**, then averages them implicitly through matrix multiplication.

> 💡 **Cross-domain insight**:  
> Backpropagation is the **adjoint method** from numerical analysis, applied to computational graphs. In physics simulations, the adjoint method computes sensitivity of a final state to initial conditions—just as backpropagation computes sensitivity of loss to parameters. The same math powers both rocket trajectory optimization and deep learning.

> 🔍 **Try this yourself**:  
> Suppose you have a minibatch of 3 examples. Sketch the matrices $ \Delta^{(l)} $ and $ \mathbf{A}^{(l-1)} $. Then compute one element of $ \frac{\partial J}{\partial \mathbf{W}^{(l)}} $ by hand—what does it represent? How is averaging happening?

---

### Step 6: Pitfalls and Practical Insights

#### Vanishing Gradients
In deep networks with sigmoid or tanh, $ f'(z) $ is often << 1. When chained across layers, $ \delta^{(l)} $ shrinks exponentially—early layers learn almost nothing.

> 🔍 **Try this yourself**:  
> Suppose each $ f'(z) \approx 0.1 $, and $ \|(\mathbf{W}^{(l)})^\top\| \approx 1 $. After 5 layers, how much smaller is $ \delta^{(1)} $ than $ \delta^{(5)} $? (Answer: ~$ 10^{-5} $)

ReLU helps: $ f'(z) = 1 $ for $ z > 0 $, so gradients can flow unchanged—if neurons stay active.

#### Exploding Gradients
Opposite problem: gradients grow exponentially. Solution: gradient clipping, weight regularization, or proper initialization (e.g., Xavier/He).

#### Dead Neurons
With ReLU, if a neuron outputs 0 for all examples, its gradient is always 0—it never recovers. This is **irreversible sparsity**. Leaky ReLU or batch normalization can help.

> 💡 **Non-obvious framing**:  
> Backpropagation doesn’t compute *how to fix* the network—it computes *who to blame*. Optimization (e.g., SGD, Adam) decides how to respond. This separation—blame assignment vs. action—is why we can swap optimizers without changing backprop.

---

### Practical Applications in Industry

Backpropagation is not merely an academic construct—it is the computational engine behind nearly every modern deep learning application.