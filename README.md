p2pchan
=======

Peer-to-peer imageboard for cjdns. In it's current state it's incredibly broken and kinda sorta works.
It is likely one of the following two things will happen:

 * I will fix the brokeness and forget to update this
 * I will get bored with this and forget about the whole project in under a week.
 
Possibly both. Use at your own risk.


Installation
---------

1. Get the code:
```bash
git clone https://github.com/thefinn93/p2pchan
cd p2pchan
```
2. Get the dependency:

```bash
sudo pip install twisted
# OR
sudo easy_install twisted
# OR
sudo apt-get install python-twisted
# OR
(arch commad to install shit, i've been told the package is called twisted)
```
3. Make sure you have your `~/.cjdnsadmin` file in place. If you don't know how:
```bash
git clone https://gist.github.com/6086341.git    # Clone this gist
cd 6086341                                       # go into it
sudo python cjdnsadminmaker.py                   # Follow the prompts, if any
cd ..                                            # go back
rm -rf 6086341                                   # delete it as you'll likely not need it again
```

4. Run it:

```bash
python p2pchan.py
```
