# gpXmlMidi
A flexible postprocessor that converts Guitar Pro XML output to MIDI files.

## Prerequisites
gpXmlMidi requires Python 3.5+ and virtualenv.

### MacOS
```
$ xcode-select --install
$ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
$ brew install python3
$ pip3 install virtualenv
$ pip3 install virtualenvwrapper
$ make
```

## Usage
```
$ . local/bin/activate
$ ./converter
Usage: converter [-h/--help] [-v/--verbose] [-f/--force] [-p postprocessor] [-n/-normalize] XML-filename
```
