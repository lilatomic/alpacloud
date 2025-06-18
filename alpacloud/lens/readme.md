# Lens

A library for modifying Kubernetes manifests and other json-like objects.

## Theoretical underpinnings

Lenses have several formulations.
- Profunctors : These are generalisations of functions (think a fancy way of writing `map`). The advantage is that optical composition is just function composition. The disadvantage is that this composition is not introspectable. This means that it isn't really possible to report when an optic fails to find an expected value.
- 

## Bibliography

- [Don't Fear the Profunctor Optics!](https://github.com/hablapps/DontFearTheProfunctorOptics) : a clear walkthrough of concrete optics, profunctors, and profunctor optics. It includes diagrams which visualise the core principle of "just gluing arrows together". It also uses more practical examples for motivation and illustration.
- [](https://bartoszmilewski.com/2015/07/13/from-lenses-to-yoneda-embedding/) : 