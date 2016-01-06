filein = open('whatever.csv') #first input file
print (filein)

fileout = open('output_oclc.txt', 'w') #output file
print(fileout) 

import urllib.request  
a=[]
ar=[]

for q in filein:
    a.append(q.split(','))
for e in a:

    
    base_url = 'http://xissn.worldcat.org/webservices/xid/issn/'
    end_url = '?method=getForms&format=csv'
    url = base_url + e[5] + end_url    #e[] specifies field in input file containing issn to trigger xissn matched
    x = urllib.request.urlopen(url)
    ar.append('\r')
    ap='\t'.join([e[0],e[1],e[5],e[8]]) #list creation of fields from input file to be included in output file
    ar.append(ap)
    for t in x:
        t1 = str( t, encoding='utf8' )
        ar.append(t1.split('\r\n')[0][0:9])
    print(e[5])
    
fileout.write('\t'.join(ar)) 
fileout.close() 
filein.close()
