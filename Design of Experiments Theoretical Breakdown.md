## Design of Experiments: theoretical breakdown

**Design of Experiments**, often shortened to **DOE**, is a statistical methodology for planning, running, analyzing, and interpreting controlled tests so that you can understand how input variables affect one or more outcomes.

At its core, DOE answers questions like:

> Which factors matter?
> How much do they matter?
> Do factors interact?
> What settings optimize the response?
> How confident are we in the result?

DOE is widely used in engineering, manufacturing, agriculture, product development, biotech, chemistry, operations, software experimentation, and quality improvement.

---

# 1. The basic idea

A system has **inputs**, called **factors**, and **outputs**, called **responses**.

For example, suppose you are improving a baking process.

| DOE concept      | Example                                                            |
| ---------------- | ------------------------------------------------------------------ |
| Response         | Cake height                                                        |
| Factors          | Oven temperature, baking time, flour type                          |
| Factor levels    | 175°C vs. 200°C, 30 min vs. 40 min                                 |
| Experimental run | One specific combination of factor settings                        |
| Noise            | Variation from humidity, ingredient differences, measurement error |

DOE studies the relationship:

[
Y = f(X_1, X_2, ..., X_k) + \varepsilon
]

where:

[
Y
]

is the response,

[
X_1, X_2, ..., X_k
]

are experimental factors, and

[
\varepsilon
]

is random error.

The goal is not merely to collect data, but to collect data **efficiently and informatively**.

---

# 2. DOE versus one-factor-at-a-time testing

A common but weak approach is **one-factor-at-a-time**, or OFAT. In OFAT, you vary one input while holding all others fixed.

Example:

1. Test temperature while holding time constant.
2. Test time while holding temperature constant.
3. Test material while holding temperature and time constant.

The problem is that OFAT often misses **interactions**.

An interaction occurs when the effect of one factor depends on the level of another factor.

For example:

* Higher temperature may improve yield at short bake times.
* But higher temperature may reduce yield at long bake times.

That means the effect of temperature cannot be understood without considering time.

DOE is designed to estimate both:

[
\text{main effects}
]

and

[
\text{interaction effects}
]

systematically.

---

# 3. Core principles of DOE

The classical theory of DOE rests on three major principles:

## 3.1 Randomization

**Randomization** means running experimental trials in random order.

This protects the experiment from hidden time-related or order-related effects.

For example, if you test all low-temperature runs in the morning and all high-temperature runs in the afternoon, any difference might be caused by temperature, but it might also be caused by humidity, operator fatigue, machine warm-up, or raw-material changes.

Randomization helps make uncontrolled variation behave like random noise rather than systematic bias.

---

## 3.2 Replication

**Replication** means repeating experimental runs under the same conditions.

Replication allows you to estimate experimental error.

For example, if you run the same condition three times and get:

[
52,\ 55,\ 53
]

you have a sense of natural variation.

Without replication, it is harder to distinguish a real effect from random fluctuation.

Replication supports:

[
\text{error estimation}
]

[
\text{confidence intervals}
]

[
\text{hypothesis testing}
]

[
\text{power analysis}
]

---

## 3.3 Blocking

**Blocking** is used when there is a known source of variation that is not the main focus of the experiment.

For example:

* Different machines
* Different operators
* Different batches of material
* Different days
* Different production lines

A block groups similar experimental units together.

Example:

| Block | Meaning                     |
| ----- | --------------------------- |
| Day 1 | Runs performed on Monday    |
| Day 2 | Runs performed on Tuesday   |
| Day 3 | Runs performed on Wednesday |

Instead of pretending that all days are identical, DOE can explicitly account for day-to-day variation.

A common model might be:

[
Y_{ij} = \mu + \tau_i + \beta_j + \varepsilon_{ij}
]

where:

[
\mu
]

is the overall mean,

[
\tau_i
]

is the treatment effect,

[
\beta_j
]

is the block effect, and

[
\varepsilon_{ij}
]

is random error.

---

# 4. Fundamental DOE terminology

## Factor

A **factor** is an input variable you deliberately vary.

Examples:

* Temperature
* Pressure
* Concentration
* Speed
* Supplier
* Algorithm version
* User-interface layout

Factors may be:

| Type         | Example                          |
| ------------ | -------------------------------- |
| Quantitative | Temperature: 100°C, 120°C, 140°C |
| Qualitative  | Material type: A, B, C           |

---

## Level

A **level** is a setting of a factor.

Example:

| Factor      | Levels         |
| ----------- | -------------- |
| Temperature | Low, High      |
| Pressure    | 10 psi, 20 psi |
| Catalyst    | A, B, C        |

A two-level design uses two settings for each factor, often coded as:

[
-1 \quad \text{and} \quad +1
]

---

## Treatment

A **treatment** is a specific combination of factor levels.

Example:

| Temperature | Pressure | Treatment   |
| ----------- | -------- | ----------- |
| Low         | Low      | Treatment 1 |
| Low         | High     | Treatment 2 |
| High        | Low      | Treatment 3 |
| High        | High     | Treatment 4 |

---

## Response

A **response** is the measured output.

Examples:

* Yield
* Strength
* Defect rate
* Conversion rate
* Cost
* Customer satisfaction
* Processing time

---

## Experimental unit

The **experimental unit** is the object or entity to which a treatment is applied.

Examples:

* A patient
* A machine part
* A batch of chemical material
* A website visitor
* A field plot

---

# 5. Main effects

A **main effect** measures the average effect of changing one factor from one level to another.

Suppose factor (A) has two levels: low and high.

[
\text{Effect of A} = \bar{Y}*{A+} - \bar{Y}*{A-}
]

where:

[
\bar{Y}_{A+}
]

is the average response when (A) is high, and

[
\bar{Y}_{A-}
]

is the average response when (A) is low.

Example:

| Temperature | Average yield |
| ----------- | ------------- |
| Low         | 60            |
| High        | 75            |

Then:

[
\text{Temperature effect} = 75 - 60 = 15
]

So increasing temperature is associated with a 15-unit increase in yield, averaged over the other factors.

---

# 6. Interaction effects

An **interaction** exists when the effect of one factor changes depending on another factor.

For two factors (A) and (B), the interaction is often written as:

[
AB
]

A simple interaction contrast is:

[
AB = \frac{(Y_{++} - Y_{-+}) - (Y_{+-} - Y_{--})}{2}
]

Conceptually, this asks:

> Is the effect of (A) the same at low (B) and high (B)?

Example:

| Temperature | Time  | Yield |
| ----------- | ----- | ----- |
| Low         | Short | 50    |
| High        | Short | 70    |
| Low         | Long  | 65    |
| High        | Long  | 66    |

At short time:

[
70 - 50 = 20
]

At long time:

[
66 - 65 = 1
]

Temperature has a large effect when time is short, but almost no effect when time is long. That is an interaction.

Interactions are one of the biggest reasons DOE is more powerful than one-factor-at-a-time testing.

---

# 7. The statistical model behind DOE

Many DOE analyses use a linear model:

[
Y = X\beta + \varepsilon
]

where:

[
Y
]

is the vector of observed responses,

[
X
]

is the design matrix,

[
\beta
]

is the vector of unknown effects, and

[
\varepsilon
]

is the random error.

Usually, the error is assumed to satisfy:

[
\varepsilon \sim N(0, \sigma^2)
]

That means the errors are assumed to be independent, normally distributed, centered at zero, and have constant variance.

For a two-factor experiment, the model may be:

[
Y = \beta_0 + \beta_A A + \beta_B B + \beta_{AB}AB + \varepsilon
]

where:

* (\beta_0) is the overall mean
* (\beta_A) is the effect of factor (A)
* (\beta_B) is the effect of factor (B)
* (\beta_{AB}) is the interaction effect
* (\varepsilon) is random error

---

# 8. Analysis of variance, or ANOVA

**ANOVA** is a central tool in DOE.

It decomposes total variation in the response into components attributable to:

[
\text{factors}
]

[
\text{interactions}
]

[
\text{blocks}
]

[
\text{random error}
]

The basic decomposition is:

[
SS_T = SS_{\text{model}} + SS_E
]

where:

* (SS_T) is total sum of squares
* (SS_{\text{model}}) is variation explained by the experimental factors
* (SS_E) is unexplained error variation

For a factor (A), a typical F-test is:

[
F = \frac{MS_A}{MS_E}
]

where:

* (MS_A) is the mean square for factor (A)
* (MS_E) is the mean square error

A large F-statistic suggests the factor explains more variation than would be expected from random error alone.

---

# 9. Major types of experimental designs

## 9.1 Completely randomized design

A **completely randomized design** assigns treatments randomly to experimental units.

This is the simplest design.

Example:

You have 40 parts and 4 treatments. Randomly assign 10 parts to each treatment.

Use this when experimental units are relatively homogeneous.

---

## 9.2 Randomized block design

A **randomized block design** groups experimental units into blocks and randomizes treatments within each block.

Example:

You test four coatings on metal parts across three production batches.

Each batch receives all four coatings, but the order is randomized within each batch.

This reduces noise due to batch differences.

---

## 9.3 Full factorial design

A **full factorial design** tests every combination of factor levels.

For (k) factors, each at two levels, the number of runs is:

[
2^k
]

Example:

For three factors (A), (B), and (C), each at low and high levels:

[
2^3 = 8
]

runs are required.

| Run |  A |  B |  C |
| --- | -: | -: | -: |
| 1   |  - |  - |  - |
| 2   |  + |  - |  - |
| 3   |  - |  + |  - |
| 4   |  + |  + |  - |
| 5   |  - |  - |  + |
| 6   |  + |  - |  + |
| 7   |  - |  + |  + |
| 8   |  + |  + |  + |

Full factorial designs can estimate all main effects and interactions.

They are powerful, but they become expensive as the number of factors grows.

---

## 9.4 Fractional factorial design

A **fractional factorial design** uses only a fraction of the full factorial combinations.

For example, instead of running:

[
2^5 = 32
]

runs for five factors, you might run a half-fraction:

[
2^{5-1} = 16
]

runs.

Fractional factorial designs are based on the idea that high-order interactions are often less important than main effects and two-factor interactions.

The tradeoff is **aliasing**.

Aliasing means that two or more effects are confounded and cannot be estimated separately.

Example:

[
A \text{ may be aliased with } BCD
]

This means the estimated effect for (A) actually represents a combination of (A) and the interaction (BCD).

---

## 9.5 Screening designs

A **screening design** is used when many factors are possible, but only a few are expected to matter.

The objective is not final optimization. The objective is to identify the most influential factors.

Common screening designs include:

* Fractional factorial designs
* Plackett-Burman designs
* Definitive screening designs

Screening is common early in process development.

---

## 9.6 Response surface methodology

**Response Surface Methodology**, or **RSM**, is used when the goal is optimization.

It typically fits a second-order model:

[
Y = \beta_0 + \sum_{i=1}^{k}\beta_i X_i + \sum_{i=1}^{k}\beta_{ii}X_i^2 + \sum_{i<j}\beta_{ij}X_iX_j + \varepsilon
]

This model includes:

* Linear terms
* Interaction terms
* Curvature terms

RSM is used to find maxima, minima, or target settings.

Common RSM designs include:

| Design                   | Purpose                              |
| ------------------------ | ------------------------------------ |
| Central Composite Design | Estimates curvature and interactions |
| Box-Behnken Design       | Efficient quadratic modeling         |
| Three-level factorial    | Full quadratic exploration           |

Example use:

You might first use a screening design to identify that temperature, pressure, and concentration matter. Then you use RSM to optimize those three factors.

---

## 9.7 Mixture designs

A **mixture design** is used when factors are proportions that must sum to one.

Example:

[
x_1 + x_2 + x_3 = 1
]

This is common in:

* Chemical formulations
* Food recipes
* Pharmaceutical blends
* Polymer mixtures

Because increasing one component necessarily decreases another, ordinary factorial designs are not appropriate.

---

## 9.8 Split-plot designs

A **split-plot design** is used when some factors are hard to change and others are easy to change.

Example:

In a manufacturing process:

* Oven temperature is hard to change.
* Conveyor speed is easy to change.

Rather than randomly changing oven temperature every run, you may set a temperature for a batch of runs and randomize conveyor speed within that batch.

Split-plot designs require special analysis because there are different levels of experimental error.

---

## 9.9 Robust parameter designs

Robust design aims to find factor settings that make performance less sensitive to noise.

The goal is not only to improve the average response, but also to reduce variation.

Example:

A product should perform well despite changes in temperature, humidity, user behavior, or raw-material variation.

This approach is associated with quality engineering and Taguchi methods.

---

# 10. Confounding and aliasing

Confounding occurs when the effect of one factor cannot be separated from another source of variation.

Example:

If all high-temperature runs are done on Machine 1 and all low-temperature runs are done on Machine 2, then temperature and machine are confounded.

You cannot tell whether the observed difference was caused by temperature or machine.

Aliasing is a structured form of confounding common in fractional factorial designs.

For example:

[
I = ABCD
]

is a defining relation. This implies aliases such as:

[
A = BCD
]

[
B = ACD
]

[
AB = CD
]

The **resolution** of a fractional factorial design describes the severity of aliasing.

| Resolution | Meaning                                                                                                   |
| ---------- | --------------------------------------------------------------------------------------------------------- |
| III        | Main effects may be aliased with two-factor interactions                                                  |
| IV         | Main effects clear of two-factor interactions, but two-factor interactions may be aliased with each other |
| V          | Main effects and two-factor interactions are generally separable from lower-order effects                 |

Higher resolution is usually better, but it requires more runs.

---

# 11. Orthogonality

A design is **orthogonal** when estimates of effects are statistically independent.

In an orthogonal two-level design, columns of the design matrix are uncorrelated:

[
X_i^T X_j = 0 \quad \text{for } i \neq j
]

This is valuable because the estimated effect of one factor is not distorted by the presence of another factor.

Orthogonality makes interpretation cleaner and analysis more stable.

---

# 12. Balance

A design is **balanced** when each treatment or factor level appears equally often.

For example, in a balanced two-level design, factor (A) appears equally often at low and high levels.

Balance helps ensure fair comparisons and often simplifies analysis.

---

# 13. Power and sample size

DOE is not only about which combinations to test. It is also about how many observations are needed.

Power depends on:

* Effect size
* Experimental error variance
* Number of replicates
* Significance level
* Design structure

Statistical power is the probability of detecting an effect if the effect truly exists.

A general intuition is:

[
\text{Power increases when noise decreases}
]

[
\text{Power increases when replication increases}
]

[
\text{Power increases when the effect size is larger}
]

Before running an experiment, good DOE practice asks:

> What effect size is practically meaningful, and how many runs are needed to detect it?

---

# 14. Sequential experimentation

DOE is often best used sequentially.

A common workflow is:

1. **Screening**
   Identify which factors matter.

2. **Characterization**
   Understand main effects and interactions.

3. **Optimization**
   Find the best factor settings.

4. **Confirmation**
   Validate the predicted optimum.

This matters because trying to design one giant experiment that answers everything is often expensive, slow, and fragile.

DOE is strongest when used as an iterative learning process.

---

# 15. Assumptions behind DOE analysis

Most classical DOE analysis assumes:

| Assumption                           | Meaning                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| Independence                         | Errors are not correlated                                   |
| Constant variance                    | Error variance is stable across conditions                  |
| Normality                            | Errors are approximately normally distributed               |
| Correct model form                   | The fitted model includes the important terms               |
| Additivity, unless modeled otherwise | Effects combine additively unless interactions are included |

These assumptions should be checked using residual analysis.

Common diagnostics include:

* Residuals versus fitted values
* Normal probability plots
* Residuals versus run order
* Residuals by factor level
* Leverage and influence checks

If assumptions are violated, possible remedies include:

* Transforming the response
* Using generalized linear models
* Adding missing interaction or curvature terms
* Blocking
* Modeling correlation
* Using nonparametric or robust methods

---

# 16. DOE for non-normal responses

Not every response is continuous and normally distributed.

Examples:

| Response type | Example          | Possible model                     |
| ------------- | ---------------- | ---------------------------------- |
| Binary        | Pass/fail        | Logistic regression                |
| Count         | Defects per unit | Poisson or negative binomial model |
| Proportion    | Conversion rate  | Binomial model                     |
| Time-to-event | Failure time     | Survival model                     |
| Ordinal       | Rating scale     | Ordinal regression                 |

For example, if the response is conversion rate in an A/B test, a binomial or logistic model may be more appropriate than ordinary linear regression.

---

# 17. Optimization in DOE

Once a model is fitted, you can use it to optimize the response.

For a response surface model:

[
\hat{Y} = \hat{\beta}*0 + \sum \hat{\beta}*i X_i + \sum \hat{\beta}*{ii}X_i^2 + \sum \hat{\beta}*{ij}X_iX_j
]

optimization means finding values of (X) that maximize, minimize, or hit a target value of (\hat{Y}).

For multiple responses, DOE often uses **desirability functions**.

Example:

You may want to:

* Maximize yield
* Minimize cost
* Keep viscosity within a target range
* Minimize defect rate

A desirability function converts each response into a score between 0 and 1, then combines the scores into an overall objective.

---

# 18. Confirmation experiments

A DOE model is not complete until it is validated.

After identifying promising settings, you run **confirmation experiments** at the predicted optimum or selected condition.

The goal is to check whether the observed response agrees with the model prediction.

Example:

[
\text{Predicted yield} = 92%
]

[
\text{Observed confirmation yield} = 90.8%
]

If this falls within the prediction interval, the model is reasonably supported.

If not, the model may be missing important factors, interactions, curvature, or noise sources.

---

# 19. Practical DOE workflow

A good DOE project usually follows this structure:

## Step 1: Define the objective

Examples:

* Increase yield
* Reduce defects
* Improve customer conversion
* Minimize cycle time
* Identify important variables
* Optimize a formulation

A vague objective leads to a weak experiment.

---

## Step 2: Define the response variable

The response should be measurable, relevant, and reliable.

Bad response:

> “Quality”

Better response:

> “Percent of parts passing tensile-strength specification”

---

## Step 3: Choose factors and levels

Select controllable factors that may influence the response.

Example:

| Factor      |    Low |   High |
| ----------- | -----: | -----: |
| Temperature |  150°C |  180°C |
| Pressure    | 20 psi | 40 psi |
| Time        | 10 min | 20 min |

Factor ranges should be wide enough to reveal effects but not so wide that the system becomes unsafe, infeasible, or irrelevant.

---

## Step 4: Choose the design

The design depends on the goal.

| Goal                           | Likely design                            |
| ------------------------------ | ---------------------------------------- |
| Compare a few treatments       | Completely randomized design             |
| Account for nuisance variation | Randomized block design                  |
| Study all combinations         | Full factorial                           |
| Screen many variables          | Fractional factorial or screening design |
| Optimize                       | Response surface design                  |
| Study formulations             | Mixture design                           |
| Handle hard-to-change factors  | Split-plot design                        |

---

## Step 5: Randomize and run

Randomization protects against bias.

The run sheet should include:

* Run order
* Factor settings
* Blocking information
* Measurement instructions
* Operator notes
* Environmental conditions, if relevant

---

## Step 6: Analyze

Analysis typically includes:

* Main effects
* Interactions
* ANOVA
* Regression model
* Residual diagnostics
* Confidence intervals
* Prediction intervals
* Practical significance, not just statistical significance

---

## Step 7: Interpret practically

A statistically significant effect is not always practically important.

For example:

[
p < 0.05
]

does not necessarily mean the improvement is economically meaningful.

DOE should connect statistical findings to real-world decisions.

---

## Step 8: Confirm

Run confirmation trials before implementing the final setting.

---

# 20. Common mistakes in DOE

## Mistake 1: Not randomizing

This can confound treatment effects with time, operator, batch, or environmental variation.

## Mistake 2: Using too narrow a factor range

If levels are too close together, effects may be too small to detect.

## Mistake 3: Ignoring interactions

Important systems often behave differently under different combinations of factors.

## Mistake 4: Too little replication

Without replication, error estimation is weak.

## Mistake 5: Changing uncontrolled variables during the experiment

This introduces hidden confounding.

## Mistake 6: Optimizing from a screening design

Screening designs identify important factors; they usually do not provide a final optimum.

## Mistake 7: Relying only on p-values

Effect size, uncertainty, cost, feasibility, and robustness matter too.

---

# 21. The central philosophy of DOE

DOE is built around a few powerful ideas:

1. **Experiment deliberately, not casually.**
2. **Vary multiple factors together.**
3. **Use randomization to protect against bias.**
4. **Use replication to estimate noise.**
5. **Use blocking to control nuisance variation.**
6. **Model interactions, not just main effects.**
7. **Experiment sequentially.**
8. **Confirm before implementing.**

In short:

> DOE is the disciplined use of statistical structure to learn as much as possible from as few experimental runs as practical.

It is not just a collection of experimental layouts. It is a methodology for turning uncertainty into evidence-based decisions.
