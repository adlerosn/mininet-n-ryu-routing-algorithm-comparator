boxplots: __all__.autotests.json
	./topoboxplot.py __all__.autotests.json boxplots

testall: clos.json clos5.json grid.json simpletree.json fattree.json principle.json bipartite.json dcellswitched.json bcubeswitched.json
	./topoautostandalonetest.py 30 clos clos5 grid simpletree fattree principle bipartite dcellswitched bcubeswitched
	mn -c
	-rm -f *.state

__all__.autotests.json: testall
	@echo -n ""

testdcell:
	mn -c
	nohup ryu-manager latencycontroller.py dcellswitched.json&
	./topoautotest.py dcellswitched
	mn -c
	-rm -f nohup.out
	-rm -f dcellswitched.autotest.json

generatetopos:
	./topocreatedcell.py
	./topocreatedcellswitched.py
	./topocreatebcube.py
	./topocreatebcubeswitched.py
	./topocreatebig.py
	./topocreategrid.py
	./topocreatebipartite.py
	./topocreateclos.py
	./topocreateclos5.py
	./topocreatefattree.py
	./topocreatesimpletree.py
	./topomn2json.py principle

allpdfs: nopdfs clos.pdf clos5.pdf bigtopo.pdf grid.pdf simpletree.pdf fattree.pdf principle.pdf bipartite.pdf dcellswitched.pdf bcubeswitched.pdf dcell.pdf bcube.pdf
	@echo -n ""

nopdfs:
	rm -f clos.pdf clos5.pdf bigtopo.pdf grid.pdf simpletree.pdf fattree.pdf principle.pdf bipartite.pdf dcellswitched.pdf bcubeswitched.pdf dcell.pdf bcube.pdf
	rm -f *.pdf.bw.txt

%.pdf: %.json
	./toporenderpdfgraph.py $<
	pdfcrop $@ tmp.pdf
	mv tmp.pdf $@

dcell.json:
	./topocreatedcell.py

dcellswitched.json:
	./topocreatedcellswitched.py

bcube.json:
	./topocreatebcube.py

bcubeswitched.json:
	./topocreatebcubeswitched.py

bigtopo.json:
	./topocreatebig.py

grid.json:
	./topocreategrid.py

bipartite.json:
	./topocreatebipartite.py

clos.json:
	./topocreateclos.py

clos5.json:
	./topocreateclos5.py

fattree.json:
	./topocreatefattree.py

simpletree.json:
	./topocreatesimpletree.py

principle.json:
	./topomn2json.py principle
