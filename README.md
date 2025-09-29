# emailparser
emailparser identifies and removes signature blocks from emails. 

## example
here is a sample email. we'd like to remove the last three lines, which correspond to the sender's email signature.
```
Wendy – thanks for the intro! Moving you to bcc.
 
Hi Vincent – nice to meet you over email. Apologize for the late reply, I was on PTO for a couple weeks and this is my first week back in office. As Wendy mentioned, I am leading an AR/VR taskforce at Foobar Retail Solutions. The goal of the taskforce is to better understand how AR/VR can apply to retail/commerce and if/what is the role of a shopping center in AR/VR applications for retail.
 
Wendy mentioned that you would be a great person to speak to since you are close to what is going on in this space. Would love to set up some time to chat via phone next week. What does your availability look like on Monday or Wednesday?
 
Best,
Joe Smith
 
Joe Smith | Strategy & Business Development
111 Market St. Suite 111| San Francisco, CA 94103
M: 111.111.1111| joe@foobar.com
```
after parsing, the email should look like this:
```
Wendy – thanks for the intro! Moving you to bcc.
 
Hi Vincent – nice to meet you over email. Apologize for the late reply, I was on PTO for a couple weeks and this is my first week back in office. As Wendy mentioned, I am leading an AR/VR taskforce at Foobar Retail Solutions. The goal of the taskforce is to better understand how AR/VR can apply to retail/commerce and if/what is the role of a shopping center in AR/VR applications for retail.
 
Wendy mentioned that you would be a great person to speak to since you are close to what is going on in this space. Would love to set up some time to chat via phone next week. What does your availability look like on Monday or Wednesday?
```

## getting started
1. Create and activate the virtual environment, then install dependencies and the spaCy model:

	```bash
	python3 -m venv venv
	source venv/bin/activate
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm
	```

	Alternatively, you can simply run:

	```bash
	source activate_env.sh
	```

	This script activates the bundled `venv/`, verifies that `numpy`, `spacy`, and the `en_core_web_sm` model are available, and prints the paths in use.

2. Run the parser against any email text file:

	```bash
	python -c "from Parser import convert; print(convert('emails/test0.txt'))"
	```

	The command prints the path to a new `*_clean.txt` file created alongside the input. The cleaned file omits detected signatures while preserving the message body and quoted threads.

3. (Optional) Remove generated files when you are done:

	```bash
	rm emails/*_clean.txt
	```