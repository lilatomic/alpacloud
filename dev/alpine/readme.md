# Alpine build

This builds many Pythons and Pants

## Actions

### Start the container

```shell
docker run --name alpinebuild --rm -it -v "$(pwd)/dev/alpine:/home/packager/dev/alpine" $(docker build -q dev/alpine/)
```

### Init keys

```shell
abuild-keygen -n --append --install
```

### Build an APK

```shell
REPODEST=/tmp/pkg0 abuild -r -K
```