"Bootstraps the doctest testing using tests.txt file"

import doctest,os,sys
sys.path.append(os.path.dirname(os.getcwd()))

doctest.testfile("tests.txt",verbose=True)
