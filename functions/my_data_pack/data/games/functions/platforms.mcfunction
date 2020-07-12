#
# set the game rules
#
gamerule keepInventory true
gamerule doDaylightCycle false
gamerule doMobSpawning false
#
# start the game in the day
#
time set day
#
# create the central platform
#
execute positioned ~ 124 ~ run function games:central
#
# create the home platforms
#
execute positioned ~34 124 ~ run function games:home
execute positioned ~-34 124 ~ run function games:home
execute positioned ~ 124 ~34 run function games:home
execute positioned ~ 124 ~-34 run function games:home
#
# set the spawn point and then teleport the other players
#
spawnpoint @p ~34 125 ~
teleport @p ~34 125 ~
spawnpoint @p ~-34 125 ~
teleport @p ~-34 125 ~
spawnpoint @p ~ 125 ~34
teleport @p ~ 125 ~34
#
# set the spawn point and then teleport yourself
#
spawnpoint @s ~ 125 ~-34
teleport @s ~ 125 ~-34
#
# clear all inventories apart from elytra
#
clear @a
give @a minecraft:elytra
give @a minecraft:wooden_axe
#
# set all game modes to survival
#
gamemode survival @a

