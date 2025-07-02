# Lens

A library for modifying Kubernetes manifests and other json-like objects.

## Examples

You can use lenses for directly getting, setting, or mapping (modifying) data

```python
# set the namespace of a Kubernetes object
namespace = kord("metadata") / KeyLens("namespace")
namespace.l_set(my_pod, "my-ns")

# modify the contents of a Kubernetes secret
admin_password = kord("data") / KeyLens("admin-password") / B64()
admin_password.l_set(my_secret, "super-secret-password")

# get the number of ready replicas of a Kubernetes deployment
ready_replicas = Lens()["status"]["readyReplicas"]
ready_replicas.l_get(my_deployment)

# get the name and resources of every container in a Kubernetes pod
containers = Lens()["spec"]["containers"]
resources = (containers * KeyLens("name")) % (containers * KeyLens("resources"))

# add one more replica to a deployment
replicas = Lens()["spec"]["replicas"]
replicas.l_map(my_deployment, lambda n: n + 1)
```

You can bind the mapping function to easily apply the same transformation multiple times:

```python
# note how we can re-use `replicas` from above
add_replica = replicas @ (lambda n: n + 1)
add_replica.map(my_deployment)
```

You can combine several bound lenses to create pipelines

```python
set_namespace = namespace @ Const("my-ns")

labels = kord("metadata") / kord("labels")
add_team_label = (labels / KeyLens("team", None)) @ Const("my_team")

global_pipeline = set_namespace % add_team_label
```

## Usage

Lenses can be built using either their classes or their helpers. The helpers are the most convenient, and look like
standard access:

```python
# These are equivalent
l = Lens()["my-key"][0].my_attribute / B64()
l
KeyLens("my-key").l_compose(IndexLens(0)).l_compose(AttrLens("my_attribute")).l_compose(B64())
```

Lenses support 3 operations. They're all prefixed with "l_" to avoid conflicting with attributes that your objects might
have.

- `l_get` : get the value focused by the lens
- `l_set` : set the value focused by the lens
- `l_map` : use a function to modify the value focused by the lens

### Types of Lenses

There are several lenses for moving through objects:

| Name           | Description                                       | equivalence and example                                                                               |
|----------------|---------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| AttrLens       | get an attribute                                  | `AttrLens("foo")` -> `object.foo`                                                                     |
| IndexLens      | get an item by its index                          | `IndexLens(1)` -> `object[1]`                                                                         |
| KeyLens        | get an item by its key                            | `KeyLens("foo")` -> `object["foo"]`                                                                   |
| ForEachLens    | apply the sublens to all elements of a collection | a for loop                                                                                            |
| CodecLens      | decode the item                                   | `CodecLens(json.loads, json.dumps)` decodes the payload and re-encodes after modification             |
| DataclassCodec | instantiate a dataclass from a dict               | `DataclassCodec(User)`                                                                                |
| FilterLens     | focus if a predicate matches                      | `ForEachLens(FilterLens(lambda x: x.value > 0))` will only operate on items whose `value` is positive |

There are helper lenses for common JSON/YAML operations:

| Name | Description                                    | equivalence and example                       |
|------|------------------------------------------------|-----------------------------------------------|
| kord | get the key, defaulting to an empty dictionary | `kord("labels")` -> `KeyLens("labels", {})`   | 
| korl | get the key, defaulting to an empty list       | `korl("volumes")` -> `KeyLens("volumes", [])` |


## Theoretical underpinnings

Lenses have several formulations.

- Profunctors : These are generalisations of functions (think a fancy way of writing `map`). The advantage is that
  optical composition is just function composition. The disadvantage is that this composition is not introspectable.
  This means that it isn't really possible to report when an optic fails to find an expected value.
-

## Bibliography

- [Don't Fear the Profunctor Optics!](https://github.com/hablapps/DontFearTheProfunctorOptics) : a clear walkthrough of
  concrete optics, profunctors, and profunctor optics. It includes diagrams which visualise the core principle of "just
  gluing arrows together". It also uses more practical examples for motivation and illustration.
- [](https://bartoszmilewski.com/2015/07/13/from-lenses-to-yoneda-embedding/) : 