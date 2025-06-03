obj=report
BUILD_DIR := build
LATEX_AUX_FILES := $(obj).aux $(obj).log $(obj).out $(obj).toc $(obj).lof $(obj).lot $(obj).gz $(obj).fls $(obj).fdb_latexmk $(obj).synctex.gz $(obj).nav $(obj).snm $(obj).vrb $(obj).nlo $(obj).nls $(obj).glo $(obj).ist $(obj).blg $(obj).bcf $(obj).run.xml

.PHONY: all clean clear_build clear_aux distclean

all: $(BUILD_DIR)/$(obj).pdf

$(BUILD_DIR)/$(obj).pdf: $(obj).tex uc3mthesisIEEE.cls parts/* img/* | $(BUILD_DIR) $(BUILD_DIR)/parts # Añade dependencia a build/parts
	latexmk -cd -g -pdflua -shell-escape -outdir=$(BUILD_DIR) $(obj).tex
	mv $(BUILD_DIR)/$(obj).pdf $(obj).pdf

# Crea el directorio de build si no existe
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Crea el directorio de build/parts si no existe
$(BUILD_DIR)/parts:
	mkdir -p $(BUILD_DIR)/parts

# Limpia solo el PDF y los auxiliares en el directorio de build
clean: clear_build

glosar: 
	cd $(BUILD_DIR) && \
	makeglossaries report
	make -B

clear_build:
	rm -f $(BUILD_DIR)/$(obj).pdf
	# Eliminar los archivos auxiliares en el directorio de build
	rm -f $(addprefix $(BUILD_DIR)/, $(LATEX_AUX_FILES))
	# Eliminar los archivos auxiliares que se puedan generar en build/parts
	rm -f $(addprefix $(BUILD_DIR)/parts/, $(obj).aux introduction.aux state_of_the_art.aux analysis.aux design.aux implementation.aux validation.aux planning.aux regulation.aux conclusions.aux manual.aux) # Ajusta esta lista

# Limpia los archivos auxiliares que podrían quedar en el directorio raíz (si no se usa -outdir)
clear_aux:
	rm -f $(LATEX_AUX_FILES)

# Limpia todo el directorio de build
distclean:
	rm -rf $(BUILD_DIR)