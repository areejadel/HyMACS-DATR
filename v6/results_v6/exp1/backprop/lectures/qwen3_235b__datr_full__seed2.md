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

If you can compute $\frac{d}{dw} \sin(w^T x)$, you are prepared. If not, review the multivariable chain rule before proceeding.

> **Formative Check (Prerequisites)**  
> Compute $\frac{d}{dw} \left( (w^2 + 1)^3 \right)$.

**Solution**:  
Let $u = w^2 + 1$, so $f = u^3$. Then:  
$$
\frac{df}{dw} = \frac{df}{du} \cdot \frac{du}{dw} = 3u^2 \cdot 2w = 6w(w^2 + 1)^2
$$

> 🔍 **Interactive Prompt: Gradient Prediction**  
> Before we move on: imagine you could only update *one* parameter in the network—$W^{(1)}_{11}$, $W^{(2)}_{11}$, or $b^{(1)}_1$—to reduce the cost fastest. Which would you pick? Jot down your guess. We’ll test it by the end.

---

### 2. Forward Pass: Computing Predictions and Cost

Imagine you're debugging a self-driving car that misclassified a stop sign as a speed limit sign. The model was confident—98% sure—but *wrong*. How do you fix it? You can't just say "try again." You need to know *why* it failed: which neurons were overconfident? Which weights misled the prediction?

The answer lies not in the forward pass alone—but the forward pass is where the crime scene is established.

The forward pass computes the network’s output and cost. It also stores intermediate values—$z^{(l)}$, $h^{(l)}$, $\hat{y}$, $J$—not for immediate use, but to enable gradient computation during backpropagation. Influence flows forward; responsibility flows backward.

#### Example Network

Consider a two-layer feedforward network:  
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
- Output: $\hat{y} = z^{(2)}$ (no activation on output)  
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

All intermediate values are stored. The forward pass builds the computational history; the backward pass uses it to assign responsibility.

> ✅ **Misconception Alert**  
> The forward pass computes predictions and cost. It does **not** compute gradients. However, it **must store** intermediate values—$z^{(l)}$, $h^{(l)}$—required during backpropagation.

> **Formative Check (Forward Pass)**  
> Using the same network, what is $h^{(1)}$ if $x = -1$?

**Solution**:  
$z^{(1)} = W^{(1)}(-1) + b^{(1)} = \begin{bmatrix} -1 \\ 1 \end{bmatrix} + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} -1 \\ 2 \end{bmatrix}$, so  
$h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$

> 🧩 **Interactive Prompt: Debugging Intuition**  
> Suppose you could "freeze" one neuron so its weights never update. Which neuron would you freeze to minimize damage to learning? The one with $z^{(1)}_1 = 2$ or $z^{(1)}_2 = -1$? Why?

#### Real-World Application: Image Classification with CNNs

In industry-scale applications such as image classification using convolutional neural networks (CNNs), the forward pass is executed millions of times per day across platforms like Instagram or Tesla Autopilot. For example, in a self-driving car, raw pixel data from cameras undergoes a forward pass through a deep network (e.g., ResNet-50) to predict lane boundaries or detect pedestrians. Each forward pass computes activations layer-by-layer, storing intermediate feature maps—such as edge detectors in early layers and object parts in deeper layers—for subsequent backpropagation during training.

These stored values are essential: without them, gradients cannot be computed, and the model cannot learn. In practice, memory optimization techniques like **gradient checkpointing** trade recomputation for reduced memory usage by selectively discarding and later reconstructing intermediate activations, a direct consequence of understanding what the forward pass must preserve.

---

### 3. Computational Graph and Chain Rule Intuition

Here’s a paradox:  
You have 100 layers. Each layer has 1,000 parameters. Naively computing gradients would require evaluating thousands of partial derivatives per parameter—billions of operations. Yet, backpropagation computes all gradients in *one backward pass*, roughly the same cost as the forward pass.

How? It exploits structure. Not magic—topology.

Think of a city’s water supply: a leak at a house doesn’t mean you inspect every pipe from the reservoir. You trace backward from the leak, checking valves and junctions. Similarly, backpropagation starts at the cost $J$ and flows backward through the computational graph, asking at each node: *How much did you contribute to the error?*

This dependency structure is captured in a computational graph:

```
x → z¹ → h¹ → z² → ŷ → J
     ↑     ↑         ↑
    W¹    f¹        W²
```

To compute $\frac{\partial J}{\partial W^{(1)}}$, follow the path:
$$
W^{(1)} \to z^{(1)} \to h^{(1)} \to z^{(2)} \to \hat{y} \to J
$$

By the chain rule:
$$
\frac{\partial J}{\partial W^{(1)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} \cdot \frac{\partial z^{(2)}}{\partial h^{(1)}} \cdot \frac{\partial h^{(1)}}{\partial z^{(1)}} \cdot \frac{\partial z^{(1)}}{\partial W^{(1)}}
$$

A naive computation would recompute shared subexpressions multiple times. Backpropagation avoids this by traversing the graph **backward**, computing and reusing gradients at each node—this is reverse-mode automatic differentiation.

> ✅ **Misconception Alert**  
> Backpropagation is **not** “reverse chain rule.” It is the **efficient implementation** of the chain rule using memoization: each node’s gradient with respect to $J$ is computed once and reused in upstream computations.

> **Try This Yourself**  
> Sketch the computational graph for $f(w) = \sin(w^T x)^2$. Identify all nodes and edges. Now, without computing, predict how many times $\frac{\partial f}{\partial \sin(w^T x)}$ will be used in the full gradient.

> 🔁 **Interactive Prompt: Gradient Reuse Quiz**  
> In the expression $f = (a + b)^2$, with $a = wx$ and $b = wy$, how many times is $\frac{\partial f}{\partial (a+b)}$ computed if you apply chain rule naively? How many times *should* it be computed? What does this imply for backpropagation?

#### Real-World Application: Natural Language Processing with Transformers

In modern NLP systems such as BERT or GPT, computational graphs are vastly more complex, involving attention mechanisms, layer normalization, and residual connections. However, the core principle remains: gradients are computed via backpropagation over the graph. For instance, when training a language model to predict the next word, a single forward pass computes logits over a vocabulary of 50,000+ words, and the backward pass assigns credit to hundreds of millions of parameters.

Crucially, frameworks like PyTorch and TensorFlow automatically construct this graph during the forward pass, enabling efficient gradient computation. Engineers at companies like OpenAI and Google leverage this to fine-tune large models on domain-specific data—e.g., medical text or legal documents—by modifying only the final layers and re-running backpropagation. The ability to trace gradients through complex architectures is what enables transfer learning at scale.

---

### 4. Backward Pass: Computing Gradients via Backpropagation

Backpropagation computes gradients by traversing the network backward, starting from the cost. Define the error signal at layer $l$ as:
$$
\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}
$$
This represents how a change in pre-activation $z^{(l)}$ affects the cost.

#### Step 1: Output Layer Gradient

Compute the derivative of the cost:
$$
\frac{\partial J}{\partial \hat{y}} = \hat{y} - y = 4 - 1 = 3
$$

Since $\hat{y} = z^{(2)}$, we have:
$$
\frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = 3 \cdot 1 = 3
$$

Define:
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}} = 3
$$

This $\delta^{(2)}$ is the seed for all upstream gradients.

#### Step 2: Gradients for $W^{(2)}$ and $b^{(2)}$

From $z^{(2)} = W^{(2)} h^{(1)} + b^{(2)}$, the gradient with respect to $W^{(2)}$ is:
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (h^{(1)})^\top = 3 \cdot \begin{bmatrix} 2 \\ 0 \end{bmatrix}^\top = \begin{bmatrix} 6 & 0 \end{bmatrix}
$$

The bias gradient is:
$$
\frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 3
$$

> **Insight**: The bias gradient is always $\delta^{(l)}$, because $b^{(l)}$ adds directly to $z^{(l)}$.

#### Step 3: Propagate Error to Hidden Layer

Compute the gradient with respect to $h^{(1)}$:
$$
\frac{\partial J}{\partial h^{(1)}} = (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix} \cdot 3 = \begin{bmatrix} 6 \\ -3 \end{bmatrix}
$$

Now compute $\frac{\partial J}{\partial z^{(1)}}$. The ReLU derivative is:
$$
\frac{\partial h^{(1)}_i}{\partial z^{(1)}_i} =
\begin{cases}
1 & \text{if } z^{(1)}_i > 0 \\
0 & \text{if } z^{(1)}_i \leq 0
\end{cases}
$$

Given $z^{(1)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}$, the derivative is $\begin{bmatrix} 1 \\ 0 \end{bmatrix}$. Using the Hadamard product:
$$
\frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial h^{(1)}} \odot \frac{\partial h^{(1)}}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ -3 \end{bmatrix} \odot \begin{bmatrix} 1 \\ 0 \end{bmatrix} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

Define:
$$
\delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> **Analogy: Electric Circuit with Switches**  
> ReLU acts like a diode: gradient flows only when $z^{(l)} > 0$. Here, $z^{(1)}_2 = -1$, so the second neuron is "off"—no gradient passes through. The value $\delta^{(1)}_2 = 0$ reflects neural silence: no activation, no responsibility.

#### Step 4: Gradients for $W^{(1)}$ and $b^{(1)}$

From $z^{(1)} = W^{(1)} x + b^{(1)}$:

Gradient with respect to weights:
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix} 6 \\ 0 \end{bmatrix} \cdot 2 = \begin{bmatrix} 12 \\ 0 \end{bmatrix}
$$

Gradient with respect to bias:
$$
\frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> ✅ **Misconception Alert**  
> The gradient $\frac{\partial J}{\partial W^{(l)}}$ is always the outer product $\delta^{(l)} (a^{(l-1)})^\top$, where $a^{(l-1)}$ is the activation from the previous layer. This ensures correct dimensionality and captures how each input-weight pair contributed to the error.

> **Try This Yourself**  
> Suppose $x = -1$, so $h^{(1)} = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$. Recompute $\frac{\partial J}{\partial W^{(1)}}$. Which neuron now gets gradient? Why?

> 🔍 **Interactive Prompt: Revisit Your Guess**  
> Go back to your initial guess: which single parameter would reduce cost fastest? Compute the gradient magnitudes:  
> - $|\partial J / \partial W^{(1)}_{11}| = 12$  
> - $|\partial J / \partial W^{(2)}_{11}| = 6$  
> - $|\partial J / \partial b^{(1)}_1| = 6$  
> Was your intuition correct? What does this say about neurons that are "on" vs. "off"?

#### Real-World Application: Industrial Optimization with Gradient-Based Tuning

In production systems, gradients computed via backpropagation are not just theoretical—they directly inform optimization. For example, in recommendation systems at Netflix or Amazon, backpropagation is used to update embedding vectors that represent users and items. During training, the gradient $\partial J / \partial W$ indicates how to adjust a user’s latent preferences to better predict their next click or purchase.

Moreover, gradient magnitudes guide engineering decisions. A parameter with large gradient (e.g., $|\partial J / \partial W^{(1)}_{11}| = 12$) suggests high sensitivity to error, indicating it should be updated aggressively—this motivates adaptive optimizers like Adam, which scale updates by gradient magnitude. Conversely, dead neurons (like the second neuron here with $\delta^{(1)}_2 = 0$) indicate potential issues with vanishing gradients or poor initialization, prompting practitioners to switch to Leaky ReLU or adjust initialization schemes—common debugging steps in training deep networks at scale.

---

### 5. The Big Picture: Why Backpropagation Works

Backpropagation is systematic credit assignment. It answers: *Which parameters are responsible for the error?* Not by heuristics, but by following the chain of differentiable transformations.

The algorithm is efficient because:  
- **Gradients are local**: Each node computes its contribution using only downstream gradients and local derivatives.  
- **Computation is reused**: Each $\delta^{(l)}$ is computed once and used for all upstream gradients.  
- **Order is backward**: Influence flows forward, so we reverse the computation to assign responsibility—like rewinding a video to find the source of an error.

This structure reduces the complexity of gradient computation from exponential to linear in depth—enabling deep learning at scale.

> **Non-Obvious Insight**:  
> Backpropagation is equivalent to the **adjoint method** from optimal control. In this view, the forward pass solves the state equations, and the backward pass solves the adjoint equations to compute sensitivities. This connection allows backpropagation to generalize to continuous models like neural ODEs.

> 🔄 **Final Interactive Prompt: Design Your Own Neuron**  
> Invent a new activation function $f(z)$ that is zero for $z < 0$, but has a learnable slope $\alpha$ for $z \geq 0$. How would $\frac{\partial J}{\partial \alpha}$ be computed? Sketch the modified computational graph. Where would $\alpha$ appear? This is the idea behind **parametric ReLU**—you’ve just derived its backpropagation rule.

#### Real-World Application: Debugging and Improving Training in Industry

In practice, backpropagation is