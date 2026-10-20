# Methodology

The Stochastic Action and Pointer Interaction Engine for Naturalistic Sessions is a hierarchical generative model. It separates the interaction into two levels:

1. **Motor layer** — where the pointer goes, how long the reach takes, and how velocity changes.
2. **Session layer** — how long a page is inspected, how deep a session runs, and when a longer pause occurs.

This separation matters. A smooth cursor path does not make an interaction trace realistic if every page is visited at identical intervals; a plausible session cadence does not repair mechanically linear pointer motion.

## Motor layer

For a target at distance `D` and width `W`, expected movement duration follows the Shannon form of Fitts's law:

```text
T = a + b log2(D / W + 1)
```

The current calibration uses `a = 0.12` and `b = 0.14`, then adds bounded between-movement variation. Those constants are starting assumptions and should be re-estimated for a measured population, device, and task.

The implementation can sample one of four trajectory families for each reach:

- **Minimum jerk** uses `10τ³ − 15τ⁴ + 6τ⁵` as temporal progress along a gently curved path.
- **Sigma lognormal** combines a primary stroke with a temporally overlapping corrective submovement.
- **Wind dynamics** integrates attraction to the target with autocorrelated lateral force and a distance-sensitive velocity cap.
- **Bézier** uses randomized control points with minimum-jerk timing.

Mixed mode samples a family independently for each reach. It is a mixture model, not evidence that one person changes control strategy with those exact probabilities.

## Session layer

Page dwell is sampled from a Weibull distribution with shape below one, producing many short inspections and a smaller tail of longer reading episodes. A reading component depends on page word count. Session depth uses an inverse-Gaussian draw, and longer pauses use a bounded Pareto distribution.

The default interval for quota-spreading is centered at `86,400 / N` seconds for `N` events per day, with triangular variation. This is a scheduling primitive; it is not inferred from the research papers.

## Validation status

The implementation is **mechanistically informed and not empirically calibrated** against a named human-interaction dataset. The appropriate next validation step is to compare synthetic and measured traces on held-out distributions of:

- movement time conditional on target distance and width;
- velocity, acceleration, and jerk profiles;
- path efficiency and curvature;
- endpoint error and corrective submovements;
- page dwell and session depth;
- within-person and between-person variance.

The project should be described as a research prototype until that calibration is complete. It is unsuitable for identity inference, biometric authentication, or claims about an individual.

## Research basis

- P. M. Fitts (1954), “The information capacity of the human motor system in controlling the amplitude of movement.” [DOI 10.1037/h0055392](https://doi.org/10.1037/h0055392)
- T. Flash and N. Hogan (1985), “The coordination of arm movements: an experimentally confirmed mathematical model.” [DOI 10.1523/JNEUROSCI.05-07-01688.1985](https://doi.org/10.1523/JNEUROSCI.05-07-01688.1985)
- R. Plamondon and M. Djioua (2006), “A multi-level representation paradigm for handwriting stroke generation.” [DOI 10.1016/j.humov.2006.07.004](https://doi.org/10.1016/j.humov.2006.07.004)
- C. Liu, R. W. White, and S. Dumais (2010), “Understanding web browsing behaviors through Weibull analysis of dwell time.” [Microsoft Research](https://www.microsoft.com/en-us/research/publication/understanding-web-browsing-behaviors-through-weibull-analysis-of-dwell-time/)
- B. A. Huberman, P. L. T. Pirolli, J. E. Pitkow, and R. M. Lukose (1998), “Strong regularities in World Wide Web surfing.” [DOI 10.1126/science.280.5360.95](https://doi.org/10.1126/science.280.5360.95)
- P. Barford and M. Crovella (1998), “Generating representative Web workloads for network and server performance evaluation.” [DOI 10.1145/277858.277897](https://doi.org/10.1145/277858.277897)
