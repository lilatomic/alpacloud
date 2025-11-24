# alpacloud.eztag

`eztag` helps you easily filter things by tags.

## Usage

### Filtering in code

You can directly invoke the filters as functions. For example:

```python
from alpacloud.eztag.tag import TagSet

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

### Filtering external data

If your objects don't have tags, you can associate tag data with them using `Selector`:

```python
from alpacloud.eztag.logic import TagMatch
from alpacloud.eztag.selector import Selector
from alpacloud.eztag.tag import TagSet

tasks = Selector([
    (TagSet.from_dict({"env":"prd", "dangerous": "true"}), task0),
    (TagSet.from_dict({"env":"stg", "dangerous": "false"}), task1),
])

dangerous_tasks = tasks.select(TagMatch("dangerous", "true"))
```

### Filtering from the CLI

`eztag` allows you to input filters in a simple language from the CLI. You can build this filtering into your own tools.


```python
import click

from alpacloud.eztag.parser import Parser, transformer
from alpacloud.eztag.selector import Selector

tagged_tasks = Selector(...)

@click.command()
@click.argument("filter")
def cli(filter):
    expr = transformer.transform(Parser(filter).parse())
    selected_tasks = tagged_tasks.select(expr)

    for task in selected_tasks:
        task.run()
```

Then you can invoke it like this:
```shell
task-run --filter 'and(match(env, prd), re(name, /cert.*/)'
```

## Advanced usage

### Adding custom filters or operators

1. Implement your filter as a subclass of `alpacloud.eztag.logic.Expr`

   ```python
   from dataclasses import dataclass
   from alpacloud.eztag.logic import Expr
   
   @dataclass(frozen=True)
   class Shard(Expr):
       """Run tasks with this shard identifier"""
       shard: int
   
       def check(self, tags) -> bool:
           return tags.contains("shard", str(self.shard))
   ```
   
2. Register your filter in the `transformer` dictionary:

   ```python
   from alpacloud.eztag.transformer import transformer, TokenTransformer, TokenTransformation
   
   my_transformer = transformer.extended({
       "SHARD": TokenTransformation("SHARD", Shard, args=["shard"]),
   })
   ```
