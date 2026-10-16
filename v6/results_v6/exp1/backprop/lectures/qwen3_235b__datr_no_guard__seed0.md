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

Now imagine this: you're a coach reviewing game footage. The final score was bad—but was it the offense, defense, or play-calling? You don’t just say “try harder.” You break down every play, assign responsibility, and fix what failed.

Backpropagation is the **film session** of neural networks: it doesn’t just measure loss—it dissects *who* contributed to the error and *how much*, layer by layer, using calculus as its playbook.

But here’s the twist: unlike a coach watching video, the network has no eyes. It can’t “see” which neurons misbehaved. It only sees the final score—the loss. So how does it trace blame backward through layers of nonlinear transformations, where each neuron’s output depends on dozens of inputs, all tangled together?

This is the **credit assignment problem**—and backpropagation solves it with precision, not guesswork.

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

> 🔍 **Try this yourself**:  
> Suppose the first neuron in the hidden layer had $ z_1^{(1)} = 0 $. Would it receive any gradient? What if $ z_1^{(1)} = 10^{-8} $? Test your intuition—then check the derivative of ReLU.

Pause here. Before reading the backward pass, **sketch the computational graph** from $ \mathbf{x} $ to $ J $. Label each node: $ \mathbf{z}^{(1)}, \mathbf{h}, \hat{y}, J $. Now, trace a path from $ J $ back to $ w_{21}^{(1)} $, the weight connecting input 1 to hidden neuron 2. How many functions compose along this path? Write down the chain rule for $ \partial J / \partial w_{21}^{(1)} $—don’t calculate it yet. Just map the dependencies.

Now, here’s a challenge: **pick one weight that you suspect will have zero gradient**. Justify your guess using the forward pass values. Then, as we compute gradients, verify whether your prediction was correct. This turns passive reading into active investigation.

This act of mapping paths builds muscle memory for backpropagation. You’re not just computing—you’re auditing influence.

---

### Step 3: Intuition — How Backpropagation Works

Imagine a long chain of people passing buckets to put out a fire. The last person splashes water everywhere. Who’s responsible? The one who missed—or the one who passed a weak bucket?

Now scale this: imagine not one bucket line, but a **circuit board** where each wire carries both signal and sensitivity. When the final output is wrong, the error doesn’t vanish—it propagates backward like a voltage surge, revealing which components most amplified the fault.

Backpropagation treats the network like a **responsibility pipeline**: each neuron passes not just data forward, but *blame* backward. The loss is the final report card, and backpropagation distributes credit and fault through the chain rule.

Here’s the tension:  
We know $ \partial J / \partial \hat{y} $—that’s easy. But no single neuron directly controls $ \hat{y} $. Each weight is buried under layers of nonlinear transformations. To reach them, we must **decompose influence through composition**.

This is where the chain rule becomes a detective tool. Every derivative is a trail:  
$ \frac{\partial J}{\partial w} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial h_2} \cdot \frac{\partial h_2}{\partial z_2^{(1)}} \cdot \frac{\partial z_2^{(1)}}{\partial w} $

But computing this naively for every weight would be exponential in depth. Backpropagation avoids this by **reusing intermediate gradients**, like memoizing subproblems in dynamic programming.

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
> Suppose you could only measure the impact of one weight on the loss. Which would give you the most information: a weight near the input or near the output? Why? Sketch a short computational graph and apply the chain rule mentally.

Now simulate a neuron’s perspective: you’re a hidden unit, and you’ve just been told your output contributed to a large error. You don’t know *how much* yet. What do you need to compute your responsibility?  
1. How sensitive the loss is to your output: $ \partial J / \partial a_i $  
2. How your output responds to your input: $ \partial a_i / \partial z_i $  
3. How your pre-activation depends on your inputs: $ \partial z_i / \partial w_{ij} $  

But you don’t have $ \partial J / \partial a_i $ directly. Instead, you get a message from above: “Your downstream effect is $ \delta^{(l+1)} $, and your outgoing weights are $ w_k $.” So you compute:  
$$
\frac{\partial J}{\partial a_i} = \sum_k \delta_k^{(l+1)} w_{ki}
$$
This is **credit assignment via weighted sum of downstream blame**—a principle seen in economic input-output models and ecosystem energy flow.

Here’s a striking analogy: think of the network as a **supply chain**. Raw materials (input) flow forward through factories (layers), each adding value. When the final product fails quality control (high loss), auditors don’t inspect every screw. They trace backward: which factory introduced the defect? How much did earlier stages amplify it? The cost of failure propagates upstream, weighted by each stage’s contribution—just like $ \delta^{(l)} $.

> 🔍 **Try this yourself**:  
> Imagine a deep network where all weights are 0.5 and all activations are sigmoid. After five layers, what happens to a gradient signal? Compute $ (0.5)^5 \times (\sigma'(z))^5 $ for $ z=0 $. Now try $ z=5 $. What does this imply for learning in early layers?

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

Think of this as a **wiring diagram**: each hidden neuron contributes to the output through its outgoing weight. So the "upstream" gradient splits and scales by those weights—like current dividing across parallel resistors in a circuit.

But there’s a catch: only *active* neurons can carry blame. If a neuron was off (ReLU output 0), changing its input does nothing—it’s electrically disconnected. So we **gate** the backward flow with the derivative of the activation.

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
> What would happen to the gradients if we replaced ReLU with sigmoid? Would gradient sparsity still occur? Test it numerically using $ z = 3 $ and $ z = -3 $. Now consider a deep network: what happens when you chain five sigmoid gradients of ~0.1?

Before moving on, **compute the gradient for $ w_{11}^{(1)} $** by hand using only the chain rule—no backprop formulas. Follow the path:  
$ w_{11}^{(1)} \to z_1^{(1)} \to h_1 \to \hat{y} \to J $.  
Did you get zero? Why? Now compare with the matrix result. This manual verification ensures you’re not just running code—you’re auditing causality.

Now, here’s a deeper question: **why did $ w_{11}^{(1