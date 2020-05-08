# Minecraft - Custom Functions

Custom function can be developed that allow players to enhance their builds. Some example functions
have been include in `/functions` (and some placeholder functions for in-place updating) and these
can be deployed using:

```sh
# for a local deployment:
docker cp functions/dev mc:/data/behavior_packs/vanilla/functions/
# for a cluster deployment:
kubectl cp /minecraft/functions/dev/ $POD:/data/behavior_packs/vanilla/functions/dev
```

If you add new functions to the server, this will require a server restart for them to be loaded.
However, if you update an existing function, you only need to run 
[`/reload'](https://minecraft.gamepedia.com/Commands/reload) from your client.

Current, for simplicity, these functions are deployed to an existing 
[behavior pack](https://minecraft.gamepedia.com/Tutorials/Creating_behavior_packs). If further
functions are developed, it may be worth creating a seperate behavior pack project.

## Generating Custom Functions with Python

Minecraft custom functions simply a list of commands with no other programming constructs. I have
starting experimenting with generating these functions using a python script. For example, this
project contains `domes.py` that generates a set of functions that create glass domes with varying
sizes and colours. A container has been provided with the required python libraries and can be
built using `docker build --tag minecraft-functions .` Then the script can be run with:

```sh
docker run --user $(id -u):$(id -g) --rm -it -v $PWD:/scripts minecraft-functions dome.py
```
