obj=report

build/$(obj).pdf: $(obj).tex uc3mthesisIEEE.cls parts/* img/*
	latexmk -cd -pdflua -shell-escape $(obj).tex	
	mkdir -p build
	bash -c 'mv $$(ls | grep $(obj) | grep -v *.tex) build/'

clear_same_dir:
	bash -c 'rm $$( ls | grep $(obj) | grep -v *.tex)'

clear:
	rm -r build/

