clean:
	rm -rf *.zip *.md *.json otter

# make name=example template
template:
	rm -f $(name).zip
	zip -r $(name).zip *.java test check

autograder:
	rm -f autograder.zip
	zip -r autograder.zip test setup.sh run_autograder
