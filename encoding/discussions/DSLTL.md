# Problems with LTL and how to fix them

In the experiments with LTL as a target language, it turned out that many features of LTL are counterproductive
for specifying *what needs to be accomplished*. 
For a trace 
```
   noise; noise;wet,noise; wet; wet; dry
```

LTL descriptions can be meaningful, e.g. `F(dry)`, `F(wet U dry)`, but also completely useless, e.g. 
`F(dry) U wet`. There are a couple of things that turned out to be problematic
 - implications: the tool will come up with all sorts of trivially true implications (with false antecedent)
 - combinations of temporal operators: true-value of temporal operators is often justified later than 
 for what it is used. One example is `F(dry) U wet`
 
More examples of useless formulas, but satisfied by a trace are [here](positiveExamplesAnalysis) and [here](positiveExamplesAnalysis2).
In order to avoid such behaviors, we need a better language. I suggest a restriction of LTL and the introduction
of new operators.


## Domain specific LTL: proposal

The syntax of the language is given by

```
<a> : AP | not AP 
<b> : E <a>  | <a> U <a> | G<a>  
<c> : <a> | <a> B <c>
<d> : <c> | <b>
<e> : <d> or <d> | <d> and <d> 
```

The semantics of the newly introduced operators E (ends), and B (before) is

```
t,i |= E p   iff  t, last |= p
t,i |= p B q iff t,i |= F(p and F(q))
```

This language enables us to reason about the relative ordering of events, about the situation in the end, and about 
safety requirements.
(Optionally, B operator could be defined as *strictly before*. For experiments reasons, in the codebase its marked by `S`)

Kinds of properties that this language can express:

 - sequencing (happens before relation and exact order of events)
 - end conditions
 - safety until reaching the end condition (operator `U`)   
 - global conditions (operator `G`)

When running the tool for that grammar and the trace `safe; safe, goal1;wet,safe; safe, wet; safe, wet; safe,dry, goal2`,
and with hints `safe, goal1, goal2`, we get these results
- `(E goal2)`, 
- `(goal2 B goal2)`, 
- `(E dry)`, 
- `(dry B dry)`, 
- `(safe U goal2)`, 
- `(goal2 B safe)`,
 - `(safe B goal2)`, 
 - `(goal1 B goal2)`, 
 - `(dry B safe)`, 
 - `(safe & (E goal2))`, 
 - `(safe & (goal2 B safe))`, 
 - `(safe & (goal2 B goal2))`, 
 - `(safe & (safe U goal2))`, 
 - `(safe & (safe B goal2))`, 
 - `(safe & (goal1 B goal2))`
 
 These candidates - while not always correct - are at least all meaningful with respect to what the user
 might want to specify.
 
 ### Shortcomings of this restriction (and justifications)
 One cannot say things such as
 - `if wet, then eventually dry` : this makes a lot of sense in the RL/IRL/reactive setting, but for us, 
unless the world is very skewed, the user will want to talk about the goals, and not conditions
- `from some point have_hammer until nail` : we can change the available atomic propositions to express
 similar things, for example `take_hammer B nail and never drop_hammer`
 
 ### Usage in the context of Flipper
 We can restate Flipper into Minecraft-like context where one has to gather different objects (but there is no 
 dropping).
 Atomic propositions are then `picked<single | every >_<color>, picked<single | every>_<shape>, picked<single | every>_<color_shape>` 
 We could additionally introduce different colors of fields (e.g., lava, water etc.), giving birth to `at_<field_type>`
 atomic proposition.