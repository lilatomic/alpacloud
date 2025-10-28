# alpacloud.eztag

`eztag` helps you easily filter things by tags. For example:
```python
@dataclass
class Snippet:
    name: str
    content: str
    tags: TagSet
```

you can filter them with convenient syntax:

```python
filter(lambda s: s.tags.has("python"), snippets)
```

There are several filter functions available:

- has : check if a TagSet has a tag
- match : check if a TagSet has a key with a value
- rematch : check if a TagSet has a key with a value that matches a regex
- contains : check if a TagSet has a key whose value contains a substring
