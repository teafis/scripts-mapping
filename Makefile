PY=python3
PI=pip

VENV_DIR=venv
ACT_FILE=$(VENV_DIR)/bin/activate

BASE_EXEC = basemap_gen.py
BASE_SRC = $(BASE_EXEC) terrain_library.py

SRTM_EXEC = terrain_download.py
SRTM_SRC = $(SRTM_EXEC) terrain_library.py

ELEV_EXEC = terrain_basemap_from_srtm3.py
EXEV_SRC = $(ELEV_EXEC) terrain_download.py terrain_library.py terrain_hash_generator.py

all: base elev

$(VENV_DIR):
	$(PY) -m venv $(VENV_DIR)
	( \
		. $(ACT_FILE); \
		$(PI) install wheel; \
		$(PI) install pyshp requests numpy shapely \
	)

srtm3: $(VENV_DIR) $(SRTM_SRC)
	. $(ACT_FILE); $(PY) $(SRTM_EXEC)

base: $(VENV_DIR) $(BASE_SRC)
	. $(ACT_FILE); $(PY) $(BASE_EXEC)

elev: $(VENV_DIR) $(ELEV_SRC) srtm3
	. $(ACT_FILE); $(PY) $(ELEV_EXEC)

clean-venv:
	rm -rf venv

clean-base:
	rm -rf output/*.dat

clean-elev:
	rm -rf output/*.hgt

clean-srtm3:
	rm -rf srtm3

clean: clean-venv clean-base clean-elev clean-srtm3
	rm -rf output

.PHONY: base elev clean-venv clean-base clean-elev clean-srtm3 clean

