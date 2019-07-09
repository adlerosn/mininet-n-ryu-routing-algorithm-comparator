# Mininet+Ryu Routing algorithm Comparator
A bunch of scripts and files that describe topology creation, the topologies,
the testing data, real-time graph rendering, table creation and chart creation.

## How to replicate these results
- Install Mininet, Ryu and Python3
-  - Untested on Mininet compiled against Python2
-  - Untested on Ryu compiled against Python2
- Either run `pip3 install -r requirements.txt` with enough privileges on your system or install those requirements from your package manager.
- Run `make` as root.

## Files which are safe to delete
- `rm -rf boxplots`
- `rm -rf resultcache`
- `rm -rf *.json`
- `rm -rf *.pdf`
- `rm -rf *.pdf.bw.txt`
- `rm -rf *.state`

Or, you can simply run `make clear` to run them all.

## How to add more algorithms to the comparison:
1. On `latencycontroller.py`, create your algorithm as a class child of AbstractPathEvaluator (example: `MyPathEvaluator`), where you override “`__call__(self, ...)`” with your algorithm.
2. On `latencycontroller.py`, add the class you created as an entry of the `path_evaluators` dict (example: “`'my_path_eval': MyPathEvaluator,`”).
3. Add the key in the previous dict for your class into the `ALGOS` list (example: “`'my_path_eval',`”).

That's it.

## How to add more topologies to the comparison:

### From miniedit
1. Create a topology and save it; we're going to use `my_topo.mn` in this example.
2. Add a recipe to `Makefile`:
<br>`my_topo.json:`
<br>&nbsp;&nbsp;&nbsp;&nbsp;`./topomn2json.py my_topo`
3. Add that same last line to the end of `generatetopos` recipe.
4. Add add `my_topo.json` as a requirement for `testall` recipe.
5. Add `my_topo.json` at the end of the `topoautostandalonetest.py` line of the `testall` recipe.

### With generator script
1. Create a copy from an existing one, such as `topocreatesimpletree.py`.
2. Give your name to the copy, such as `topocreatemy.py`.
3. Edit your `topocreatemy.py` to the default value be the name you want, such as `my_topo`.
4. Edit `create_topo` on your `topocreatemy.py` to return the topology you want.
5. Add a recipe to `Makefile`:
<br>`my_topo.json:`
<br>&nbsp;&nbsp;&nbsp;&nbsp;`./topocreatemy.py`
6. Add that same last line to the end of `generatetopos` recipe.
7. Add add `my_topo.json` as a requirement for `testall` recipe.
8. Add `my_topo.json` at the end of the `topoautostandalonetest.py` line of the `testall` recipe.

## How to visualize the topology
Assumption: you already have a recipe for “`my_topo.json`” created and configured on the `Makefile`.
### For articles
- Run `make my_topo.pdf`.
### For presentations, with (almost) real-time updates
- Run `make viewer`.

Your topology will show on screen as soon as your controller starts up.

- About node color meaning:
- - Light green nodes are hosts.
- - Pink nodes are switches which weren't already initialized by the controller.
- - Cyan nodes are switches which were already initialized by the controller.
- About edge color meaning:
- - If the edge has its green channel on, that edge is connected to a switch which color is light red.
- - If the edge has its red channel on, that's the route OSPF would choose.
- - If the edge has its blue channel on, its intensity indicates what fraction of the traffic is being routed on there.
- The node labels indicates the fraction of the link that is being used. As all links are Full-Duplex links, it ranges from 0 to 2.

## Starting up the controller:
`ryu-manager latencycontroller.py my_topo.json`
