- make fixtures for two months

- add demo function to cli.py 

In order to insure that the database of two months dont get mixed with user database, we will separate them.
we will create demo_habits.db

Inside `demo_habits.db`, we will load two months worth of **fixtures**. We should make sure to cover edge cases.
The fixtures will exist in form of python dictionary inside `fixtures.py`
(we may or may not have helper functions inside fixtures.py to load them all at once into demo)

Inside `demo.py`, there will be demo click function that will have the following characteristics. 

`python cli.py demo` by default, if it doesnt find `demo_habits.db`, it will create it then load fixtures.
it has other an extra command called `python cli.py demo --reset`. This one will delete the old db 
and replace it with new one. The user can use it to reset his changes and test other things.

`python cli.py demo` also accepts every single function in cli.py. 
for example we can use it like this `python cli.py demo add "demo" -d "this was aded to demo" -p daily`
demo essentially is like a playground to test habits. 