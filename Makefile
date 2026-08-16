.PHONY: install data run test clean

install:
	pip install -r requirements.txt

data:
	python preprocessing/preprocess.py --raw-dir data/raw --out-dir data

run:
	streamlit run streamlit_app.py

test:
	python all_pages_test.py

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
