**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Remember** the forward and backward pass steps in a neural network and identify the role of each in gradient computation.  
2. **Understand** how the chain rule applies to a computational graph by tracing gradients through a simple example.  
3. **Apply** the backpropagation algorithm to compute gradients for weights and biases in a two-layer neural network.  
4. **Analyze** the structure of a computational graph to determine the order and dependencies of gradient calculations.  
5. **Create** a complete forward and backward pass for a small neural network given inputs, weights, and a cost function.

---

### 1. Prerequisites

This lecture assumes familiarity with:  
- **Matrix and vector operations**, including matrix-vector multiplication and transposition.  
- **Basic calculus**, particularly the chain rule for composite functions.  
- **Neural network components**: layers, weights $W^{(l)}$, biases $b^{(l)}$, activation functions $f^{(l)}$, and cost functions $J$.

If you can compute $\frac{d}{dw} \sin(w^T x)$, you are prepared. Otherwise, review the multivariable chain rule.

> **Formative Check (Prerequisites)**  
> Compute $\frac{d}{dw} \left( (w^2 + 1)^3 \right)$.

**Solution**:  
Let $u = w^2 + 1$, so $f = u^3$. Then:  
$$
\frac{df}{dw} = \frac{df}{du} \cdot \frac{du}{dw} = 3u^2 \cdot 2w = 6w(w^2 + 1)^2
$$

> 💡 **Interactive Prompt: Predict the Gradient Path**  
> Suppose $w$ increases slightly. Does $f = (w^2 + 1)^3$ increase or decrease when $w = -1$? Use your computed gradient to decide. What does the sign tell you about responsibility?

---

### 2. Forward Pass: Computing Predictions and Cost

**Imagine you're training a neural network to detect tumors in medical scans — but every time it makes a mistake, no one knows which part of the network was responsible.** There’s no mechanism to assign blame, no way to improve. The model fails again tomorrow. This is why backpropagation matters: **without it, deep learning doesn’t learn at all.**

Now imagine a detective arriving at a crime scene. The damage is done. But to solve the case, the detective must reconstruct the sequence of events—trace each action back to its origin. Who opened the door? Who disabled the alarm? In machine learning, **the cost is the crime**, and **backpropagation is the detective**. It doesn’t prevent errors—it investigates them.

The forward pass computes the network’s output and cost from input to prediction. It also stores intermediate values—because **influence flows forward, but responsibility flows backward**.

Each computed value ($z^{(l)}, h^{(l)}, \hat{y}, J$) is preserved for backpropagation. These values form the computational history needed to trace how each parameter contributed to the final cost.

We illustrate this using a two-layer feedforward network.

#### Example Network
- Input: $x = 2$  
- Weights:  
  $$
  W^{(1)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix} \in \mathbb{R}^{2 \times 1},\quad
  W^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix} \in \mathbb{R}^{1 \times 2}
  $$  
- Biases:  
  $$
  b^{(1)} = \begin{bmatrix} 0 \\ 1 \end{bmatrix} \in \mathbb{R}^2,\quad
  b^{(2)} = 0 \in \mathbb{R}
  $$  
- Activation function: $\text{ReLU}(z) = \max(0, z)$  
- Output: $\hat{y} = z^{(2)}$ (linear output layer)  
- Cost function: $J = \frac{1}{2}(\hat{y} - y)^2$, with true label $y = 1$

#### Forward Pass Steps

1. Compute first pre-activation:  
   $$
   z^{(1)} = W^{(1)}x + b^{(1)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix} \cdot 2 + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}
   $$

2. Apply ReLU activation:  
   $$
   h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} \max(0, 2) \\ \max(0, -1) \end{bmatrix} = \begin{bmatrix} 2 \\ 0 \end{bmatrix}
   $$

3. Compute second pre-activation:  
   $$
   z^{(2)} = W^{(2)} h^{(1)} + b^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix} \begin{bmatrix} 2 \\ 0 \end{bmatrix} + 0 = 4
   $$

4. Output prediction:  
   $$
   \hat{y} = z^{(2)} = 4
   $$

5. Compute cost:  
   $$
   J = \frac{1}{2}(4 - 1)^2 = \frac{9}{2} = 4.5
   $$

All intermediate values—$x$, $z^{(1)}$, $h^{(1)}$, $z^{(2)}$, $\hat{y}$, $J$—are stored. The forward pass does **not** compute gradients, but it prepares the data required to compute them.

> ✅ **Misconception Alert**  
> The forward pass computes only predictions and cost. Gradient computation occurs during the backward pass. However, intermediate values must be cached for use in backpropagation.

> **Formative Check (Forward Pass)**  
> Using the same network, what is $h^{(1)}$ if $x = -1$?

**Solution**:  
$z^{(1)} = W^{(1)}(-1) + b^{(1)} = \begin{bmatrix} -1 \\ 1 \end{bmatrix} + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} -1 \\ 2 \end{bmatrix}$, so  
$h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$

> 🔍 **Interactive Prompt: Blame Assignment Preview**  
> With $x = -1$, which neuron in layer 1 is active? If the cost were high, which weight in $W^{(1)}$ should get a gradient update? Why would the other weight remain unchanged?

#### Practical Relevance: Real-World Use in Industry

In industrial applications such as **computer vision** (e.g., object detection in autonomous vehicles) or **natural language processing** (e.g., sentiment analysis in customer feedback), the forward pass is executed billions of times daily across distributed systems. For example, Tesla’s Autopilot runs forward passes on camera inputs in real time to predict lane positions and detect obstacles. Each forward computation must be fast and memory-efficient, but crucially, during training, the intermediate activations ($z^{(l)}, h^{(l)}$) are cached precisely so that backpropagation can later assign blame and update weights.

Modern frameworks like **PyTorch** and **TensorFlow** automate this caching via *autograd* engines. When you call `loss.backward()`, the system uses the stored forward pass values to compute gradients. This design enables rapid prototyping—engineers at companies like OpenAI or Google Brain can modify network architectures without manually deriving gradients.

Consider **DeepMind’s AlphaFold**: during training, each incorrect protein structure prediction generated a massive cost signal. But without backpropagation, that signal would be useless—there’d be no way to determine which of the 100+ million weights were responsible. Only by tracing gradients backward could the model refine its predictions to atomic precision.

Similarly, in **medical imaging**, a misdiagnosis by a tumor-detection model could have life-or-death consequences. But if the model learns from its mistakes—thanks to backprop assigning precise responsibility—each error becomes a step toward higher accuracy. This is not abstract math; it's the mechanism that makes AI *learn*.

---

### 3. Computational Graph and Chain Rule Intuition

Changing a parameter like $W^{(1)}_{11}$ affects the cost $J$ through a sequence of dependencies:  
$$
W^{(1)} \to z^{(1)} \to h^{(1)} \to z^{(2)} \to \hat{y} \to J
$$

The total effect is computed using the chain rule:  
$$
\frac{\partial J}{\partial W^{(1)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} \cdot \frac{\partial z^{(2)}}{\partial h^{(1)}} \cdot \frac{\partial h^{(1)}}{\partial z^{(1)}} \cdot \frac{\partial z^{(1)}}{\partial W^{(1)}}
$$

Computing this naively for each weight would be inefficient—many partial derivatives are reused. Backpropagation avoids redundancy by traversing the computational graph **backward**, computing and reusing intermediate gradients.

This is reverse-mode automatic differentiation: a dynamic programming approach to gradient computation.

**Analogy: Water Flow Through Pipes**  
Imagine the gradient as water flowing from the cost $J$ back to each parameter. At each node, the pipe splits or merges according to the chain rule. The amount of water (gradient) reaching a weight depends on how much "flow" passed through each connection—and whether a valve (activation function) was open. ReLU acts like a one-way valve: if $z^{(1)}_i \leq 0$, the valve is closed, and no water reaches $W^{(1)}_{i}$.

This explains why gradients vanish in dead neurons: **no flow, no learning**.

The computational graph for this network is:  
```
x → z¹ → h¹ → z² → ŷ → J
     ↑     ↑         ↑
    W¹    f¹        W²
```

Each node represents a value; each edge a dependency. Gradients flow backward from $J$, with each node computing its contribution using local derivatives.

> ✅ **Misconception Alert**  
> Backpropagation is **not** “reverse chain rule.” It is the **efficient implementation** of the chain rule via memoization: each $\frac{\partial J}{\partial \text{node}}$ is computed once and reused for upstream gradients.

> **Try This Yourself**  
> Sketch the computational graph for $f(w) = \sin(w^T x)^2$. Identify all nodes and edges. Without computing, predict how many times $\frac{\partial f}{\partial \sin(w^T x)}$ will be used in the full gradient.

> 💡 **Interactive Prompt: Sensitivity Prediction**  
> In $f = \sin(w^T x)^2$, suppose $w^T x = \pi/2$. If $w$ increases, will the gradient be positive or negative? Sketch the slope of $\sin^2(\cdot)$ at $\pi/2$. How does this affect the weight update direction?

#### Practical Relevance: Debugging and Optimization in Production

In practice, understanding the computational graph is essential for **debugging training failures**. For instance, at Meta, engineers analyzing a failing recommendation model discovered that gradients were vanishing in early layers due to an improperly placed sigmoid activation—this was diagnosed by visualizing the computational graph and gradient flow using **TensorBoard**.

Moreover, **model optimization techniques** like **gradient checkpointing** (used in training large language models such as LLaMA) trade off memory for recomputation by selectively storing only parts of the forward pass. This is only possible because the computational graph structure is known: engineers can recompute intermediate values during backpropagation instead of storing them all, reducing GPU memory usage by up to 60% at the cost of modest compute overhead.

Frameworks like **JAX** exploit this explicitly, allowing users to define pure functions and automatically generate both forward and backward passes using composable transformations (`grad`, `vmap`, `jit`), enabling research-to-production pipelines at companies like DeepMind.

**Here’s a striking case**: when training a model to simulate fluid dynamics for climate prediction, researchers at NVIDIA embedded a differentiable Navier-Stokes solver into the network. During backpropagation, gradients flowed *through the physics simulation itself*, allowing the model to learn corrections to initial conditions by comparing predicted and observed weather patterns. This is **differentiable programming**—and it only works because backpropagation can trace gradients through complex, non-neural computations.

---

### 4. Backward Pass: Computing Gradients via Backpropagation

We now compute gradients starting from the output and moving backward. Define the error signal at layer $l$ as:  
$$
\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}
$$  
This represents how a change in pre-activation $z^{(l)}$ affects the cost $J$.

#### Step 1: Output Layer Gradient

Start with the cost derivative:  
$$
\frac{\partial J}{\partial \hat{y}} = \hat{y} - y = 4 - 1 = 3
$$

Since $\hat{y} = z^{(2)}$:  
$$
\frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = 3 \cdot 1 = 3
$$

Define:  
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}} = 3
$$

This $\delta^{(2)}$ is the seed for all upstream gradients.

#### Step 2: Gradients for $W^{(2)}$ and $b^{(2)}$

From $z^{(2)} = W^{(2)} h^{(1)} + b^{(2)}$:  
$$
\frac{\partial z^{(2)}}{\partial W^{(2)}} = h^{(1)} \quad \Rightarrow \quad \frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (h^{(1)})^\top
$$

Substitute values:  
$$
\frac{\partial J}{\partial W^{(2)}} = 3 \cdot \begin{bmatrix} 2 \\ 0 \end{bmatrix}^\top = \begin{bmatrix} 6 & 0 \end{bmatrix}
$$

The bias gradient is:  
$$
\frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 3
$$

> **Insight**: The bias gradient equals $\delta^{(l)}$ because $b^{(l)}$ adds directly to $z^{(l)}$.

#### Step 3: Propagate Error to Hidden Layer

Compute $\frac{\partial J}{\partial h^{(1)}}$:  
$$
\frac{\partial J}{\partial h^{(1)}} = \left( \frac{\partial z^{(2)}}{\partial h^{(1)}} \right)^\top \delta^{(2)} = (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix} \cdot 3 = \begin{bmatrix} 6 \\ -3 \end{bmatrix}
$$

Now compute $\frac{\partial J}{\partial z^{(1)}}$. For ReLU:  
$$
\frac{\partial h^{(1)}_i}{\partial z^{(1)}_i} =
\begin{cases}
1 & \text{if } z^{(1)}_i > 0 \\
0 & \text{if } z^{(1)}_i \leq 0
\end{cases}
$$

With $z^{(1)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}$, the derivative is $\begin{bmatrix} 1 \\ 0 \end{bmatrix}$. Then:  
$$
\frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial h^{(1)}} \odot \frac{\partial h^{(1)}}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ -3 \end{bmatrix} \odot \begin{bmatrix} 1 \\ 0 \end{bmatrix} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

Define:  
$$
\delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> **Analogy: Electric Circuit with Switches**  
> ReLU acts like a diode: gradient flows only if $z^{(1)}_i > 0$. Here, the second neuron is off ($z^{(1)}_2 = -1$), so $\delta^{(1)}_2 = 0$. No activation, no responsibility.

> 🔍 **Interactive Prompt: What If We Used Sigmoid?**  
> With sigmoid instead of ReLU, would $\delta^{(1)}_2$ be zero? Estimate its value. How would this affect learning compared to ReLU?

#### Step 4: Gradients for $W^{(1)}$ and $b^{(1)}$

From $z^{(1)} = W^{(1)} x + b^{(1)}$:  
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix} 6 \\ 0 \end{bmatrix} \cdot 2 = \begin{bmatrix} 12 \\ 0 \end{bmatrix}
$$

$$
\frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> ✅ **Misconception Alert**  
> The gradient $\frac{\partial J}{\partial W^{(l)}}$ is the outer product $\delta^{(l)} (a^{(l-1)})^\top$, where $a^{(l-1)}$ is the activation from the previous layer. This ensures correct dimensionality and captures input-weight contributions.

> **Try This Yourself**  
> Suppose $x = -1$, so $h^{(1)} = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$. Recompute $\frac{\partial J}{\partial W^{(1)}}$. Which neuron now receives gradient? Why?

> 💡 **Interactive Prompt: Gradient Flow Debugging**  
> You observe near-zero gradients in early layers. Based on ReLU behavior, what might be happening during the forward pass? Could activation function choice or initialization affect this? Sketch a scenario where all hidden neurons are inactive at initialization.

#### Practical Relevance: Addressing Real Training Challenges

In practice, the ReLU gradient behavior observed here—zeroing out gradients for inactive neurons—leads to a common issue known as the **"dying ReLU" problem**, where entire neurons stop updating. This was observed during training of early versions of Google’s BERT model, where poor initialization caused up to 30% of neurons to become inactive. Engineers mitigated this by switching to **Leaky ReLU** or **He initialization**, both of which ensure non-zero gradients and better signal propagation.

Furthermore, the computed gradients are directly used in **optimization algorithms** like **Adam** or **SGD with momentum**, which are standard in industry. For example, in training OpenAI’s GPT-3, gradients from backpropagation are aggregated across thousands of GPUs using **data parallelism**, then synchronized via **AllReduce** operations. The efficiency of backpropagation enables such massive