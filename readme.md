when your only debugger is a log file, better add some extra-verbose traceback formatting (a bit of source context & the current local variables)


### Before:

```
Traceback (most recent call last):
  File "tracebacks.py", line 130, in some_function
    a_broken_function(thing)
  File "tracebacks.py", line 126, in a_broken_function
    raise Exception('something happened')
Exception: something happened

```
### After:

```
File tracebacks.py, line 129 in some_function
    127     def some_function(boing, zap='!'):
    128         thing = boing + zap
--> 129         a_broken_function(thing)
    ..................................................
       boing = 'hello'
       thing = 'hello!'
       zap = '!'
    ..................................................


File tracebacks.py, line 125 in a_broken_function
    117     def a_broken_function(thing, otherthing=1234):
       (...)
    120         # and various weird variables
    121         X = np.zeros((5, 5))
    122         X[0] = len(thing)
    123         for k in X:
    124             if np.sum(k) != 0:
--> 125                 raise Exception('something happened')
    ..................................................
       X = array([[6., 6., 6., 6., 6.],
                  [0., 0., 0., 0., 0.],
                  [0., 0., 0., 0., 0.],
                  [0., 0., 0., 0., 0.],
                  [0., 0., 0., 0., 0.]])
       k = array([6., 6., 6., 6., 6.])
       otherthing = 1234
       thing = 'hello!'
    ..................................................
Exception: something happened


```
