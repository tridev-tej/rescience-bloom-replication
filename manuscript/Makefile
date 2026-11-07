.PHONY: all figures clean
RESULTS := ../replication/results
all: article.pdf

figures:
	python3 render_results.py $(RESULTS) generated
	rsvg-convert -f pdf -o generated/figure3.pdf $(RESULTS)/figure3.svg
	rsvg-convert -f pdf -o generated/figure4.pdf $(RESULTS)/figure4.svg

article.pdf: article.tex content.tex bibliography.bib metadata.tex rescience.cls header.tex figures
	xelatex -halt-on-error -interaction=nonstopmode article.tex
	biber article
	xelatex -halt-on-error -interaction=nonstopmode article.tex
	xelatex -halt-on-error -interaction=nonstopmode article.tex

metadata.tex: metadata.yaml yaml-to-latex.py article.py
	python3 yaml-to-latex.py -i metadata.yaml -o metadata.tex

clean:
	rm -f article.aux article.bbl article.bcf article.blg article.log article.out article.pdf article.run.xml metadata.tex
	rm -f generated/figure3.pdf generated/figure4.pdf generated/*.tex
