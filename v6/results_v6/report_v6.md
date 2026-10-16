# تقرير تجارب التقوية v6

كل الأرقام محسوبة آلياً من ملفات النتائج. لا تُنقل للورقة قبل مراجعتها.


## A. موثوقية اللوحة

لوحة v5: Claude-sonnet-4-6 + Kimi-K2.6 + GLM-5.1 (Kimi/GLM بحرارة 0.7 فعلياً).  لوحة v6: Claude-sonnet-4-6 + moonshotai/Kimi-K3 + zai-org/GLM-5.2 (كلها 0.2).

α المجمّع مرتفع لأن النماذج متباعدة جداً؛ α داخل الفئة هو المقياس الصادق لمقارنات داخل النموذج.

| topic | α v5 panel (paper) | α v6 panel | α v6 strong-only | α v6 weak-only |
|---|---|---|---|---|
| backprop | 0.931 | 0.914 | 0.754 | 0.575 |
| normalization | 0.951 | 0.945 | 0.766 | 0.741 |
| pooled | 0.943 | 0.931 | 0.761 | 0.675 |

| model | backprop | normalization |
|---|---|---|
| ALLaM-7B | 0.619 | 0.578 |
| Llama-3-8B | 0.317 | 0.413 |
| Llama-3.3-70B | 0.349 | 0.478 |
| Gemma-4-31B | 0.751 | 0.797 |
| DeepSeek-V4-Pro | 0.745 | 0.745 |
| Qwen3-235B | 0.756 | 0.763 |

نفس المحاضرات: حَكَم v5 (إصدار قديم، حرارة 0.7) مقابل خلَفه في v6 (حرارة 0.2). الفرق يجمع أثر الإصدار والحرارة معاً؛ لا يُنسب للحرارة وحدها.

| judge | n | mean(v5 − v6) | Spearman | MAE |
|---|---|---|---|---|
| kimi | 238 | -0.408 | 0.893 | 0.562 |
| glm | 230 | 0.150 | 0.936 | 0.377 |

ثبات إعادة القياس (نفس المحاضرة تُقيَّم مرّتين).

| judge | n | ICC(A,1) | Pearson | MAE |
|---|---|---|---|---|
| claude | 48 | 0.998 | 0.998 | 0.101 |
| kimi | 48 | 0.991 | 0.990 | 0.181 |
| glm | 48 | 0.996 | 0.996 | 0.161 |
| PANEL (median) | 48 | 0.998 | 0.998 | 0.105 |

| pair | Spearman |
|---|---|
| claude–kimi | 0.918 |
| claude–glm | 0.928 |
| kimi–glm | 0.934 |

تشغيلات بلوحة ناقصة (<3 حكّام) في v6: **0** (كانت 12 في v5).


## R. صمود نتائج v5 عند تبديل اللوحة (v5 → v6)

| topic | n | Spearman per-lecture | Spearman model ranking | Spearman condition ranking | mean shift (v6 − v5) |
|---|---|---|---|---|---|
| backprop | 120 | 0.962 | 0.943 | 1.000 | 0.085 |
| normalization | 120 | 0.960 | 0.943 | 0.400 | 0.013 |

اتفاق إشارة أثر الشرط (مقابل No-Refine) بين اللوحتين: 75% من 36 خلية.

| topic | model | cond | Δ v5 panel | Δ v6 panel | same sign |
|---|---|---|---|---|---|
| backprop | ALLaM-7B | datr_full | 0.450 | 0.538 | True |
| backprop | ALLaM-7B | datr_no_guard | 0.188 | 0.362 | True |
| backprop | ALLaM-7B | self_refine | 0.337 | 0.312 | True |
| backprop | Llama-3-8B | datr_full | 0.381 | 0.463 | True |
| backprop | Llama-3-8B | datr_no_guard | -0.100 | -0.062 | True |
| backprop | Llama-3-8B | self_refine | 0.000 | 0.238 | False |
| backprop | Llama-3.3-70B | datr_full | 0.169 | 0.213 | True |
| backprop | Llama-3.3-70B | datr_no_guard | 0.056 | -0.112 | False |
| backprop | Llama-3.3-70B | self_refine | 0.006 | 0.000 | False |
| backprop | Gemma-4-31B | datr_full | 0.148 | 0.155 | True |
| backprop | Gemma-4-31B | datr_no_guard | -0.106 | 0.030 | False |
| backprop | Gemma-4-31B | self_refine | 0.078 | 0.092 | True |
| backprop | DeepSeek-V4-Pro | datr_full | 0.335 | 0.322 | True |
| backprop | DeepSeek-V4-Pro | datr_no_guard | 0.283 | 0.510 | True |
| backprop | DeepSeek-V4-Pro | self_refine | 0.113 | -0.025 | False |
| backprop | Qwen3-235B | datr_full | -0.100 | -0.083 | True |
| backprop | Qwen3-235B | datr_no_guard | -0.200 | -0.245 | True |
| backprop | Qwen3-235B | self_refine | 0.125 | 0.030 | True |
| normalization | ALLaM-7B | datr_full | 0.363 | 0.163 | True |
| normalization | ALLaM-7B | datr_no_guard | 0.388 | 0.175 | True |
| normalization | ALLaM-7B | self_refine | 0.163 | -0.013 | False |
| normalization | Llama-3-8B | datr_full | -0.025 | -0.162 | True |
| normalization | Llama-3-8B | datr_no_guard | 0.000 | -0.237 | False |
| normalization | Llama-3-8B | self_refine | 0.212 | -0.050 | False |
| normalization | Llama-3.3-70B | datr_full | -0.562 | -0.450 | True |
| normalization | Llama-3.3-70B | datr_no_guard | -0.688 | -0.537 | True |
| normalization | Llama-3.3-70B | self_refine | -0.513 | -0.562 | True |
| normalization | Gemma-4-31B | datr_full | 0.174 | 0.330 | True |
| normalization | Gemma-4-31B | datr_no_guard | 0.172 | 0.018 | True |
| normalization | Gemma-4-31B | self_refine | 0.160 | 0.195 | True |
| normalization | DeepSeek-V4-Pro | datr_full | 0.295 | 0.172 | True |
| normalization | DeepSeek-V4-Pro | datr_no_guard | 0.277 | 0.350 | True |
| normalization | DeepSeek-V4-Pro | self_refine | 0.234 | 0.275 | True |
| normalization | Qwen3-235B | datr_full | 0.133 | 0.300 | True |
| normalization | Qwen3-235B | datr_no_guard | 0.042 | -0.020 | False |
| normalization | Qwen3-235B | self_refine | 0.100 | 0.090 | True |


## B. GPT-4o: أثر النموذج مقابل أثر البرومبت

| topic | model | panel v6 | GPT-4o inner-prompt (v5) | GPT-4o inner-neutral | GPT-4o panel-prompt |
|---|---|---|---|---|---|
| backprop | ALLaM-7B | 3.403 | 5.987 | — | 6.369 |
| backprop | Llama-3-8B | 3.834 | 6.562 | — | 6.891 |
| backprop | Llama-3.3-70B | 5.088 | 6.800 | — | 7.125 |
| backprop | Gemma-4-31B | 8.047 | 7.800 | — | 7.809 |
| backprop | DeepSeek-V4-Pro | 7.959 | 7.819 | — | 7.881 |
| backprop | Qwen3-235B | 8.296 | 7.850 | — | 7.912 |
| normalization | ALLaM-7B | 2.494 | 4.856 | — | 5.094 |
| normalization | Llama-3-8B | 3.438 | 5.978 | — | 6.481 |
| normalization | Llama-3.3-70B | 4.838 | 6.675 | — | 7.178 |
| normalization | Gemma-4-31B | 8.148 | 7.794 | — | 7.819 |
| normalization | DeepSeek-V4-Pro | 7.887 | 7.787 | — | 7.928 |
| normalization | Qwen3-235B | 8.092 | 7.862 | — | 8.053 |

إن بقي مدى GPT-4o ببرومبت اللوحة ضيّقاً ⇒ الانضغاط من النموذج نفسه؛ إن اتّسع ⇒ من البرومبت.

| topic | evaluator | min model mean | max model mean | range |
|---|---|---|---|---|
| backprop | panel v6 | 3.403 | 8.296 | 4.892 |
| backprop | GPT-4o inner-prompt (v5) | 5.987 | 7.850 | 1.862 |
| backprop | GPT-4o panel-prompt | 6.369 | 7.912 | 1.544 |
| normalization | panel v6 | 2.494 | 8.148 | 5.654 |
| normalization | GPT-4o inner-prompt (v5) | 4.856 | 7.862 | 3.006 |
| normalization | GPT-4o panel-prompt | 5.094 | 8.053 | 2.959 |


## C. التوافق مع المحكّمين البشريين

عدد الأشخاص (ملفات الردود): **17** — عدد المحاضرات: 24.

| evaluator | topic | n | MAE | MAE calibrated (LOO) | Spearman | Pearson |
|---|---|---|---|---|---|---|
| panel v6 (median-composite) | backprop | 12 | 1.213 | 1.234 | 0.588 | 0.765 |
| panel v6 (median-composite) | normalization | 12 | 0.481 | 0.446 | 0.942 | 0.987 |
| panel v6 (median-composite) | pooled | 24 | 0.847 | 0.848 | 0.817 | 0.887 |
| panel v5 (as in paper) | backprop | 12 | 1.288 | 1.283 | 0.639 | 0.745 |
| panel v5 (as in paper) | normalization | 12 | 0.533 | 0.581 | 0.884 | 0.978 |
| panel v5 (as in paper) | pooled | 24 | 0.910 | 0.918 | 0.806 | 0.876 |
| Claude alone | backprop | 12 | 1.174 | 1.255 | 0.614 | 0.765 |
| Claude alone | normalization | 12 | 0.422 | 0.473 | 0.912 | 0.984 |
| Claude alone | pooled | 24 | 0.798 | 0.840 | 0.807 | 0.888 |
| Kimi-K3 alone (v6) | backprop | 12 | 1.122 | 1.207 | 0.595 | 0.780 |
| Kimi-K3 alone (v6) | normalization | 12 | 0.653 | 0.513 | 0.900 | 0.982 |
| Kimi-K3 alone (v6) | pooled | 24 | 0.888 | 0.844 | 0.804 | 0.900 |
| GLM-5.2 alone (v6) | backprop | 12 | 1.492 | 1.310 | 0.644 | 0.724 |
| GLM-5.2 alone (v6) | normalization | 12 | 0.684 | 0.548 | 0.919 | 0.974 |
| GLM-5.2 alone (v6) | pooled | 24 | 1.088 | 0.974 | 0.821 | 0.858 |
| GPT-4o inner-prompt (paper's inner) | backprop | 12 | 1.173 | 1.316 | 0.654 | 0.760 |
| GPT-4o inner-prompt (paper's inner) | normalization | 12 | 1.697 | 1.071 | 0.945 | 0.916 |
| GPT-4o inner-prompt (paper's inner) | pooled | 24 | 1.435 | 1.106 | 0.835 | 0.847 |
| GPT-4o panel-prompt | backprop | 12 | 1.210 | 1.391 | 0.661 | 0.712 |
| GPT-4o panel-prompt | normalization | 12 | 1.618 | 1.310 | 0.914 | 0.889 |
| GPT-4o panel-prompt | pooled | 24 | 1.414 | 1.208 | 0.815 | 0.825 |
| panel of 4 (+GPT-4o) | backprop | 12 | 1.148 | 1.225 | 0.599 | 0.775 |
| panel of 4 (+GPT-4o) | normalization | 12 | 0.506 | 0.421 | 0.912 | 0.988 |
| panel of 4 (+GPT-4o) | pooled | 24 | 0.827 | 0.817 | 0.803 | 0.896 |

فترة ثقة تشمل الصفر ⇒ لا فرق دالّ إحصائياً مع هذا العدد من المحاضرات.

| evaluator vs panel v6 | ΔMAE (evaluator − panel) | ΔMAE 95% CI | Δρ (evaluator − panel) | Δρ 95% CI |
|---|---|---|---|---|
| panel v5 (as in paper) | 0.064 | [-0.06, 0.20] | -0.013 | [-0.12, 0.09] |
| Claude alone | -0.050 | [-0.14, 0.03] | -0.011 | [-0.12, 0.10] |
| Kimi-K3 alone (v6) | 0.039 | [-0.15, 0.23] | -0.014 | [-0.11, 0.06] |
| GLM-5.2 alone (v6) | 0.243 | [0.09, 0.41] | 0.003 | [-0.06, 0.07] |
| GPT-4o inner-prompt (paper's inner) | 0.582 | [-0.03, 1.17] | 0.021 | [-0.16, 0.25] |
| GPT-4o panel-prompt | 0.571 | [-0.06, 1.21] | -0.004 | [-0.15, 0.16] |
| panel of 4 (+GPT-4o) | -0.020 | [-0.13, 0.09] | -0.012 | [-0.09, 0.03] |

| topic | human α (interval) | lectures |
|---|---|---|
| backprop | 0.581 | 12 |
| normalization | 0.703 | 12 |
| pooled | 0.662 | 24 |


## D. الحكم المتقاطع: تفضيل ذاتي حقيقي أم تساهل؟

متوسط الدرجة التي أعطاها كل حَكَم (صف) لمحاضرات كل مولّد (عمود). القطر = حكم الذات.

| judge ↓ / generator → | ALLaM-7B | Llama-3-8B | Llama-3.3-70B | Gemma-4-31B | DeepSeek-V4-Pro | Qwen3-235B |
|---|---|---|---|---|---|---|
| gen:allam_7b | 9.05 | 8.80 | 8.65 | 8.85 | 9.06 | 8.74 |
| gen:deepseek_v3_1 | 1.90 | 3.34 | 4.88 | 8.29 | 8.30 | 8.40 |
| gen:gemma_4_31b | 2.71 | 3.56 | 5.23 | 8.59 | 8.38 | 8.50 |
| gen:llama_3_3_70b | 7.77 | 8.03 | 8.19 | 8.94 | 8.72 | 8.95 |
| gen:llama_3_8b | 7.02 | 7.33 | 7.50 | 8.36 | 8.05 | 7.90 |
| gen:qwen3_235b | 4.99 | 6.12 | 7.61 | 8.67 | 8.42 | 8.69 |
| claude | 2.60 | 3.52 | 5.15 | 7.88 | 7.72 | 7.80 |
| glm | 2.50 | 3.10 | 4.35 | 7.51 | 7.33 | 7.20 |
| kimi | 3.21 | 4.45 | 5.96 | 8.03 | 7.76 | 7.83 |

self-bias = كم يرفع الحَكَم درجة محاضرته فوق ما يعطيه لمحاضرات الآخرين بعد ضبط الجودة. إن كانت الفترة تشمل الصفر فلا دليل على تفضيل ذاتي؛ الفرق الساذج حينها هو تساهل.

| generator | naive self − panel (v5 method) | leniency vs claude | self-bias (controlled) | 95% CI |
|---|---|---|---|---|
| ALLaM-7B | 6.34 | 2.55 | 3.17 | [2.82, 3.48] |
| Llama-3-8B | 3.81 | 1.68 | 1.40 | [1.19, 1.59] |
| Llama-3.3-70B | 3.04 | 2.63 | 0.13 | [-0.05, 0.32] |
| Gemma-4-31B | 0.82 | 0.19 | 1.13 | [0.98, 1.29] |
| DeepSeek-V4-Pro | 0.66 | -0.16 | 1.37 | [1.06, 1.68] |
| Qwen3-235B | 1.01 | 1.69 | -0.30 | [-0.41, -0.20] |


## E. التحسين من نفس المسودة (تصميم مقترن)

كل الفروق مقترنة على نفس المسودة. تصحيح Holm على كل المقارنات المعروضة معاً.

| comparison | scope | n pairs | mean Δ | 95% CI | Wilcoxon p | Cliff δ | Holm p |
|---|---|---|---|---|---|---|---|
| self_refine − no_refine | backprop | 30 | 0.253 | [0.08, 0.44] | 0.013 | 0.064 | 0.294 |
| self_refine − no_refine | normalization | 30 | 0.264 | [0.16, 0.37] | 0.000 | 0.152 | 0.003 |
| self_refine − no_refine | pooled | 60 | 0.258 | [0.16, 0.37] | 0.000 | 0.101 | 0.000 |
| self_refine_guard − no_refine | backprop | 30 | 0.189 | [0.04, 0.34] | 0.027 | 0.030 | 0.517 |
| self_refine_guard − no_refine | normalization | 30 | 0.091 | [0.00, 0.18] | 0.085 | 0.076 | 1.000 |
| self_refine_guard − no_refine | pooled | 60 | 0.140 | [0.06, 0.23] | 0.005 | 0.052 | 0.131 |
| datr_no_guard − no_refine | backprop | 30 | 0.167 | [0.01, 0.35] | 0.147 | 0.038 | 1.000 |
| datr_no_guard − no_refine | normalization | 30 | 0.075 | [-0.09, 0.23] | 0.262 | 0.092 | 1.000 |
| datr_no_guard − no_refine | pooled | 60 | 0.121 | [0.00, 0.24] | 0.049 | 0.070 | 0.689 |
| datr_full − no_refine | backprop | 30 | 0.153 | [0.05, 0.27] | 0.041 | 0.078 | 0.687 |
| datr_full − no_refine | normalization | 30 | 0.164 | [0.06, 0.28] | 0.011 | 0.114 | 0.252 |
| datr_full − no_refine | pooled | 60 | 0.158 | [0.08, 0.24] | 0.001 | 0.090 | 0.031 |
| datr_composite_guard − no_refine | backprop | 30 | 0.295 | [0.17, 0.43] | 0.000 | 0.127 | 0.009 |
| datr_composite_guard − no_refine | normalization | 30 | 0.163 | [0.07, 0.26] | 0.016 | 0.119 | 0.335 |
| datr_composite_guard − no_refine | pooled | 60 | 0.229 | [0.15, 0.31] | 0.000 | 0.121 | 0.000 |
| datr_full − self_refine_guard | backprop | 30 | -0.036 | [-0.18, 0.11] | 0.510 | 0.031 | 1.000 |
| datr_full − self_refine_guard | normalization | 30 | 0.073 | [-0.02, 0.18] | 0.236 | 0.053 | 1.000 |
| datr_full − self_refine_guard | pooled | 60 | 0.019 | [-0.07, 0.11] | 0.824 | 0.043 | 1.000 |
| datr_full − datr_no_guard | backprop | 30 | -0.014 | [-0.16, 0.12] | 0.758 | 0.021 | 1.000 |
| datr_full − datr_no_guard | normalization | 30 | 0.089 | [-0.05, 0.23] | 0.280 | 0.034 | 1.000 |
| datr_full − datr_no_guard | pooled | 60 | 0.038 | [-0.06, 0.13] | 0.375 | 0.019 | 1.000 |
| self_refine_guard − self_refine | backprop | 30 | -0.064 | [-0.22, 0.10] | 0.365 | -0.034 | 1.000 |
| self_refine_guard − self_refine | normalization | 30 | -0.173 | [-0.29, -0.05] | 0.013 | -0.092 | 0.294 |
| self_refine_guard − self_refine | pooled | 60 | -0.119 | [-0.22, -0.02] | 0.021 | -0.057 | 0.411 |
| datr_no_guard − self_refine | backprop | 30 | -0.086 | [-0.24, 0.07] | 0.328 | -0.009 | 1.000 |
| datr_no_guard − self_refine | normalization | 30 | -0.189 | [-0.35, -0.03] | 0.043 | -0.027 | 0.687 |
| datr_no_guard − self_refine | pooled | 60 | -0.138 | [-0.25, -0.03] | 0.032 | -0.021 | 0.572 |
| datr_composite_guard − datr_full | backprop | 30 | 0.142 | [0.02, 0.26] | 0.040 | 0.056 | 0.687 |
| datr_composite_guard − datr_full | normalization | 30 | -0.001 | [-0.13, 0.11] | 0.852 | -0.006 | 1.000 |
| datr_composite_guard − datr_full | pooled | 60 | 0.070 | [-0.01, 0.16] | 0.128 | 0.026 | 1.000 |

| topic | model | no_refine | self_refine | self_refine_guard | datr_no_guard | datr_full | datr_composite_guard |
|---|---|---|---|---|---|---|---|
| backprop | ALLaM-7B | 3.11 | 3.41 | 3.60 | 3.29 | 3.39 | 3.70 |
| backprop | Llama-3-8B | 3.65 | 4.45 | 4.17 | 4.17 | 3.91 | 4.28 |
| backprop | Llama-3.3-70B | 5.09 | 5.38 | 5.24 | 5.20 | 5.29 | 5.25 |
| backprop | Gemma-4-31B | 8.11 | 8.19 | 8.27 | 8.26 | 8.32 | 8.21 |
| backprop | DeepSeek-V4-Pro | 7.81 | 8.18 | 8.00 | 8.13 | 7.83 | 8.16 |
| backprop | Qwen3-235B | 8.38 | 8.06 | 8.01 | 8.10 | 8.33 | 8.32 |
| normalization | ALLaM-7B | 2.21 | 2.60 | 2.20 | 2.34 | 2.50 | 2.39 |
| normalization | Llama-3-8B | 3.54 | 3.95 | 3.62 | 3.59 | 3.59 | 3.60 |
| normalization | Llama-3.3-70B | 5.24 | 5.34 | 5.22 | 4.80 | 5.14 | 5.29 |
| normalization | Gemma-4-31B | 8.11 | 8.24 | 8.26 | 8.39 | 8.36 | 8.36 |
| normalization | DeepSeek-V4-Pro | 7.72 | 8.11 | 7.88 | 8.14 | 7.89 | 8.05 |
| normalization | Qwen3-235B | 7.96 | 8.13 | 8.14 | 7.97 | 8.28 | 8.06 |

هل يرفع DATR البُعد المستهدف فعلاً بحكم اللوحة؟ وما الضرر الجانبي على البقية؟

| condition | Δ targeted dims (panel) | Δ non-targeted dims (panel) | rollback rate | Δ chars | final == draft (%) |
|---|---|---|---|---|---|
| self_refine | — | 0.258 | 0.000 | 1167.850 | 0.000 |
| self_refine_guard | — | 0.140 | 0.594 | 944.433 | 26.667 |
| datr_no_guard | 0.376 | -0.039 | 0.000 | 3127.517 | 0.000 |
| datr_full | 0.517 | 0.073 | 0.672 | 1807.950 | 28.333 |
| datr_composite_guard | 0.666 | 0.071 | 0.450 | 2386.450 | 18.333 |

| condition | academic_acc | pedagogical_ | clarity_orga | practical_re | completeness | engagement_p | technical_qu | innovation |
|---|---|---|---|---|---|---|---|---|
| self_refine | +0.18 | +0.24 | +0.12 | +0.58 | +0.04 | +0.28 | +0.25 | +0.37 |
| self_refine_guard | +0.05 | +0.14 | +0.10 | +0.32 | +0.00 | +0.17 | +0.13 | +0.21 |
| datr_no_guard | -0.01 | -0.01 | -0.23 | +0.80 | -0.09 | +0.15 | +0.03 | +0.33 |
| datr_full | +0.03 | +0.10 | +0.02 | +0.50 | +0.16 | +0.13 | +0.14 | +0.19 |
| datr_composite_guard | +0.06 | +0.14 | -0.01 | +0.88 | +0.19 | +0.17 | +0.04 | +0.36 |


## F. اختبار أثر الطول

إن بقيت درجات النماذج القوية بعد القصّ إلى 4000 حرف أعلى بوضوح من ALLaM/Llama ⇒ الترتيب ليس أثراً للطول.

| topic | model | full length | truncated to 4000 | drop |
|---|---|---|---|---|
| backprop | DeepSeek-V4-Pro | 7.76 | 6.94 | 0.82 |
| backprop | Gemma-4-31B | 7.98 | 6.51 | 1.47 |
| backprop | Qwen3-235B | 8.37 | 7.26 | 1.11 |
| backprop | ALLaM-7B (reference, full) | 3.10 | — | — |
| backprop | Llama-3-8B (reference, full) | 3.67 | — | — |
| backprop | Llama-3.3-70B (reference, full) | 5.06 | — | — |
| normalization | DeepSeek-V4-Pro | 7.69 | 7.17 | 0.51 |
| normalization | Gemma-4-31B | 8.01 | 7.29 | 0.72 |
| normalization | Qwen3-235B | 8.00 | 7.26 | 0.74 |
| normalization | ALLaM-7B (reference, full) | 2.41 | — | — |
| normalization | Llama-3-8B (reference, full) | 3.55 | — | — |
| normalization | Llama-3.3-70B (reference, full) | 5.22 | — | — |


## H. الرموز المستهلكة في الحكم (لتقدير التكلفة)

| model_id | prompt_tokens | completion_tokens | calls |
|---|---|---|---|
| ALLaM-AI/ALLaM-7B-Instruct-preview | 91191 | 5122 | 36 |
| claude-sonnet-4-6 | 307229 | 57611 | 116 |
| deepseek/deepseek-v4-pro | 76261 | 4104 | 36 |
| google/gemma-4-31b-it | 79241 | 4274 | 36 |
| gpt-4o | 704615 | 78581 | 240 |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | 77989 | 3888 | 36 |
| meta-llama/Meta-Llama-3-8B-Instruct@GGUF-Q4_K_M | 77269 | 3282 | 36 |
| moonshotai/Kimi-K3 | 960956 | 193859 | 354 |
| qwen/qwen3-235b-a22b-2507 | 78084 | 3902 | 36 |
| zai-org/GLM-5.2 | 992594 | 169319 | 354 |
