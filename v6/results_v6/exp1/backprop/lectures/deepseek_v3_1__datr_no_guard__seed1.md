## 5. Backpropagation in a Two-Layer Network

We now apply the backpropagation algorithm to a concrete neural network with one hidden layer, transforming the abstract graph into a real training step.

Consider this puzzle: you have a function with thousands of parameters (weights). You can only observe the final output error. How do you determine which parameter to adjust, in which direction, and by how much, to reduce that error? Backpropagation answers this question with a computational cost roughly equal to computing the function *once*. This efficiency was the key insight that made deep learning practical. As we trace through the two-layer network, ask: *where is the information about each parameter's responsibility being routed?*

**Interactive check — before we dive in:** Given a function with 10,000 parameters, how many forward passes would a naive, finite-difference approach (perturbing each parameter one at a time and re-evaluating the loss) require to estimate the full gradient? Now, compare that to backpropagation's single forward and backward pass. The ratio of these two numbers is why deep learning was impossible before this algorithm was widely adopted.

**Architecture:**
- Input: \(x \in \mathbb{R}^d\) (a vector of \(d\) features).
- Hidden layer: \(h = \sigma(z^{[1]})\), where \(z^{[1]} = W^{[1]} x + b^{[1]}\), \(W^{[1]} \in \mathbb{R}^{h \times d}\), \(b^{[1]} \in \mathbb{R}^h\), and \(\sigma\) is an element-wise activation function (e.g., ReLU).
- Output layer: \(\hat{y} = z^{[2]} = W^{[2]} h + b^{[2]}\), where \(W^{[2]} \in \mathbb{R}^{o \times h}\), \(b^{[2]} \in \mathbb{R}^o\).
- Loss: \(J = \frac{1}{2} \|\hat{y} - y\|_2^2\) (mean squared error for a single training example \(y \in \mathbb{R}^o\)).

We trace both passes for a single example. The minibatch case is a sum over examples.

### 5.1 Forward Pass

1. **Linear 1:** \(z^{[1]} = W^{[1]} x + b^{[1]}\). Store \(x, W^{[1]}, z^{[1]}\).
2. **Activation:** \(h = \sigma(z^{[1]})\) (applied element-wise). Store \(h\) (or \(z^{[1]}\), depending on the framework).
3. **Linear 2:** \(z^{[2]} = W^{[2]} h + b^{[2]}\). Store \(h, W^{[2]}, z^{[2]}\).
4. **Loss:** \(J = \frac{1}{2} \|z^{[2]} - y\|_2^2\). Store \(y\) and \(z^{[2]}\).

*Pause and reflect:* The forward pass computes a prediction. The "store" instructions are the only hint of the backward pass to come. These intermediate values are stored because the backward pass needs them to compute gradients. Without storing \(h\), it would have to be recomputed during the backward pass, doubling the computation. This storage is the memory bottleneck in training large models. **Try this yourself:** For the architecture above with \(d=784\), \(h=128\), \(o=10\), and a batch size of 64, estimate how many floating-point numbers must be stored during the forward pass. (Hint: count the elements in each stored tensor and multiply by the batch size.)

### 5.2 Backward Pass

We start with \(\frac{\partial J}{\partial J} = 1\) and work backward.

**Step 1: Gradient of the Loss**

For \(J = \frac{1}{2} \sum_{k} (\hat{y}_k - y_k)^2\), the gradient with respect to the output layer's pre-activation \(z^{[2]}\) (which equals \(\hat{y}\) here) is:

\[
\frac{\partial J}{\partial z^{[2]}} = \hat{y} - y
\]

This is the upstream gradient entering the Linear 2 operation. **Practical relevance — why this form matters:** The \(L_2\) loss paired with a linear output layer yields this simple error vector. This is a design choice that makes the initial gradient signal directly proportional to the prediction error. In modern frameworks, this is why `nn.MSELoss` in PyTorch or `mean_squared_error` in TensorFlow is implemented to compute this difference directly, often fused with the backward pass of the preceding layer for efficiency. When you fine-tune a pre-trained object detection model like YOLOv8 or a segmentation model like SAM, the box and mask regression heads often use MSE or a smooth L1 loss, and this exact gradient \(\hat{y} - y\) is the starting signal that flows back through the feature pyramid network.

**Quick check — what's flowing here?:** The gradient \(\hat{y} - y\) is a vector. For a batch of 64 images with 10 output classes, what is the shape of this tensor? If the prediction for class 3 is too high by 0.8, what is the sign and approximate magnitude of the gradient flowing back to that output neuron? What about a neuron whose prediction was exactly correct?

**Step 2: Gradient through Linear 2**

Operation: \(z^{[2]} = W^{[2]} h + b^{[2]}\).

We need \(\frac{\partial J}{\partial W^{[2]}}\), \(\frac{\partial J}{\partial b^{[2]}}\), and \(\frac{\partial J}{\partial h}\).

- **Local Jacobians:** \(\frac{\partial z^{[2]}}{\partial W^{[2]}}\) is a tensor; for a single weight \(W^{[2]}_{ij}\), \(\frac{\partial z^{[2]}_k}{\partial W^{[2]}_{ij}} = h_j\) if \(k=i\) and 0 otherwise.
- **Gradient for weights:** Using the chain rule and summing over output dimensions:
  \[
  \frac{\partial J}{\partial W^{[2]}_{ij}} = \sum_{k} \frac{\partial J}{\partial z^{[2]}_k} \frac{\partial z^{[2]}_k}{\partial W^{[2]}_{ij}} = \frac{\partial J}{\partial z^{[2]}_i} h_j
  \]
  In matrix form: \(\frac{\partial J}{\partial W^{[2]}} = \frac{\partial J}{\partial z^{[2]}} h^T\).

- **Gradient for bias:** \(\frac{\partial J}{\partial b^{[2]}} = \frac{\partial J}{\partial z^{[2]}}\).

- **Gradient for input \(h\):** \(\frac{\partial J}{\partial h} = (W^{[2]})^T \frac{\partial J}{\partial z^{[2]}}\).

**Analogy — the outer product as "responsibility assignment":** Imagine each output neuron \(i\) looks at the error signal \(\frac{\partial J}{\partial z^{[2]}_i}\) and asks: "Which hidden neurons made me wrong?" The answer is: those that were active (\(h_j\) large) and connected to me by a weight. The outer product \(\frac{\partial J}{\partial z^{[2]}} h^T\) captures exactly this: it is a matrix where entry \((i,j)\) is the product of "how wrong output \(i\) is" and "how active hidden neuron \(j\) was." If a hidden neuron was silent (\(h_j \approx 0\)), it gets little blame regardless of the error. If it was active (\(h_j\) large) and the output was wrong, its connecting weight gets a large gradient. This is the mathematical formalization of credit assignment.

**Coding exercise — implement the outer product:** In PyTorch or NumPy, create a random error vector `grad_output` of shape `(batch_size, output_dim)` and a random activation matrix `h` of shape `(batch_size, hidden_dim)`. Compute the weight gradient using the outer product formula above. Verify that the shape of the result is `(output_dim, hidden_dim)`. Now, compare your result to `torch.matmul(grad_output.T, h)` — are they the same? Why or why not? (Hint: think about how the batch dimension is handled in the sum.)

**Practical relevance — the outer product:** The weight gradient \(\frac{\partial J}{\partial W^{[2]}} = \frac{\partial J}{\partial z^{[2]}} h^T\) is an outer product of the error vector and the hidden layer's activation. This operation is the computational heart of training. On GPUs, it is implemented as a highly optimized GEMM (General Matrix Multiply) operation. In a large language model like Llama 3 or Mistral, during every training step on a corpus of text, millions of these outer products are computed in parallel across attention heads and feed-forward layers. The efficiency of this single operation — literally `torch.matmul(grad_output, input.T)` in PyTorch — is what makes training transformer models on terabytes of data feasible. The memory for storing activations \(h\) from the forward pass, however, is the limiting factor. This is why techniques like FlashAttention, which fuse the attention computation to avoid storing the full \(QK^T\) matrix, have been crucial for scaling context lengths to 128k tokens and beyond.

**Step 3: Gradient through Activation**

Operation: \(h = \sigma(z^{[1]})\).

We receive \(\frac{\partial J}{\partial h}\) from upstream. The local Jacobian is diagonal (since \(\sigma\) is element-wise): \(\frac{\partial h_i}{\partial z^{[1]}_j} = 0\) for \(i \neq j\), and \(\frac{\partial h_i}{\partial z^{[1]}_i} = \sigma'(z^{[1]}_i)\).

\[
\frac{\partial J}{\partial z^{[1]}} = \frac{\partial J}{\partial h} \odot \sigma'(z^{[1]})
\]
where \(\odot\) is element-wise multiplication. For ReLU: \(\sigma'(z) = 1\) if \(z > 0\) else \(0\).

**Analogy — the activation as a "valve" on the gradient:** Think of the backward pass as water flowing upstream through a network of pipes. The forward pass opened valves based on the input: ReLU opened valves only where \(z^{[1]} > 0\). During the backward pass, the gradient signal can only flow through valves that were left open. If a valve is closed (\(\sigma' = 0\)), the gradient stops dead — that neuron receives no learning signal, and its incoming weights will not be updated based on this example. This is why dead ReLUs are permanent: once a neuron's valve closes for all training examples, no gradient ever flows through it again.

**Practical relevance — the dying ReLU and modern alternatives:** The gradient of ReLU is a hard gate: it is 1 for positive inputs and 0 for negative inputs. If a neuron receives a negative input for all training examples (e.g., due to a large negative bias or a bad weight initialization), its gradient is always zero, and it stops learning permanently — the "dying ReLU" problem. This was a significant practical issue in early deep networks. Modern architectures like the Vision Transformer (ViT) or ConvNeXt often use GeLU (Gaussian Error Linear Unit) activations instead. GeLU's gradient is \(\sigma'(z) = \Phi(z) + z \phi(z)\), where \(\Phi\) and \(\phi\) are the CDF and PDF of a standard normal. This gradient is smooth and never exactly zero, allowing a small gradient signal to flow even for negative inputs. In PyTorch, swapping `nn.ReLU()` for `nn.GELU()` is a one-line change, but the gradient flow dynamics are fundamentally different. When training a large vision transformer on ImageNet-21k, this choice can be the difference between a model that converges and one where 20% of the MLP neurons die in the first 1000 iterations.

**Try this yourself:** Initialize a small network with ReLU activations and a large negative bias. After one epoch of training, check how many neurons have zero gradient. Then repeat with GeLU. What fraction survives?

**Step 4: Gradient through Linear 1**

Operation: \(z^{[1]} = W^{[1]} x + b^{[1]}\).

This is structurally identical to Step 2. We receive \(\frac{\partial J}{\partial z^{[1]}}\) as the upstream gradient.

\[
\frac{\partial J}{\partial W^{[1]}} = \frac{\partial J}{\partial z^{[1]}} x^T
\]
\[
\frac{\partial J}{\partial b^{[1]}} = \frac{\partial J}{\partial z^{[1]}}
\]
\[
\frac{\partial J}{\partial x} = (W^{[1]})^T \frac{\partial J}{\partial z^{[1]}}
\]

**Practical relevance — gradient with respect to the input:** The gradient \(\frac{\partial J}{\partial x}\) is typically not used for updating parameters (the input \(x\) is data, not a parameter). However, it is crucial for two major applications:
1.  **Adversarial examples:** The Fast Gradient Sign Method (FGSM) creates an adversarial input \(x_{adv} = x + \epsilon \cdot \text{sign}(\frac{\partial J}{\partial x})\) to fool a trained classifier. This gradient is computed via backpropagation, exactly as derived here. This technique is a standard tool in the red-teaming of production models, including large multimodal models like GPT-4V or Gemini, to test their robustness against visual attacks.
2.  **Neural style transfer and DeepDream:** These artistic applications optimize the *input pixels* rather than the network weights to maximize certain feature activations. The algorithm is gradient ascent on \(x\), using \(\frac{\partial J}{\partial x}\) computed via backpropagation. The popular mobile app "Prisma" and Google's DeepDream images are direct consumer-facing applications of this exact gradient computation.

This completes the backward pass for a single example. For a minibatch of \(m\) examples, the forward and backward passes are computed for each example, and the parameter gradients are averaged:
\[
\frac{\partial J_{batch}}{\partial W} = \frac{1}{m} \sum_{i=1}^m \frac{\partial J^{(i)}}{\partial W}
\]
This averaging is the "data parallelism" that allows training to be distributed across thousands of GPUs. Each GPU computes the sum for its micro-batch, and an all-reduce operation averages the gradients before the optimizer step. This is how models like Stable Diffusion 3 or Llama 3.1 405B are trained on clusters of tens of thousands of H100 GPUs — the backpropagation algorithm on a single chip is identical to what we derived here; the scale comes from the minibatch sum and distributed communication.

**Quiz — tracing a single weight's update:** Consider a weight \(W^{[1]}_{ij}\) connecting input feature \(j\) to hidden neuron \(i\). Write down the chain of operations from the loss \(J\) back to this weight. Your answer should mention: the loss gradient, the output layer's weight matrix, the activation function's derivative, and the input \(x_j\). If the activation is ReLU and \(z^{[1]}_i < 0\), what is the gradient for this weight? If the weight is in a network trained with L2 regularization (weight decay), how would the update rule change?

---

## 6. The Autograd Pattern: From Manual Derivation to Automatic Differentiation

Manually deriving the backward pass for every new operation is error-prone. Modern frameworks (PyTorch, TensorFlow, JAX) use **automatic differentiation** (autograd) to automate this process. You define only the forward computation, and the framework builds the computational graph and executes backpropagation.

**How it works:** Every tensor is a node in the graph. When you write `z = x * y`, the framework:
1.  Creates a `Multiply` node in the graph.
2.  Stores references to the input tensors `x` and `y`.
3.  Registers the *backward function* for multiplication: a function that, given the upstream gradient \(\frac{\partial J}{\partial z}\), computes \(\frac{\partial J}{\partial x} = \frac{\partial J}{\partial z} \cdot y\) and \(\frac{\partial J}{\partial y} = \frac{\partial J}{\partial z} \cdot x\) and accumulates them into `x.grad` and `y.grad`.

When `.backward()` is called on the final loss tensor, the framework topologically sorts the graph in reverse and executes each registered backward function.

**Practical relevance — defining a custom autograd function:** In practice, you can extend autograd with custom operations. This is essential for implementing operations that are not composed of existing primitives or where a fused implementation is more efficient. For example, the `triton` language is used to write custom GPU kernels for novel attention mechanisms. In a recent paper like "FlashAttention-3," the authors implemented a custom forward and backward pass in CUDA/Triton to achieve a 2x speedup over standard attention. In PyTorch, you subclass `torch.autograd.Function` and define `forward` (which computes the output and saves any tensors needed for the backward pass via `ctx.save_for_backward`) and `backward` (which receives the upstream gradient and returns gradients for each input). This pattern is how cutting-edge research in efficient transformers or novel quantization schemes gets integrated into production frameworks — it is a direct application of the mathematical rules from Sections 3 and 4, codified in a Python class.