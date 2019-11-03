PY=python3

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
		pip install wheel; \
		pip install pyshp requests numpy shapely \
	)

srtm3: $(VENV_DIR) $(SRTM_SRC)
	. $(ACT_FILE); python3 $(SRTM_EXEC)

base: $(VENV_DIR) basemap_gen.py $(BASE_SRC)
	. $(ACT_FILE); python3 basemap_gen.py

elev: $(VENV_DIR) $(EXEV_SRC) srtm3
	. $(ACT_FILE); python3 $(ELEV_EXEC)

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

