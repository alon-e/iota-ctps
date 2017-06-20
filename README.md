# iota-ctps
This tool is used to analyze IOTA tangle.

parsing transaction files exported from IRI, iota-ctps calculates a wide set of metrics.

### Install:
```
git clone ...
cd iota-ctps
sudo python setup.py install
```
you may also need to run:
```
sudo pip install pyota
```
if you are missing `ffi` run - `sudo apt-get install libffi libffi-dev`

### Features:
##### Live feed:
historical & current data is accumulated:
```
'timestamp', 
'Total Tx.', 
'Confirmed Tx.', 
'Conf. rate', 
'TPS', 
'CTPS', 
'Tangle width',
'avg. confirmation time', 
'all-time avg. TPS', 
'all-time avg. CTPS', 
'max TPS', 
'max CTPS'
```

##### Tangle width:
Tangle width can be plotted, together with confirmed transactions.

```
milestone: # confirmed: * unconfirmed_non_tips: = unconfirmed_tips: + 

  35729    1                        =
  35728   12                        ===========+
  35727    8                        =======+
  35726    8                        ======++
  35725    8                        ========
  35724   11                        =========++
  35723   15                        ===========++++
  35722   19                        ==================+
  35721   19                        **==============+++
  35720   19                        **================+
  35719   26 [#75669  / 1497782545] #***=====================+
  35718   20                        *****=============++
  35717   28 [#75668  / 1497782498] #**********==============+++
  35716   23                        ***************========
  35715   23 [#75667  / 1497782430] #***************=======
  35714   27                        **********************==+++
  35713   28 [#75666  / 1497782376] #***********************++++
  35712   27                        ************************+++
  35711   21 [#75665  / 1497782310] #******************++
  35710   19                        ******************+
  35709   27 [#75664  / 1497782256] #*********************+++++

```

##### Push feed to API end-point and slack channel.

##### Export exact confirmation time for all transactions. 

-------

### Usage:
```
Usage:
  ctps.py [-e DIR] [-i INTERVAL] [options]


  Options:
      -h --help                                 show this help message and exit
      --version                                 show version and exit
      --testnet                                 sets Coordinator address to testnet Coo
      -e DIR --export_folder=DIR                export folder
      -i INTERVAL --interval=INTERVAL           sampling interval [default: 30]
      --auth_key=AUTH_KEY                       authentication key for url api endpoint
      --url=URL                                 url api endpoint
      --slack_key=SLACK_KEY                     slack token
      --width                                   calculate & plot width histogram
      --poisson                                 calculate & plot confirmation time distribution

      --prune                                   prune confirmed transactions
      
```

