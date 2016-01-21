#Install a working python 3.5 environment

The following instructions will guide youthrough creating a fresh environment into which to install python 3.5, anaconda, numpy, pandas, matplotlib, and seaborn along with several modules that are commonly used at BU Libraries: pymarc, marcx, textblob, and gensim. The commands below should accomplish that.

This assumes you have installed anaconda.  

**source deactivate**

**conda create --name py3x python=3.5 anaconda numpy pandas matplotlib seaborn**

**source activate py3x**

**pip install https://github.com/edsu/pymarc/archive/python3.zip**

**pip install https://github.com/miku/marcx/archive/master.zip**

**pip install textblob**

**conda install gensim**





