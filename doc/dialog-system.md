I need to brainstorm puzzles and scenarios for a computer game.

It is a 1p 3d game. The setting is a non-descript pre-industrial society. There may be several locations, but the central location is a village, "Babbling Brook", that's set in a karst forest around a flowing river that is uncrossable in certain seasons. There may also a location where farming is done. The player is a child who lives in a village and is at least old enough to have friends and go out on their own. The player interacts with the game strictly through dialog and commands, similar to a text adventure. The player character commands a party. Party members need not occupy the same map as the player character and are only distinguished by complying with certain commands. The player character has a line-of-sight, and cannot see characters or items outside their line-of-sight. There is no HP system - at most, characters may be "hurt" in which case they cannot walk or run until healed.

The intent of the game is to teach language by the natural method. Commands are in an arbitrary language that the player wants to learn. In its most-developed state, the game will teach declension, prepositions/postpositions, conjugation, adjective agreement, comparatives, and question formation. Translation is done by automation that only supports simple sentences. I would like it to work with a large number of languages, so the number of concepts expressed by commands must be kept extremely limited.

The commands allow the player to:

- start or stop conversation with a character
- ask party members to scout and return information on state of play
  - where characters are
  - who has an item
  - who has more of a quality
  - what items a character has
  - how many characters of a type there are
  - yes/no questions regarding character state or ability
- control character inventories
  - trade items of similar value between characters and party members
  - transfer items between party member inventories
  - command party members to use items in their inventory
  - command party members to take or drop items from the map
- move party members
  - indicate which party members are going 
  - indicate whether they should walk or run
  - indicate whether they should stand at, by, on, in, under, within, before, or against a location, character, or item, each of which can be associated with an exact position on a map except for "by" something, which can simply be within a radius of the "at" position
- tell characters things that alter their mental model of the world
  - where characters are
  - where places are
  - who has an item
  - how many characters of a type there are
  - whether characters are in a state

Due to the complexity of the command system, the number of items, characters, or map locations should be kept to a small list of highly versatile thingsl

A major mechanic is that certain players have certain abilities and disabilities:
  * some characters run faster than others
  * some characters do not know where another character or place is
  * small party members can fit through narrow gaps and holes
  * literate party member can read signs and carvings at a location
  * strong characters can lift heavy objects
  * small children will wander unless accompanied
  * small children will attract predators
  * blind elder cannot move without being accompanied
  * deaf characters cannot answer questions and can only be commanded while being accompanied
  * only certain party members are liked by an animal and will be followed by it
  * characters that have a profession can give more clues about items
  * literate party members will send messages accurately
  * numerate party member can estimate large numbers accurately
  * innumerate party member will refuse to estimate numbers
  * color blind characters cannot report color accurately and cannot collect items accurately
  * fat or old characters cannot run
  * some characters (e.g. twins, pet owners) must always be accompanied by another character
  * some party members cannot swim
  * only some party members can climb trees or rock walls
  * only some party members can pick locks
  * only some party members can speak another language
  * only some party members can only speak another language and cannot converse unless accompanied by a character that speaks the language
  * only some party members can access certain sites, e.g. household, workshop, courthouse
  * only some party members can access certain people, e.g. village hetman
  * only some characters can heal
  * only some characters can mend
  * only some characters can craft

Inability to do something will result in outright refusal. This is necessary to reduce the player's turnaround time and frustration.

possible (nonexhaustive) character motivations that motivate tasks:
* thirst
* hunger
* safety
* livelihood
* ownership
* status
* justice
* guardianship

tutorials:
* get water from well
* get wood from forest
* scout: how many animals are in the pen?
* ask party members to search different places to find lost animal
* you arrive where a scout said the fox was, and it's not there anymore — teaches that a location report is a snapshot, not a live tracker, especially in a chase.
* assembly
  * ask party members to assemble at a location
  * tell party member to tell party member the location
  * meeting place becomes unavailable

opportunities:
* fetch quest
  * elder tells player to walk to somewhere on another map, the place is distinguished by e.g. color
  * get water from well
  * get wood from forest
  * player must ask locals where something they are seeking is at
* scouting
  * ask party members to search for a lost ball
  * scout may report accurate information but world updates
* hide-and-seek
  * for each iteration, go to a place
  * once other friends are found, they can scout in other places
* tower defense
  * party fort is under seige
  * tell characters where to stand in defense
  * standing against gate will reinforce gate
* capture-the-flag
  * Retrieve a stolen ball from an rival party's fort
  * scout guard positions and states (awake/asleep)
  * pick prepositions that block sightlines (under the cart, against the fence — not on top of it)
  * tell party member to stand in position to act as a distraction
  * tell PC to walk until the final dash, since running early flips a guard's state to alert.
  * command party members to search, navigate maze, take inventory, and return
* standing puzzle
  * party member must stand on house/tree, jump onto lever, and lift player elsewhere
  * party member must stand on switch
  * party member must lean against a gate to keep it open
  * party member must take rope, stand in place, and use rope
  * party member blocks exits while recovering lost animal
  * sluice gates close only when character stands on gate
  * a character must stand in place to act as scarecrow or guard
* boat puzzle
  * a fast river must be crossed by boat but some characters must stay together or apart
* lock and key puzzle
  * party member may be at door but without key
  * animal will only accompanies the character that carries food
  * animal will only accompanies only a certain character
  * only a certain character can read a sign
  * characters can only enter area if disguised as guard or rival group
* stealth
  * party members must sneak past dogs
  * how many dogs? where are the dogs? are the dogs mean? are the dogs asleep?
  * player may assume a position in a tree to determine when coast is clear
  * command party members to sneak past when coast is clear
  * scout ahead to indicate which paths are clear
  * scout ahead to determine when character is asleep

Underdeveloped ideas:
* ambush - tell party members where to wait
* misdirection
  * party member is wrongly accused and adult is looking for him, give false information to misdirect him
  * bully is looking for party member, give false information to misdirect him
  * scout for party member and tell them
* misdirection
  * report fewer wolves to embolden party member
  * report more party members to intimidate bully
* given stolen goods to enemy to frame them
* hide evidence by distributing among party members
* trust as a resource
  * repeated lying causes characters to automatically distrust

Rejected ideas:
* telephone effect
  * tell party member to tell another results in lossy transmission
  * too much turnaround time for failure, difficult to diagnose problem

* to move information from map A to map Z, someone has to physically carry it: member learns something on A, walks to B, tells member 2 (now co-located), who walks to C and tells member 3. The "tell" command's mechanical requirement — same map — turns geography into the delivery mechanism.
* Sheep get out at night. Recount at dawn against your baseline, scout the fields for stragglers, then physically block the gap by standing within the fence rather than merely by it — the wrong preposition here is a silent failure you only discover at the final recount.
* Someone accuses a kid of stealing a pie. Scout what several suspects are actually carrying, then tell the accuser the true holder — the same "tell" verb used earlier to deceive, now used to clear someone's name, which is a nice mechanical rhyme.
* telling a small sibling "the wolf is at the north field" makes them scared and hide; telling the hunter the same fact sends him out with traps.
